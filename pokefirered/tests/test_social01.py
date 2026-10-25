"""SOCIAL host fixtures; live production-path acceptance is separate."""
import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from test_world01 import BUILD,TAG,SIZES,flash,msg
from test_memory01 import visible,RICK,JANICE
from world.saves import fingerprint
from world.store import WorldError,WorldStore,dump
from memory.store import MemoryStore,actor_id
from social.store import SocialStore
from social import policy

DOUG=actor_id('fr:trainer:0103')
CONFIG=json.loads((Path(__file__).resolve().parents[1]/'config/social_slice.json').read_text())


class SocialTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'social.sqlite3'
        self.w=SocialStore(self.path,BUILD,TAG);self.s1=fingerprint(flash(),SIZES)
        self.w.import_save(self.s1);self.w.authorize_launch(100,self.s1);self.w.activate()

    def tearDown(self):self.w.close();self.tmp.cleanup()

    def battle(self,first=1,bid=1,trainer=102,win=True):
        messages=[msg(first,1,bid,trainer=trainer),msg(first+1,2,bid,trainer=trainer)]
        if bid==1 and trainer==102:messages.append(visible(first+2))
        else:messages.append(msg(first+2,6,bid,trainer=trainer))
        messages.append(msg(first+3,3,bid,trainer=trainer))
        if trainer and win:messages.append(msg(first+4,4,bid,trainer=trainer))
        messages.append(msg(first+len(messages),5,bid,trainer=trainer,outcome=1 if win else 2))
        for m in messages:self.w.ingest(m)

    def post(self):return next(iter(self.w.social_state()['posts']))

    def player_count(self):return sum(e['followed']==self.w.player_actor() for e in self.w.social_state()['follows'].values())

    def save(self,counter,last=6):
        previous=self.s1 if counter==2 else fingerprint(flash(counter-1,counter-1),SIZES)
        data=fingerprint(flash(counter,counter),SIZES)
        intent=self.w.begin_save(100,previous)
        receipt=dict(event='savedataUpdated',nonce=100,run=1,eventCounter=last,ack=last,depth=0,state=0,drops=0,counter=counter)
        self.w.finish_save(intent,data,receipt);return data

    def manual(self):
        self.w.close();self.path.unlink()
        cfg=copy.deepcopy(CONFIG);cfg['autoPublish']=False
        self.w=SocialStore(self.path,BUILD,TAG,config=cfg)
        self.w.import_save(self.s1);self.w.authorize_launch(100,self.s1);self.w.activate();self.battle()
        opportunity=self.w.for_social_actor(RICK).opportunities()[0]
        return policy.propose(opportunity)

    def test_first_follow_is_directed_and_once(self):
        self.battle();self.assertEqual(self.player_count(),1)
        self.battle(first=7,bid=2);self.assertEqual(self.player_count(),1)
        self.assertEqual(len(self.w.social_state()['posts']),2)
        self.assertFalse(any(e['follower']==self.w.player_actor() for e in self.w.social_state()['follows'].values()))
        self.assertNotIn('friendship',dump(self.w.social_state()))

    def test_no_follow_wild_loss_or_aborted(self):
        self.battle(trainer=0);self.assertEqual(self.player_count(),0)
        self.battle(first=6,bid=2,win=False);self.assertEqual(self.player_count(),0)
        self.w.ingest(msg(11,1,3));self.assertEqual(self.player_count(),0)

    def test_unclassified_actor_no_accidental_eligibility(self):
        self.battle(trainer=103);self.assertEqual(self.player_count(),0)
        self.assertEqual(self.w.social_state()['posts'],{})

    def test_hostile_story_explicit_exclusion(self):
        self.assertEqual(list(self.w.config['eligibility']),[RICK])
        self.assertNotIn(actor_id('fr:trainer:0348'),self.w.config['eligibility'])
        with self.assertRaises(WorldError):self.w.for_social_actor('unknown')

    def test_graph_authored_not_vanilla(self):
        e=next(iter(self.w.social_state()['follows'].values()))
        self.assertEqual((e['follower'],e['followed'],e['cause']),(JANICE,RICK,'authored_vertical_slice'))
        self.assertEqual(self.player_count(),0)

    def test_publication_not_feed_or_knowledge(self):
        self.battle();s=self.w.social_state();self.assertEqual(len(s['posts']),1)
        self.assertFalse(s['feeds']);self.assertFalse(s['exposures'])
        self.assertFalse(self.w.for_actor(JANICE).context()['deliveries'])
        self.assertFalse(self.w.for_actor(DOUG).context()['deliveries'])

    def test_feed_is_metadata_only_and_no_memory(self):
        self.battle();self.w.tick(1)
        j=self.w.for_social_actor(JANICE);metadata=j.feed_metadata()
        self.assertEqual(len(metadata),1);self.assertFalse(metadata[0]['seen'])
        self.assertNotIn('claims',dump(metadata));self.assertNotIn('body',dump(metadata))
        self.assertFalse(self.w.for_actor(JANICE).context()['deliveries'])
        with self.assertRaisesRegex(WorldError,'requires recorded exposure'):j.read_post(self.post())

    def test_exposure_exact_subset_attribution(self):
        self.battle();self.w.tick(1);j=self.w.for_social_actor(JANICE);j.expose(self.post())
        ctx=self.w.for_actor(JANICE).context()
        self.assertFalse(ctx['directObservations']);self.assertEqual(len(ctx['deliveries']),2)
        self.assertEqual({x['claim']['type'] for x in ctx['deliveries']},{'TRAINER_BATTLE_RESULT','POKEMON_SEEN'})
        self.assertTrue(all(x['attribution']['kind']=='reported_post' for x in ctx['deliveries']))
        self.assertNotIn('TACKLE',dump(ctx));self.assertNotIn('moveID',dump(ctx))

    def test_no_unrelated_recipient(self):
        self.battle();self.w.tick(1)
        d=self.w.for_social_actor(DOUG);self.assertEqual(d.feed_metadata(),[])
        with self.assertRaisesRegex(WorldError,'not delivered'):d.expose(self.post())
        self.assertEqual(self.w.for_actor(DOUG).context()['directObservations'],[])

    def test_recipient_cannot_traverse_private_provenance(self):
        self.battle();self.w.tick(1);self.w.for_social_actor(JANICE).expose(self.post())
        for r in self.w.for_actor(JANICE).records()['records']:
            chain=self.w.for_actor(JANICE).provenance(r['memoryID'])
            self.assertEqual(len(chain),1)
            self.assertNotIn('parentMemoryID',dump(chain));self.assertNotIn('turnID',dump(chain))
        private=self.w.for_actor(RICK).records()['records'][0]['memoryID']
        with self.assertRaises(WorldError):self.w.for_actor(JANICE).provenance(private)
        post=self.w.for_social_actor(JANICE).read_post(self.post())
        self.assertNotIn('evidenceIDs',dump(post))

    def test_transport_tick_exposure_idempotent(self):
        self.battle();before=self.w.social_state();self.w.ingest(msg(6,5))
        self.assertEqual(before,self.w.social_state());self.w.tick(1);mid=self.w.social_state()
        self.w.tick(1);self.assertEqual(mid,self.w.social_state())
        self.w.for_social_actor(JANICE).expose(self.post());end=self.w.social_state()
        self.w.for_social_actor(JANICE).expose(self.post());self.assertEqual(end,self.w.social_state())
        self.assertEqual(len(self.w.for_actor(JANICE).records()['records']),2)

    def test_deterministic_text_and_no_extra_payload(self):
        proposal=self.manual();proposal['body']='The player knows Tackle.'
        with self.assertRaisesRegex(WorldError,'body/extra'):self.w.for_social_actor(RICK).submit(proposal)
        del proposal['body'];pid=self.w.for_social_actor(RICK).submit(proposal)
        self.assertEqual(self.w.for_social_actor(RICK).read_post(pid)['body'],'I lost to the player. I saw BULBASAUR.')

    def test_supported_single_claim_subset(self):
        proposal=self.manual();proposal['evidenceIDs']=proposal['evidenceIDs'][:1]
        pid=self.w.for_social_actor(RICK).submit(proposal)
        self.assertEqual(self.w.for_social_actor(RICK).read_post(pid)['body'],'I lost to the player.')

    def test_foreign_and_unpublished_move_evidence_rejected(self):
        proposal=self.manual()
        move=next(r for r in self.w.for_actor(RICK).records()['records'] if r['claim']['type']=='MOVE_REVEALED')
        proposal['evidenceIDs']=[move['memoryID']]
        with self.assertRaisesRegex(WorldError,'unsupported evidence'):self.w.for_social_actor(RICK).submit(proposal)
        with self.assertRaises(WorldError):self.w.for_social_actor(JANICE).submit(proposal)

    def test_private_post_not_feed_distributed(self):
        proposal=self.manual();proposal['visibility']='private'
        self.w.for_social_actor(RICK).submit(proposal);self.w.tick(1)
        self.assertEqual(self.w.social_state()['feeds'],{});self.assertFalse(self.w.social_state()['pending'])

    def test_proposal_limits_and_unknown_policy(self):
        proposal=self.manual()
        for p in [{**proposal,'policyVersion':2},{**proposal,'evidenceIDs':[]},{**proposal,'evidenceIDs':proposal['evidenceIDs']*2},{**proposal,'visibility':'broadcast'},{**proposal,'futureCutoff':999}]:
            with self.assertRaises(WorldError):self.w.for_social_actor(RICK).submit(p)

    def test_no_evidence_policy_no_post(self):
        self.assertIsNone(policy.propose({'evidence':[],'battleID':'x'}))

    def test_exposure_atomic_failure_recovers(self):
        self.battle();self.w.tick(1);before=self.w.verify_memory_replay()
        with self.assertRaisesRegex(WorldError,'injected exposure'):
            self.w._expose(self.w.for_social_actor(JANICE),self.post(),fail=True)
        self.assertEqual(before,self.w.verify_memory_replay());self.assertFalse(self.w.social_state()['exposures'])
        self.w.for_social_actor(JANICE).expose(self.post());self.assertEqual(len(self.w.for_actor(JANICE).records()['records']),2)

    def test_restart_and_committed_replay(self):
        self.battle();self.w.tick(1);self.w.for_social_actor(JANICE).expose(self.post())
        before=self.w.social_state();memory=self.w.verify_memory_replay();sha=self.w.verify_social_replay()
        self.w.close();self.w=SocialStore(self.path,BUILD,TAG)
        self.assertEqual(before,self.w.social_state());self.assertEqual(memory,self.w.verify_memory_replay());self.assertEqual(sha,self.w.verify_social_replay())

    def test_old_memory_writer_rejected(self):
        with self.assertRaisesRegex(WorldError,'requires SocialStore'):MemoryStore(self.path,BUILD,TAG)
        with self.assertRaises(WorldError):WorldStore(self.path,BUILD,TAG)

    def test_migration_does_not_backfill(self):
        self.w.close();self.path.unlink()
        with MemoryStore(self.path,BUILD,TAG) as m:
            m.import_save(self.s1);m.authorize_launch(100,self.s1)
            for n,t in enumerate([1,2,6,3,4,5],1):m.ingest(msg(n,t))
        self.w=SocialStore(self.path,BUILD,TAG)
        self.assertEqual(self.w.social_state()['posts'],{});self.assertEqual(self.w.social_state()['follows'],{})
        self.w.activate();self.assertEqual(self.player_count(),0);self.assertEqual(self.w.social_state()['posts'],{})

    def test_configuration_version_rejected(self):
        bad=copy.deepcopy(CONFIG);bad['policyVersion']=2
        with self.assertRaises(WorldError):SocialStore(self.path,BUILD,TAG,config=bad)
        self.w.db.execute('UPDATE social_version SET reducer=2')
        with self.assertRaises(WorldError):SocialStore(self.path,BUILD,TAG)

    def test_restore_pre_exposure_and_social_only_divergence(self):
        self.battle();self.w.tick(1);s2=self.save(2);post=self.post()
        grant=self.w.for_social_actor(JANICE);grant.expose(post);a=self.w.get_active_branch()
        s3=self.save(3)
        self.w.authorize_launch(200,s2)
        self.assertFalse(self.w.for_actor(JANICE).context()['deliveries'])
        self.assertFalse(self.w.social_state()['exposures']);self.assertEqual(len(self.w.social_state()['feeds']),1)
        with self.assertRaises(WorldError):grant.read_post(post)
        self.w.for_social_actor(JANICE).expose(post)
        self.assertNotEqual(a,self.w.get_active_branch());self.assertEqual(self.w.get_current_world_cursor(),5)
        self.assertEqual(len(self.w.for_actor(JANICE).context()['deliveries']),2)
        self.w.authorize_launch(300,s3)
        self.assertEqual(a,self.w.get_active_branch());self.assertEqual(len(self.w.social_state()['exposures']),1)

    def test_restore_before_battle_pending_jobs_do_not_leak(self):
        saved=self.save(2,last=0);self.battle();post=self.post();self.w.tick(1)
        self.w.for_social_actor(JANICE).expose(post)
        self.w.authorize_launch(200,saved)
        self.assertEqual(self.player_count(),0);self.assertFalse(self.w.social_state()['posts']);self.assertFalse(self.w.social_state()['pending'])
        self.w.tick(1)
        self.assertFalse(self.w.social_state()['feeds']);self.assertFalse(self.w.for_actor(JANICE).context()['deliveries'])

    def test_publication_checkpoint_preserves_pending_job(self):
        self.battle();s2=self.save(2);self.w.tick(1)
        self.w.authorize_launch(200,s2)
        self.assertEqual(len(self.w.social_state()['pending']),1);self.assertFalse(self.w.social_state()['feeds'])
        self.w.tick(1);self.assertEqual(len(self.w.social_state()['feeds']),1)

    def test_save_barrier_blocks_social_mutation(self):
        self.battle();self.w.begin_save(100,self.s1)
        with self.assertRaisesRegex(WorldError,'save barrier'):self.w.tick(1)

    def test_stale_cross_campaign_cutoff_grants(self):
        grant=self.w.for_social_actor(JANICE);self.battle()
        with self.assertRaisesRegex(WorldError,'stale'):grant.feed_metadata()
        proposal=policy.propose(self.w.for_social_actor(RICK).opportunities()[0]);proposal['campaignID']='other'
        with self.assertRaises(WorldError):self.w.for_social_actor(RICK).submit(proposal)

    def test_tick_limits_and_no_polling_time(self):
        self.battle()
        for tick in (0,2,True):
            with self.assertRaises(WorldError):self.w.tick(tick)
        self.w.tick(1);self.w.tick(2);self.assertEqual(len(self.w.social_state()['feeds']),1)

    def test_history_immutable(self):
        self.battle()
        for table in ('social_log','social_branches','social_checkpoints'):
            with self.assertRaises(sqlite3.IntegrityError):self.w.db.execute('DELETE FROM '+table)

    def test_follower_counts_real_edges_not_fake_audience(self):
        self.battle();self.assertEqual(self.player_count(),1)
        self.assertEqual(len(self.w.social_state()['follows']),2)

    def test_actor_api_no_actor_selector(self):
        j=self.w.for_social_actor(JANICE)
        with self.assertRaises(TypeError):j.feed_metadata(actor=RICK)
        with self.assertRaises(TypeError):j.expose('x',recipient=RICK)

    def test_trigger_failure_rolls_back_canonical_memory_and_social(self):
        from unittest.mock import patch
        for n,t in enumerate([1,2,6,3,4],1):self.w.ingest(msg(n,t))
        before=(self.w.verify_replay(),self.w.verify_memory_replay(),self.w.social_state())
        with patch.object(self.w,'_commit',side_effect=WorldError('injected publication interruption')):
            with self.assertRaisesRegex(WorldError,'publication interruption'):self.w.ingest(msg(6,5))
        self.assertEqual(before,(self.w.verify_replay(),self.w.verify_memory_replay(),self.w.social_state()))
        self.w.ingest(msg(6,5));self.assertEqual(self.player_count(),1);self.assertEqual(len(self.w.social_state()['posts']),1)

    def test_four_jobs_eight_recipients_bounds_and_no_old_post_on_follow(self):
        def seed():
            for n in range(120,130):
                actor=actor_id('fr:trainer:'+str(n).zfill(4));self.w.get_actor(actor)
                self.w._append('FOLLOW',actor+'>'+RICK,{'follower':actor,'followed':RICK,'cause':'authored_vertical_slice'})
        self.w._tx(seed)
        for n in range(5):self.battle(first=1+6*n,bid=1+n)
        self.w.tick(1);state=self.w.social_state()
        self.assertEqual(len(state['feeds']),32);self.assertEqual(len(state['pending']),1)
        self.w.tick(2);self.assertEqual(len(self.w.social_state()['feeds']),40)
        self.w._tx(lambda:self.w._append('FOLLOW',DOUG+'>'+RICK,{'follower':DOUG,'followed':RICK,'cause':'authored_vertical_slice'}))
        self.w.tick(3);self.assertEqual(self.w.for_social_actor(DOUG).feed_metadata(),[])

    def test_pre_activation_opportunities_empty(self):
        self.w.close();self.path.unlink()
        with MemoryStore(self.path,BUILD,TAG) as m:
            m.import_save(self.s1);m.authorize_launch(100,self.s1)
            for n,t in enumerate([1,2,6,3,4,5],1):m.ingest(msg(n,t))
        self.w=SocialStore(self.path,BUILD,TAG);self.w.activate()
        self.assertEqual(self.w.for_social_actor(RICK).opportunities(),[])

    def test_writer_open_before_social_migration_is_revoked(self):
        self.w.close();self.path.unlink()
        m=MemoryStore(self.path,BUILD,TAG);m.import_save(self.s1)
        try:
            self.w=SocialStore(self.path,BUILD,TAG)
            with self.assertRaisesRegex(WorldError,'SocialStore'):m.authorize_launch(100,self.s1)
        finally:m.close()

    def test_exposure_retry_returns_identical_receipt(self):
        self.battle();self.w.tick(1)
        first=self.w.for_social_actor(JANICE).expose(self.post())
        self.assertEqual(first,self.w.for_social_actor(JANICE).expose(self.post()))

    def test_offline_committed_fixture_no_policy_rerun(self):
        import sys
        from unittest.mock import patch
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
        from social01_replay import export,replay_fixture
        self.battle();self.w.tick(1);self.w.for_social_actor(JANICE).expose(self.post())
        fixture=Path(self.tmp.name)/'fixture.json';fixture.write_text(json.dumps(export(self.w)))
        with patch('social.policy.propose',side_effect=AssertionError('policy must not rerun')):
            self.assertTrue(replay_fixture(fixture)['passed'])

    def test_malformed_untrusted_proposal_is_domain_rejection(self):
        p=self.manual()
        for proposal in [{**p,'policyVersion':True},{**p,'evidenceIDs':[{}]},{**p,'battleID':{}},{**p,'evidenceIDs':[42]}]:
            with self.assertRaises(WorldError):self.w.for_social_actor(RICK).submit(proposal)
        with self.assertRaises(WorldError):self.w.for_social_actor(JANICE).expose({})

    def test_author_submission_records_actual_selection_once(self):
        proposal=self.manual();proposal['evidenceIDs']=proposal['evidenceIDs'][:1]
        pid=self.w.for_social_actor(RICK).submit(proposal);state=self.w.social_state()
        key='author:'+proposal['battleID']
        self.assertEqual(state['proposals'][key]['proposal'],proposal)
        self.assertEqual(state['outcomes'][key]['postID'],pid)
        self.assertEqual(state['outcomes'][key]['status'],'published')
        self.w.for_social_actor(RICK).submit(proposal)
        self.assertEqual(state,self.w.social_state())
