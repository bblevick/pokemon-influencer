#!/usr/bin/env python3
"""Audit recorded SOCIAL live acceptance; this does not run a new playthrough."""
import hashlib,json
from social01 import ROOT,E,offline_store,snapshot,save_identity,RICK,JANICE,DOUG

def main():
    checks=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(name)
    def read(name):return json.loads((E/(name+'.json')).read_text())
    a=read('publication-live');f=read('feed-unread');x=read('exposure-live');s=x['snapshot']
    r=read('restored-s2-unread');b=read('social-only-divergence')['snapshot'];old=read('restored-s1');c=read('s1-divergent-empty-tick');end=read('s3-positive-reload')
    post=next(iter(a['social']['posts']));p=a['social']['posts'][post];battle=p['battleID'];branch=a['campaign']['active_branch']
    check('unchanged B3 ROM',a['romSHA256']=='739bd3eebb91aaa5210f8f8cd1f357a8272dc98db7060356c649b4c38a0dbc2d')
    check('actual ROM binary',hashlib.sha256((ROOT/'.local/phase1-ui-enabled/pokefirered.gba').read_bytes()).hexdigest()==a['romSHA256'])
    check('new battle distinct from MEMORY run',battle!=json.loads((ROOT/'evidence/phase2/memory01/rick-live.json').read_text())['rick']['directObservations'][0]['claim']['battleID'])
    claims={q['claim']['type']:q['claim'] for q in a['rick']['directObservations']}
    for typ in ['BATTLE_PARTICIPATION','TRAINER_BATTLE_RESULT','POKEMON_SEEN','MOVE_REVEALED']:check('Rick actual '+typ,typ in claims)
    check('actual loss outcome',claims['TRAINER_BATTLE_RESULT']['nativeOutcome']==1)
    check('actual Bulbasaur',claims['POKEMON_SEEN']['speciesID']==1)
    check('actual Tackle',claims['MOVE_REVEALED']['moveID']==33)
    check('new ingestion counts',a['counts']==dict(events=27,observations=8,memory_evidence=25,social_log=9))
    check('one first follow',a['playerFollowerCount']==1)
    check('one recap and pending job',len(a['social']['posts'])==len(a['social']['pending'])==1)
    check('publication no feed/exposure',not a['social']['feeds'] and not a['social']['exposures'])
    edges=list(a['social']['follows'].values())
    check('authored Janice->Rick distinct from Rick->player',any(e['follower']==JANICE and e['followed']==RICK and e['cause']=='authored_vertical_slice' for e in edges) and any(e['follower']==RICK and e['followed'].startswith('player:') and e['cause']=='first_confirmed_eligible_win' for e in edges))
    check('deterministic exact text',p['body']=='I lost to the player. I saw BULBASAUR.')
    check('exact published subset',p['claims']==[claims['TRAINER_BATTLE_RESULT'],claims['POKEMON_SEEN']])
    check('no Tackle in published body/claims','moveID' not in json.dumps(p['claims']) and 'TACKLE' not in p['body'])
    check('policy/template1 and bound sources',p['policyVersion']==p['templateVersion']==1 and len(p['evidenceIDs'])==2 and p['contextMemoryCutoff']==25 and p['contextWorldCursor']==27)
    for name,z in [('publication',a),('unread feed',f),('restored unread',r)]:
        check(name+' Janice no knowledge',not z['janice']['directObservations'] and not z['janice']['deliveries'])
        check(name+' Doug no knowledge',not z['doug']['directObservations'] and not z['doug']['deliveries'])
    check('one unread feed, completed job',len(f['social']['feeds'])==1 and not f['social']['pending'] and not f['social']['exposures'] and f['janiceFeedMetadata'][0]['seen'] is False)
    check('feed metadata no content',set(f['janiceFeedMetadata'][0])=={'postID','author','seen','channel'})
    for name,z in [('exposure',s),('divergent exposure',b),('original positive reload',end)]:
        check(name+' exactly two reported claims',not z['janice']['directObservations'] and len(z['janice']['deliveries'])==2 and {q['claim']['type'] for q in z['janice']['deliveries']}=={'TRAINER_BATTLE_RESULT','POKEMON_SEEN'})
        check(name+' no omitted move','moveID' not in json.dumps(z['janice']))
        check(name+' attribution',all(q['mode']=='delivered' and q['sender']==RICK and q['attribution']=={'kind':'reported_post','postID':post,'author':RICK,'channel':'pokebook'} for q in z['janice']['deliveries']))
        check(name+' Doug empty',not z['doug']['directObservations'] and not z['doug']['deliveries'])
        check(name+' feed seen',z['janiceFeedMetadata'][0]['seen'] is True)
    for n,chain in enumerate(x['recipientProvenance']):
        check('public lineage stops '+str(n),len(chain)==1 and chain[0]['mode']=='delivered')
        check('private lineage removed '+str(n),'parentMemoryID' not in json.dumps(chain) and 'turnID' not in json.dumps(chain) and 'evidenceIDs' not in json.dumps(chain))
    check('public post cannot traverse sources','evidenceIDs' not in x['publicPost'] and 'contextMemoryCutoff' not in x['publicPost'])
    for name in ['host-reopen','idempotent-retry']:
        z=read(name)
        check(name+' counts/IDs identical',z['counts']==s['counts'] and z['social']==s['social'] and z['rick']==s['rick'] and z['janice']==s['janice'])
    check('unread restore excludes exposure',not r['social']['exposures'] and r['social']==f['social'] and r['campaign']['pending_fork']==1)
    check('social-only child without canonical event',b['campaign']['active_branch']!=branch and b['campaign']['cursor']==27 and b['counts']['events']==27 and b['counts']['observations']==8)
    check('social-only receipts have distinct IDs',next(iter(b['social']['exposures'].values()))['memoryIDs']!=x['exposure']['memoryIDs'])
    for name,z in [('prebattle restore',old),('prebattle divergent tick',c)]:
        check(name+' no new follow',z['playerFollowerCount']==0 and len(z['social']['follows'])==1)
        check(name+' no future social objects',all(not z['social'][k] for k in ('posts','pending','feeds','exposures','outcomes','proposals')))
        check(name+' no future memories',not z['rick']['directObservations'] and not z['janice']['deliveries'])
        check(name+' canonical cutoff zero',z['campaign']['cursor']==0)
    check('empty tick forks at canonical zero',c['campaign']['active_branch']!=branch)
    check('original later checkpoint intact',end['campaign']['active_branch']==branch and end['social']==s['social'] and end['janice']==s['janice'] and end['rick']==s['rick'])
    launches=[json.loads(l) for l in (E/'launches.jsonl').read_text().splitlines()]
    check('four fresh managed launches',len(launches)==4 and len({l['nonce'] for l in launches})==4 and len({l['origin'] for l in launches})==4)
    check('native launch counters sequence',[l['save']['counter'] for l in launches]==[6,8,7,9])
    check('same ROM all launches',all(l['romSHA256']==a['romSHA256'] and not l['credentialsUsed'] for l in launches))
    host=[json.loads(l) for l in (E/'host.jsonl').read_text().splitlines()]
    check('real host opens and reconnect',sum(l['event']=='host-open' for l in host)>=5 and sum(l['event']=='hello' for l in host)>=5)
    for name in ['exposure-offline-replay','divergent-offline-replay','final-offline-replay']:check(name,read(name)['passed'])
    check('regressions passed',read('regressions/results')['passed'])
    with offline_store(ROOT/'.local/social01/world.sqlite3') as w:
        current=snapshot(w);check('final SQLite view matches recorded reload',current==end)
        for name,counter,world,memory,social in [('S1',7,0,0,4),('S2',8,27,25,12),('S3',9,27,27,13)]:
            identity=save_identity(ROOT/('.local/social01/'+name+'.sav'));cp=w.get_save_checkpoint(identity.fingerprint)
            check(name+' native paired checkpoint',cp['kind']=='normal_save' and identity.counter==counter and cp['cursor']==world and cp['branch']==branch)
            check(name+' memory cutoff',w._one('SELECT cutoff FROM memory_checkpoints WHERE checkpoint=?',(cp['id'],))['cutoff']==memory)
            check(name+' social cutoff',w._one('SELECT cutoff FROM social_checkpoints WHERE checkpoint=?',(cp['id'],))['cutoff']==social)
        for name,z,parent_m,parent_s in [('B',b,25,12),('C',c,0,4)]:
            child=z['campaign']['active_branch'];row=w._one('SELECT * FROM branches WHERE id=?',(child,))
            check(name+' parent branch preserved',row['parent']==branch)
            check(name+' memory parent boundary',w._one('SELECT parent_cutoff FROM memory_branches WHERE branch=?',(child,))['parent_cutoff']==parent_m)
            check(name+' social parent boundary',w._one('SELECT parent_cutoff FROM social_branches WHERE branch=?',(child,))['parent_cutoff']==parent_s)
        check('full immutable history retained',current['counts']==dict(events=27,observations=8,memory_evidence=29,social_log=15))
        check('no pending save/battle/job',not w.pending_save() and not current['social']['pending'] and all(b['ended'] for b in w.state()['battles'].values()))
        for source,claim in zip(p['evidenceIDs'],p['claims']):
            row=w._one('SELECT * FROM memory_evidence WHERE id=?',(source,))
            check('post bound Rick source '+claim['type'],row['actor']==RICK and row['mode']=='direct' and json.loads(row['claim'])==claim)
        for receipt,source in zip(x['exposure']['memoryIDs'],p['evidenceIDs']):
            row=w._one('SELECT * FROM memory_evidence WHERE id=?',(receipt,))
            check('internal lineage '+receipt,row['parent']==source and row['actor']==JANICE and row['sender']==RICK and row['source_id']==post and row['channel']=='pokebook')
            check('Janice private traversal denied '+source,denied(lambda:w.for_actor(JANICE).provenance(source)))
        check('Doug post exposure denied',denied(lambda:w.for_social_actor(DOUG).expose(post)))
        check('Doug content denied',denied(lambda:w.for_social_actor(DOUG).read_post(post)))
    result={'passed':True,'checks':checks,'checkCount':len(checks),'scope':'recorded new SOCIAL live acceptance plus offline/retained verification; not a new playthrough'}
    (E/'emulator-integration.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

def denied(fn):
    from world.store import WorldError
    try:fn()
    except WorldError:return True
    return False
if __name__=='__main__':main()
