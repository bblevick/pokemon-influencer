"""WORLD tests use constructed flash and typed wire fixtures, never live claims."""
import copy,json,sqlite3,struct,tempfile,unittest
from pathlib import Path
from bridge.events_wire import Message
from world.store import WorldStore,WorldError,dump
from world.saves import fingerprint
ROOT=Path(__file__).resolve().parents[1];BUILD='a'*64;TAG=123;SIZES=(4,)*14

def flash(counter=1,fill=1,rotation=0,slot=None,footer=b''):
 data=bytearray(b'\xff'*131072);slot=counter%2 if slot is None else slot
 for sid in range(14):
  sector=bytearray(4096);struct.pack_into('<I',sector,0,fill+sid);crc=(fill+sid)&0xffff
  struct.pack_into('<HHII',sector,4084,sid,crc,0x08012025,counter)
  index=slot*14+(sid+rotation)%14;data[index*4096:(index+1)*4096]=sector
 return bytes(data)+footer

def msg(seq,typ=1,battle=1,turn=None,nonce=100,trainer=102,outcome=1):
 phase={1:0,2:1,3:2,4:3,5:3,6:1}[typ];turn=0 if typ==1 else 1 if turn is None else turn
 payload={1:struct.pack('<IHBB',8 if trainer else 0,trainer,1,0),2:b'',3:struct.pack('<BBHH',1,1,33,13),4:struct.pack('<HBB',trainer,1,outcome),5:struct.pack('<HBB',trainer,1,outcome),6:struct.pack('<HHHHI4H4BHBB4H4B',trainer,13,10,10,0,33,0,0,0,20,0,0,0,1,48,0,0,0,0,0,0,0,0,0)}[typ]
 header=struct.pack('<HHIIHHIHH',1,typ,seq,battle,turn,phase,seq*10,len(payload),0)
 return Message(1,nonce,1,seq,TAG,3,header+payload)
class WorldTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'world.sqlite3';self.w=WorldStore(self.path,BUILD,TAG);self.s1=fingerprint(flash(),SIZES);self.w.import_save(self.s1);self.w.authorize_launch(100,self.s1)
 def tearDown(self):self.w.close();self.tmp.cleanup()
 def battle(self,nonce=100,first=1,bid=1,trainer=102):
  for seq,t in enumerate([1,2,6,3,4,5],first):self.w.ingest(msg(seq,t,bid,nonce=nonce,trainer=trainer))
 def receipt(self,counter=2,last=6,nonce=100):return {'event':'savedataUpdated','nonce':nonce,'run':1,'eventCounter':last,'ack':last,'depth':0,'state':0,'drops':0,'counter':counter}
 def test_valid_and_observation_separation(self):
  self.battle();s=self.w.state();self.assertEqual(s['cursor'],5);self.assertEqual(s['trainers']['fr:trainer:0102']['defeats'],1)
  self.assertEqual(self.w.db.execute('SELECT COUNT(*) FROM observations').fetchone()[0],1);self.assertFalse(any(x['record']['recordClass']=='observation' for x in self.w.get_canonical_events()));self.assertNotIn('memory',dump(s));self.w.verify_replay()
 def test_duplicate_delivery_reopen(self):
  self.battle();before=self.w.state();self.w.close();self.w=WorldStore(self.path,BUILD,TAG)
  self.assertTrue(self.w.ingest(msg(5,4))['duplicate']);self.assertEqual(before,self.w.state());self.w.verify_replay()
 def test_conflicting_duplicate(self):
  self.w.ingest(msg(1))
  with self.assertRaisesRegex(ValueError,'conflicting'):self.w.ingest(msg(1,trainer=103))
 def test_duplicate_canonical_defeat_different_delivery(self):
  for seq,t in enumerate([1,2,4],1):self.w.ingest(msg(seq,t))
  with self.assertRaises(ValueError):self.w.ingest(msg(4,4))
  self.assertEqual(self.w.state()['trainers']['fr:trainer:0102']['defeats'],1)
 def test_order_gap(self):
  with self.assertRaisesRegex(ValueError,'gap'):self.w.ingest(msg(2))
  self.assertEqual(self.w.state()['cursor'],0)
 def test_unknown_event_schema(self):
  m=msg(1);bad=Message(1,100,1,1,TAG,3,b'\x02\0'+m.payload[2:])
  with self.assertRaisesRegex(ValueError,'schema'):self.w.ingest(bad)
 def test_malformed_identity_and_reset(self):
  for bad in [Message(1,0,1,1,TAG,3,msg(1).payload),Message(1,100,2,1,TAG,3,msg(1).payload),Message(1,100,1,1,999,3,msg(1).payload)]:
   with self.assertRaises(ValueError):self.w.ingest(bad)
 def test_lifecycle_missing_start(self):
  with self.assertRaises(ValueError):self.w.ingest(msg(1,2))
 def test_concurrent_battle_start(self):
  self.w.ingest(msg(1))
  with self.assertRaisesRegex(ValueError,'concurrent'):self.w.ingest(msg(2,battle=2))
  self.assertEqual(self.w.state()['cursor'],1)
 def test_trainer_correlation(self):
  self.w.ingest(msg(1));self.w.ingest(msg(2,2))
  with self.assertRaises(ValueError):self.w.ingest(msg(3,4,trainer=103))
 def test_end_requires_defeat(self):
  self.w.ingest(msg(1));self.w.ingest(msg(2,2))
  with self.assertRaisesRegex(ValueError,'defeat'):self.w.ingest(msg(3,5))
 def test_unknown_trainer(self):
  with self.assertRaisesRegex(ValueError,'unknown trainer'):self.w.ingest(msg(1,trainer=65535))
  self.assertEqual(self.w.state()['cursor'],0)
 def test_rematch_registry_and_repeated_encounters(self):
  registry=self.w.registry;family=next(f for f in registry['families'] if f['kind']=='vs_seeker' and len(f['sourceIDs'])>1);a,b=family['sourceIDs'][:2]
  self.assertEqual(registry['mapping'][str(a)],registry['mapping'][str(b)])
  self.battle(trainer=a);self.battle(first=7,bid=2,trainer=b)
  f=self.w.get_trainer(registry['mapping'][str(a)])['facts'];self.assertEqual((f['encounters'],f['completedBattles'],f['defeats']),(2,2,2))
 def test_immutable_tables(self):
  self.w.ingest(msg(1))
  with self.assertRaises(sqlite3.IntegrityError):self.w.db.execute('DELETE FROM events')
 def test_pair_restore_branch_replay(self):
  self.battle();a=self.w.get_active_branch();s2=fingerprint(flash(2,2),SIZES);intent=self.w.begin_save(100,self.s1);cp=self.w.finish_save(intent,s2,self.receipt())
  self.battle(first=7,bid=2);ahead=self.w.state();self.w.authorize_launch(200,self.s1)
  self.assertEqual(self.w.get_active_branch(),a);self.assertEqual(self.w.state()['cursor'],0);self.assertEqual(self.w.campaign()['pending_fork'],1);self.assertEqual(self.w.get_canonical_events(),[])
  self.w.ingest(msg(1,nonce=200));b=self.w.get_active_branch();self.assertNotEqual(a,b);self.assertEqual(len(self.w.get_canonical_events(a)),ahead['cursor']);self.w.verify_replay()
  self.assertEqual(cp['cursor'],5);self.assertEqual(self.w.get_trainer('fr:trainer:0102')['facts']['defeats'],0)
 def test_s2_restore_discards_only_later(self):
  self.battle();s2=fingerprint(flash(2,2),SIZES);self.w.finish_save(self.w.begin_save(100,self.s1),s2,self.receipt());self.battle(first=7,bid=2);self.w.authorize_launch(200,s2)
  self.assertEqual(self.w.get_trainer('fr:trainer:0102')['facts']['defeats'],1);self.assertEqual(self.w.get_current_world_cursor(),5)
 def test_unknown_save_no_merge(self):
  self.battle();before=self.w.state()
  with self.assertRaisesRegex(ValueError,'unpaired'):self.w.restore(fingerprint(flash(9,9),SIZES))
  self.assertEqual(before,self.w.state())
 def test_incompatible_build_schema_newer(self):
  for build,tag in [('b'*64,TAG),(BUILD,999)]:
   with self.assertRaisesRegex(ValueError,'incompatible'):WorldStore(self.path,build,tag)
  self.w.db.execute('PRAGMA user_version=2')
  with self.assertRaisesRegex(ValueError,'newer'):WorldStore(self.path,BUILD,TAG)
 def test_reducer_version_rejected(self):
  self.w.db.execute("UPDATE metadata SET value='2' WHERE key='reducer'")
  with self.assertRaisesRegex(ValueError,'incompatible'):WorldStore(self.path,BUILD,TAG)
 def test_checkpoint_transaction_failure(self):
  self.battle();s2=fingerprint(flash(2,2),SIZES);intent=self.w.begin_save(100,self.s1)
  with self.assertRaisesRegex(ValueError,'injected'):self.w.finish_save(intent,s2,self.receipt(),fail=True)
  self.assertIsNone(self.w.get_save_checkpoint(s2.fingerprint));self.assertEqual(self.w.pending_save()['id'],intent)
  self.w.finish_save(intent,s2,self.receipt());self.assertIsNone(self.w.pending_save())
 def test_save_incomplete_and_barrier(self):
  intent=self.w.begin_save(100,self.s1)
  with self.assertRaises(ValueError):self.w.finish_save(intent,self.s1,self.receipt(last=0))
  with self.assertRaisesRegex(ValueError,'pending save'):self.w.ingest(msg(1))
  self.w.abandon_save(intent);self.assertIsNone(self.w.pending_save())
 def test_resave_restored_cursor_does_not_fork(self):
  self.battle();self.w.authorize_launch(200,self.s1);branch=self.w.get_active_branch()
  intent=self.w.begin_save(200,self.s1);s2=fingerprint(flash(2,2),SIZES);self.w.finish_save(intent,s2,self.receipt(last=0,nonce=200))
  self.assertEqual(self.w.get_active_branch(),branch);self.assertEqual(self.w.get_current_world_cursor(),0);self.assertEqual(self.w.campaign()['pending_fork'],1)
 def test_save_requires_no_active_battle(self):
  self.w.ingest(msg(1))
  with self.assertRaises(ValueError):self.w.begin_save(100,self.s1)
 def test_restore_invalidates_old_launch(self):
  self.w.authorize_launch(200,self.s1)
  with self.assertRaisesRegex(ValueError,'unmanaged'):self.w.ingest(msg(1))
 def test_suspension_blocks_enhanced_ingestion_until_restore(self):
  self.w.suspend('gap');self.assertEqual(self.w.campaign()['status'],'incomplete')
  with self.assertRaisesRegex(ValueError,'suspended'):self.w.ingest(msg(1))
  self.w.authorize_launch(200,self.s1);self.w.ingest(msg(1,nonce=200));self.assertEqual(self.w.state()['cursor'],1)
 def test_registry_integrity(self):
  registry=copy.deepcopy(self.w.registry);registry['mapping']['102']='fake'
  with self.assertRaisesRegex(ValueError,'registry integrity'):WorldStore(Path(self.tmp.name)/'other.sqlite3',BUILD,TAG,registry)
 def test_checkpoint_unknown_schema(self):
  self.w.db.execute('DROP TRIGGER immutable_checkpoints_UPDATE')
  self.w.db.execute('UPDATE checkpoints SET schema=2')
  with self.assertRaisesRegex(ValueError,'incompatible pairing'):self.w.restore(self.s1)
 def test_crash_reopen_pending_intent(self):
  intent=self.w.begin_save(100,self.s1);self.w.close();self.w=WorldStore(self.path,BUILD,TAG)
  self.assertEqual(self.w.pending_save()['id'],intent);self.assertEqual(self.w.state()['cursor'],0)
