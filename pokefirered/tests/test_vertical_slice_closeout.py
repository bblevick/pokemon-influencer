"""New authorization/isolation regressions, no hosted requests or emulator claims."""
import copy,json,tempfile,unittest
from pathlib import Path
from campaign.budget import CampaignBudget
from world.store import WorldError
from tests.test_vertical_slice01 import FirstGymTests

class AdditionalAllowanceTests(unittest.TestCase):
 def seed(self,path):
  with CampaignBudget(path) as b:
   for role,count in (('puppeteer',6),('strategy',2),('battle',2)):
    for i in range(count):b.charge(role,role+str(i),'fixture:free',role+str(i))
   b.close();b.rebalance_closeout();b.reallocate_remaining_to_tactics();b.continue_authorized_run()
   for i in range(2,20):b.charge('battle','battle'+str(i),'fixture:free','battle'+str(i))
   for i in range(2):b.charge('puppeteer','later'+str(i),'fixture:free','later'+str(i))
   b.close()
 def test_seventy_cap_preserves_original_thirty_and_role_exclusions(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'budget.json';self.seed(path)
   with CampaignBudget(path) as b:
    original=copy.deepcopy(b.read()['attempts']);b.authorize_gym_closeout()
    self.assertEqual(b.read()['attempts'],original)
    with self.assertRaises(WorldError):b.authorize_gym_closeout()
    b.continue_authorized_run()
    for role in ('strategy','preparation'):
     with self.assertRaises(WorldError):b.charge(role,'forbidden','fixture:free',role)
    for i in range(36):b.charge('battle','new'+str(i),'fixture:free','new'+str(i))
    with self.assertRaises(WorldError):b.charge('battle','over','fixture:free','over')
    for i in range(4):b.charge('puppeteer','recap'+str(i),'fixture:free','recap'+str(i))
    self.assertEqual(len(b.read()['attempts']),70)
    self.assertEqual(b.read()['attempts'][:30],original)
    with self.assertRaises(WorldError):b.charge('puppeteer','extra','fixture:free','extra')
    b.close()
    with self.assertRaises(WorldError):b.continue_authorized_run()
 def test_original_receipts_cannot_be_changed_after_extension(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'budget.json';self.seed(path)
   with CampaignBudget(path) as b:
    b.authorize_gym_closeout();before=copy.deepcopy(b.read()['attempts'])
    with self.assertRaises(WorldError):b.finish(1,{'costUSD':0})
    self.assertEqual(b.read()['attempts'],before)
   value=json.loads(path.read_text());value['attempts'][0]['jobID']='rewritten';path.write_text(json.dumps(value))
   with CampaignBudget(path) as b:
    with self.assertRaises(WorldError):b.read()

class CleanRestoreTests(FirstGymTests):
 # Inherited host tests remain the separately labeled prior fixture suite.
 def test_gym_closeout_scheduler_cannot_generate_missing_strategy(self):
  from campaign.runtime import Services
  from unittest.mock import patch
  self.publish_rick();self.checkpoint(False)
  scheduler=Services(str(self.path),live=True,gym_closeout=True)
  with patch.object(scheduler,'log'):
   scheduler.tick(self.w)
   self.assertEqual(self.w.memo_records(),[]);self.assertIsNone(scheduler.worker)
   scheduler.close(self.w)

class ScopeTests(unittest.TestCase):
 def test_gym_only_provider_never_calls_for_rick(self):
  from campaign.provider import CampaignBattleProvider
  from unittest.mock import patch
  provider=CampaignBattleProvider(lambda:{},gym_closeout=True)
  with patch('campaign.provider.subprocess.run') as request:
   self.assertIsNone(provider.decide_scoped({'nativeState':{'trainerID':102}}))
   request.assert_not_called()

if __name__=='__main__':unittest.main()
