"""Host fixtures only: bounded selection, immutable commitment and paired replay."""
import unittest,copy,json,tempfile,time
from pathlib import Path
from unittest.mock import patch
from tests import test_prep01 as f
from strategy.memo import MemoStore,run_memo_job
from strategy.provider import FixtureProvider,ProviderError
from system1.store import PreparationDecisionStore
from system1.domain import validate_decision,debit_stock,symbol
from system1.provider import FixtureDecisionProvider,run_selection,preflight,NativeDecisionProvider,Budget
MEMO='Rick wants unavailable Sleep Powder and a Water starter. Preserve his partners and slow the opponent. The next lead is unknown.'
class PreparationTests(unittest.TestCase):
    battle=f.PrepTests.battle;checkpoint=f.PrepTests.checkpoint;eligible=f.PrepTests.eligible
    def setUp(self):
        f.PrepTests.setUp(self);self.w.close();self.w=MemoStore(self.path,f.BUILD,f.TAG);self.eligible();run_memo_job(self.w,self.w.begin_strategy(f.RICK),FixtureProvider(MEMO));self.w.close();self.w=PreparationDecisionStore(self.path,f.BUILD,f.TAG)
    def tearDown(self):f.PrepTests.tearDown(self)
    def choose(self):
        job=self.w.begin_selection(f.RICK);p=FixtureDecisionProvider(next(k for k in job['request']['choices'] if k!=job['request']['fallbackCandidateID']));return job,run_selection(self.w,job,p,source='mock')
    def test_full_choices_exact_memo_qualified_moves_and_purity(self):
        before=self.w.preparation_state();job=self.w.begin_selection(f.RICK);r=job['request'];self.assertEqual(len(r['choices']),16);self.assertIn(MEMO,r['state']);self.assertIn('AUTHORIZED OPPONENT KNOWLEDGE',r['state']);self.assertIn('STRATEGY MEMO — SUBJECTIVE',r['state']);self.assertEqual(before,self.w.preparation_state());self.assertEqual(symbol(self.w.content.cat,'moves',40),'Poison Sting');self.assertEqual(symbol(self.w.content.cat,'moves',33),'Tackle')
        self.assertLessEqual(len(json.dumps({'model':'inception/mercury-decide:free','state':r['state'],'questions':{'preparation':{'type':'choice','instructions':r['question'],'criteria':r['choices']}}},separators=(',',':')).encode()),32768)
    def test_record_then_atomic_commit_lineage_and_lock(self):
        before=self.w.preparation_state();job,d=self.choose();self.assertEqual(before,self.w.preparation_state());c=self.w.commit_preparation(d['decisionID']);self.assertEqual(c,self.w.commit_preparation(d['decisionID']));self.assertEqual(self.w.begin_selection(f.RICK)['status'],'committed');self.assertEqual([p['lineage'] for p in c['companions']],[p['lineage'] for p in before['actors'][f.RICK]['companions']]);self.assertEqual(c['strategyText'],MEMO);self.assertEqual(c['remainingStock'],[]);self.assertEqual(c['candidate']['acquisitionCount'],0);self.assertEqual(self.w.get_preparation_opportunity(f.RICK)['status'],'committed')
    def test_restore_before_and_after_commit_then_fresh_process(self):
        before=self.save;job,d=self.choose();c=self.w.commit_preparation(d['decisionID']);self.checkpoint(True);after=self.save;sha=self.w.verify_decision_replay();self.w.restore(before);self.assertIsNone(self.w.locked_preparation(f.RICK));self.w.restore(after);self.assertEqual(self.w.locked_preparation(f.RICK),c);self.w.close();self.w=PreparationDecisionStore(self.path,f.BUILD,f.TAG);self.assertEqual(self.w.verify_decision_replay(),sha);self.assertEqual(self.w.begin_selection(f.RICK)['commitment'],c)
    def test_restore_revokes_late_selection(self):
        job=self.w.begin_selection(f.RICK);self.w.restore(self.save)
        with self.assertRaises(ValueError):run_selection(self.w,job,FixtureDecisionProvider(job['request']['fallbackCandidateID']),source='mock')
    def test_save_barrier_rejects_commit(self):
        job,d=self.choose();intent=self.w.begin_save(self.nonce,self.save)
        with self.assertRaises(ValueError):self.w.commit_preparation(d['decisionID'])
        self.w.abandon_save(intent);self.assertTrue(self.w.commit_preparation(d['decisionID'])['locked'])
    def test_fallback_is_legal_and_labeled(self):
        job=self.w.begin_selection(f.RICK);d=run_selection(self.w,job,FixtureDecisionProvider('invented'));self.assertEqual(d['source'],'fallback');self.assertEqual(d['result']['choiceID'],job['request']['fallbackCandidateID']);self.assertEqual(self.w.preparation_state()['opportunities'][job['request']['scope']['opportunityID']]['status'],'available')
    def test_conflicting_duplicate_and_legacy_writer_rejected(self):
        job,d=self.choose();r=copy.deepcopy(d['result']);r['choiceID']=job['request']['fallbackCandidateID']
        with self.assertRaises(ValueError):self.w.finish_selection(job['request'],r,'mock')
        with self.assertRaises(ValueError):MemoStore(self.path,f.BUILD,f.TAG)
    def test_five_impossible_wishes_never_change_choice_universe(self):
        # These fixtures prove authority, not model semantic reasoning.
        for wish in ('Sleep Powder at level 10','a Water starter','invent a Potion','raise level to 100','replace every original partner'):
            job=self.w.begin_selection(f.RICK);self.assertEqual(len(job['request']['choices']),16)
            bad={'choiceID':wish,'probabilities':None,'confidence':.4}
            with self.assertRaises(ValueError):validate_decision(bad,job['request']['choices'])
    def test_finite_resource_debit_and_rollback(self):
        self.assertEqual(debit_stock([[1,2]],[[1,1]]),[[1,1]])
        for cost in ([[1,3]],[[1,1],[1,1]],[[1,-1]],[[9,1]]):
            with self.assertRaises(ValueError):debit_stock([[1,2]],cost)
    def test_distribution_not_resampled_or_argmaxed(self):
        x={'choiceID':'b','probabilities':{'a':.6,'b':.4},'confidence':.4};self.assertIs(validate_decision(x,{'a':'A','b':'B'}),x)
        for probs in ({'a':1},{'a':.1,'b':.1},{'a':float('nan'),'b':0}):
            with self.assertRaises(ValueError):validate_decision({**x,'probabilities':probs},{'a':'A','b':'B'})