class FingerprintTests(unittest.TestCase):
 def test_stable(self):self.assertEqual(fingerprint(flash(),SIZES),fingerprint(flash(),SIZES))
 def test_footer_rotation_and_slot_independent(self):
  a=fingerprint(flash(),SIZES)
  for data in [flash(footer=b'R'*16),flash(rotation=9),flash(slot=0)]:self.assertEqual(a.fingerprint,fingerprint(data,SIZES).fingerprint)
 def test_padding_oldslot_auxiliary_ignored(self):
  a=flash();b=bytearray(a);b[14*4096+100]=51;b[30*4096]=4
  self.assertEqual(fingerprint(a,SIZES).fingerprint,fingerprint(bytes(b),SIZES).fingerprint)
 def test_new_counter_and_content(self):
  a=fingerprint(flash(),SIZES);b=fingerprint(flash(2),SIZES);c=fingerprint(flash(2,2),SIZES)
  self.assertEqual(a.content_sha256,b.content_sha256);self.assertNotEqual(a.fingerprint,b.fingerprint);self.assertNotEqual(b.fingerprint,c.fingerprint)
 def test_two_slots_latest_and_wrap(self):
  for old,new in [(1,2),(0xffffffff,0)]:
   a=flash(old);b=flash(new);data=b[:14*4096]+a[14*4096:28*4096]+b[28*4096:]
   self.assertEqual(fingerprint(data,SIZES).counter,new)
 def test_corrupt_incomplete_unknown_size(self):
  data=bytearray(flash());data[14*4096]^=1
  for x in [bytes(data),b'',flash(footer=b'x')]:
   with self.assertRaises(ValueError):fingerprint(x,SIZES)
 def test_duplicate_section(self):
  data=bytearray(flash());data[15*4096:16*4096]=data[14*4096:15*4096]
  with self.assertRaises(ValueError):fingerprint(bytes(data),SIZES)
class ReceiptTests(unittest.TestCase):
 def test_partial_crash_tail_and_resume(self):
  from world.receipts import read_receipts
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'receipts.jsonl';p.write_bytes(b'{"counter":5}\n{"counter":')
   rows,offset=read_receipts(p,0);self.assertEqual(rows,[{'counter':5}]);self.assertEqual(read_receipts(p,offset),([],offset))
   with p.open('ab') as f:f.write(b'6}\n')
   rows,end=read_receipts(p,offset);self.assertEqual(rows,[{'counter':6}]);self.assertEqual(end,p.stat().st_size)
 def test_truncated_receipt_file(self):
  from world.receipts import read_receipts
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'receipts.jsonl';p.write_text('')
   with self.assertRaisesRegex(ValueError,'truncated'):read_receipts(p,100)
 def test_receipt_size_bound(self):
  from world.receipts import read_receipts
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'receipts.jsonl';p.write_bytes(b'x'*513)
   with self.assertRaisesRegex(ValueError,'oversized'):read_receipts(p,0)
if __name__=='__main__':unittest.main()
