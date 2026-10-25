"""Pure source-bound distribution and evidence descriptors (no world mutation)."""
import copy
from collections import deque
from memory.store import digest
from world.store import WorldError, dump, ROOT

KINDS = {'ordinary','gym','rival','elite_four','champion','rocket_leader'}
OBSERVED = {'BATTLE_PARTICIPATION','TRAINER_BATTLE_RESULT','POKEMON_SEEN','MOVE_REVEALED','ITEM_USE_OBSERVED'}


def validate(config, registry):
    if config['version'] != 1 or config['sourceCommit'] != registry['sourceCommit'] or config['registrySHA256'] != registry['catalogSHA256']:
        raise WorldError('virality source/config version mismatch')
    for key,maximum in (('maxPostsPerTick',16),('maxAudience',580),('maxEvidenceContext',256),('maxExposuresPerTick',580),('maxIntelPerTick',580)):
        if type(config[key]) is not int or not 1 <= config[key] <= maximum:raise WorldError('virality work bounds')
    previous = (-1, -1, -1)
    for band in config['reachBands']:
        current = (band['minFollowers'], band['budget'], band['window'])
        if any(type(x) is not int or x < 0 for x in current) or any(a > b for a,b in zip(previous,current)) or current[0] == previous[0]:
            raise WorldError('nonmonotonic follower reach policy')
        previous = current
    if config['reachBands'][0]['minFollowers'] != 0 or not 1 <= config['maxPostsPerTick'] <= 16 or not 1 <= config['maxAudience'] <= 580:
        raise WorldError('virality bounds')
    classes={'TRAINER_CLASS_LEADER':'gym','TRAINER_CLASS_RIVAL_EARLY':'rival','TRAINER_CLASS_RIVAL_LATE':'rival','TRAINER_CLASS_ELITE_FOUR':'elite_four','TRAINER_CLASS_CHAMPION':'champion','TRAINER_CLASS_BOSS':'rocket_leader'}
    expected={str(s['sourceID']):classes.get(s['class'],'ordinary') for x in registry['trainers'].values() for s in x['sourceRecords']}
    if config['sourceActors'] != {s:'trainer:'+a for s,a in registry['mapping'].items()}:raise WorldError('untrusted native actor binding')
    if config['eventKinds'] != expected:raise WorldError('untrusted event prominence binding')
    for band in config['reachBands']+[config['highProfile']]:
        if not 0 <= band['budget'] <= config['maxAudience'] or not 0 <= band['window'] <= 32:raise WorldError('reach bounds')
    stages = {p['stageID'] for p in config['progression']}
    expected_stages={}
    map_stages={p['source'].replace('map.json','scripts.inc'):p['stageID'] for p in config['progression']}
    map_ids={p['mapID']:p['stageID'] for p in config['progression']}
    for actor in registry['trainers'].values():
        for source in actor['sourceRecords']:
            stage=next((map_stages[x] for x in source['scripts'] if x in map_stages),None)
            family=actor['rematchFamily']
            if stage is None and family and family['kind']=='vs_seeker':stage=map_ids.get(family['map'])
            expected_stages[str(source['sourceID'])]=stage
    if config['encounterStages'] != expected_stages:raise WorldError('untrusted native encounter stage binding')
    for actor, p in config['profiles'].items():
        entry = registry['trainers'].get(actor.removeprefix('trainer:') if hasattr(actor,'removeprefix') else actor[8:])
        if not actor.startswith('trainer:') or not entry or p['sourceTrainerIDs'] != [s['sourceID'] for s in entry['sourceRecords']] or p['sourceClass'] != entry['sourceRecords'][0]['class']:
            raise WorldError('untrusted actor classification')
        if p['prominence'] not in KINDS or p['rocketRole'] not in ('none','member','leader') or p['encounterStage'] not in stages | {None}:
            raise WorldError('actor policy bounds')
    for p in config['progression']:
        import json
        data = json.loads((ROOT / p['source']).read_text())
        groups = json.loads((ROOT / 'data/maps/map_groups.json').read_text())
        name = data['name'] if 'name' in data else p['source'].split('/')[-2]
        if data['id'] != p['mapID'] or groups[groups['group_order'][p['mapGroup']]][p['mapNumber']] != name:
            raise WorldError('campaign map source mismatch')
    return config


def profile(config, actor):
    return config['profiles'].get(actor, {'encounterStage':None,'scouting':None,'prominence':'ordinary','rocketRole':'none'})


def stage_order(config, stage):
    return next((p['order'] for p in config['progression'] if p['stageID'] == stage), None)


def distance(config, origin, recipient):
    a,b=stage_order(config,origin),stage_order(config,profile(config,recipient)['encounterStage'])
    return abs(a-b) if a is not None and b is not None else None


def active_edges(edges):
    # Branch/cursor filtering belongs to the scoped store before this pure call.
    return sorted({(e['follower'],e['followed']) for e in edges if e.get('active',True)})


def follower_count(player, edges, known_actors):
    return len({a for a,b in active_edges(edges) if b == player and a in known_actors and a != player})


