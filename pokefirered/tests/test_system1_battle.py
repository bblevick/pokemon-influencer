"""No-network live-role boundaries: budget, shadow isolation, cancellation."""
import unittest,tempfile,json,time
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import Future
from types import SimpleNamespace
from battle.live import BattleBudget,LiveBattleProvider
from battle.transport import Handler
from strategy.provider import ProviderError
class BattleLiveTests(unittest.TestCase):
 def test_host_window_is_bounded_and_retains_old_default(self):
  with tempfile.TemporaryDirectory() as td:
   for bound in (0,3,float('inf'),float('nan')):
    with self.assertRaises(ValueError):Handler({},Path(td),decision_seconds=bound)
   h=Handler({},Path(td));self.assertEqual(h.decision_seconds,2.5);h.close()
   h=Handler({},Path(td),decision_seconds=2.75);self.assertEqual(h.decision_seconds,2.75);h.close()
 def test_durable_thirty_total_and_no_duplicate(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'requests.json'
   with BattleBudget(p) as b:
    b.charge('smoke','fixture:free')
    with self.assertRaises(ProviderError):b.charge('smoke','fixture:free')
    for i in range(29):b.charge('turn-'+str(i),'fixture:free')
    with self.assertRaises(ProviderError):b.charge('over-budget','fixture:free')
   with BattleBudget(p) as reopened:self.assertEqual(len(reopened.read()['attempts']),30);reopened.close()
   with BattleBudget(p) as b:
    with self.assertRaises(ProviderError):b.charge('after-close','fixture:free')
 def test_shadow_retains_selected_probability_without_native_send(self):
  class Sock:
   def sendall(self,data):raise AssertionError('shadow must never execute model action')
  class Store:
   def campaign(self):return {'id':'c','status':'paired'}
   def get_active_branch(self):return 'b'
   def _one(self,*args):return True
  with tempfile.TemporaryDirectory() as td:
   h=Handler({},Path(td),shadow=True,decision_source='mercury');f=Future();f.set_result({'choiceID':'legal','probabilities':{'legal':1},'confidence':.01,'diagnostics':{'model':'fixture'}})
   r={'receivedMonotonic':time.monotonic(),'request':{'state':'exact subjective memo','question':'q','choices':{'legal':'move'},'nativeActions':{'legal':256},'scope':{'campaign':'c','branch':'b'},'requestID':'r'}}
   h.job={'future':f,'record':r,'deadline':time.monotonic()+1,'message':SimpleNamespace(nonce=7)};h.tick(Store(),Sock());self.assertEqual(r['nativeSelected'],256);self.assertEqual(r['source'],'mercury_shadow');self.assertEqual(r['result']['confidence'],.01);h.close()
 def test_worker_timeout_disables_further_network(self):
  import subprocess
  with tempfile.TemporaryDirectory() as td,patch('battle.live.LEDGER',Path(td)/'requests.json'):
   with patch('battle.live.subprocess.run',side_effect=subprocess.TimeoutExpired('fixture',2.25)) as run:
    with self.assertRaises(ProviderError):LiveBattleProvider().decide('s','q',{'x':'move'})
    self.assertIsNone(LiveBattleProvider().decide('s','q',{'x':'move'}));self.assertEqual(run.call_count,1)
 def test_worker_error_and_invalid_output_close_without_retry(self):
  for output in (SimpleNamespace(returncode=1,stderr='{"error":"system1_request_deadline"}',stdout=''),SimpleNamespace(returncode=0,stderr='',stdout='broken')):
   with self.subTest(output=output.returncode),tempfile.TemporaryDirectory() as td,patch('battle.live.LEDGER',Path(td)/'requests.json'):
    with patch('battle.live.subprocess.run',return_value=output) as run:
     with self.assertRaises(ProviderError):LiveBattleProvider().decide('s','q',{'x':'move'})
     self.assertIsNone(LiveBattleProvider().decide('s','q',{'x':'move'}));self.assertEqual(run.call_count,1)
if __name__=='__main__':unittest.main()
