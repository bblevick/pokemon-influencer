"""Actual adapter with mocked HTTP, real isolated durable memo and restart; no network."""
import io,json,sqlite3,tempfile,time,unittest,urllib.error,subprocess,sys
from concurrent.futures import Future
from pathlib import Path
from unittest.mock import patch
from campaign.expansion import ExpansionStore
from campaign.expansion_runtime import ExpansionServices
from strategy.provider import OpenRouterProvider,Limits,ProviderError
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/phase6/campaign_expansion01_gate_repair'
class BadResponse:
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def read(self,n):return b'{invalid'
class DiagnosticsTests(unittest.TestCase):
 def test_parent_preserves_worker_diagnostic_and_scope(self):
  from campaign.runtime import Services
  from types import SimpleNamespace
  from strategy.diagnostics import failure_diagnostics
  with tempfile.TemporaryDirectory() as tmp:
   service=Services(Path(tmp)/'unused.sqlite3');logs=[];service.log=lambda event,**data:logs.append({'event':event,**data})
   binding={'provider':'openrouter_chat','model':'fixture:free','adapterVersion':6}
   route={'checkedAtUnix':time.time(),'model':'fixture:free','providerName':'Fixture','providerNames':['Fixture'],'endpoint':{'supported_parameters':[]}}
   job={'jobID':'mock-logical-job','packet':{'scope':{'actor':'trainer:fr:trainer:0106','campaign':'test','branch':'test','restore_epoch':3,'cutoff':217},'contextID':'test-context','modelInput':{}}}
   diagnostic=failure_diagnostics(ProviderError('http_429'),job=job['jobID'],binding=binding,stage='provider_request')
   worker=SimpleNamespace(returncode=1,communicate=lambda *a,**kw:('',json.dumps({'diagnostics':diagnostic})),poll=lambda:1)
   try:
    with patch('campaign.runtime.configuration',return_value=(binding,None)),patch('campaign.runtime.preflight_text',return_value=route),patch('campaign.runtime.subprocess.Popen',return_value=worker):
     with self.assertRaises(ValueError) as caught:service.strategy(job)
    d=caught.exception.diagnostics
    self.assertEqual(d['category'],'rate_limit');self.assertEqual(d['httpStatus'],429);self.assertEqual(d['scope'],job['packet']['scope']);self.assertEqual(d['contextID'],'test-context')
    self.assertTrue(any(r.get('diagnostics')==d for r in logs))
   finally:service.mailbox.close();service.pool.shutdown(wait=False)
 def test_six_failure_categories_persist_across_real_store_reopen(self):
  results=[]
  cases=[('http400',urllib.error.HTTPError('https://fixture',400,'rejected',{},io.BytesIO(b'{}')),'http_rejection',400),('http429',urllib.error.HTTPError('https://fixture',429,'limited',{},io.BytesIO(b'{}')),'rate_limit',429),('timeout',TimeoutError('DO NOT STORE secret-key'),'timeout',None),('network',OSError('DO NOT STORE secret-key'),'transport',None),('malformed',None,'malformed_response',None),('preflight',ProviderError('no_healthy_verified_zero_price_text_route'),'preflight_rejection',None)]
  for name,error,category,status in cases:
   with self.subTest(case=name),tempfile.TemporaryDirectory() as tmp:
    db=Path(tmp)/'world.sqlite3';src=sqlite3.connect('file:'+str(ROOT/'.local/campaign_expansion01/world.sqlite3')+'?mode=ro',uri=True);dst=sqlite3.connect(db);src.backup(dst);src.close();dst.close()
    binding={'provider':'openrouter_chat','model':'fixture:free','adapterVersion':6}
    with ExpansionStore(db,ROOT/'evidence/phase6/campaign_expansion01/manifest-native.json') as w:
     job=w.begin_strategy('trainer:fr:trainer:0107','first',provider_binding=binding)
     route={'checkedAtUnix':time.time(),'model':'fixture:free','providerName':'Fixture','endpoint':{'supported_parameters':[]}}
     provider=OpenRouterProvider(binding,'secret-key',route,Path(tmp)/'mock-budget.json',job['jobID'])
     if name=='preflight':route['model']='different:free'
     try:
      with patch('urllib.request.urlopen',side_effect=error,return_value=BadResponse()) as http:
       provider.complete(job['packet']['modelInput'],Limits(attempts=1))
     except Exception as failure:
      d=failure.diagnostics
      # Worker-owned diagnostic is enriched by the parent with the trusted scope.
      d.update(contextID=job['packet']['contextID'],scope=job['packet']['scope'])
      self.assertEqual(d['category'],category);self.assertEqual(d['httpStatus'],status)
      self.assertNotIn('secret-key',json.dumps(d));self.assertNotIn('DO NOT STORE',json.dumps(d))
      future=Future();future.set_exception(failure)
     else:self.fail('failure was accepted')
     if name=='preflight':http.assert_not_called()
     service=ExpansionServices(db,live=False);service.worker=future;service.job=job;service.kind='strategy';service.stopped=True
     log=Path(tmp)/'diagnostics.jsonl'
     def record(event,**data):
      with log.open('a') as f:f.write(json.dumps({'event':event,**data})+'\n')
     service.log=record
     try:service.tick(w)
     finally:service.mailbox.close();service.pool.shutdown(wait=False)
     memo=next(m for m in w.memo_records() if m['jobID']==job['jobID'])
     self.assertEqual(memo['diagnostics']['diagnostics'],d)
     expected=json.loads(log.read_text().splitlines()[0])
    with ExpansionStore(db,ROOT/'evidence/phase6/campaign_expansion01/manifest-native.json') as reopened:
     actual=next(m for m in reopened.memo_records() if m['jobID']==job['jobID'])
     self.assertEqual(actual,memo);self.assertEqual(json.loads(log.read_text().splitlines()[0]),expected)
     reopened.verify_strategy_replay()
    code='import json,sys; from campaign.expansion import ExpansionStore; from pathlib import Path; w=ExpansionStore(Path(sys.argv[1]),Path(sys.argv[2])); print(json.dumps(next(m for m in w.memo_records() if m["jobID"]==sys.argv[3]))); w.close()'
    fresh=json.loads(subprocess.check_output([sys.executable,'-c',code,str(db),str(ROOT/'evidence/phase6/campaign_expansion01/manifest-native.json'),job['jobID']],cwd=ROOT,text=True))
    self.assertEqual(fresh,memo)
    results.append({'freshProcessReloadPassed':True,'case':name,'category':category,'httpStatus':status,'durableMemoSurvivedReopen':True,'evidenceCollectionSurvived':True,'diagnostics':d})
  (E/'future-diagnostics.json').write_text(json.dumps({'hostedGenerationRequests':0,'cases':results,'pairedCheckpointApplicability':'Diagnostics belong to guarded durable memo history; checkpoint visibility/rollback is covered by retained strategy/save regressions. External diagnostic logs are incident evidence, never NPC knowledge.'},indent=2)+'\n')
if __name__=='__main__':unittest.main()
