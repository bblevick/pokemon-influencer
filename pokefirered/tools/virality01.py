#!/usr/bin/env python3
"""Reproduce host VIRALITY proofs using a private copy of accepted native history.

No emulator is launched and no model is contacted. Fixture save proofs are in
unittest; this command demonstrates original real Rick post -> prebattle Brock.
"""
import argparse,hashlib,json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from virality.store import ViralityPuppeteerStore
from virality import policy
from strategy.social_context import build_social_evidence
from world.saves import SaveIdentity
from world.store import dump


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,default=ROOT/'.local/hermes01/acceptance-closeout.sqlite3');parser.add_argument('--destination',type=Path,default=ROOT/'.local/virality01/world.sqlite3');args=parser.parse_args()
    source=args.source.resolve();dest=args.destination.resolve();evidence=ROOT/'evidence/phase4/virality01';evidence.mkdir(parents=True,exist_ok=True)
    if dest==source or dest.exists():raise ValueError('destination must be a fresh private database')
    if (ROOT/'.local') not in dest.parents:raise ValueError('private destination required')
    # This accepted closeout is closed and WAL-free. Never copy a live WAL base.
    if Path(str(source)+'-wal').exists():raise ValueError('source must be a closed WAL-free accepted snapshot')
    before=sha(source);dest.parent.mkdir(parents=True,exist_ok=True)
    read=sqlite3.connect(source.as_uri()+'?mode=ro&immutable=1',uri=True);write=sqlite3.connect(dest);read.backup(write);read.close();write.close()
    db=sqlite3.connect(dest);meta={k:json.loads(v) for k,v in db.execute('SELECT * FROM metadata')};db.close()
    rick='trainer:fr:trainer:0102';brock='trainer:fr:trainer:0414';checks=[]
    def check(name,value):
        if not value:raise AssertionError(name)
        checks.append(name)
    with ViralityPuppeteerStore(dest,meta['build'],meta['tag']) as store:
        canonical=store.verify_replay();legacy=dump(store.social_state());pp=store.verify_puppeteer_replay();store.verify_memory_replay()
        check('Brock has never encountered player',store.get_trainer('fr:trainer:0414')['facts'] is None)
        posts=[p for p in store.social_state()['posts'].values() if p['author']==rick and p['visibility']=='public'];check('active actual Rick public recap',len(posts)==1);post=posts[0]
        check('confirmed real source battle',store.get_battle(post['battleID'])['ended'] and store.get_battle(post['battleID'])['sourceTrainerID']==102)
        check('private observed Tackle retained',any(r['claim'].get('moveID')==33 for r in store.for_actor(rick).records()['records']))
        check('Tackle omitted publicly',all('moveID' not in c for c in post['claims']))
        store.activate_virality();store.advance_social('publication',expose=False)
        check('scouting access precedes knowledge',any(f['postID']==post['postID'] and not f['seen'] for f in store.public_feed(brock)) and not store.for_actor(brock).context()['deliveries'])
        unread=store.public_feed(brock);store.advance_social('exposure');packet=build_social_evidence(store,brock)
        check('Brock has exactly published claims',sorted(dump(r['claim']) for r in packet['authorizedFacts'])==sorted(map(dump,post['claims'])))
        check('Brock is not direct observer',not store.for_actor(brock).context()['directObservations'])
        check('original public source HIGH',all(r['evidenceQuality']['sourceQuality']=='HIGH' and r['evidenceQuality']['channel']=='pokebook' for r in packet['authorizedFacts']))
        check('no omitted move or hidden facts','moveID' not in dump(packet) and 'hiddenParty' not in dump(packet))
        check('no private provenance traversal',all(len(store.for_actor(brock).provenance(r['evidenceID']))==1 for r in packet['authorizedFacts']))
        check('no fake scout follow',not any(e['follower']==brock for e in store.social_state()['follows'].values()))
        check('legacy social history unchanged',legacy==dump(store.social_state()));check('canonical history unchanged',canonical==store.verify_replay());check('director episodes unchanged',pp==store.verify_puppeteer_replay())
        state=store.virality_state();memory=store._maximum();store.advance_social('exposure');check('idempotent repeated tick',state==store.virality_state() and memory==store._maximum())
        viralsha=store.verify_virality_replay();scope=store.virality_scope();snap={'source':'accepted HERMES-01 native history copied read-only; no new playthrough','sourceDatabaseSHA256':before,'sourcePath':str(source.relative_to(ROOT)),'campaign':store.campaign(),'publicPost':{k:post[k] for k in ('postID','author','battleID','claims','body')},'unreadBrockFeed':unread,'brockStrategyContext':packet,'epoch':next(iter(state['epochs'].values())),'viralityReplaySHA256':viralsha}
        checkpoint=store._one('SELECT save_identity FROM checkpoints ORDER BY cursor DESC LIMIT 1');paired=SaveIdentity(**json.loads(checkpoint['save_identity']))
    with ViralityPuppeteerStore(dest,meta['build'],meta['tag']) as store:
        check('fresh host retains same scoped packet',packet==build_social_evidence(store,brock));check('fresh host replay',viralsha==store.verify_virality_replay())
        store.restore(paired);check('old native pair excludes later virality adoption',not store.virality_state()['exposures'] and not store.for_actor(brock).context()['deliveries'])
        try:store.advance_social('publication',expected_scope=scope)
        except ValueError:checks.append('pre-restore diffusion grant rejected')
        else:raise AssertionError('stale grant accepted')
    check('original database byte-identical',sha(source)==before)
    (evidence/'brock-production.json').write_text(json.dumps(snap,indent=2)+'\n')
    config=json.loads((ROOT/'config/virality_policy.json').read_text());registry=json.loads((ROOT/'config/trainer_registry.json').read_text());actors={'trainer:'+w for w in registry['trainers']}
    # Explicitly synthetic follower populations, never inserted into production.
    follower_proofs=[]
    for count in (0,5,20):
        edges=[{'follower':a,'followed':'player:fixture'} for a in sorted(actors)[:count]]
        p=policy.plan(config,player='player:fixture',post={'postID':'fixture-rick-post','author':rick,'visibility':'public','sourceTrainerID':102},edges=edges,known_actors=actors,post_order=1)
        follower_proofs.append({'fixture':True,'requestedFollowerCount':count,**p})
    (evidence/'follower-fixtures.json').write_text(json.dumps(follower_proofs,indent=2)+'\n')
    prominence=[]
    for kind in ('ordinary','gym','rival','elite_four','champion','rocket_leader'):
        source_id=next(s for s,k in config['eventKinds'].items() if k==kind and (kind!='ordinary' or s=='102'))
        author=config['sourceActors'][source_id]
        planned=policy.plan(config,player='player:fixture',post={'postID':'fixture-'+kind,'author':author,'sourceTrainerID':int(source_id),'visibility':'public'},edges=[],known_actors=actors,post_order=1)
        prominence.append({'fixture':True,'sourceTrainerID':int(source_id),'author':author,**planned})
    (evidence/'prominence-fixtures.json').write_text(json.dumps(prominence,indent=2)+'\n')
    member=next(a for a,p in config['profiles'].items() if p['rocketRole']=='member' and p['encounterStage']=='mtmoon');leader=next(a for a,p in config['profiles'].items() if p['rocketRole']=='leader')
    claims=[{'type':'POKEMON_SEEN','speciesID':1},{'type':'MOVE_REVEALED','speciesID':1,'moveID':33},{'type':'POKEMON_SEEN','speciesID':17},{'type':'ITEM_USE_OBSERVED','itemID':13}]
    records=[{'actorID':member,'campaignID':'fixture-campaign','branchID':'fixture-branch','mode':'direct','memoryID':'fixture-direct-'+str(i),'claim':{'battleID':'fixture-rocket-battle','trainerID':member[8:],**c}} for i,c in enumerate(claims)]
    rocket=policy.rocket_intelligence(config,member=member,leader=leader,records=records,campaign='fixture-campaign',branch='fixture-branch')
    (evidence/'rocket-fixture.json').write_text(json.dumps({'fixture':True,'nativeItemObservationExportQualified':False,'observations':records,'publicClaims':[records[0]['claim']],'internalIntelligence':rocket},indent=2)+'\n')
    (evidence/'production-checks.json').write_text(json.dumps({'checks':checks,'count':len(checks),'hostedCalls':0,'newEmulatorRuns':0,'newROMSaves':0,'originalProtected':True},indent=2)+'\n')
    print(json.dumps({'productionChecks':len(checks),'evidence':str(evidence.relative_to(ROOT)),'hostedCalls':0}))

if __name__=='__main__':main()
