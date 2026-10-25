"""Host packet/transport checks; native C matrix is a separate test layer."""
import unittest,json,struct,copy,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from battle.domain import decode,request_for,DeterministicProvider
from battle.transport import Handler
from bridge.events_wire import Message
E=ROOT/'evidence/phase4/battle01'
class CodecTests(unittest.TestCase):
 def fixture(self):
  m=json.loads((E/'manifest-native.json').read_text());abi=m['battle_abi'];data=bytearray(abi[0]);struct.pack_into('<HHHBB4IH4BH',data,0,1,len(data),102,1,3,1,1,7,1,1,1,0,12,0,1);data[32]=48;own=abi[4]
  for slot,species in enumerate((13,10)):
   struct.pack_into('<8H',data,own+48*slot,species,20,20,0,40 if slot==0 else 33,81,0,0);data[own+48*slot+28]=6;data[own+48*slot+32:own+48*slot+40]=bytes([35,40,0,0]*2)
  for i,a in enumerate(((0x100,40,1,0,0,0),(0x101,81,1,1,0,0),(0x201,10,2,1,1,0))):struct.pack_into('<HH4B',data,abi[5]+8*i,*a)
  return data,abi,m
 def test_codec_closed_sanitized_fields(self):
  data,abi,_=self.fixture();s=decode(data,abi);self.assertEqual(len(s['actions']),3);self.assertEqual(s['opponent'],{'species':1,'hpBar':48,'status':0,'revealedMoves':[0,0,0,0]});self.assertNotIn('opponentParty',s)
 def test_size_phase_identity_rejection(self):
  data,abi,_=self.fixture()
  with self.assertRaises(ValueError):decode(data[:-1],abi)
  data[6]=3
  with self.assertRaises(ValueError):decode(data,abi)
 def test_duplicate_action_rejected(self):
  data,abi,_=self.fixture();data[abi[5]+8:abi[5]+16]=data[abi[5]:abi[5]+8]
  with self.assertRaises(ValueError):decode(data,abi)
 def test_deterministic_provider_fixed_choices(self):
  p=DeterministicProvider('switch_once');choices={'1:1:NORMAL_TURN:1:2:a:MOVE:0':'move','1:1:NORMAL_TURN:1:2:a:SWITCH:1':'switch'}
  self.assertIn(':SWITCH:',p.decide('subjective impossible wishes','q',choices)['choiceID']);self.assertIn(':MOVE:',p.decide('same','q',choices)['choiceID']);self.assertIsNone(DeterministicProvider('timeout').decide('s','q',choices))
 def test_fragment_order_bounded(self):
  import tempfile
  data,abi,m=self.fixture()
  with tempfile.TemporaryDirectory() as td:
   h=Handler(m,Path(td));msg=Message(8,7,1,1,m['build_tag'],9,struct.pack('<IIHH',1,3,abi[0],80)+bytes(data[:80]))
   with self.assertRaises(ValueError):h.receive(msg,None,None)
 def test_exact_subjective_memo_and_zero_inventory(self):
  from battle01_launch import open_store
  import tempfile,sqlite3
  data,abi,m=self.fixture()
  with tempfile.TemporaryDirectory() as td:
   db=Path(td)/'w.sqlite3';a=sqlite3.connect(ROOT/'.local/battle01/world.sqlite3');b=sqlite3.connect(db);a.backup(b);a.close();b.close()
   with open_store(db) as w:
    from battle01_launch import save_identity
    w.restore(save_identity(ROOT/'.local/system1_01a/installed-save19.sav'));r=request_for(w,decode(data,abi),123)
    self.assertIn(w.locked_preparation('trainer:fr:trainer:0102')['strategyText'],r['state']);self.assertEqual(len(r['choices']),3);self.assertFalse(any(':ITEM:' in k for k in r['choices']));self.assertIn('STRATEGY MEMO — SUBJECTIVE',r['state']);self.assertNotIn('rng',r['nativeState']);self.assertLessEqual(len(r['state'].encode()),32768)
 def test_async_provider_timeout_and_malformed(self):
  import tempfile,time
  from concurrent.futures import Future
  from types import SimpleNamespace
  class Sock:
   def sendall(self,data):raise AssertionError('invalid output must not send')
  with tempfile.TemporaryDirectory() as td:
   _,_,m=self.fixture();h=Handler(m,Path(td));f=Future();r={'request':{'state':'subjective','choices':{},'nativeActions':{},'requestID':'q'},'receivedMonotonic':time.monotonic()}
   h.job={'future':f,'message':SimpleNamespace(sequence=1),'record':r,'deadline':time.monotonic()+1}
   start=time.monotonic();h.tick(None,Sock());self.assertLess(time.monotonic()-start,.05);self.assertIsNotNone(h.job)
   h.job['deadline']=time.monotonic()-1;h.tick(None,Sock());self.assertIsNone(h.job);self.assertEqual(r['source'],'unavailable')
   f=Future();f.set_result('untyped output');h.job={'future':f,'message':SimpleNamespace(sequence=2),'record':r,'deadline':time.monotonic()+1};h.tick(None,Sock());self.assertIsNone(r['result'])
   f=Future();f.set_result({'choiceID':['malformed']});h.job={'future':f,'message':SimpleNamespace(sequence=3),'record':r,'deadline':time.monotonic()+1};h.tick(None,Sock());self.assertIsNone(r['result']);h.close()
 def test_audit_save_restore_prefix_and_duplicate(self):
  from battle01_launch import open_store,save_identity
  import tempfile,sqlite3
  with tempfile.TemporaryDirectory() as td:
   db=Path(td)/'w.sqlite3';a=sqlite3.connect(ROOT/'.local/battle01/world.sqlite3');b=sqlite3.connect(db);a.backup(b);a.close();b.close()
   with open_store(db) as w:
    save=save_identity(ROOT/'.local/system1_01a/installed-save19.sav');w.restore(save);self.assertEqual(w.battle_audit(),[])
    import inspect
    self.assertEqual(len(inspect.signature(w.audit).parameters),3) # inherited puppeteer audit must remain callable
    r={'session':9,'generation':1,'nativeRequest':1,'nativeHash':'a','battle':1,'turn':1,'phase':1,'battler':1,'source':'external_test','fallbackReason':0,'nativeSelected':256}
    key=w.record_battle_audit(r);self.assertEqual(key,w.record_battle_audit(r));self.assertEqual(len(w.battle_audit()),1)
    bad={**r,'nativeSelected':257}
    with self.assertRaises(ValueError):w.record_battle_audit(bad)
    w.restore(save);self.assertEqual(w.battle_audit(),[]);self.assertIsNotNone(w._one('SELECT 1 FROM battle_decision_audit WHERE id=?',(key,)))
 def test_live_packet_schemas_and_privacy_source(self):
  import jsonschema
  schema=json.loads((ROOT/'schemas/battle/request.schema.json').read_text());resolver=jsonschema.RefResolver((ROOT/'schemas/battle/').as_uri()+'/',schema)
  packets=list(E.glob('turn-384821213-*.json'));self.assertTrue(packets)
  for p in packets:
   packet=json.loads(p.read_text());jsonschema.validate(packet,schema,resolver=resolver);self.assertEqual(set(packet['choices']),set(packet['nativeActions']));self.assertEqual(len(packet['choices']),len(packet['nativeState']['actions']))
   self.assertNotIn('opponentParty',packet['nativeState']);self.assertEqual(set(packet['nativeState']['opponent']),{'species','hpBar','status','revealedMoves'});self.assertTrue(all(x==0 for x in packet['nativeState']['inventory']))
  source=(ROOT/'native/battle01/pi_battle.c').read_text()
  for forbidden in ('gPlayerParty','gRngValue','Random(','gChosenMoveByBattler'):self.assertNotIn(forbidden,source)
 def test_source_actual_c_rules_and_controller_matrix(self):
  r=subprocess.run([sys.executable,str(ROOT/'tools/battle01_c_tests.py')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);self.assertIn('controller execution/lifecycle matrix passed',r.stdout)
if __name__=='__main__':unittest.main()
