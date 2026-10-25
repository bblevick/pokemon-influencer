"""A known old normal-save checkpoint must not satisfy a new pending intent."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from hermes01_scenario import paired_intent
import test_hermes01 as fixtures
from test_world01 import flash,SIZES
from world.saves import fingerprint
class SaveHelperTests(unittest.TestCase):
 setUp=fixtures.PuppeteerTests.setUp
 tearDown=fixtures.PuppeteerTests.tearDown
 save=fixtures.PuppeteerTests.save
 def test_old_checkpoint_rejected_until_exact_new_intent_paired(self):
  old=self.save(2,0);intent=self.w.begin_save(100,old)
  self.assertIsNone(paired_intent(self.w,intent,old))
  new=fingerprint(flash(3,3),SIZES)
  cp=self.w.finish_save(intent,new,dict(event='savedataUpdated',nonce=100,run=1,eventCounter=0,ack=0,depth=0,state=0,drops=0,counter=3))
  self.assertIsNone(paired_intent(self.w,intent,old));self.assertEqual(paired_intent(self.w,intent,new)['id'],cp['id'])
