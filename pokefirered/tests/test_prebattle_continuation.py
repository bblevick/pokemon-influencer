"""Actual retained commitment regression on disposable copies, no providers."""
import copy,json,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from campaign.scripted import ScriptedStore
from world.store import WorldError
from world.continuation import METHODS
from world.saves import fingerprint,layout_from_build

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/phase8/rival01-prebattle-continuation'
M=E/'manifest-native.json'

class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'world.sqlite3'
        self.record=json.loads((E/'admissibility.json').read_text());self.identity=self.record['continuationID'];self.d=self.record['descriptor']
        source=sqlite3.connect('file:'+str(ROOT/'.local/rival01-rollback/dots-renewal-committed-host.sqlite3')+'?mode=ro',uri=True)
        target=sqlite3.connect(self.path);source.backup(target);source.close();target.close()
        self.w=ScriptedStore(self.path,M)
        self.save=fingerprint((ROOT/'.local/rival01-rollback/pre-rival-pair.sav').read_bytes(),layout_from_build(ROOT/json.loads(M.read_text())['rom_path']))
    def tearDown(self):self.w.close();self.temp.cleanup()
    def create(self,proof=None,**kw):
        return self.w.create_prebattle_continuation(kw.get('parent',self.d['parent']['id']),kw.get('actor',self.d['actor']),kw.get('trainer',self.d['nativeTrainer']),kw.get('opportunity',self.d['opportunityID']),self.save,proof or self.d['nativeProof'])
    def launch(self,nonce=42130001,**kw):
        origin=self.w.authorize_continuation_launch(self.identity,nonce,kw.get('save',self.save),kw.get('actor',self.d['actor']),kw.get('trainer',self.d['nativeTrainer']),kw.get('opportunity',self.d['opportunityID']))
        if kw.get('settle',True):
            native={**self.d['nativeProof']['native'],'origin':origin,'nonce':nonce,'frame':100}
            self.w.settle_continuation_session(origin,self.save,native)
        return origin
    def test_real_retained_records_parent_hashes_and_repeated_restart(self):
        before={m:getattr(self.w,m)() for m in METHODS};cp=dict(self.w._one('SELECT * FROM checkpoints WHERE id=?',(self.d['parent']['id'],)))
        self.assertEqual(self.create(),self.identity);self.assertEqual(self.create(),self.identity)
        self.launch();self.w.close();self.w=ScriptedStore(self.path,M);self.launch(42130002)
        self.assertEqual(before,{m:getattr(self.w,m)() for m in METHODS})
        self.assertEqual(cp,dict(self.w._one('SELECT * FROM checkpoints WHERE id=?',(cp['id'],))))
        self.assertEqual(self.w.locked_preparation(self.d['actor']),self.d['lock'])
        self.assertEqual(self.w.continuation_encounter(self.identity,self.save,self.d['actor'],self.d['nativeTrainer'],self.d['opportunityID'])['memo'],self.d['memo'])
        self.assertIn(self.d['memo'],self.w.memo_records())
        self.assertEqual(self.w._one('SELECT COUNT(*) n FROM prebattle_continuations')['n'],1)
    def test_wrong_opportunity_actor_encounter_and_campaign_parent(self):
        self.create()
        for kwargs in ({'opportunity':'other'},{'actor':'trainer:fr:trainer:0334'},{'trainer':333}):
            with self.subTest(kwargs=kwargs),self.assertRaisesRegex(WorldError,'OPPORTUNITY_ID_MISMATCH'):self.launch(**kwargs)
        with self.assertRaisesRegex(WorldError,'INVALID_CONTINUATION_PARENT'):self.create(parent='different-campaign-checkpoint')
    def test_rollback_abandons_and_does_not_revive_future(self):
        self.create();self.w.restore(self.save)
        self.assertIsNone(self.w.locked_preparation(self.d['actor']))
        with self.assertRaisesRegex(WorldError,'INVALID_CONTINUATION_LINEAGE'):self.launch()
        self.assertTrue(self.w.campaign()['pending_fork'])
    def test_wrong_native_identity_and_unproved_field_equivalence(self):
        for key,value in [('nonce',9),('origin','wrong'),('run',2),('drops',1),('eventCounter',1)]:
            p=copy.deepcopy(self.d['nativeProof']);p['native'][key]=value
            with self.subTest(key=key),self.assertRaises(WorldError):self.create(p)
        p=copy.deepcopy(self.d['nativeProof']);p['kind']='field-without-equivalence'
        with self.assertRaisesRegex(WorldError,'NATIVE_EQUIVALENCE_UNPROVED'):self.create(p)
    def test_crash_before_descriptor_commit_is_atomic(self):
        real=self.w._continuation_material
        def interrupted(*args,**kw):
            real(*args,**kw);raise RuntimeError('crash before seal')
        with patch.object(self.w,'_continuation_material',side_effect=interrupted):
            with self.assertRaises(RuntimeError):self.create()
        self.assertIsNone(self.w._one("SELECT name FROM sqlite_master WHERE name='prebattle_continuations'"))
        self.assertEqual(self.create(),self.identity)
    def test_crash_during_validation_and_before_session_commit(self):
        self.create();before=[tuple(r) for r in self.w.db.execute('SELECT * FROM launches')]
        with patch('world.continuation.uid',side_effect=RuntimeError('crash before grant')):
            with self.assertRaises(RuntimeError):self.launch()
        self.assertEqual(before,[tuple(r) for r in self.w.db.execute('SELECT * FROM launches')])
        self.launch()
    def test_partial_handshake_new_nonce_and_stale_old_launch(self):
        self.create();self.launch();self.launch(42130002)
        with self.assertRaises(WorldError):self.w._launch(42130001,1)
        self.w._launch(42130002,1)
        with self.assertRaisesRegex(WorldError,'NATIVE_SESSION_REUSE'):self.launch(42130002)
    def test_mismatched_native_save(self):
        from dataclasses import replace
        self.create()
        with self.assertRaisesRegex(WorldError,'NATIVE_STATE_MISMATCH'):
            self.launch(save=replace(self.save,fingerprint='0'*64))
    def test_sibling_branch_and_abandoned_generation(self):
        self.create()
        # Deterministic corruption fixtures; no production helper issues SQL.
        self.w.db.execute("UPDATE campaigns SET active_branch='fixture-sibling'")
        with self.assertRaises(WorldError):self.launch()
    def test_completed_or_superseded_status(self):
        self.create()
        for status in ['consumed','completed','abandoned','incomplete','invalid']:
            self.w.db.execute('UPDATE prebattle_continuations SET status=?',(status,))
            with self.assertRaisesRegex(WorldError,'ABANDONED_CONTINUATION'):self.launch()
    def test_descriptor_and_future_version_immutability(self):
        self.create()
        with self.assertRaises(sqlite3.IntegrityError):self.w.db.execute("UPDATE prebattle_continuations SET descriptor='{}'")
        self.launch()
        with self.assertRaises(sqlite3.IntegrityError):self.w.db.execute('DELETE FROM prebattle_session_closures')
        self.w.db.execute('UPDATE prebattle_version SET version=99')
        with self.assertRaisesRegex(WorldError,'UNSUPPORTED_CONTINUATION_VERSION'):self.w.continuation_catalog()
        self.w.close()
        with self.assertRaisesRegex(WorldError,'UNSUPPORTED_CONTINUATION_VERSION'):ScriptedStore(self.path,M)
    def test_incomplete_memo_or_prep_rejected(self):
        with patch.object(self.w,'locked_preparation',return_value=None):
            with self.assertRaisesRegex(WorldError,'COMMITMENT_INCOMPLETE'):self.create()
        with patch.object(self.w,'memo_records',return_value=[]):
            with self.assertRaisesRegex(WorldError,'COMMITMENT_INCOMPLETE'):self.create()
    def test_native_start_consumption_and_no_model_work(self):
        self.create()
        with patch('strategy.provider.OpenRouterProvider._request',side_effect=AssertionError('network forbidden')):
            self.launch()
        self.assertEqual(self.w._one("SELECT count(*) n FROM strategy_jobs WHERE status='active'")['n'],0)
        with patch.object(self.w,'decision_state',return_value={**self.w.decision_state(),'installations':{self.d['encounterID']:{}}}):
            # Nonempty installation marks actual consumption.
            state=self.w.decision_state();state['installations'][self.d['encounterID']]={'installed':True}
            with patch.object(self.w,'decision_state',return_value=state):
                with self.assertRaisesRegex(WorldError,'ENCOUNTER_ALREADY_CONSUMED'):self.launch(42130002)
    def test_crash_after_grant_requires_native_revalidation(self):
        self.create();self.launch(settle=False)
        with self.assertRaisesRegex(WorldError,'PRIOR_NATIVE_SESSION_UNSETTLED'):self.launch(42130002)
    def test_battle_start_consumes_and_completion_never_reattaches(self):
        from dataclasses import replace
        from test_world01 import msg
        self.create();self.launch()
        start=replace(msg(1,trainer=self.d['nativeTrainer'],nonce=42130001),tag=self.w.compatibility['nativeTag'])
        self.w.ingest(start)
        self.assertEqual(self.w._one('SELECT status FROM prebattle_continuations')['status'],'consumed')
        with self.assertRaises(WorldError):self.launch(42130002)
        for seq,typ in enumerate([2,4,5],2):
            packet=replace(msg(seq,typ,trainer=self.d['nativeTrainer'],nonce=42130001),tag=self.w.compatibility['nativeTag'])
            self.w.ingest(packet)
        self.assertEqual(self.w._one('SELECT status FROM prebattle_continuations')['status'],'completed')
        with self.assertRaises(WorldError):self.launch(42130002)
    def test_committed_fallback_has_equal_durability(self):
        from strategy.memo import fallback_text
        from system1.provider import run_selection
        self.w.close();self.path=Path(self.temp.name)/'fallback.sqlite3'
        src=sqlite3.connect('file:'+str(ROOT/'.local/rival01-rollback/pre-rival-pair.sqlite3')+'?mode=ro',uri=True)
        dst=sqlite3.connect(self.path);src.backup(dst);dst.close();src.close()
        self.w=ScriptedStore(self.path,M);origin=self.w.authorize_launch(42130000,self.save);self.w.adopt_content()
        actor=self.d['actor'];job=self.w.begin_strategy(actor,'first',provider_binding={'provider':'fixture','model':'fallback-fixture','adapterVersion':1})
        memo=self.w.finish_memo(job['jobID'],fallback_text(job['packet']),'fallback',{'fixture':True},job['packet']['contextID'])
        selected=run_selection(self.w,self.w.begin_selection(actor,'first'))
        lock=self.w.commit_preparation(selected['decisionID'])
        proof=copy.deepcopy(self.d['nativeProof']);proof['native'].update(origin=origin,nonce=42130000)
        identity=self.w.create_prebattle_continuation(self.d['parent']['id'],actor,self.d['nativeTrainer'],lock['opportunityID'],self.save,proof)
        self.w.authorize_continuation_launch(identity,42130001,self.save,actor,self.d['nativeTrainer'],lock['opportunityID'])
        result=self.w.continuation_encounter(identity,self.save,actor,self.d['nativeTrainer'],lock['opportunityID'])
        self.assertEqual(result['memo'],memo);self.assertEqual(result['preparation'],lock)