class AdditionalPreparationTests(unittest.TestCase):
    setUp=PreparationTests.setUp;tearDown=PreparationTests.tearDown
    battle=PreparationTests.battle;checkpoint=PreparationTests.checkpoint;eligible=PreparationTests.eligible;choose=PreparationTests.choose
    def test_evolution_commit_preserves_individual_history(self):
        before=self.w.get_trainer_companion_state(f.RICK);job=self.w.begin_selection(f.RICK);candidate=next(c for c in job['request']['bundle']['candidateSet']['candidates'] if c['descriptors']['evolvedCompanions']==1);d=run_selection(self.w,job,FixtureDecisionProvider(candidate['candidateID']),source='mock');c=self.w.commit_preparation(d['decisionID']);self.assertEqual(c['candidate'],candidate);self.assertEqual({p['lineage'] for p in before},{p['lineage'] for p in c['companions']});self.assertTrue(any(p['history'] for p in c['companions']));self.assertTrue(all(p['level']<=10 for p in c['companions']));self.assertEqual(c['remainingStock'],[])
    def test_later_evidence_does_not_reroll_locked_preparation(self):
        job,d=self.choose();c=self.w.commit_preparation(d['decisionID']);self.battle(103);provider=FixtureDecisionProvider('must-not-call');self.assertEqual(run_selection(self.w,self.w.begin_selection(f.RICK),provider)['commitment'],c);self.assertEqual(provider.calls,0)
    def test_future_commit_excluded_from_divergent_branch(self):
        before=self.save;job,d=self.choose();c=self.w.commit_preparation(d['decisionID']);self.checkpoint(True);later=self.save;self.w.restore(before);self.w.authorize_launch(201,before)
        for seq,typ in enumerate((1,2,6,3,4,5),1):self.w.ingest(f.replace(f.msg(seq,typ,battle=99,trainer=103,nonce=201),tag=f.TAG))
        self.assertNotEqual(self.w.get_active_branch(),c['scope']['branch']);self.assertIsNone(self.w.locked_preparation(f.RICK));self.w.restore(later);self.assertEqual(self.w.locked_preparation(f.RICK),c)
    def test_selection_and_commit_do_not_deliver_npc_knowledge(self):
        before=self.w.trainer_packet(f.JANICE);job,d=self.choose();self.w.commit_preparation(d['decisionID']);self.assertEqual(self.w.trainer_packet(f.JANICE),before)

class TransportTests(unittest.TestCase):
    def test_exact_endpoint_discovery_and_paid_rejection(self):
        row={'id':'fixture:free','architecture':{'output_modalities':['decisions']},'endpoints':[{'model_id':'fixture:free','status':0,'uptime_last_5m':100,'pricing':{'prompt':'0','completion':'0'}}]}
        with patch('system1.provider.public_get',side_effect=[{'data':[]},{'data':row}]):self.assertEqual(preflight('fixture:free')['catalogDiscovery'],'exact-model-endpoints')
        row['endpoints'][0]['pricing']['prompt']='1'
        with patch('system1.provider.public_get',side_effect=[{'data':[]},{'data':row}]),self.assertRaises(ProviderError):preflight('fixture:free')
    def test_native_wire_stats_and_no_chat(self):
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,n):return json.dumps({'model':'fixture:free','answers':{'preparation':{'type':'choice','choice':'b','probabilities':{'a':.6,'b':.4},'confidence':.4}},'usage':{'cost':0}}).encode()
        with tempfile.TemporaryDirectory() as td:
            route={'model':'fixture:free','checkedAtUnix':time.time(),'api':'https://openrouter.ai/api/v1/systemone','catalog':{}}
            p=NativeDecisionProvider({'model':'fixture:free'},'dummy-key',route,Path(td)/'budget.json','test')
            def http(req,timeout):
                body=json.loads(req.data);self.assertEqual(set(body),{'model','state','questions'});self.assertEqual(body['questions']['preparation']['criteria'],{'a':'A','b':'B'});return Response()
            with patch('urllib.request.urlopen',http):r=p.decide('facts; subjective memo','Choose',{'a':'A','b':'B'})
            self.assertEqual(r['choiceID'],'b');self.assertEqual(r['confidence'],.4);self.assertNotIn('dummy-key',(Path(td)/'budget.json').read_text())
