"""Domain-only HERMES tests; actual Hermes transport/isolation tests are separate."""
import json,tempfile,unittest
from pathlib import Path
from test_world01 import BUILD,TAG,SIZES,flash,msg
from test_memory01 import visible,RICK,JANICE
from puppeteer.store import PuppeteerStore
from social.store import SocialStore
from world.saves import fingerprint
from world.store import WorldError

DOUG='trainer:fr:trainer:0103'
class PuppeteerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'game.sqlite3';self.w=PuppeteerStore(self.path,BUILD,TAG)
        self.s1=fingerprint(flash(),SIZES);self.w.import_save(self.s1);self.w.authorize_launch(100,self.s1);self.w.activate_puppeteer()
    def tearDown(self):self.w.close();self.tmp.cleanup()
    def battle(self,first=1,bid=1,trainer=102,win=True):
        ms=[msg(first,1,bid,trainer=trainer),msg(first+1,2,bid,trainer=trainer),visible(first+2) if bid==1 and trainer==102 else msg(first+2,6,bid,trainer=trainer),msg(first+3,3,bid,trainer=trainer)]
        if trainer and win:ms.append(msg(first+4,4,bid,trainer=trainer))
        ms.append(msg(first+len(ms),5,bid,trainer=trainer,outcome=1 if win else 2))
        for m in ms:self.w.ingest(m)
    def job(self,mode='offline'):
        o=next(o for o in self.w.puppeteer_state()['obligations'].values() if o['status']!='PUBLISHED');return self.w.begin_job(o['obligationID'],mode)
    def process(self):
        j=self.job();return self.w.fallback(j['jobID'])
    def save(self,counter,last):
        prior=self.s1 if counter==2 else fingerprint(flash(counter-1,counter-1),SIZES);save=fingerprint(flash(counter,counter),SIZES)
        intent=self.w.begin_save(100,prior);self.w.finish_save(intent,save,dict(event='savedataUpdated',nonce=100,run=1,eventCounter=last,ack=last,depth=0,state=0,drops=0,counter=counter));return save
    def test_required_before_generation_no_automatic_optional_post(self):
        self.battle();s=self.w.puppeteer_state();self.assertEqual(len(s['obligations']),1);self.assertFalse(s['episodes']);self.assertFalse(self.w.social_state()['posts'])
        self.assertEqual(next(iter(s['obligations'].values()))['status'],'RECAP_REQUIRED')
    def test_both_outcomes_all_single_trainers(self):
        self.battle(win=False);x=self.process();self.assertEqual(x['producer'],'deterministic_fallback')
        self.assertEqual(next(iter(self.w.social_state()['posts'].values()))['body'],'I won against the player. I saw BULBASAUR.')
        self.battle(first=6,bid=2,trainer=103);self.process();self.assertEqual(len(self.w.social_state()['posts']),2)
        self.assertFalse(any(e['followed'].startswith('player:') for e in self.w.social_state()['follows'].values()))
    def test_multiple_completed_battles_one_follow(self):
        self.battle();self.process();self.battle(first=7,bid=2);self.process()
        self.assertEqual(len(self.w.social_state()['posts']),2);self.assertEqual(len(self.w.puppeteer_state()['episodes']),2)
        self.assertEqual(sum(e['followed'].startswith('player:') for e in self.w.social_state()['follows'].values()),1)
    def test_wild_aborted_no_obligation(self):
        self.battle(trainer=0);self.assertFalse(self.w.puppeteer_state()['obligations'])
        self.w.ingest(msg(6,1,2));self.assertFalse(self.w.puppeteer_state()['obligations'])
    def test_invalid_no_post_private_refusal_extra_claim(self):
        self.battle();j=self.job();r=self.w.fallback_result(j['jobID'])
        for invalid in [{'NO_POST':True},{**r,'visibility':'private'},{**r,'summary':'player always uses grass'},{**r,'publicEvidenceIDs':[]}]:
            with self.assertRaises(WorldError):self.w.settle_job(j['jobID'],invalid,producer='hermes')
        self.w.fallback(j['jobID'],'invalid_output');self.assertEqual(len(self.w.social_state()['posts']),1)
    def test_public_move_omission_and_knowledge_packets(self):
        self.battle();x=self.process();p=x['postID'];self.w.tick(1)
        self.assertFalse(self.w.trainer_packet(JANICE)['reportedClaims']);self.w.for_social_actor(JANICE).expose(p)
        packet=self.w.trainer_packet(JANICE);self.assertEqual(len(packet['reportedClaims']),2);self.assertNotIn('moveID',json.dumps(packet))
        self.assertEqual(len(self.w.trainer_packet(RICK)['retainedEpisodes']),1);self.assertTrue(self.w.trainer_packet(RICK)['retainedEpisodes'][0]['summary']['observedPlayerMoves'])
        self.assertFalse(self.w.trainer_packet(DOUG)['reportedClaims']);self.assertFalse(self.w.trainer_packet(DOUG)['retainedEpisodes'])
        self.assertEqual(len(self.w.puppeteer_state()['links']),2)
    def test_restart_and_meaningful_recall(self):
        self.battle();self.process();sha=self.w.verify_puppeteer_replay();self.w.close();self.w=PuppeteerStore(self.path,BUILD,TAG)
        self.assertEqual(self.w.verify_puppeteer_replay(),sha);self.battle(first=7,bid=2);j=self.job('mock');tools=self.w.job_tools(j['jobID'])
        recall=tools.recall_puppeteer_memory();self.assertEqual(recall['episodes'][0]['summary']['seenSpeciesIDs'],[1]);self.assertEqual(recall['episodes'][0]['summary']['observedPlayerMoves'],[[1,33]])
        self.assertEqual(len(tools.get_actor_context()['retainedEpisodes']),1)
    def test_atomic_failure_and_recovery(self):
        self.battle();j=self.job();r=self.w.fallback_result(j['jobID']);before=self.w.verify_puppeteer_replay()
        with self.assertRaisesRegex(WorldError,'interruption'):self.w.settle_job(j['jobID'],r,producer='hermes',fail=True)
        self.assertEqual(before,self.w.verify_puppeteer_replay());self.assertFalse(self.w.social_state()['posts']);self.assertFalse(self.w.puppeteer_state()['episodes'])
        self.w.fallback(j['jobID']);self.assertEqual(len(self.w.puppeteer_state()['episodes']),1)
    def test_late_result_after_fallback_denied(self):
        self.battle();j=self.job();r=self.w.fallback_result(j['jobID']);x=self.w.fallback(j['jobID'])
        with self.assertRaises(WorldError):self.w.settle_job(j['jobID'],r,producer='hermes')
        self.assertEqual(len(self.w.social_state()['posts']),1)
    def test_restore_pending_jobs_and_private_memory(self):
        before=self.save(2,0);self.battle();j=self.job();r=self.w.fallback_result(j['jobID']);tools=self.w.job_tools(j['jobID']);self.w.fallback(j['jobID']);later=self.save(3,6)
        original=self.w.get_active_branch();self.w.authorize_launch(200,before)
        self.assertFalse(self.w.puppeteer_state()['episodes']);self.assertFalse(self.w.puppeteer_state()['obligations'])
        with self.assertRaises(WorldError):tools.recall_puppeteer_memory()
        with self.assertRaises(WorldError):self.w.settle_job(j['jobID'],r,producer='hermes')
        self.w.tick(1);self.assertNotEqual(self.w.get_active_branch(),original);self.assertFalse(self.w.puppeteer_state()['episodes'])
        self.w.authorize_launch(300,later);self.assertEqual(len(self.w.puppeteer_state()['episodes']),1)
    def test_pending_obligation_checkpoint_restores(self):
        self.battle();before=self.save(2,6);self.process();self.w.authorize_launch(200,before)
        self.assertFalse(self.w.puppeteer_state()['episodes']);self.assertEqual(next(iter(self.w.puppeteer_state()['obligations'].values()))['status'],'RECAP_REQUIRED')
        self.process();self.assertEqual(len(self.w.puppeteer_state()['episodes']),1)
    def test_stale_foreign_future_refs_and_tools_no_selectors(self):
        self.battle();j=self.job();r=self.w.fallback_result(j['jobID'])
        for bad in [{**r,'actorID':JANICE},{**r,'publicEvidenceIDs':['0'*64]},{**r,'priorEpisodeIDs':['1'*64]}]:
            with self.assertRaises(WorldError):self.w.settle_job(j['jobID'],bad,producer='hermes')
        with self.assertRaises(TypeError):self.w.job_tools(j['jobID']).get_battle_evidence(actor=DOUG)
        with self.assertRaises(WorldError):self.w.begin_job(j['scope']['obligationID'])
    def test_legacy_social_writer_rejected(self):
        with self.assertRaisesRegex(WorldError,'PuppeteerStore'):SocialStore(self.path,BUILD,TAG)
    def test_shadow_records_valid_result_but_fallback_commits(self):
        self.battle();j=self.job('shadow');r=self.w.fallback_result(j['jobID']);out=self.w.settle_job(j['jobID'],r,producer='hermes')
        self.assertEqual(out['producer'],'deterministic_fallback');self.assertEqual(out['fallbackReason'],'shadow_policy')
    def test_no_historical_backfill(self):
        self.w.close();self.path.unlink()
        with SocialStore(self.path,BUILD,TAG) as s:
            s.import_save(self.s1);s.authorize_launch(100,self.s1)
            for n,t in enumerate([1,2,6,3,4,5],1):s.ingest(msg(n,t))
        self.w=PuppeteerStore(self.path,BUILD,TAG);self.w.activate_puppeteer();self.assertFalse(self.w.puppeteer_state()['obligations'])
