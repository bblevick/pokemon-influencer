"""Only final authorization bounds; no providers or emulator fixtures."""
import unittest,tempfile,copy,json
from pathlib import Path
from campaign.budget import CampaignBudget
from world.store import WorldError
from tests.test_vertical_slice_closeout import AdditionalAllowanceTests
class FinalBudgetTests(unittest.TestCase):
 def seed(self,path):
  AdditionalAllowanceTests().seed(path)
  with CampaignBudget(path) as b:
   b.authorize_gym_closeout();b.continue_authorized_run()
   for i in range(36):b.charge('battle','gym'+str(i),'fixture:free','gym'+str(i))
   b.close()
 def test_final_allowance_freezes66_and_roles(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'ledger.json';self.seed(p)
   with CampaignBudget(p) as b:
    old=copy.deepcopy(b.read()['attempts']);b.authorize_final_closeout();self.assertEqual(b.read()['attempts'],old)
    with self.assertRaises(WorldError):b.authorize_final_closeout()
    with self.assertRaises(WorldError):b.finish(66,{'rewritten':True})
    b.continue_authorized_run()
    for role in ('strategy','preparation'):
     with self.assertRaises(WorldError):b.charge(role,'no','fixture:free','no')
    for i in range(80):b.charge('battle','final'+str(i),'fixture:free','final'+str(i))
    with self.assertRaises(WorldError):b.charge('battle','over','fixture:free','over')
    for i in range(4):b.charge('puppeteer','recap'+str(i),'fixture:free','recap'+str(i))
    self.assertEqual(len(b.read()['attempts']),150);self.assertEqual(b.read()['attempts'][:66],old)
    b.close()
    with self.assertRaises(WorldError):b.continue_authorized_run()
 def test_tampered_original66_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'ledger.json';self.seed(p)
   with CampaignBudget(p) as b:b.authorize_final_closeout()
   value=json.loads(p.read_text());value['attempts'][65]['jobID']='changed';p.write_text(json.dumps(value))
   with CampaignBudget(p) as b:
    with self.assertRaises(WorldError):b.read()
