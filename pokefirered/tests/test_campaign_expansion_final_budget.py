"""Authorization accounting only; mock charges, no provider requests."""
import copy,json,tempfile,unittest
from pathlib import Path
from campaign.budget import CampaignBudget
ROOT=Path(__file__).resolve().parents[1]
class FinalBudgetTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'requests.json'
  self.value=json.loads((ROOT/'evidence/phase6/campaign_expansion01_final/requests.json').read_text());self.value['closed']=False
  # Additional authorization begins after the immutable historical sixteen.
  # Actual gameplay receipts must not consume a temporary test's allowance.
  self.value['attempts']=self.value['attempts'][:16]
  self.value.pop('kentResolutionAuthorization',None)
  with CampaignBudget(self.path) as b:b.write(self.value)
 def tearDown(self):self.tmp.cleanup()
 def test_exact_additional_caps_and_sequential_numbers(self):
  original=copy.deepcopy(self.value['attempts'])
  with CampaignBudget(self.path) as b:
   for role,n in [('strategy',2),('preparation',0),('battle',84),('puppeteer',12)]:
    for i in range(n):b.charge(role,role+str(i),'fixture:free',role+str(i))
    with self.assertRaises(ValueError):b.charge(role,'overflow','fixture:free','overflow')
   self.assertEqual(len(b.read()['attempts']),114);self.assertEqual(b.read()['attempts'][:16],original)
   self.assertEqual([a['attempt'] for a in b.read()['attempts']],list(range(1,115)))
 def test_original_outcome_and_prefix_are_immutable(self):
  with CampaignBudget(self.path) as b:
   with self.assertRaises(ValueError):b.finish(1,{'changed':True})
   value=b.read();value['attempts'][0]['jobID']='tampered';b.write(value)
   with self.assertRaises(ValueError):b.read()
 def test_closed_ledger_and_nonfungible_caps(self):
  with CampaignBudget(self.path) as b:
   with self.assertRaises(ValueError):b.charge('preparation','forbidden','fixture:free','forbidden')
   b.close()
   with self.assertRaises(ValueError):b.charge('battle','closed','fixture:free','closed')
if __name__=='__main__':unittest.main()

class KentRemainingBudgetTests(unittest.TestCase):
 def test_zero_strategy_and_prior_receipts_frozen(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'requests.json';v=json.loads((ROOT/'evidence/phase6/campaign_expansion01_final/requests.json').read_text());v['closed']=False
   v['attempts']=v['attempts'][:52]
   with CampaignBudget(p) as b:
    b.write(v)
    for role in ('strategy','preparation'):
     with self.assertRaises(ValueError):b.charge(role,'not-authorized','fixture:free','not-authorized')
    with self.assertRaises(ValueError):b.finish(52,{'rewritten':True})
    for role,cap in (('battle',53),('puppeteer',8)):
     for i in range(cap):b.charge(role,role+str(i),'fixture:free',role+str(i))
     with self.assertRaises(ValueError):b.charge(role,'overflow','fixture:free','overflow')
    self.assertEqual(len(b.read()['attempts']),113)
    self.assertEqual(v['attempts'],b.read()['attempts'][:52])
