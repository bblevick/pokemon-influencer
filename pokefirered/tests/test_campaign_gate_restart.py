"""Restart B/E fixtures: domain-only Rick events, no emulator or model claims."""
import tempfile,unittest
from pathlib import Path
from test_world01 import BUILD,TAG,SIZES,flash,msg
from puppeteer.store import PuppeteerStore
from world.saves import fingerprint
from world.restart import recover_durable_work
class QueuedRestartTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'world.sqlite3';self.w=PuppeteerStore(self.path,BUILD,TAG);self.save=fingerprint(flash(),SIZES);self.w.import_save(self.save);self.w.authorize_launch(100,self.save);self.w.activate_puppeteer()
 def tearDown(self):self.w.close();self.tmp.cleanup()
 def battle(self):
  for i,t in enumerate([1,2,6,3,4,5],1):self.w.ingest(msg(i,t))
 def reopen(self):self.w.close();self.w=PuppeteerStore(self.path,BUILD,TAG)
 def test_queued_recap_survives_restart_and_settles_once(self):
  self.battle();o=next(iter(self.w.puppeteer_state()['obligations'].values()));j=self.w.begin_job(o['obligationID'],'offline');self.reopen()
  self.assertEqual(recover_durable_work(self.w)['status'],'recovered');self.assertEqual(len(self.w.social_state()['posts']),1);before=self.w.verify_social_replay()
  self.assertEqual(recover_durable_work(self.w)['operations'],[]);self.assertEqual(before,self.w.verify_social_replay());self.assertEqual(self.w._one('SELECT status FROM puppeteer_jobs WHERE id=?',(j['jobID'],))['status'],'completed')
 def test_ingested_unacked_event_is_reacked_without_new_history(self):
  self.w.ingest(msg(1));before=self.w.verify_replay();self.reopen();self.assertTrue(self.w.ingest(msg(1))['duplicate']);self.assertEqual(before,self.w.verify_replay())
 def test_emitted_not_ingested_event_is_committed_once_after_restart(self):
  event=msg(1);self.reopen();self.assertFalse(self.w.ingest(event)['duplicate']);self.assertTrue(self.w.ingest(event)['duplicate']);self.assertEqual(self.w.get_current_world_cursor(),1)
 def test_old_emitted_event_cannot_commit_after_managed_restore(self):
  event=msg(1);self.w.authorize_launch(200,self.save)
  with self.assertRaisesRegex(ValueError,'unmanaged'):self.w.ingest(event)
  self.assertEqual(self.w.get_current_world_cursor(),0)
if __name__=='__main__':unittest.main()
