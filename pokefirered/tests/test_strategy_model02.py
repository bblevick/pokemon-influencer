"""Generic metadata nullability and text contract; no hosted requests."""
import copy,json,unittest
from pathlib import Path
from strategy.provider import qualify_text_route,ProviderError
ROOT=Path(__file__).resolve().parents[1]
class Model02Tests(unittest.TestCase):
 def setUp(self):self.s=json.loads((ROOT/'evidence/phase3/strategy_model02/gemma-metadata.json').read_text());self.model='google/gemma-4-31b-it:free'
 def test_published_null_short_uptime_uses_known_daily_metric(self):
  route=qualify_text_route(self.model,self.s['catalog'],self.s['endpoints']);self.assertEqual(route['healthEvidence'],{'Google AI Studio':'uptime_last_1d'})
 def test_zero_short_measurement_or_inactive_is_not_overridden(self):
  for changes in ({'uptime_last_5m':0},{'status':-2},{'uptime_last_1d':None},{'uptime_last_5m':-1},{'uptime_last_1d':101}):
   s=copy.deepcopy(self.s);s['endpoints']['data']['endpoints'][0].update(changes)
   with self.assertRaises(ProviderError):qualify_text_route(self.model,s['catalog'],s['endpoints'])
 def test_text_only_needs_no_tools_or_json_and_rejects_paid(self):
  s=copy.deepcopy(self.s);s['catalog']['data'][0]['supported_parameters']=['max_tokens'];s['endpoints']['data']['endpoints'][0]['supported_parameters']=['max_tokens']
  self.assertEqual(qualify_text_route(self.model,s['catalog'],s['endpoints'])['model'],self.model)
  s['endpoints']['data']['endpoints'][0]['pricing']['prompt']='0.001'
  with self.assertRaises(ProviderError):qualify_text_route(self.model,s['catalog'],s['endpoints'])
if __name__=='__main__':unittest.main()
