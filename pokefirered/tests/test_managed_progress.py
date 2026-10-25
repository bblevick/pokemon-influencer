"""Existing frame counter must advance; freshness and connection are insufficient."""
import json,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from bridge.managed import Health

class Store:
    def campaign(self):return {'id':'campaign','active_branch':'branch','cursor':10,'status':'paired'}
    def _one(self,*args):return {'last':0}

class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
        (self.p/'manifest').write_text(json.dumps({'rom_sha256':'a'*64}))
        self.cfg={'nonce':9,'origin':'new','manifest':str(self.p/'manifest'),'continuity':{'native':str(self.p/'native'),'host':str(self.p/'host'),'telemetry':str(self.p/'trace')}}
        self.h=Health(self.cfg);self.native={'nonce':9,'origin':'new','run':1,'build':'a'*64,'frame':10,'authenticated':True,'drops':0,'ack':0,'depth':0,'eventCounter':0}
    def tearDown(self):self.tmp.cleanup()
    def publish(self,**changes):
        self.native.update(changes);(self.p/'native').write_text(json.dumps(self.native));self.h.publish(Store(),'CONNECTED');return json.loads((self.p/'host').read_text())
    def test_first_packet_and_cached_packets_not_ready(self):
        self.assertFalse(self.publish()['nativeProgress']);self.assertFalse(self.publish()['nativeProgress'])
    def test_current_frames_reach_host_and_progress(self):
        self.publish();x=self.publish(frame=20);self.assertTrue(x['nativeProgress']);self.assertEqual(x['nativeFrame'],20)
        self.assertEqual(len((self.p/'trace').read_text().splitlines()),2)
    def test_no_frames_paused_or_stale_never_ready(self):
        self.publish();self.publish(frame=20)
        with patch('bridge.managed.time.time',return_value=time.time()+2):self.assertFalse(self.publish().get('nativeProgress',False))
    def test_wrong_run_nonce_origin_build_ack_and_gaps(self):
        for field,value in [('run',2),('nonce',8),('origin','old'),('build','b'*64),('ack',1),('eventCounter',5),('drops',1)]:
            with self.subTest(field=field):
                original=self.native[field];self.assertFalse(self.publish(**{field:value}).get('nativeProgress',False));self.native[field]=original
    def test_frame_regression_fails_closed(self):
        self.publish();self.publish(frame=20);self.assertFalse(self.publish(frame=5)['nativeProgress'])
    def test_new_host_requires_new_progression(self):
        self.publish();self.publish(frame=20);self.h=Health(self.cfg)
        self.assertFalse(self.publish()['nativeProgress']);self.assertTrue(self.publish(frame=30)['nativeProgress'])
