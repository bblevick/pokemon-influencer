"""Failure matrix uses explicit native witnesses as fixtures, not live proof."""
import dataclasses,json,sqlite3,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from test_world01 import BUILD,TAG,SIZES,flash,msg
from bridge.continuity import Inbox,NativeWitness
from bridge.events import Consumer,decode_event
from bridge.events_wire import Message,checksum
from bridge.managed import freeze,process_identity
from world.saves import fingerprint
from world.store import WorldStore,WorldError

ROOT=Path(__file__).resolve().parents[1]
class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
        self.path=self.root/'world.sqlite3';self.inbox_path=self.root/'inbox.sqlite3'
        self.w=WorldStore(self.path,BUILD,TAG);self.save=fingerprint(flash(),SIZES)
        self.w.import_save(self.save);self.origin=self.w.authorize_launch(100,self.save)
        self.i=Inbox(self.inbox_path)
        self.n=NativeWitness(BUILD,100,1,self.origin,self.save.fingerprint,'fixture-native-process',100,20,0,0,True)
    def tearDown(self):
        self.i.close();self.w.close();self.t.cleanup()
    def stage(self,m):return self.i.stage(self.w,m,self.n)
    def apply(self,m):return self.i.apply(self.w,self.stage(m),self.n,method='fixture-recovery')
    def reopen(self):
        self.i.close();self.w.close();self.w=WorldStore(self.path,BUILD,TAG);self.i=Inbox(self.inbox_path)
    def test_retained_receipt_after_expiry_requires_counterpart(self):
        m=msg(1);key=self.stage(m);self.reopen()
        with self.assertRaisesRegex(WorldError,'counterpart unavailable'):
            self.i.apply(self.w,key,dataclasses.replace(self.n,counterpart_available=False))
        self.assertEqual(self.w.get_current_world_cursor(),0)
        self.assertFalse(self.i.apply(self.w,key,self.n)['duplicate'])
    def test_expiry_before_delivery_retained_native_stages_after_restart(self):
        # No host receipt exists at expiry. This fixture explicitly supplies a
        # surviving native counterpart containing the original unACKed event.
        m=msg(1);self.reopen();self.assertEqual(self.i.pending(),[])
        n=dataclasses.replace(self.n,frame=110,event_counter=1)
        key=self.i.stage(self.w,m,n)
        self.assertFalse(self.i.apply(self.w,key,n)['duplicate'])
        self.assertTrue(self.i.apply(self.w,key,n)['duplicate'])
        self.assertEqual(self.w.get_current_world_cursor(),1)
    def test_receipt_durable_before_application_restart(self):
        key=self.stage(msg(1));self.assertEqual(self.w.get_current_world_cursor(),0);self.reopen()
        self.assertEqual(len(self.i.pending()),1)
        self.assertFalse(self.i.apply(self.w,key,self.n)['duplicate'])
        self.assertEqual(self.w.get_current_world_cursor(),1)
    def test_expiry_after_commit_before_inbox_mark_and_ack(self):
        m=msg(1);key=self.stage(m);self.w.ingest(m);self.reopen()
        self.assertTrue(self.i.apply(self.w,key,self.n)['duplicate'])
        self.assertEqual(self.w.get_current_world_cursor(),1)
        self.assertEqual(len(self.w.get_canonical_events()),1)
    def test_after_ack_commit_authoritative_and_duplicate_noop(self):
        m=msg(1);self.apply(m);before=self.w.verify_replay();self.reopen()
        self.assertTrue(self.apply(m)['duplicate']);self.assertEqual(before,self.w.verify_replay())
    def test_native_replaced_or_rewound_rejected(self):
        key=self.stage(msg(1))
        for n in (dataclasses.replace(self.n,process_identity='replacement'),dataclasses.replace(self.n,frame=99)):
            with self.assertRaisesRegex(WorldError,'replaced/reset'):self.i.apply(self.w,key,n)
        self.assertEqual(self.w.get_current_world_cursor(),0)
    def test_later_event_never_skips_gap(self):
        second=msg(2,2);key=self.stage(second)
        with self.assertRaisesRegex(WorldError,'gap'):self.i.apply(self.w,key,self.n)
        self.assertEqual(self.w.get_current_world_cursor(),0)
        self.apply(msg(1));self.assertFalse(self.i.apply(self.w,key,self.n)['duplicate'])
        self.assertEqual(self.w.get_current_world_cursor(),2)
    def test_transaction_failure_recovery_applies_once(self):
        key=self.stage(msg(1));original=self.w._project
        with patch.object(self.w,'_project',side_effect=RuntimeError('fixture commit interruption')):
            with self.assertRaises(RuntimeError):self.i.apply(self.w,key,self.n)
        self.assertEqual(self.w.get_current_world_cursor(),0);self.assertEqual(len(self.i.pending()),1)
        self.i.apply(self.w,key,self.n);self.assertTrue(self.i.apply(self.w,key,self.n)['duplicate'])
    def test_abandoned_launch_and_generation_rejected(self):
        key=self.stage(msg(1));self.w.authorize_launch(200,self.save)
        with self.assertRaisesRegex(WorldError,'unmanaged'):self.i.apply(self.w,key,self.n)
        with self.assertRaises(WorldError):self.stage(msg(1,nonce=200))
    def test_different_campaign_rejected(self):
        key=self.stage(msg(1))
        with WorldStore(self.root/'other.sqlite3',BUILD,TAG) as other:
            other.import_save(self.save);other.authorize_launch(100,self.save,origin=self.origin)
            with self.assertRaisesRegex(WorldError,'different campaign'):self.i.apply(other,key,self.n)
    def test_valid_checksum_invalid_causal_identity_rejected(self):
        m=msg(1,2);key=self.stage(m)
        with self.assertRaisesRegex(ValueError,'start'):self.i.apply(self.w,key,self.n)
        self.assertEqual(self.w.get_current_world_cursor(),0)
    def test_conflicting_duplicate_slot_rejected(self):
        self.apply(msg(1))
        with self.assertRaisesRegex(WorldError,'conflicting'):self.stage(msg(1,trainer=103))
    def test_bad_witness_drops_build_session_origin_rejected(self):
        for n in (dataclasses.replace(self.n,drops=1),dataclasses.replace(self.n,build='b'*64),
                  dataclasses.replace(self.n,run=2),dataclasses.replace(self.n,origin='unknown')):
            with self.assertRaises(WorldError):self.i.stage(self.w,msg(1),n)
        self.assertEqual(self.i.pending(),[])
    def test_rival_gym_ordinary_events_share_identical_path(self):
        for battle,trainer in enumerate((334,414,91),1):
            first=(battle-1)*4+1
            for seq,typ in enumerate((1,2,4,5),first):self.apply(msg(seq,typ,battle,trainer=trainer))
        self.assertEqual(len(self.w.state()['battles']),3)
        self.assertTrue(all(b['ended'] for b in self.w.state()['battles'].values()))
    def test_receipts_immutable_and_audit_separate(self):
        result=self.apply(msg(1))
        with self.assertRaises(sqlite3.IntegrityError):self.i.db.execute('DELETE FROM receipts')
        self.assertEqual(len(self.w.get_canonical_events()),1)
        self.assertEqual(self.i.db.execute('SELECT COUNT(*) FROM recovery_audit').fetchone()[0],1)
        audit=json.loads(self.i.db.execute('SELECT provenance FROM recovery_audit').fetchone()[0])
        self.assertEqual(audit['originalEventID'],result['eventID'])
        self.assertEqual(audit['sequence'],1)
        self.assertTrue(audit['attemptID'])
        self.assertEqual(audit['captureBranch'],self.w.get_active_branch())

