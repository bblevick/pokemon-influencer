"""Actual pinned Hermes runtime, deterministic inference transport. No live calls."""
import json,os,unittest,uuid
from pathlib import Path
import test_hermes01 as fixtures
from puppeteer.runtime import run_job,cleanup,create_home,HOMES,MARKER,checked_home
from world.store import WorldError

class RuntimeTests(unittest.TestCase):
    # Reuse setup helpers, without duplicating the domain test suite.
    setUp=fixtures.PuppeteerTests.setUp
    tearDown=fixtures.PuppeteerTests.tearDown
    battle=fixtures.PuppeteerTests.battle
    job=fixtures.PuppeteerTests.job
    def test_actual_hermes_two_fresh_jobs_and_cleanup(self):
        self.battle();j=self.job('mock');first=run_job(self.path,j['jobID'])
        self.assertEqual(first['outcome']['producer'],'hermes',first['failures']);self.assertEqual(len(first['requests']),3)
        self.assertEqual([t['name'] for t in first['tools']],['get_battle_evidence','recall_puppeteer_memory','get_actor_context','submit_recap_and_memory_result'])
        home=Path(first['runtimeHome']);(home/'MEMORY.md').write_text('PI_PRIVATE_CANARY_OLD_SESSION')
        cleanup(home,False);self.assertFalse(home.exists());self.assertTrue(self.path.exists())
        self.battle(first=7,bid=2);j=self.job('mock');second=run_job(self.path,j['jobID'])
        self.assertNotEqual(first['runtimeHome'],second['runtimeHome']);self.assertEqual(second['outcome']['producer'],'hermes',second['failures'])
        recalled=next(t['output'] for t in second['tools'] if t['name']=='recall_puppeteer_memory')['episodes']
        self.assertEqual(recalled[0]['summary']['observedPlayerMoves'],[[1,33]])
        self.assertNotIn('PI_PRIVATE_CANARY',json.dumps(second['requests']));self.assertIn('observedPlayerMoves',json.dumps(second['requests']))
        cleanup(Path(second['runtimeHome']),False)
    def test_actual_hermes_invalid_and_refusal_fallback(self):
        for behavior in ('invalid','refusal'):
            self.battle(first=1 if behavior=='invalid' else 7,bid=1 if behavior=='invalid' else 2)
            j=self.job('mock');r=run_job(self.path,j['jobID'],behavior=behavior)
            self.assertEqual(r['outcome']['producer'],'deterministic_fallback');self.assertLessEqual(len(r['requests']),3);self.assertLessEqual(len(r['tools']),6)
            cleanup(Path(r['runtimeHome']),False)
    def test_cleanup_paths_ownership_symlinks_active_and_dry_run(self):
        self.battle();j=self.job();home,owner=create_home(j['jobID'],self.path)
        for target in ('', '/',str(Path.home()),str(HOMES.parent.parent.parent),str(HOMES/'..'/home.name)):
            with self.assertRaises(WorldError):cleanup(Path(target))
        with self.assertRaises(WorldError):cleanup(home)
        owner.update(active=False,pid=os.getpid());(home/MARKER).write_text(json.dumps(owner))
        with self.assertRaises(WorldError):cleanup(home)
        owner['pid']=0;(home/MARKER).write_text(json.dumps(owner));self.w.fallback(j['jobID'])
        (home/'escape').symlink_to(self.path)
        with self.assertRaises(WorldError):cleanup(home)
        (home/'escape').unlink();preview=cleanup(home);self.assertEqual(preview['candidates'],[str(home)]);self.assertTrue(home.exists())
        cleanup(home,False);self.assertTrue(self.path.exists())
    def test_quarantine_abandoned_symlink_preserves_external_data(self):
        from puppeteer.runtime import recover_runtime
        self.battle();j=self.job();home,owner=create_home(j['jobID'],self.path)
        canary=Path(self.tmp.name)/'unrelated-personal-profile';canary.mkdir();(canary/'MEMORY.md').write_text('private')
        (home/'unsafe').symlink_to(canary,target_is_directory=True)
        with self.assertRaises(WorldError):cleanup(home,False)
        result=recover_runtime(home,quarantine=True);q=Path(result['quarantined'])
        self.assertFalse(home.exists());self.assertTrue((canary/'MEMORY.md').exists());self.assertEqual(len(self.w.puppeteer_state()['episodes']),1)
        # Remove only the test symlink, then bring the owned quarantined fixture
        # back for normal checked cleanup; production never reuses quarantine.
        (q/'unsafe').unlink();q.rename(home);cleanup(home,False)
    def test_unavailable_provider_keeps_mandatory_obligation(self):
        from unittest.mock import patch
        self.battle();j=self.job('enabled-test')
        with patch('puppeteer.runtime.verify_free_model',side_effect=WorldError('offline test provider absent')):
            r=run_job(self.path,j['jobID'],transport='live',live=True)
        self.assertFalse(r['requests']);self.assertEqual(r['outcome']['producer'],'deterministic_fallback');self.assertEqual(len(self.w.social_state()['posts']),1)
    def test_readonly_fresh_runtime_retrieves_durable_memory_without_republication(self):
        self.battle();j=self.job();first=self.w.fallback(j['jobID']);before=self.w.verify_puppeteer_replay();j=self.w.begin_recall_job(fixtures.RICK)
        r=run_job(self.path,j['jobID'],behavior='recall')
        self.assertEqual(r['outcome']['producer'],'hermes_memory_retrieval',r['failures']);self.assertEqual(len(r['requests']),2)
        self.assertEqual(self.w.verify_puppeteer_replay(),before);self.assertEqual(len(self.w.social_state()['posts']),1)
        recall=next(t['output'] for t in r['tools'] if t['name']=='recall_puppeteer_memory');self.assertEqual(recall['episodes'][0]['episodeID'],first['episodeID'])
        cleanup(Path(r['runtimeHome']),False)
    def test_hard_job_deadline_falls_back_without_waiting_for_model(self):
        import time
        self.battle();j=self.w.begin_job(next(iter(self.w.puppeteer_state()['obligations'])),'mock',deadline=.05)
        started=time.monotonic();r=run_job(self.path,j['jobID'])
        self.assertLess(time.monotonic()-started,5);self.assertEqual(r['outcome']['producer'],'deterministic_fallback')
        if r['runtimeHome']:cleanup(Path(r['runtimeHome']),False)
    def test_stop_refuses_unrelated_live_pid_before_touching_game(self):
        from puppeteer.runtime import recover_runtime
        self.battle();j=self.job();home,owner=create_home(j['jobID'],self.path)
        owner['pid']=os.getpid();(home/MARKER).write_text(json.dumps(owner))
        with self.assertRaisesRegex(WorldError,'PID ownership mismatch'):recover_runtime(home,stop=True)
        self.assertFalse(self.w.puppeteer_state()['episodes'])
        owner.update(pid=0,active=False);(home/MARKER).write_text(json.dumps(owner));recover_runtime(home);cleanup(home,False)
    def test_serial_bundled_retrieval_submits_within_three_requests(self):
        self.battle();j=self.job('mock');first=run_job(self.path,j['jobID'],behavior='bundle')
        self.assertEqual(first['outcome']['producer'],'hermes',first['failures']);self.assertEqual(len(first['requests']),3)
        self.assertEqual([t['name'] for t in first['tools']],['get_battle_evidence','submit_recap_and_memory_result'])
        cleanup(Path(first['runtimeHome']),False)
        self.battle(first=7,bid=2);j=self.job('mock');r=run_job(self.path,j['jobID'],behavior='bundle')
        bundle=r['tools'][0]['output'];self.assertEqual(bundle['priorMemory']['episodes'][0]['summary']['observedPlayerMoves'],[[1,33]])
        self.assertEqual(bundle['actorContext']['trainer']['actorID'],fixtures.RICK)
        self.assertEqual(r['outcome']['producer'],'hermes',r['failures']);cleanup(Path(r['runtimeHome']),False)

    def test_closeout_bundle_commits_without_finished_request(self):
        self.battle();j=self.job('mock');r=run_job(self.path,j['jobID'],behavior='bundle',experiment='closeout')
        self.assertEqual(r['outcome']['producer'],'hermes',r['failures']);self.assertEqual(len(r['requests']),2)
        self.assertEqual([t['name'] for t in r['tools']],['get_battle_evidence','submit_recap_and_memory_result'])
        self.assertEqual(r['workerExit'],0);self.assertEqual(len(self.w.social_state()['posts']),1)
        result=r['tools'][-1]['arguments']['result']
        with self.assertRaises(WorldError):self.w.settle_job(j['jobID'],result,producer='hermes')
        cleanup(Path(r['runtimeHome']),False)
        j=self.w.begin_recall_job(fixtures.RICK);fresh=run_job(self.path,j['jobID'],behavior='recall',experiment='closeout')
        self.assertEqual(fresh['tools'][0]['output']['episodes'][0]['episodeID'],r['outcome']['episodeID'])
        self.assertEqual(fresh['outcome']['producer'],'hermes_memory_retrieval');cleanup(Path(fresh['runtimeHome']),False)
    def test_renewed_budget_persists_separately_across_restarts(self):
        import tempfile
        from unittest.mock import patch
        from puppeteer.runtime import charge_live
        with tempfile.TemporaryDirectory() as folder,patch('puppeteer.runtime.ROOT',Path(folder)):
            for i in range(10):self.assertEqual(charge_live(),i+1)
            with self.assertRaises(WorldError):charge_live()
            for i in range(10):self.assertEqual(charge_live('closeout'),i+1)
            with self.assertRaises(WorldError):charge_live('closeout')
            self.assertEqual(json.loads((Path(folder)/'.local/hermes01/live-budget.json').read_text())['attempts'],10)
            renewed=Path(folder)/'.local/hermes01/closeout-live-budget.json'
            renewed.write_text(json.dumps({'attempts':2,'limit':10,'closed':True}))
            with self.assertRaisesRegex(WorldError,'experiment closed'):charge_live('closeout')
            self.assertEqual(json.loads(renewed.read_text())['attempts'],2)