def social_path(source, recipient, edges):
    graph={}
    for a,b in active_edges(edges):
        graph.setdefault(a,set()).add(b);graph.setdefault(b,set()).add(a)
    todo=deque([(source,[source])]);seen={source}
    while todo:
        actor,path=todo.popleft()
        if actor == recipient:return path
        if len(path) >= 16:continue
        for child in sorted(graph.get(actor,())):
            if child not in seen:seen.add(child);todo.append((child,path+[child]))
    return None


def plan(config, *, player, post, edges, known_actors, post_order):
    author=post['author'];p=profile(config,author)
    origin=config['encounterStages'].get(str(post['sourceTrainerID'])) if post.get('sourceTrainerID') is not None else p['encounterStage']
    count=follower_count(player,edges,known_actors)
    band=next(b for b in reversed(config['reachBands']) if count >= b['minFollowers'])
    if post.get('sourceTrainerID') is not None and config['sourceActors'].get(str(post['sourceTrainerID'])) != author:raise WorldError('post encounter source/author mismatch')
    prominence=config['eventKinds'].get(str(post.get('sourceTrainerID')),p['prominence'])
    reach=config['highProfile'] if prominence != 'ordinary' else band
    receipts={}
    def add(actor,reason):
        if actor == author or actor not in known_actors:return
        receipts[actor]={'recipient':actor,'postID':post['postID'],'reason':reason,'originStage':origin,'recipientStage':profile(config,actor)['encounterStage'],'campaignDistance':distance(config,origin,actor),'socialPath':social_path(author,actor,edges),'publicationOrder':post_order,'sourceActor':author,'channel':'pokebook','prominence':prominence}
    if post['visibility']=='public':
        for actor,followed in active_edges(edges):
            if followed == author:add(actor,'direct_follower')
        for actor in sorted(known_actors):
            if profile(config,actor)['scouting']:add(actor,'chronically_online')
        candidates=[]
        for actor in known_actors:
            d=distance(config,origin,actor)
            if actor == author or actor in receipts:continue
            if d is None:
                if prominence == 'ordinary' or profile(config,actor)['encounterStage'] is None:continue
                d=999 # Qualified high-profile discovery needs no fabricated origin.
            elif d > reach['window']:continue
            path=social_path(author,actor,edges)
            candidates.append((d,len(path) if path else 999,actor))
        for _,_,actor in sorted(candidates)[:reach['budget']]:add(actor,'ordinary_discovery' if prominence=='ordinary' else 'high_profile_discovery')
    if len(receipts) > config['maxAudience']:raise WorldError('qualified audience exceeds explicit bound')
    return {'followerCount':count,'reachBand':band['id'],'reach':copy.deepcopy(reach),'originStage':origin,'prominence':prominence,'deliveries':[receipts[k] for k in sorted(receipts)]}


def quality(*, mode, source_actor, channel, origin_stage, campaign_distance, path, reason, publication_order, latest_order, independent_origins=1, original_source_actor=None):
    degree=len(path)-1 if path else None
    if mode=='direct':band='DIRECT'
    elif channel=='ROCKET_INTEL' or reason in ('chronically_online','direct_follower'):band='HIGH'
    elif degree is not None and degree <= 1:band='HIGH'
    elif degree is not None and degree > 3:band='LOW'
    else:band='MODERATE'
    lag=max(0,latest_order-publication_order)
    if campaign_distance is None:relevance='OLDER'
    elif campaign_distance <= 1 and lag <= 1:relevance='CURRENT'
    elif campaign_distance <= 3 and lag <= 4:relevance='RECENT'
    else:relevance='OLDER'
    return {'version':1,'sourceActor':source_actor,'originalSourceActor':original_source_actor or source_actor,'channel':channel,'attribution':'direct' if mode=='direct' else 'reported','sourceQuality':band,'currentRelevance':relevance,'originStage':origin_stage,'campaignDistance':campaign_distance,'socialDegree':degree,'path':path,'publicationOrder':publication_order,'publicationLag':lag,'independentOriginCount':independent_origins,'organizationalFidelity':'full_observed_claim' if channel=='ROCKET_INTEL' else None}


def rocket_intelligence(config, *, member, leader, records, campaign, branch):
    """Trusted observation adapter input, not a model/NPC tool. Never prose."""
    if profile(config,member)['rocketRole'] != 'member' or profile(config,leader)['rocketRole'] != 'leader':
        raise WorldError('Rocket membership/leadership required')
    result=[]
    for r in records:
        if r['actorID'] != member or r['campaignID'] != campaign or r['branchID'] != branch or r['mode'] != 'direct':
            raise WorldError('Rocket observation scope/ownership')
        claim=r['claim']
        fields={'BATTLE_PARTICIPATION':set(), 'TRAINER_BATTLE_RESULT':{'nativeOutcome'},'POKEMON_SEEN':{'speciesID'},'MOVE_REVEALED':{'speciesID','moveID'},'ITEM_USE_OBSERVED':{'itemID'}}
        if claim.get('type') not in fields or set(claim) != {'type','battleID','trainerID'} | fields[claim['type']]:
            raise WorldError('unsupported or hidden observation fields')
        if not r.get('memoryID') or not claim['battleID']:raise WorldError('observation provenance required')
        result.append({'sourceMemoryID':r['memoryID'],'sourceActor':member,'recipient':leader,'campaignID':campaign,'branchID':branch,'claim':copy.deepcopy(claim),'channel':'ROCKET_INTEL'})
    return result
