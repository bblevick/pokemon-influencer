"""Retained native receipt provenance, zero provider calls/state recovery."""
import unittest,tempfile,struct,copy
from pathlib import Path
from types import SimpleNamespace
from battle.transport import Handler
class RetainedTerminalTests(unittest.TestCase):
 def case(self,selected=256,source=1):
  prior={'session':77,'generation':1,'nativeRequest':9,'nativeHash':'f27dd2e1','battle':3,'turn':8,'phase':1,'battler':1,'source':'mercury','fallbackReason':0,'nativeSelected':256,'selection':{'original':'live receipt'}}
  recorded=[];store=SimpleNamespace(_launch=lambda *a:None,battle_audit=lambda:[copy.deepcopy(prior)],record_battle_audit=lambda r:recorded.append(r))
  message=SimpleNamespace(kind=10,typ=11,nonce=77,generation=1,sequence=9,payload=struct.pack('<IIIHBBBBH',9,int(prior['nativeHash'],16),3,8,1,1,source,0,selected))
  return prior,recorded,store,message
 def test_offline_restart_keeps_actual_mercury_provenance(self):
  with tempfile.TemporaryDirectory() as t:
   h=Handler({},Path(t),decision_source='external_test');prior,rows,w,m=self.case()
   try:h.receive(m,w,None);self.assertEqual(rows,[prior]);self.assertFalse(h.pending);self.assertIsNone(h.job)
   finally:h.close()
 def test_conflicting_selection_and_source_still_rejected(self):
  for selected,source in ((257,1),(256,2)):
   with tempfile.TemporaryDirectory() as t:
    h=Handler({},Path(t));prior,rows,w,m=self.case(selected,source)
    try:
     with self.assertRaisesRegex(ValueError,'conflicting retained'):h.receive(m,w,None)
     self.assertFalse(rows)
    finally:h.close()
