"""Focused integration contracts; fixtures do not claim a native playthrough."""
import copy,json,tempfile,unittest
from pathlib import Path
from tests import test_prep01 as f
from strategy.memo import run_memo_job
from strategy.provider import FixtureProvider
from system1.store import PreparationDecisionStore
from system1.provider import FixtureDecisionProvider,run_selection
from virality.store import ViralityMixin
from campaign.context import ScoutingContextMixin,BROCK
from campaign.budget import CampaignBudget,LIMITS
from world.store import WorldError

class Store(ScoutingContextMixin,ViralityMixin,PreparationDecisionStore):pass

class FirstGymTests(unittest.TestCase):
    battle=f.PrepTests.battle;checkpoint=f.PrepTests.checkpoint
    def setUp(self):
        f.PrepTests.setUp(self);self.w.close();self.w=Store(self.path,f.BUILD,f.TAG)
        self.w.activate_puppeteer();self.w.activate_virality();self.checkpoint(False)
    def tearDown(self):f.PrepTests.tearDown(self)
    def publish_rick(self):
        self.battle()
        o=next(o for o in self.w.puppeteer_state()['obligations'].values() if o['status']!='PUBLISHED')
        job=self.w.begin_job(o['obligationID'],'offline');self.w.fallback(job['jobID'])
    def memo(self):
        return run_memo_job(self.w,self.w.begin_strategy(BROCK,'first'),FixtureProvider('Brock considers the public report but the current opposing lead remains unknown. He wants to preserve his Rock companions and use their legal moves patiently.'))
    def commit(self):
        self.memo();job=self.w.begin_selection(BROCK,'first')
        self.assertEqual(len(job['request']['choices']),1)
        provider=FixtureDecisionProvider('must-not-call')
        d=run_selection(self.w,job,provider,source='mock')
        self.assertEqual(provider.calls,0);self.assertEqual(d['source'],'sole')
        return self.w.commit_preparation(d['decisionID'])
    def test_automatic_offline_scheduler_runs_whole_host_chain(self):
        from campaign.runtime import Services
        from unittest.mock import patch
        scheduler=Services(str(self.path),live=False)
        with patch.object(scheduler,'log'):
            self.battle()
            scheduler.tick(self.w)
            self.assertIsNone(self.w.locked_preparation(BROCK))
            self.assertEqual(self.w.memo_records(),[])
            self.checkpoint(False)
            for _ in range(4):scheduler.tick(self.w)
            lock=self.w.locked_preparation(BROCK)
            self.assertIsNotNone(lock)
            self.assertEqual(len(self.w.memo_records()),1)
            self.assertTrue(self.w.evidence_context(BROCK)['authorizedEvidence'])
            before=self.w.verify_strategy_replay()
            for _ in range(4):scheduler.tick(self.w)
            self.assertEqual(before,self.w.verify_strategy_replay())
            scheduler.close(self.w)
    def test_first_commit_replays_without_earned_token(self):
        c=self.commit();state=self.w.preparation_state()
        behavior=self.w.battle_behavior(c)
        self.assertEqual(behavior['reference'],'brock-scouting-opening-v1')
        self.assertEqual(state['opportunities'][c['opportunityID']]['earnedAllowance'],0)
        self.assertEqual(self.w.get_preparation_opportunity(BROCK,'first')['status'],'committed')
        self.assertEqual([p['species'] for p in c['candidate']['party']],[74,95])
        self.assertEqual([p['level'] for p in c['candidate']['party']],[12,14])
        self.assertEqual(c['remainingStock'],[]);self.assertEqual(c['candidate']['acquisitionCount'],0)
        self.checkpoint(False);self.w.close();self.w=Store(self.path,f.BUILD,f.TAG)
        self.assertEqual(self.w.locked_preparation(BROCK),c);self.assertEqual(self.w.begin_selection(BROCK,'first')['commitment'],c)
        self.assertEqual(self.w.battle_behavior(c),behavior)
    def test_scouting_context_is_reported_public_only(self):
        self.publish_rick();p=self.w.context_packet(BROCK,'first');social=p['modelInput']['authorizedSocialEvidence']
        self.assertTrue(social['authorizedFacts']);self.assertEqual(p['scope']['promptVersion'],3)
        self.assertTrue(all(r['mode']=='delivered' for r in social['authorizedFacts']))
        self.assertTrue(all(r['claim']['type']!='MOVE_REVEALED' for r in social['authorizedFacts']))
        self.assertTrue(all(r['evidenceQuality']['sourceQuality']=='HIGH' for r in social['authorizedFacts']))
        self.assertNotIn('candidateID',json.dumps(p['modelInput']))
        before=self.w.verify_memory_replay();r=self.memo();self.assertEqual(r['promptVersion'],3);self.assertEqual(before,self.w.verify_memory_replay())
    def test_later_reports_do_not_change_frozen_battle_facts(self):
        self.publish_rick();c=self.commit();before=copy.deepcopy(c['authorizedPrebattleFacts'])
        self.battle(103);o=next(o for o in self.w.puppeteer_state()['obligations'].values() if o['status']!='PUBLISHED')
        j=self.w.begin_job(o['obligationID'],'offline');self.w.fallback(j['jobID'])
        self.assertNotEqual(self.w.prebattle_facts(BROCK),before)
        self.assertEqual(self.w.locked_preparation(BROCK)['authorizedPrebattleFacts'],before)
    def test_normal_pair_restore_excludes_memo_commit_and_reports(self):
        early=self.save;self.publish_rick();c=self.commit();self.checkpoint(False);later=self.save
        self.w.restore(early);self.assertIsNone(self.w.locked_preparation(BROCK));self.assertEqual(self.w.memo_records(),[])
        self.assertEqual(self.w.evidence_context(BROCK)['authorizedEvidence'],[])
        self.w.restore(later);self.assertEqual(self.w.locked_preparation(BROCK),c)

class BudgetTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'requests.json'
    def tearDown(self):self.tmp.cleanup()
    def charge(self,role,i):
        with CampaignBudget(self.path) as b:return b.charge(role,'job-'+str(i),'fixture:free','hash-'+str(i))
    def test_aggregate_and_role_caps_include_interrupted_requests(self):
        for role,count in (('puppeteer',6),('strategy',4),('battle',20)):
            for i in range(count):self.charge(role,role+str(i))
        with self.assertRaises(WorldError):self.charge('preparation','extra')
        with CampaignBudget(self.path) as b:self.assertEqual(len(b.read()['attempts']),30);self.assertTrue(all(a['outcome'] is None for a in b.read()['attempts']))
    def test_role_limit_duplicate_restart_and_close(self):
        for i in range(4):self.charge('strategy',i)
        with self.assertRaises(WorldError):self.charge('strategy',4)
        self.charge('battle',0)
        with self.assertRaises(WorldError):self.charge('battle',0)
        with CampaignBudget(self.path) as b:b.close()
        with self.assertRaises(WorldError):self.charge('battle',1)
    def test_outcome_immutable_and_no_config_reopen(self):
        n=self.charge('puppeteer',0)
        with CampaignBudget(self.path) as b:b.finish(n,{'costUSD':0});b.finish(n,{'costUSD':0})
        with CampaignBudget(self.path) as b:
            with self.assertRaises(WorldError):b.finish(n,{'costUSD':1})
        value=json.loads(self.path.read_text());value['maximumAttempts']=31;self.path.write_text(json.dumps(value))
        with CampaignBudget(self.path) as b:
            with self.assertRaises(WorldError):b.read()
    def test_explicit_continuation_preserves_aggregate_charges(self):
        for i in range(4):self.charge('strategy',i)
        with CampaignBudget(self.path) as b:
            before=b.read()['attempts'];b.close();b.continue_authorized_run()
            self.assertEqual(b.read()['attempts'],before)
            self.assertEqual(b.read()['continuations'][-1]['priorAttempts'],4)
        with self.assertRaises(WorldError):self.charge('strategy',4)
        self.charge('battle',0)
        with CampaignBudget(self.path) as b:
            self.assertEqual(len(b.read()['attempts']),5);b.close()
        with self.assertRaises(WorldError):self.charge('battle',1)

