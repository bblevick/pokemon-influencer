import json,tempfile,unittest
from pathlib import Path
from campaign.budget import CampaignBudget,RIVAL_LIMITS
from world.store import WorldError
class RivalBudgetTests(unittest.TestCase):
 def test_nonfungible_lower_readiness_caps(self):
  with tempfile.TemporaryDirectory() as d,CampaignBudget(Path(d)/'requests.json') as b:
   b.authorize_rival();self.assertEqual(b.read()['roleLimits'],RIVAL_LIMITS)
   for role,cap in RIVAL_LIMITS.items():
    for n in range(cap):b.charge(role,f'{role}{n}','verified-free-model',f'{role}{n}')
    with self.assertRaises(WorldError):b.charge(role,role+'excess','verified-free-model','excess')
   self.assertEqual(len(b.read()['attempts']),37)
   b.close();b.continue_authorized_run()
   with self.assertRaises(WorldError):b.charge('battle','new','verified-free-model','new')
 def test_tampered_limits_and_historical_authorizations_rejected(self):
  with tempfile.TemporaryDirectory() as d,CampaignBudget(Path(d)/'requests.json') as b:
   b.authorize_rival();v=b.read();v['roleLimits']['strategy']=3;b.write(v)
   with self.assertRaises(WorldError):b.read()

 def test_runtime_guards_reject_other_actor_and_oversized_packet_before_provider(self):
  from campaign.rival_runtime import RivalServices,ACTOR
  service=object.__new__(RivalServices)
  with self.assertRaisesRegex(ValueError,'rival_strategy_scope'):
   service.strategy({'packet':{'scope':{'actor':'trainer:fr:trainer:0091'},'modelInput':{'encounter':{'nativeTrainerID':91}}}})
  with self.assertRaisesRegex(ValueError,'rival_context_budget'):
   service.strategy({'packet':{'scope':{'actor':ACTOR},'modelInput':{'encounter':{'nativeTrainerID':334},'oversized':'x'*8192}}})
