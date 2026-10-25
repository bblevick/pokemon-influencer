"""No hosted calls. Actual packet fixtures and append-only branch audit checks."""
import unittest,json,tempfile,sqlite3,time,copy
from pathlib import Path
from concurrent.futures import Future
from types import SimpleNamespace
from unittest.mock import patch
from battle.transport import Handler
from battle.lifecycle import TERMINAL
from bridge.events_wire import Message
from bridge.events import Consumer
ROOT=Path(__file__).resolve().parents[1]
class LifecycleTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.e=Path(self.tmp.name)
  import sys;sys.path.insert(0,str(ROOT/'tools'))
  import battle_end01 as fixture
  self.fixture=fixture;self.db=self.e/'world.sqlite3'
  with sqlite3.connect(ROOT/'.local/vertical_slice01/world.sqlite3') as s,sqlite3.connect(self.db) as d:s.backup(d)
  self.w=fixture.open_store(self.db);self.w.restore(fixture.save_identity(ROOT/'.local/vertical_slice01/closeout-gym-ready.sav'))
  # A genuine host audit append forks a restored paired prefix, not canonical gameplay.
  self.w._tx(self.w._writable)
  self.h=Handler({},self.e);self.h.store=self.w
  prior=json.loads((ROOT/'evidence/phase4/vertical_slice01/gate-turn-traces.json').read_text())['turns'][-1]
  self.packet={'scope':{'campaign':self.w.campaign()['id'],'branch':self.w.get_active_branch()},'nativeState':prior['fairState'],'actionSetHash':'12345678'}
  self.record={'request':self.packet,'nativeSelected':256,'source':'external_test'}
 def tearDown(self):self.h.close();self.w.close();self.tmp.cleanup()
 def stages(self):return [r['stage'] for r in self.w.decision_lifecycle()]
 def test_unknown_lifecycle_stage_rejected(self):
  with self.assertRaises(ValueError):self.h.disposition(self.record,'MADE_UP_EXECUTION')
  self.assertEqual(self.stages(),[])
 def test_accepted_abort_terminal_and_duplicate_no_rewrite(self):
  self.h.disposition(self.record,'REQUESTED');self.h.disposition(self.record,'RESULT_PUBLISHED')
  key=(self.packet['nativeState']['nonce'],1,12);self.h.awaiting[key]=self.record;self.h.cancel()
  self.assertEqual(self.stages(),['REQUESTED','RESULT_PUBLISHED','CANCELED_RUN_ABORT'])
  self.h.disposition(self.record,'CANCELED_RUN_ABORT');self.assertEqual(len(self.stages()),3)
  with self.assertRaises(ValueError):self.h.disposition(self.record,'EXECUTED')
 def event(self,kind):
  n=self.packet['nativeState'];import struct
  data=struct.pack('<HBB',414,False,1) if kind==5 else struct.pack('<BBHH',1,1,33,95)
  body=struct.pack('<HHIIHHIHH',1,kind,900,n['battle'],n['turn'],3 if kind==5 else 2,100,len(data),0)+data
  return Message(1,n['nonce'],n['generation'],900,123,3,body)
 def test_canonical_resolution_and_end_dominate_delayed_provider(self):
  self.h.disposition(self.record,'REQUESTED');key=(self.packet['nativeState']['nonce'],1,12);self.h.awaiting[key]=self.record
  self.h.observe_event(self.event(3),self.w);self.assertIn('EXECUTED',self.stages());self.assertFalse(self.h.awaiting)
  self.record=copy.deepcopy(self.record);self.record['request']['nativeState']['request']+=1
  self.h.disposition(self.record,'REQUESTED');f=Future();self.h.job={'future':f,'record':self.record};self.h.pending[(9,1,13)]=self.record
  self.h.observe_event(self.event(5),self.w);self.assertIsNone(self.h.job);self.assertTrue(f.cancelled());self.assertIn('CANCELED_BATTLE_ENDED',self.stages());self.assertFalse(self.h.pending)
  self.h.tick(self.w,SimpleNamespace(sendall=lambda b:self.fail('late result must never send')))
 def test_restore_excludes_future_lifecycle_and_stale_cancellation(self):
  before=self.w.campaign()['active_branch'];self.h.disposition(self.record,'REQUESTED');self.h.disposition(self.record,'CANCELED_RESET')
  rows=len(self.w.decision_lifecycle());self.assertEqual(rows,2)
  self.w.restore(self.fixture.save_identity(ROOT/'.local/vertical_slice01/closeout-gym-ready.sav'))
  self.assertEqual(self.w.decision_lifecycle(),[])
  with self.assertRaises(ValueError):self.h.disposition(self.record,'RESULT_PUBLISHED')
  self.assertEqual(self.w.decision_lifecycle(),[])
 def test_fresh_host_cancels_unfinished_publication_once(self):
  self.h.disposition(self.record,'REQUESTED');self.h.disposition(self.record,'RESULT_PUBLISHED')
  fresh=Handler({},self.e)
  try:
   fresh.recover(self.w);fresh.recover(self.w)
   self.assertEqual(self.stages(),['REQUESTED','RESULT_PUBLISHED','CANCELED_RUN_ABORT'])
   self.assertIn((self.packet['nativeState']['nonce'],self.packet['nativeState']['generation'],self.packet['nativeState']['request']),fresh.retired_requests)
  finally:fresh.close()
 def test_durable_terminal_prevents_late_scheduling_and_publication(self):
  n=self.packet['nativeState'];r={'eventType':'BATTLE_ENDED','session':n['nonce'],'run':n['generation'],'battleID':n['battle']}
  fake=SimpleNamespace(get_canonical_events=lambda:[{'record':r}])
  fresh=Handler({},self.e)
  try:self.assertTrue(fresh.is_ended(fake,n['nonce'],n['generation'],n['battle']))
  finally:fresh.close()
  self.h.disposition(self.record,'REQUESTED');f=Future();f.set_result({'choiceID':'choice'})
  key=(n['nonce'],n['generation'],n['request']);self.h.pending[key]=self.record
  self.h.job={'record':self.record,'future':f,'message':self.event(5),'deadline':time.monotonic()+1}
  self.h.ended.add((n['nonce'],n['generation'],n['battle']))
  self.h.tick(self.w,SimpleNamespace(sendall=lambda b:self.fail('terminal result must not publish')))
  self.assertIsNone(self.h.job);self.assertEqual(self.stages()[-1],'CANCELED_BATTLE_ENDED')
 def test_restore_cancellation_cannot_suspend_or_leak_into_active_view(self):
  self.h.disposition(self.record,'REQUESTED');self.h.pending[(9,1,12)]=self.record
  self.w.restore(self.fixture.save_identity(ROOT/'.local/vertical_slice01/closeout-gym-ready.sav'))
  self.h.cancel('CANCELED_RESET');self.assertEqual(self.w.decision_lifecycle(),[])
  last=json.loads((self.e/'battle-audit.jsonl').read_text().splitlines()[-1])
  self.assertTrue(last['activeProjectionExcluded']);self.assertEqual(last['stage'],'CANCELED_RESET')
class TerminalDedupeTests(unittest.TestCase):
 def test_duplicate_terminal_reack_and_distinct_battle(self):
  import struct
  c=Consumer(11,1,12)
  def event(seq,battle,typ,data):return Message(1,11,1,seq,12,3,struct.pack('<HHIIHHIHH',1,typ,seq,battle,0,0 if typ==1 else 3,10,len(data),0)+data)
  start=struct.pack('<IHBB',8,414,1,0);end=struct.pack('<HBB',414,1,2)
  c.accept(event(1,1,1,start));m=event(2,1,5,end);r,ack=c.accept(m);self.assertEqual(r['payload']['outcome'],2)
  r,again=c.accept(m);self.assertIsNone(r);self.assertEqual(ack,again)
  c.accept(event(3,2,1,start));r,_=c.accept(event(4,2,5,end));self.assertEqual(r['battleID'],2)
if __name__=='__main__':unittest.main()
