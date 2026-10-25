"""Generic host envelope, discard isolation and bounded qualification authority."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from puppeteer.recap_contract import RECAP_VERSION,HOST_FIELDS,model_result_schema,build_submission
from puppeteer.runtime import run_job,cleanup
from puppeteer.qualification import open_qualification,QualificationStore
from puppeteer.store import PuppeteerStore
from campaign.budget import CampaignBudget
from world.store import WorldError
from hermes_qualification_fixture import create_fixture
import test_hermes01 as fixtures

class EnvelopeTests(unittest.TestCase):
    setUp=fixtures.PuppeteerTests.setUp
    tearDown=fixtures.PuppeteerTests.tearDown
    battle=fixtures.PuppeteerTests.battle
    job=fixtures.PuppeteerTests.job
    def content(self):
        self.battle();job=self.job('mock');full=self.w.fallback_result(job['jobID'])
        return job,full,{k:v for k,v in full.items() if k not in HOST_FIELDS}
    def test_host_owned_missing_version_and_identity(self):
        job,full,content=self.content();self.assertEqual(build_submission(content,job['scope']),full)
        for key in HOST_FIELDS:self.assertNotIn(key,model_result_schema()['properties'])
        outcome=self.w.job_tools(job['jobID']).submit_recap_and_memory_result(content)
        self.assertEqual(outcome['producer'],'hermes');self.assertEqual(len(self.w.social_state()['posts']),1)
        with self.assertRaises(WorldError):self.w.job_tools(job['jobID'])
    def test_current_compatibility_old_future_malformed_rejected(self):
        job,full,content=self.content();self.assertEqual(build_submission(full,job['scope']),full)
        for version in (RECAP_VERSION-1,RECAP_VERSION+1,'1',True,None,1.0):
            with self.assertRaises(WorldError):build_submission({**content,'schemaVersion':version},job['scope'])
        for key in HOST_FIELDS[1:]:
            with self.assertRaises(WorldError):build_submission({**content,key:'forged'},job['scope'])
        # Domain validator remains strict; normalization is only at the adapter.
        with self.assertRaises(WorldError):self.w.settle_job(job['jobID'],content,producer='hermes')
    def test_malformed_content_keeps_mandatory_fallback(self):
        job,full,content=self.content()
        for bad in (None,[],{}, {**content,'summary':'invented'}, {**content,'privateEvidenceIDs':['f'*64]}):
            with self.assertRaises(WorldError):self.w.job_tools(job['jobID']).submit_recap_and_memory_result(bad)
        outcome=self.w.fallback(job['jobID'],'invalid_output');self.assertEqual(outcome['producer'],'deterministic_fallback')
        sha=self.w.verify_puppeteer_replay();self.w.close();self.w=PuppeteerStore(self.path,fixtures.BUILD,fixtures.TAG)
        self.assertEqual(self.w.verify_puppeteer_replay(),sha)
        with self.assertRaises(WorldError):self.w.begin_job(outcome['obligationID'],'mock')
        self.assertEqual(len(self.w.social_state()['posts']),1)
    def test_success_terminal_does_not_regenerate(self):
        job,full,content=self.content();out=self.w.job_tools(job['jobID']).submit_recap_and_memory_result(content)
        with self.assertRaises(WorldError):self.w.begin_job(out['obligationID'],'mock')
        self.assertEqual(len(self.w.social_state()['posts']),1)

class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'qualification.sqlite3';self.fixture=create_fixture(self.path)
    def tearDown(self):self.tmp.cleanup()
    def test_actual_hermes_mocked_transport_uses_discard_sink(self):
        result=run_job(self.path,self.fixture['jobID'],behavior='content',experiment='closeout',store_factory=open_qualification)
        self.assertTrue(result['outcome']['qualificationValid'],result['failures']);self.assertFalse(result['outcome']['committed']);self.assertEqual(len(result['requests']),2)
        trusted=result['tools'][-1]['trustedSubmission'];self.assertEqual(trusted['schemaVersion'],RECAP_VERSION)
        self.assertNotIn('schemaVersion',result['tools'][-1]['arguments']['result'])
        with open_qualification(self.path) as w:
            self.assertEqual(self.fixture['hashes'],{k:getattr(w,k)() for k in self.fixture['hashes']});self.assertFalse(w.social_state()['posts']);self.assertFalse(w.puppeteer_state()['episodes'])
            with self.assertRaises(WorldError):w.job_tools(self.fixture['jobID'])
        cleanup(Path(result['runtimeHome']),False)
    def test_parser_failure_is_discard_only(self):
        result=run_job(self.path,self.fixture['jobID'],behavior='parse-error',experiment='closeout',store_factory=open_qualification)
        self.assertFalse(result['outcome']['qualificationValid']);self.assertFalse(result['outcome']['committed'])
        with open_qualification(self.path) as w:self.assertEqual(self.fixture['hashes'],{k:getattr(w,k)() for k in self.fixture['hashes']})
        cleanup(Path(result['runtimeHome']),False)
    def test_reject_active_campaign_and_unowned_fixture_before_writes(self):
        path=Path(self.tmp.name)/'ordinary.sqlite3'
        with PuppeteerStore(path,fixtures.BUILD,fixtures.TAG):pass
        before=path.read_bytes()
        with self.assertRaises(WorldError):QualificationStore(path,fixtures.BUILD,fixtures.TAG)
        self.assertEqual(before,path.read_bytes())
        with self.assertRaises(WorldError):open_qualification(ROOT/'.local/rocket01/world.sqlite3')
    def test_failed_qualification_has_no_post_or_episode(self):
        result=run_job(self.path,self.fixture['jobID'],behavior='invalid',experiment='closeout',store_factory=open_qualification)
        self.assertFalse(result['outcome']['qualificationValid']);self.assertFalse(result['outcome']['committed'])
        with open_qualification(self.path) as w:
            self.assertEqual(self.fixture['hashes'],{k:getattr(w,k)() for k in self.fixture['hashes']});self.assertFalse(w.social_state()['posts'])
        cleanup(Path(result['runtimeHome']),False)

class DispositionBudgetTests(unittest.TestCase):
    def test_only_four_new_hermes_attempts_prior_sixteen_frozen(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'ledger.json';prior=json.loads((ROOT/'evidence/phase7/rocket01/hermes-disposition/prior-requests.json').read_text());path.write_text(json.dumps(prior))
            with CampaignBudget(path) as b:
                b.authorize_rocket_qualification()
                self.assertEqual(b.read()['attempts'],prior['attempts'])
                for role in ('strategy','preparation','battle'):
                    with self.assertRaises(WorldError):b.charge(role,'qualification:test','verified-free','test')
                with self.assertRaises(WorldError):b.charge('puppeteer','production:recap','verified-free','test')
                with self.assertRaises(WorldError):b.finish(1,{'modifiedHistory':True})
                for i in range(4):b.charge('puppeteer','qualification:'+str(i),'verified-free',str(i))
                with self.assertRaises(WorldError):b.charge('puppeteer','qualification:fifth','verified-free','fifth')
                b.close()
                with self.assertRaises(WorldError):b.charge('puppeteer','qualification:closed','verified-free','closed')
if __name__=='__main__':unittest.main()
