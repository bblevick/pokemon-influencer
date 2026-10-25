"""Gate repair: isolated real C1 copies, pure request checks, no hosted calls."""
import copy,json,sqlite3,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from concurrent.futures import Future
from campaign.expansion import ExpansionStore
from strategy.provider import OpenRouterProvider,Limits,ProviderError
from world.save_recovery import receipt_disposition
from world.saves import fingerprint,layout_from_build
from battle.transport import Handler
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/phase6/campaign_expansion01'
class GateRepairTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.e=Path(self.tmp.name);self.path=self.e/'world.sqlite3'
  src=sqlite3.connect('file:'+str(ROOT/'.local/campaign_expansion01/world.sqlite3')+'?mode=ro',uri=True);dst=sqlite3.connect(self.path)
  try:src.backup(dst)
  finally:src.close();dst.close()
  self.w=ExpansionStore(self.path,E/'manifest-native.json');m=json.loads((E/'manifest-native.json').read_text())
  self.save=fingerprint((ROOT/'.local/campaign_expansion01/C1-sally-recovered.sav').read_bytes(),layout_from_build(ROOT/m['rom_path']))
 def tearDown(self):self.w.close();self.tmp.cleanup()
 def pending(self):
  nonce=self.w._one("SELECT nonce FROM launches WHERE status='active'")['nonce'];self.w.begin_save(nonce,self.save);return self.w.pending_save()
 def test_duplicate_native_audit_during_save_is_read_only(self):
  record=next(r for r in self.w.battle_audit() if r.get('event')!='decision-disposition');before=self.w.battle_audit();self.pending()
  self.w.record_battle_audit(record);self.assertEqual(self.w.battle_audit(),before)
  bad=copy.deepcopy(record);bad['nativeSelected']+=1
  with self.assertRaisesRegex(ValueError,'conflicting'):self.w.record_battle_audit(bad)
  new=copy.deepcopy(record);new['nativeRequest']+=9999
  with self.assertRaisesRegex(ValueError,'save barrier'):self.w.record_battle_audit(new)
 def test_duplicate_terminal_during_save_is_read_only(self):
  row=next(r for r in self.w.decision_lifecycle() if r['stage']=='EXECUTED');before=self.w.battle_audit();self.pending()
  self.w.record_decision_lifecycle(row);self.assertEqual(self.w.battle_audit(),before)
  conflicting=copy.deepcopy(row);conflicting['nativeHash']='conflict'
  with self.assertRaisesRegex(ValueError,'conflicting'):self.w.record_decision_lifecycle(conflicting)
  bad=copy.deepcopy(row);bad['scope']['branch']='abandoned'
  with self.assertRaisesRegex(ValueError,'stale'):self.w.record_decision_lifecycle(bad)
 def test_pending_save_survives_reopen_and_old_callback_cannot_pair(self):
  intent=self.pending();self.w.close();self.w=ExpansionStore(self.path,E/'manifest-native.json');self.assertEqual(intent,self.w.pending_save())
  old={'event':'savedataUpdated','nonce':intent['nonce'],'run':1,'counter':intent['old_counter']}
  self.assertEqual(receipt_disposition(intent,old),'historical_callback')
  self.assertEqual(receipt_disposition(intent,{**old,'nonce':0}),'unrelated_run')
  candidate={**old,'counter':(intent['old_counter']+1)&0xffffffff}
  self.assertEqual(receipt_disposition(intent,candidate),'candidate_requires_full_validation')
  with self.assertRaises(ValueError):self.w.finish_save(intent['id'],self.save,candidate)
  self.assertEqual(self.w.pending_save()['id'],intent['id'])
 def test_callback_counter_rollover(self):
  i={'nonce':1,'run':1,'old_counter':0xffffffff};r={'event':'savedataUpdated','nonce':1,'run':1,'counter':0}
  self.assertEqual(receipt_disposition(i,r),'candidate_requires_full_validation')
 def test_c1_restore_is_coherent_and_greg_is_locked(self):
  methods=['verify_replay','verify_memory_replay','verify_social_replay','verify_puppeteer_replay','verify_strategy_replay','verify_decision_replay','verify_virality_replay']
  before={m:getattr(self.w,m)() for m in methods};self.w.restore(self.save)
  self.assertEqual(before,{m:getattr(self.w,m)() for m in methods});self.assertIsNone(self.w.pending_save());self.assertEqual(len(self.w.social_state()['posts']),5)
  self.assertIsNotNone(self.w.locked_preparation('trainer:fr:trainer:0106'))
  with self.assertRaisesRegex(ValueError,'opportunity_unavailable'):self.w.context_packet('trainer:fr:trainer:0106','first')
 def test_pack_requests_are_ordinary_text_without_network_or_charge(self):
  route=json.loads((E/'strategy-preflight.json').read_text());route['checkedAtUnix']=time.time()
  binding={'model':route['model'],'adapterVersion':6,'provider':'openrouter_chat'}
  provider=OpenRouterProvider(binding,'not-a-key',route,None,None,system_prompt=(ROOT/'prompts/strategy_scouting_v3.txt').read_text())
  historic={r['actor']:r['context'] for r in map(json.loads,(E/'causal-trace.jsonl').read_text().splitlines()) if r['event']=='trainer-context'}
  with patch('urllib.request.urlopen',side_effect=AssertionError('network forbidden')):
   for i in [117,106,107,108]:
    actor='trainer:fr:trainer:%04d'%i;context=historic[actor] if actor in historic else self.w.context_packet(actor,'first',provider_binding=binding)
    body,data=provider.prepare_request(context['modelInput'],None,Limits(attempts=1),text=True)
    self.assertFalse({'tools','tool_choice','response_format'}&body.keys());self.assertLessEqual(len(data),24576);self.assertEqual(context['modelInput']['opponentCurrentLead'],'UNKNOWN')
    self.assertTrue(all(f['mode']=='delivered' for f in context['modelInput']['authorizedSocialEvidence']['authorizedFacts']))
   with self.assertRaisesRegex(ProviderError,'request_input_limit'):provider.prepare_request({'oversize':'x'*25000},None,Limits(),text=True)
 def test_future_preflight_failure_records_boundary_before_worker(self):
  from campaign.runtime import Services
  service=Services(self.path,live=False);logs=[];service.log=lambda event,**data:logs.append({'event':event,**data})
  job={'jobID':'offline-diagnostic-fixture','packet':{'modelInput':{}}}
  try:
   with patch('campaign.runtime.configuration',return_value=({'model':'nvidia/nemotron-3.5-lightning:free'},None)),patch('campaign.runtime.preflight_text',side_effect=ProviderError('no_healthy_verified_zero_price_text_route')),patch('campaign.runtime.subprocess.Popen') as worker:
    with self.assertRaises(ProviderError):service.strategy(job)
    worker.assert_not_called();self.assertEqual(logs[-1]['boundary'],'route_metadata');self.assertEqual(logs[-1]['code'],'no_healthy_verified_zero_price_text_route')
  finally:service.mailbox.close();service.pool.shutdown(wait=False)
 def test_text_route_does_not_require_tools_and_rejects_unhealthy_or_paid(self):
  from strategy.provider import qualify_text_route
  route=json.loads((E/'strategy-preflight.json').read_text());catalog={'data':[copy.deepcopy(route['catalog'])]};endpoints={'data':{'endpoints':copy.deepcopy(route['endpoints'])}}
  catalog['data'][0]['supported_parameters']=['max_tokens']
  for endpoint in endpoints['data']['endpoints']:endpoint['supported_parameters']=['max_tokens']
  self.assertEqual(qualify_text_route(route['model'],catalog,endpoints)['mode'],'ordinary-text')
  unhealthy=copy.deepcopy(endpoints)
  for endpoint in unhealthy['data']['endpoints']:endpoint['status']=1
  with self.assertRaisesRegex(ProviderError,'no_healthy_verified_zero_price_text_route'):qualify_text_route(route['model'],catalog,unhealthy)
  paid=copy.deepcopy(catalog);paid['data'][0]['pricing']['completion']='0.1'
  with self.assertRaisesRegex(ProviderError,'catalog_price_unknown_or_paid'):qualify_text_route(route['model'],paid,endpoints)
 def test_restart_strategy_is_revoked_waiting_not_regenerated(self):
  from world.restart import recover_durable_work
  from strategy.memo import fallback_text
  actor='trainer:fr:trainer:0107';job=self.w.begin_strategy(actor,'first');self.w.close();self.w=ExpansionStore(self.path,E/'manifest-native.json')
  recovery=recover_durable_work(self.w);self.assertEqual(recovery['status'],'recovered');self.assertEqual(recovery['operations'][0]['logicalDisposition'],'waiting_future_authorization')
  with self.assertRaisesRegex(ValueError,'stale_strategy_job'):self.w.finish_memo(job['jobID'],fallback_text(job['packet']),'mock',{},job['packet']['contextID'])
  self.assertEqual(recover_durable_work(self.w)['operations'],[])
 def test_restart_waits_for_save_before_recovering_jobs(self):
  from world.restart import recover_durable_work
  job=self.w.begin_strategy('trainer:fr:trainer:0107','first');intent=self.pending()
  recovery=recover_durable_work(self.w);self.assertEqual(recovery['status'],'waiting_save');self.assertEqual(self.w._one('SELECT status FROM strategy_jobs WHERE id=?',(job['jobID'],))['status'],'active')
  self.w.abandon_save(intent['id']);self.assertEqual(recover_durable_work(self.w)['status'],'recovered')
 def test_constructor_recovery_uses_only_durable_installation_prefix(self):
  from campaign.transport import CampaignHandler
  h=CampaignHandler(json.loads((E/'manifest-native.json').read_text()),self.e)
  try:
   h.recover(self.w)
   installed=next(v['receipt'] for v in self.w.decision_state()['installations'].values() if 'cumulativeNativeConstructorCount' in v['receipt'])
   self.assertEqual(h.constructions[(installed['nonce'],installed['generation'])],1)
   self.assertEqual(h.constructions[(installed['nonce'],installed['generation'],117)],1)
  finally:h.close()
 def test_abandoned_native_audit_transport_cannot_commit(self):
  from bridge.events_wire import Message
  h=Handler({},self.e)
  try:
   before=self.w.battle_audit();self.w.restore(self.save)
   with self.assertRaisesRegex(ValueError,'unmanaged'):h.receive(Message(10,1851161028,1,1,1,11,b''),self.w,SimpleNamespace())
   self.assertEqual(before,self.w.battle_audit())
  finally:h.close()
 def test_timeout_matrix_has_one_terminal_and_discards_late_results(self):
  # Virtual monotonic clock avoids race-sensitive sleeps. Real Handler.tick boundary.
  for age,completed in [(1,True),(2.749,True),(2.751,True),(9,True),(9,False)]:
   with self.subTest(age=age,completed=completed):
    h=Handler({},self.e,decision_seconds=2.75);h.recovered=True
    stages=[];h.disposition=lambda record,stage,reason=None:stages.append(stage)
    f=Future()
    if completed:f.set_result({'choiceID':'legal'})
    p={'nativeState':{'nonce':1,'generation':1,'request':1,'battle':1,'turn':1,'phase':'NORMAL_TURN','battler':1},'scope':{'campaign':'c','branch':'b'},'nativeActions':{'legal':256},'actionSetHash':'12345678'}
    record={'request':p,'receivedMonotonic':0};msg=SimpleNamespace(nonce=1,generation=1,sequence=1,tag=1)
    h.job={'future':f,'record':record,'message':msg,'deadline':2.75};h.pending[(1,1,1)]=record
    store=SimpleNamespace(campaign=lambda:{'id':'c','active_branch':'b','status':'paired'},get_active_branch=lambda:'b',_one=lambda *args:{'active':True});sent=[]
    try:
     with patch('battle.transport.time.monotonic',return_value=age):h.tick(store,SimpleNamespace(sendall=sent.append))
     if age<2.75:self.assertEqual(stages,['RESULT_PUBLISHED']);self.assertEqual(len(sent),1)
     else:
      self.assertEqual(stages,['CANCELED_TIMEOUT_FALLBACK']);self.assertEqual(sent,[])
      if not f.done() and not f.cancelled():f.set_result({'choiceID':'legal'})
      h.tick(store,SimpleNamespace(sendall=sent.append));self.assertEqual(sent,[]);self.assertEqual(len(stages),1)
    finally:h.pending.clear();h.close()
if __name__=='__main__':unittest.main()
