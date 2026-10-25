"""Memo fixtures and mocked transport; no network or emulator claims."""
import unittest,json,copy,time
from unittest.mock import patch
from tests import test_prep01 as f
from tests import test_strategy01_provider as transport_f
from strategy.memo import MemoStore,validate_text,run_memo_job
from strategy.store import StrategyStore
from strategy.provider import FixtureProvider,Limits,ProviderError,qualify_text_route

TEXT='  Rick suspects Bulbasaur might return, but the next lead is unknown.\nHe wants to protect his partners — even if his prediction is wrong.  '
class MemoTests(unittest.TestCase):
    def setUp(self):
        f.PrepTests.setUp(self);self.w.close();self.w=MemoStore(self.path,f.BUILD,f.TAG)
    def tearDown(self):f.PrepTests.tearDown(self)
    battle=f.PrepTests.battle
    checkpoint=f.PrepTests.checkpoint
    eligible=f.PrepTests.eligible
    def job(self):self.eligible();return self.w.begin_strategy(f.RICK)
    def test_exact_subjective_text_not_facts_or_choices(self):
        job=self.job();before=[self.w.preparation_state(),self.w.trainer_packet(f.RICK),self.w.trainer_packet(f.JANICE)]
        result=run_memo_job(self.w,job,FixtureProvider(TEXT));self.assertEqual(result['strategyText'],TEXT)
        self.assertEqual(before,[self.w.preparation_state(),self.w.trainer_packet(f.RICK),self.w.trainer_packet(f.JANICE)])
        self.assertEqual(job['packet']['candidateCount'],16);self.assertNotIn('normalizedOutput',result)
        self.assertEqual(result['actor'],f.RICK);self.assertEqual(result['scope'],job['packet']['scope'])
    def test_bounds_encoding_controls_only(self):
        self.assertEqual(validate_text(TEXT),TEXT)
        self.assertEqual(validate_text('I own a dragon and predict candidate 7.'),'I own a dragon and predict candidate 7.')
        for text in ('','  ',None,'x'*4097,'é'*2049,'\ud800','x\x00','x\x1b','x\x7f','x\x85','x\u202e','x\u200b','x\t'):
            with self.assertRaises(ValueError):validate_text(text)
    def test_restart_and_repeat_no_generation(self):
        job=self.job();provider=FixtureProvider(TEXT);r=run_memo_job(self.w,job,provider)
        self.w.close();self.w=MemoStore(self.path,f.BUILD,f.TAG)
        self.assertEqual(run_memo_job(self.w,self.w.begin_strategy(f.RICK),provider),r);self.assertEqual(provider.calls,1)
    def test_single_invalid_or_failed_completion_fallback(self):
        self.eligible()
        for value,error in [('',None),(None,'provider_error_502')]:
            job=self.w.begin_strategy(f.RICK,provider_binding={'provider':'fixture','model':str(error),'adapterVersion':1});provider=FixtureProvider(value,error)
            r=run_memo_job(self.w,job,provider);self.assertEqual(provider.calls,1);self.assertEqual(r['source'],'fallback');self.assertTrue(r['strategyText'])
    def test_pair_restore_excludes_future_exact_reload(self):
        job=self.job();before=self.save;r=run_memo_job(self.w,job,FixtureProvider(TEXT));self.checkpoint(True);after=self.save
        self.w.restore(before);self.assertEqual(self.w.memo_records(),[])
        with self.assertRaises(ValueError):self.w.finish_memo(job['jobID'],TEXT,'mock',{},job['packet']['contextID'])
        self.w.restore(after);self.assertEqual(self.w.recorded_strategy(f.RICK)['decision'],r)
    def test_fork_does_not_inherit_future(self):
        job=self.job();before=self.save;r=run_memo_job(self.w,job,FixtureProvider(TEXT));self.w.restore(before);new=self.w.begin_strategy(f.RICK)
        self.assertNotEqual(new['packet']['scope']['branch'],r['scope']['branch']);self.assertEqual(self.w.memo_records(),[])
    def test_save_barrier_and_wrong_grant(self):
        job=self.job()
        with self.assertRaises(ValueError):self.w.finish_memo(job['jobID'],TEXT,'mock',{},'wrong')
        intent=self.w.begin_save(self.nonce,self.save)
        with self.assertRaises(ValueError):self.w.finish_memo(job['jobID'],TEXT,'mock',{},job['packet']['contextID'])
        self.w.abandon_save(intent)
    def test_single_attempt_survives_restart(self):
        job=self.job();self.w.count_attempt(job['jobID'],job['packet']['contextID']);self.w.close();self.w=MemoStore(self.path,f.BUILD,f.TAG)
        provider=FixtureProvider(TEXT);r=run_memo_job(self.w,job,provider);self.assertEqual(provider.calls,0);self.assertEqual(r['source'],'fallback')
    def test_legacy_writer_refused(self):
        with self.assertRaises(ValueError):StrategyStore(self.path,f.BUILD,f.TAG)
    def test_no_candidate_ids_in_context_and_current_binding(self):
        job=self.job();self.assertNotIn('candidateID',json.dumps(job['packet']['modelInput']))
        self.assertEqual(job['packet']['scope']['strategySchemaVersion'],3);self.assertEqual(job['packet']['scope']['promptVersion'],2)