class HistoricalIncidentTests(unittest.TestCase):
    def test_accepted_native_adapter_preserves_physical_and_logical_identity(self):
        from campaign.scripted import ScriptedStore
        from world.saves import layout_from_build
        mpath=ROOT/'evidence/phase8/rival01/manifest-native.json';manifest=json.loads(mpath.read_text())
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=sqlite3.connect('file:'+str(ROOT/'.local/rocket01/post-rocket-pair.sqlite3')+'?mode=ro',uri=True)
            dst=sqlite3.connect(root/'world.sqlite3');src.backup(dst);dst.close();src.close()
            with ScriptedStore(root/'world.sqlite3',mpath) as w:
                save=fingerprint((ROOT/'.local/rocket01/post-rocket-pair.sav').read_bytes(),layout_from_build(ROOT/manifest['rom_path']))
                origin=w.authorize_launch(100,save);base=msg(1,trainer=0)
                packet=dataclasses.replace(base,tag=manifest['build_tag'])
                n=NativeWitness(w.build,100,1,origin,save.fingerprint,'fixture-native',100,1,0,0,True,manifest['rom_sha256'],manifest['build_tag'])
                inbox=Inbox(root/'inbox.sqlite3')
                try:
                    key=inbox.stage(w,packet,n);result=inbox.apply(w,key,n)
                    self.assertFalse(result['duplicate']);self.assertTrue(inbox.apply(w,key,n)['duplicate'])
                    self.assertEqual(w.get_current_world_cursor(),444)
                    canonical=w._one('SELECT wire FROM deliveries WHERE identity=?',(key,))['wire']
                    self.assertNotEqual(canonical,packet.encode().hex())
                    self.assertEqual(len([b for b in w.state()['battles'].values() if not b['ended']]),1)
                    self.assertFalse(any(o['actorID']=='trainer:fr:trainer:0000' for o in w.puppeteer_state()['obligations'].values()))
                finally:inbox.close()

    def test_exact_retained_event_identity_order_and_native_unavailable(self):
        v=json.loads((ROOT/'evidence/phase8/rival01/verification-blocked.json').read_text())
        payload=bytes.fromhex(v['retainedNativePayloadHex'])
        m=Message(1,2493534040,1,298,2285031545,3,payload)
        self.assertEqual(checksum(m.sequence,m.nonce,m.generation,m.typ,payload),v['retainedPayloadChecksum'])
        db=sqlite3.connect('file:'+str(ROOT/'.local/rival01/travel-gap-forensic.sqlite3')+'?mode=ro',uri=True)
        db.row_factory=sqlite3.Row
        try:
            launch=db.execute('SELECT * FROM launches WHERE nonce=?',(m.nonce,)).fetchone()
            c=db.execute('SELECT * FROM campaigns WHERE id=?',(launch['campaign'],)).fetchone()
            stream=db.execute('SELECT * FROM streams WHERE nonce=? AND run=?',(m.nonce,m.generation)).fetchone()
            self.assertEqual(c['active_branch'],v['currentCampaign']['active_branch'])
            self.assertEqual(stream['last'],297)
            self.assertIsNone(db.execute('SELECT * FROM deliveries WHERE launch=? AND sequence=298',(launch['id'],)).fetchone())
            consumer=Consumer(m.nonce,m.generation,m.tag);consumer.last=stream['last']
            consumer.battles={int(k):value for k,value in json.loads(stream['state']).items()}
            record,_=consumer.accept(m)
            self.assertFalse(record['streamIncomplete']);self.assertEqual(record['eventType'],'BATTLE_STARTED')
            self.assertEqual(record['payload']['trainerID'],0);self.assertEqual(record['payload']['battleKind'],'wild')
            self.assertEqual(c['status'],'incomplete')
            # Exact host identity and admissible sequence do not manufacture the
            # missing native counterpart. No application into this branch occurs.
            self.assertFalse(v['recoveredIntoHost']);self.assertFalse(v['nativeHostCurrentPairClaimed'])
        finally:db.close()
    def test_freeze_stops_owned_native_process_and_blocks_input(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
            try:
                time.sleep(.05)  # Wait for exec before binding the owned command identity.
                owner={'pid':child.pid,'identity':process_identity(child.pid),'nonce':7}
                (root/'owner').write_text(json.dumps(owner))
                cfg={'nonce':7,'continuity':{'owner':str(root/'owner'),'permit':str(root/'permit'),'stopped':str(root/'stopped')}}
                freeze(cfg,'fixture host expiry')
                stat=subprocess.check_output(['ps','-p',str(child.pid),'-o','stat='],text=True)
                self.assertIn('T',stat);self.assertEqual((root/'permit').read_text(),'STOPPED\n')
            finally:
                import os,signal
                os.kill(child.pid,signal.SIGCONT);child.terminate();child.wait()