class WriterTests(unittest.TestCase):
    def test_tools_execute_only_on_owner_thread(self):
        import threading,time
        from concurrent.futures import ThreadPoolExecutor
        from campaign.writer import WriterMailbox
        owner=threading.get_ident();mailbox=WriterMailbox();seen=[]
        class Tool:
            def get_actor_context(self):seen.append(threading.get_ident());return {'actor':'scoped'}
        class FakeStore:
            def job_tools(self,job):self.job=job;return Tool()
        store=FakeStore()
        def worker():
            with mailbox.open('ignored') as proxy:
                with self.assertRaises(AttributeError):proxy.db
                return proxy.job_tools('fixed-grant').get_actor_context()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(worker)
            for _ in range(100):
                mailbox.drain(store)
                if future.done():break
                time.sleep(.001)
            self.assertEqual(future.result(),{'actor':'scoped'})
        self.assertEqual(seen,[owner]);self.assertEqual(store.job,'fixed-grant');mailbox.close()
        with self.assertRaises(WorldError):mailbox.call(lambda w:None)
    def test_hermes_existing_api_key_alias_without_secret_output(self):
        from unittest.mock import patch
        from puppeteer.runtime import model_configuration
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'config').mkdir()
            (root/'config/model_profiles.yaml').write_text(json.dumps({'credentials_env':'OPENROUTER_KEY','profiles':{'experimental':{'roles':{'puppeteer':{'model_env':'POKEINFLUENCER_PUPPETEER_MODEL','default_model':'fixture:free'}}}}}))
            (root/'.env').write_text('OPENROUTER_API_KEY="dummy-test-key"\nPOKEINFLUENCER_PUPPETEER_MODEL="fixture:free"\n')
            with patch('puppeteer.runtime.ROOT',root),patch.dict('os.environ',{},clear=True):
                model,key=model_configuration();self.assertEqual(model,'fixture:free');self.assertEqual(key,'dummy-test-key')

class CloseoutBudgetTests(unittest.TestCase):
    def test_explicit_rebalance_preserves_charges_and_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'requests.json'
            with CampaignBudget(path) as b:
                for i in range(6):b.charge('puppeteer','job-'+str(i),'fixture:free','hash-'+str(i))
                prior=b.read()['attempts'];b.close();b.rebalance_closeout()
                self.assertEqual(b.read()['attempts'],prior)
                self.assertEqual(b.read()['maximumAttempts'],30)
                self.assertTrue(b.read()['closed'])
                with self.assertRaises(ValueError):b.rebalance_closeout()
                b.continue_authorized_run()
                for i in range(6,10):b.charge('puppeteer','job-'+str(i),'fixture:free','hash-'+str(i))
                with self.assertRaises(ValueError):b.charge('puppeteer','too-many','fixture:free','extra')
                for i in range(16):b.charge('battle','battle-'+str(i),'fixture:free','bhash-'+str(i))
                for i in range(4):b.charge('strategy','strategy-'+str(i),'fixture:free','shash-'+str(i))
                self.assertEqual(len(b.read()['attempts']),30)
                with self.assertRaises(ValueError):b.charge('preparation','over-total','fixture:free','phash')

class TacticalAllocationTests(unittest.TestCase):
    def test_closed_reallocation_cannot_erase_existing_charges(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'requests.json'
            with CampaignBudget(path) as b:
                for i in range(2):b.charge('strategy','s'+str(i),'fixture:free','s'+str(i))
                b.close();b.rebalance_closeout();before=b.read()['attempts']
                b.reallocate_remaining_to_tactics()
                self.assertEqual(b.read()['attempts'],before)
                self.assertEqual(b.read()['roleLimits']['battle'],20)
                self.assertEqual(b.read()['maximumAttempts'],30)
                b.continue_authorized_run()
                with self.assertRaises(ValueError):b.charge('strategy','s2','fixture:free','s2')
                with self.assertRaises(ValueError):b.charge('preparation','p','fixture:free','p')
                for i in range(20):b.charge('battle','b'+str(i),'fixture:free','b'+str(i))
                for i in range(8):b.charge('puppeteer','h'+str(i),'fixture:free','h'+str(i))
                with self.assertRaises(ValueError):b.charge('puppeteer','h8','fixture:free','h8')
                self.assertEqual(len(b.read()['attempts']),30)

class CampaignCodecTests(unittest.TestCase):
    def test_brock_explicit_profile_and_other_trainers_rejected(self):
        from tests.test_battle01 import CodecTests
        from battle.domain import decode
        import struct
        data,abi,_=CodecTests().fixture();struct.pack_into('<H',data,4,414)
        with self.assertRaises(ValueError):decode(data,abi)
        self.assertEqual(decode(data,abi,(102,414))['trainerID'],414)
        struct.pack_into('<H',data,4,103)
        with self.assertRaises(ValueError):decode(data,abi,(102,414))