class MemoProviderTests(unittest.TestCase):
    setUp=transport_f.ProviderTests.setUp
    tearDown=transport_f.ProviderTests.tearDown
    def reply(self):return {'model':'fixture:free','choices':[{'finish_reason':'stop','message':{'content':TEXT,'reasoning':'PRIVATE'}}],'usage':{'completion_tokens':90,'prompt_tokens':200,'total_tokens':290,'cost':0}}
    def test_plain_wire_no_structured_requirements(self):
        def http(req,timeout):
            body=json.loads(req.data)
            for key in ('tools','tool_choice','response_format','models'):self.assertNotIn(key,body)
            self.assertEqual(body['provider']['max_price'],{'prompt':0,'completion':0});self.assertEqual(body['model'],'fixture:free');return transport_f.Response(self.reply())
        with patch('urllib.request.urlopen',http):text,d=self.provider.complete({'actor':'Rick'},Limits(attempts=1))
        self.assertEqual(text,TEXT);audit=json.loads(self.budget.read_text());self.assertNotIn('PRIVATE',json.dumps(audit));self.assertNotIn('dummy-key',json.dumps(audit))
    def test_text_capability_not_tool_capability(self):
        row={'id':'fixture:free','pricing':{'prompt':'0','completion':'0'},'supported_parameters':['max_tokens']}
        ep={**row,'model_id':'fixture:free','provider_name':'Fixture','status':0,'uptime_last_5m':100}
        route=qualify_text_route('fixture:free',{'data':[row]},{'data':{'endpoints':[ep]}})
        self.assertEqual(route['catalog']['supported_parameters'],['max_tokens']);self.assertNotIn('supports_tool_choice',route['endpoint'])
        ep['pricing']={'prompt':'1','completion':'0'}
        with self.assertRaises(ProviderError):qualify_text_route('fixture:free',{'data':[row]},{'data':{'endpoints':[ep]}})
    def test_refusal_truncation_control_and_missing_text_rejected(self):
        for variant in ('length','refusal','control','missing'):
            r=self.reply()
            if variant=='length':r['choices'][0]['finish_reason']='length'
            if variant=='refusal':r['choices'][0]['message']['refusal']='refused'
            if variant=='control':r['choices'][0]['message']['content']='x\x1b'
            if variant=='missing':r['choices'][0]['message']['content']=None
            with patch('urllib.request.urlopen',return_value=transport_f.Response(r)),self.assertRaises(ValueError):self.provider.complete({},Limits())
    def test_text_cost_identity_error_bounds(self):
        for variant in ('cost','model','tokens','error'):
            r=self.reply()
            if variant=='cost':r['usage']['cost']=1
            if variant=='model':r['model']='other'
            if variant=='tokens':r['usage']['completion_tokens']=1801
            if variant=='error':r={'error':{'code':502,'message':'upstream'}}
            # Separate ledger for each request, otherwise per-job cap stops fourth.
            self.provider.job=variant
            with patch('urllib.request.urlopen',return_value=transport_f.Response(r)),self.assertRaises(ProviderError):self.provider.complete({},Limits())
