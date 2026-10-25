"""Backup configuration and shared contract tests; no credentials/network read."""
import unittest,tempfile,json,os,copy
from pathlib import Path
from unittest.mock import patch
from strategy.provider import live_configuration,LiveBudget,ProviderError,qualify_route
from strategy.context import build_context
from tests import test_strategy01 as fixture
class BackupConfigurationTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);(self.root/'config').mkdir()
  config=json.loads(Path('config/model_profiles.yaml').read_text());(self.root/'config/model_profiles.yaml').write_text(json.dumps(config))
  (self.root/'.env').write_text("OPENROUTER_KEY='private-fixture-key'\nPOKEINFLUENCER_STRATEGY_MODEL=primary:free\nPOKEINFLUENCER_STRATEGY_MODEL_BACKUP='backup:free'\nPOKEINFLUENCER_STRATEGY_MODEL_BACKUP_BACKUP = 'third:free'\nPOKEINFLUENCER_MODEL_BACKUP='openrouter/free'\nUNRELATED_SECRET=do-not-read\n")
 def tearDown(self):self.temp.cleanup()
 def resolve(self,role='primary'):
  with patch('strategy.provider.ROOT',self.root),patch.dict(os.environ,{},clear=True):return live_configuration(role)
 def test_explicit_roles_default_primary_no_chain(self):
  self.assertEqual(self.resolve()[0]['model'],'primary:free')
  self.assertEqual(self.resolve('backup')[0]['model'],'backup:free')
  self.assertEqual(self.resolve('backup_backup')[0]['model'],'third:free')
  self.assertNotIn('private-fixture-key',json.dumps(self.resolve('backup')[0]))
 def test_no_silent_role_fallback(self):
  (self.root/'.env').write_text('OPENROUTER_KEY=private-fixture-key\n')
  with self.assertRaisesRegex(ProviderError,'missing_strategy_model_role'):self.resolve('backup')
 def test_paid_role_rejected(self):
  (self.root/'.env').write_text('OPENROUTER_KEY=private-fixture-key\nPOKEINFLUENCER_STRATEGY_MODEL_BACKUP=paid-model\n')
  with self.assertRaisesRegex(ProviderError,'free_model_required'):self.resolve('backup')
 def test_unknown_role_and_unqualified_router_rejected(self):
  with self.assertRaisesRegex(ProviderError,'unknown_strategy_model_role'):self.resolve('arbitrary')
  with self.assertRaisesRegex(ProviderError,'unqualified_dynamic_model_router'):self.resolve('emergency')
 def test_configuration_not_overwritten(self):
  before=(self.root/'.env').read_bytes();self.resolve('backup');self.assertEqual(before,(self.root/'.env').read_bytes())
 def test_explicit_process_test_override_only(self):
  with patch('strategy.provider.ROOT',self.root),patch.dict(os.environ,{'POKEINFLUENCER_STRATEGY_MODEL_BACKUP_BACKUP':'test-override:free'},clear=True):b,k=live_configuration('backup_backup')
  self.assertEqual(b['model'],'test-override:free');self.assertIn('third:free',(self.root/'.env').read_text())
 def test_five_request_cap_survives_default_adapter_reopen(self):
  path=self.root/'ledger.json'
  with LiveBudget(path,5) as b:
   b.write(b.read())
   for i in range(5):b.charge(str(i),'backup:free')
  with LiveBudget(path) as b:
   self.assertEqual(b.read()['maximumAttempts'],5)
   with self.assertRaisesRegex(ProviderError,'budget'):b.charge('sixth','backup:free')
 def test_invalid_caps_rejected(self):
  for cap in (0,11,True):
   with self.assertRaises(ValueError):LiveBudget(self.root/'cap.json',cap)
 def test_standard_credential_alias_stays_host_only(self):
  (self.root/'.env').write_text('OPENROUTER_API_KEY=private-alias-key\nPOKEINFLUENCER_STRATEGY_MODEL_BACKUP=backup:free\n')
  binding,key=self.resolve('backup');self.assertEqual(key,'private-alias-key');self.assertNotIn(key,json.dumps(binding))
 def test_forced_tool_choice_capability_rejection(self):
  row={'id':'backup:free','pricing':{'prompt':'0','completion':'0'},'supported_parameters':['tools','max_tokens']}
  with self.assertRaisesRegex(ProviderError,'required_tool_parameters_unavailable'):qualify_route('backup:free',{'data':[row]},{'data':{'endpoints':[]}})
class BackupContextTests(unittest.TestCase):
 # Run only this additional fixture, inherited cases covered by existing focused suite.
 def test_provider_selection_leaves_model_context_identical(self):
  test=fixture.StrategyTests('test_context_no_selection_or_frequency');test.setUp()
  try:
   test.eligible();primary=build_context(test.w,'trainer:fr:trainer:0102',provider_binding={'provider':'openrouter_chat','model':'primary:free','adapterVersion':5});backup=build_context(test.w,'trainer:fr:trainer:0102',provider_binding={'provider':'openrouter_chat','model':'backup:free','adapterVersion':5})
   self.assertEqual(primary['modelInput'],backup['modelInput']);self.assertEqual(primary['candidateCount'],backup['candidateCount']);self.assertEqual(primary['scope']['envelopeID'],backup['scope']['envelopeID']);self.assertNotEqual(primary['materialContextSHA256'],backup['materialContextSHA256'])
  finally:test.tearDown()
