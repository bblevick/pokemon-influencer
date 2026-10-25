"""Deterministic host fixtures. No ROM, cloud, or live gameplay claims."""
import copy,json,sqlite3,tempfile,unittest
from pathlib import Path
from world.store import ROOT,WorldError,dump
from world.saves import fingerprint
from memory.store import actor_id
from social.store import SocialStore
from virality.store import ViralityStore
from virality import policy
from strategy.social_context import build_social_evidence
from test_world01 import BUILD,TAG,SIZES,flash,msg
from test_memory01 import visible,RICK,JANICE

BROCK=actor_id('fr:trainer:0414');DOUG=actor_id('fr:trainer:0103');SALLY=actor_id('fr:trainer:0117')
CONFIG=json.loads((ROOT/'config/virality_policy.json').read_text());REGISTRY=json.loads((ROOT/'config/trainer_registry.json').read_text())
ACTORS={'trainer:'+x for x in REGISTRY['trainers']}
MEMBER=next(a for a,p in CONFIG['profiles'].items() if p['rocketRole']=='member')
LEADER=next(a for a,p in CONFIG['profiles'].items() if p['rocketRole']=='leader')

class PolicyTests(unittest.TestCase):
    def plan(self,count=0,author=RICK,edges=None):
        if edges is None:edges=[{'follower':a,'followed':'player:fixture'} for a in sorted(ACTORS)[:count]]
        post={'postID':'fixture-post','author':author,'visibility':'public'}
        return policy.plan(CONFIG,player='player:fixture',post=post,edges=edges,known_actors=ACTORS,post_order=1)

    def test_source_bindings(self):policy.validate(CONFIG,REGISTRY)
    def test_monotonic_reach_and_far_actor(self):
        values=[self.plan(n) for n in (0,5,20)]
        audiences=[{r['recipient'] for r in p['deliveries']} for p in values]
        self.assertTrue(audiences[0] <= audiences[1] <= audiences[2]);self.assertIn(DOUG,audiences[0]);self.assertNotIn(SALLY,audiences[0]);self.assertIn(SALLY,audiences[2])
        self.assertEqual([p['reachBand'] for p in values],['local','district','regional'])
    def test_duplicate_inactive_unknown_followers(self):
        edges=[{'follower':RICK,'followed':'player:fixture'}]*2+[{'follower':DOUG,'followed':'player:fixture','active':False},{'follower':'fake','followed':'player:fixture'}]
        self.assertEqual(self.plan(edges=edges)['followerCount'],1)
    def test_direct_follow_override(self):
        self.assertIn(SALLY,{r['recipient'] for r in self.plan(edges=[{'follower':SALLY,'followed':RICK}])['deliveries']})
    def test_all_prominent_classes(self):
        ordinary=len(self.plan()['deliveries'])
        for kind in ('gym','rival','elite_four','champion','rocket_leader'):
            source_id=next(int(s) for s,k in CONFIG['eventKinds'].items() if k==kind)
            author=actor_id(REGISTRY['mapping'][str(source_id)])
            # Unknown later campaign origin does not authorize arbitrary discovery.
            cfg=copy.deepcopy(CONFIG)
            value=policy.plan(cfg,player='player:fixture',post={'postID':'p','author':author,'visibility':'public','sourceTrainerID':source_id},edges=[],known_actors=ACTORS,post_order=1)
            self.assertEqual(value['prominence'],kind);self.assertGreater(len(value['deliveries']),ordinary)
    def test_all_scout_classes_no_follows(self):
        recipients={r['recipient'] for r in self.plan()['deliveries']}
        for kind in ('gym_trainer','gym','rival','elite_four','champion','rocket_leader'):
            actors=[a for a,p in CONFIG['profiles'].items() if kind in p['scoutRoles']]
            self.assertTrue(actors,kind);self.assertTrue(set(actors)-{RICK} <= recipients,kind)
        self.assertNotIn(SALLY,recipients)
    def test_unqualified_origin_never_invents_ordinary_reach(self):
        source=next(s for s,a in CONFIG['sourceActors'].items() if a not in CONFIG['profiles'])
        value=policy.plan(CONFIG,player='player:fixture',post={'postID':'p','author':CONFIG['sourceActors'][source],'sourceTrainerID':int(source),'visibility':'public'},edges=[],known_actors=ACTORS,post_order=1)
        self.assertIsNone(value['originStage']);self.assertTrue(all(r['reason']=='chronically_online' for r in value['deliveries']))
    def test_authored_curve_is_configuration(self):
        cfg=copy.deepcopy(CONFIG);cfg['balanceVersion']='labeled-test-curve';cfg['reachBands'][0]['budget']=3
        policy.validate(cfg,REGISTRY)
        value=policy.plan(cfg,player='p',post={'postID':'p','author':RICK,'sourceTrainerID':102,'visibility':'public'},edges=[],known_actors=ACTORS,post_order=1)
        self.assertEqual(sum(r['reason']=='ordinary_discovery' for r in value['deliveries']),3)
    def test_private_never_scouted(self):
        value=policy.plan(CONFIG,player='p',post={'postID':'p','author':RICK,'visibility':'private'},edges=[],known_actors=ACTORS,post_order=1)
        self.assertEqual(value['deliveries'],[])
    def test_nonmonotonic_config_rejected(self):
        cfg=copy.deepcopy(CONFIG);cfg['reachBands'][1]['budget']=1
        with self.assertRaises(WorldError):policy.validate(cfg,REGISTRY)
    def test_forged_source_class_rejected(self):
        cfg=copy.deepcopy(CONFIG);cfg['profiles'][RICK]['sourceClass']='TRAINER_CLASS_LEADER'
        with self.assertRaises(WorldError):policy.validate(cfg,REGISTRY)
    def q(self,**kw):
        args=dict(mode='delivered',source_actor=RICK,channel='pokebook',origin_stage='forest',campaign_distance=1,path=None,reason='chronically_online',publication_order=1,latest_order=1);args.update(kw);return policy.quality(**args)
    def test_quality_direct_scout_path_faction(self):
        self.assertEqual(self.q(mode='direct')['sourceQuality'],'DIRECT');self.assertEqual(self.q()['sourceQuality'],'HIGH')
        self.assertEqual(self.q(reason='ordinary_discovery',path=[RICK,DOUG,SALLY])['sourceQuality'],'MODERATE')
        self.assertEqual(self.q(reason='ordinary_discovery',path=list('abcde'))['sourceQuality'],'LOW')
        self.assertEqual(self.q(channel='ROCKET_INTEL')['organizationalFidelity'],'full_observed_claim')
    def test_recent_near_outranks_old_far_deterministically(self):
        self.assertEqual(self.q()['currentRelevance'],'CURRENT');self.assertEqual(self.q(campaign_distance=4,latest_order=8)['currentRelevance'],'OLDER')
        self.assertEqual(self.q(),self.q())
    def rocket_records(self):
        base={'battleID':'fixture-rocket-battle','trainerID':MEMBER[8:]}
        claims=[{'type':'POKEMON_SEEN','speciesID':1},{'type':'MOVE_REVEALED','speciesID':1,'moveID':33},{'type':'POKEMON_SEEN','speciesID':17},{'type':'ITEM_USE_OBSERVED','itemID':13}]
        return [{'actorID':MEMBER,'campaignID':'fixture-campaign','branchID':'fixture-branch','mode':'direct','memoryID':'fixture-observer-'+str(i),'claim':{**base,**c}} for i,c in enumerate(claims)]
    def test_rocket_complete_observed_fixture(self):
        records=self.rocket_records();public=[records[0]['claim']]
        result=policy.rocket_intelligence(CONFIG,member=MEMBER,leader=LEADER,records=records,campaign='fixture-campaign',branch='fixture-branch')
        self.assertEqual([r['claim'] for r in result],[r['claim'] for r in records]);self.assertEqual(len(public),1);self.assertTrue(all(r['channel']=='ROCKET_INTEL' for r in result));self.assertNotIn('hiddenParty',dump(result))
    def test_rocket_nonmember_nonleader_scope_hidden_rejected(self):
        for changes in ({'member':RICK},{'leader':BROCK},{'branch':'other'},{'campaign':'other'}):
            args=dict(member=MEMBER,leader=LEADER,records=self.rocket_records(),campaign='fixture-campaign',branch='fixture-branch');args.update(changes)
            with self.assertRaises(WorldError):policy.rocket_intelligence(CONFIG,**args)
        r=self.rocket_records();r[0]['claim']['hiddenParty']=[150]
        with self.assertRaises(WorldError):policy.rocket_intelligence(CONFIG,member=MEMBER,leader=LEADER,records=r,campaign='fixture-campaign',branch='fixture-branch')

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'world.sqlite3';self.w=ViralityStore(self.path,BUILD,TAG);self.s1=fingerprint(flash(),SIZES)
        self.w.import_save(self.s1);self.w.authorize_launch(100,self.s1);self.w.activate()
    def tearDown(self):self.w.close();self.tmp.cleanup()
    def battle(self,trainer=102,first=1,bid=1):
        for i,typ in enumerate((1,2,6,3,4,5),first):
            m=visible(i) if typ==6 and trainer==102 else msg(i,typ,battle=bid,trainer=trainer)
            self.w.ingest(m)
    def save(self,counter=2):
        f=fingerprint(flash(counter,counter),SIZES)
        self.w.finish_save(self.w.begin_save(100,self.s1),f,dict(event='savedataUpdated',nonce=100,run=1,eventCounter=6,ack=6,depth=0,state=0,drops=0,counter=counter));return f
    def test_delivery_and_exposure_separate(self):
        self.battle();self.w.activate_virality();self.w.advance_social('publication',expose=False)
        self.assertFalse(self.w.for_actor(BROCK).context()['deliveries']);self.assertFalse(self.w.public_feed(BROCK)[0]['seen'])
        post=next(iter(self.w.social_state()['posts']))
        with self.assertRaises(WorldError):self.w.read_public_post(BROCK,post)
        self.w.advance_social('exposure');self.assertTrue(self.w.public_feed(BROCK)[0]['seen']);self.assertEqual(len(self.w.for_actor(BROCK).context()['deliveries']),2)
    def test_brock_public_subset_strategy_projection(self):
        self.w.activate_virality();self.battle();ctx=build_social_evidence(self.w,BROCK)
        self.assertEqual({r['claim']['type'] for r in ctx['authorizedFacts']},{'TRAINER_BATTLE_RESULT','POKEMON_SEEN'})
        self.assertFalse(self.w.for_actor(BROCK).context()['directObservations']);self.assertNotIn('moveID',dump(ctx));self.assertTrue(all(r['evidenceQuality']['sourceQuality']=='HIGH' for r in ctx['authorizedFacts']))
        self.assertTrue(any(r['claim']['type']=='MOVE_REVEALED' for r in self.w.for_actor(RICK).records()['records']));self.w.verify_virality_replay();self.w.verify_social_replay();self.w.verify_memory_replay()
    def test_idempotent_freeze_and_reload(self):
        self.w.activate_virality();self.battle();before=self.w.virality_state();mem=self.w._maximum()
        self.w.advance_social('publication');after=self.w.virality_state();self.w.advance_social('publication');self.assertEqual(after,self.w.virality_state());self.assertEqual(mem,self.w._maximum())
        self.w.close();self.w=ViralityStore(self.path,BUILD,TAG);self.assertEqual(after,self.w.virality_state());self.w.verify_virality_replay()
        self.assertEqual(next(iter(before['epochs'].values()))['followerCount'],1)
    def test_save_restore_branch_stale_job(self):
        self.w.activate_virality();self.battle();s2=self.save();after=self.w.virality_state();scope=self.w.virality_scope();self.w.restore(self.s1)
        self.assertFalse(self.w.virality_state()['epochs']);self.assertFalse(self.w.for_actor(BROCK).context()['deliveries'])
        self.assertEqual(policy.follower_count(self.w.player_actor(),list(self.w.social_state()['follows'].values()),ACTORS),0)
        with self.assertRaisesRegex(WorldError,'stale'):self.w.advance_social('publication',expected_scope=scope)
        self.w.activate_virality();self.assertNotEqual(self.w.get_active_branch(),scope['branch']);self.w.restore(s2);self.assertEqual(after,self.w.virality_state());self.w.verify_virality_replay()
    def test_legacy_and_new_exposure_deduplicate_both_orders(self):
        self.battle();post=next(iter(self.w.social_state()['posts']));self.w.tick(1);self.w.for_social_actor(JANICE).expose(post)
        n=len(self.w.for_actor(JANICE).records()['records']);self.w.activate_virality();self.w.advance_social('publication')
        self.assertEqual(n,len(self.w.for_actor(JANICE).records()['records']))
        before=self.w._maximum();self.w.for_social_actor(BROCK).expose(post);self.assertEqual(before,self.w._maximum())
        self.assertTrue(self.w.for_social_actor(BROCK).feed_metadata()[0]['seen']);self.assertEqual(self.w.for_social_actor(BROCK).read_post(post)['postID'],post)
        self.w.verify_social_replay();self.w.verify_memory_replay();self.w.verify_virality_replay()
    def test_forwarded_one_origin_is_not_independent_corroboration(self):
        self.w.activate_virality();self.battle()
        row=next(r for r in self.w.for_actor(JANICE).records()['records'] if r['claim']['type']=='POKEMON_SEEN')
        c=self.w.campaign();self.w.deliver_fixture(delivery_id='fixture-forward',sender=JANICE,recipient=BROCK,source_memory_id=row['memoryID'],campaign=c['id'],branch=c['active_branch'],cursor=c['cursor'])
        seen=[r for r in self.w.evidence_context(BROCK)['authorizedEvidence'] if r['claim']['type']=='POKEMON_SEEN']
        self.assertEqual(len(seen),2);self.assertTrue(all(r['evidenceQuality']['independentOriginCount']==1 and r['evidenceQuality']['originalSourceActor']==RICK for r in seen))
    def test_legacy_writer_revoked(self):
        with self.assertRaisesRegex(WorldError,'ViralityStore'):SocialStore(self.path,BUILD,TAG)
    def test_already_open_legacy_writer_revoked(self):
        path=Path(self.tmp.name)/'legacy.sqlite3'
        with SocialStore(path,BUILD,TAG) as old:
            old.import_save(self.s1)
            with ViralityStore(path,BUILD,TAG):
                with self.assertRaisesRegex(WorldError,'ViralityStore'):old.activate()
    def test_immutable_and_save_barrier(self):
        self.w.activate_virality()
        with self.assertRaises(sqlite3.IntegrityError):self.w.db.execute('DELETE FROM virality_log')
        self.w.begin_save(100,self.s1)
        with self.assertRaises(WorldError):self.w.advance_social('publication')
    def test_rocket_native_typed_fixture_full_and_private(self):
        self.w.activate_virality();trainer=CONFIG['profiles'][MEMBER]['sourceTrainerIDs'][0];self.battle(trainer=trainer)
        self.assertFalse(self.w.social_state()['posts']) # Internal intel needs no post.
        records=self.w.for_actor(LEADER).records()['records']
        self.w.advance_social('battle_completion')
        self.assertTrue(records);self.assertTrue(all(r['source']['channel']=='ROCKET_INTEL' for r in records));self.assertEqual(len(records),len(self.w.for_actor(MEMBER).records()['records']))
        self.assertFalse(self.w.for_actor(BROCK).records()['records']);self.w.verify_virality_replay();self.w.verify_memory_replay()
    def test_follower_change_does_not_redistribute_history(self):
        self.w.activate_virality();self.battle();first=copy.deepcopy(self.w.virality_state()['epochs'])
        def add():
            self.w._writable()
            for a in sorted(ACTORS)[:20]:self.w._append('FOLLOW','fixture:'+a,{'follower':a,'followed':self.w.player_actor(),'cause':'labeled_host_fixture'})
        self.w._tx(add);self.w.advance_social('progression');self.assertEqual(first,self.w.virality_state()['epochs'])
        self.assertEqual(policy.follower_count(self.w.player_actor(),list(self.w.social_state()['follows'].values()),ACTORS),21)
    def test_atomic_delivery_failure_rolls_back(self):
        self.battle();self.w.activate_virality();before=self.w.virality_state();maximum=self.w._maximum();original=self.w._deliver_reference
        def fail(**kwargs):
            original(**kwargs);raise RuntimeError('injected receipt failure')
        self.w._deliver_reference=fail
        with self.assertRaises(RuntimeError):self.w.advance_social('publication')
        self.w._deliver_reference=original;self.assertEqual(before,self.w.virality_state());self.assertEqual(maximum,self.w._maximum())
    def test_rocket_save_restore_and_stale_generation(self):
        self.w.activate_virality();self.battle(trainer=CONFIG['profiles'][MEMBER]['sourceTrainerIDs'][0]);self.w.advance_social('battle_completion');s2=self.save();scope=self.w.virality_scope();intel=copy.deepcopy(self.w.virality_state()['intel'])
        self.w.restore(self.s1);self.assertFalse(self.w.virality_state()['intel']);self.assertFalse(self.w.for_actor(LEADER).records()['records'])
        with self.assertRaises(WorldError):self.w.advance_social('battle_completion',expected_scope=scope)
        self.w.restore(s2);self.assertEqual(intel,self.w.virality_state()['intel']);self.w.verify_virality_replay()
    def test_new_near_evidence_ranks_above_old_without_forgetting(self):
        import struct
        self.w.close();self.path.unlink();cfg=json.loads((ROOT/'config/social_slice.json').read_text());cfg['eligibility'][SALLY]='ordinary_slice_eligible'
        self.w=ViralityStore(self.path,BUILD,TAG,config=cfg);self.w.import_save(self.s1);self.w.authorize_launch(100,self.s1);self.w.activate();self.w.activate_virality();self.battle()
        # Explicit fixture relationship authorizes Sally's reading of old Rick.
        self.w._tx(lambda:self.w._append('FOLLOW','fixture-sally',{'follower':SALLY,'followed':RICK,'cause':'labeled_host_fixture'}))
        # A distinct actual wire-fixture battle origin on Route3, not a repost.
        for seq,typ in enumerate((1,2,6,3,4,5),7):
            m=msg(seq,typ,battle=2,trainer=117)
            if typ==6:
                from bridge.events_wire import Message
                data=bytearray(m.payload);struct.pack_into('<H',data,48,17);m=Message(m.kind,m.nonce,m.generation,m.sequence,m.tag,m.typ,bytes(data))
            self.w.ingest(m)
        # High-tier fixture enables old Forest post to reach Sally once at its
        # initial epoch; here old receipt is explicitly delivered separately.
        rickpost=next(p for p in self.w.social_state()['posts'].values() if p['author']==RICK)
        self.w.tick(1);self.w.for_social_actor(SALLY).expose(rickpost['postID'])
        ctx=self.w.evidence_context(SALLY);seen=[r for r in ctx['authorizedEvidence'] if r['claim']['type']=='POKEMON_SEEN']
        self.assertEqual(seen[0]['claim']['speciesID'],17);self.assertTrue(any(r['claim']['speciesID']==1 for r in seen));self.assertEqual(seen[0]['evidenceQuality']['sourceQuality'],'DIRECT')
    def test_no_arbitrary_ticks_or_view_side_effect(self):
        with self.assertRaises(WorldError):self.w.advance_social('wall_clock')
        self.w.activate_virality();self.battle();before=self.w.virality_state();self.w.public_feed(BROCK);build_social_evidence(self.w,BROCK);self.assertEqual(before,self.w.virality_state())

if __name__=='__main__':unittest.main()
