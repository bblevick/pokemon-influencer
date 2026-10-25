"""Host fixtures only; live/native acceptance is recorded separately."""
import unittest,json,copy,tempfile,sqlite3
from pathlib import Path
from tests import test_prep01 as f
from strategy.store import StrategyStore
from strategy.context import build_context
from strategy.domain import validate,fallback
from strategy.provider import FixtureProvider,LiveBudget,qualify_route,ProviderError,Limits
from strategy.runtime import run_job
from jsonschema.exceptions import ValidationError
from prep.store import PrepStore

class StrategyTests(unittest.TestCase):
    def setUp(self):
        f.PrepTests.setUp(self);self.w.close();self.w=StrategyStore(self.path,f.BUILD,f.TAG)
    def tearDown(self):f.PrepTests.tearDown(self)
    battle=f.PrepTests.battle
    checkpoint=f.PrepTests.checkpoint
    eligible=f.PrepTests.eligible
    def packet(self):self.eligible();return build_context(self.w,f.RICK)
    def test_context_no_selection_or_frequency(self):
        p=self.packet();encoded=json.dumps(p['modelInput']);self.assertEqual(p['candidateCount'],16)
        for forbidden in ('candidateID','occurrencesInWindow','worldCursor','nativeReceipt','playerParty','director_memory'):
            self.assertNotIn(forbidden,encoded)
        self.assertEqual(p['modelInput']['preparation']['acquisitionAllowance'],0);self.assertEqual(p['modelInput']['resources']['available'],[])
        self.assertEqual(p['modelInput']['behavior']['reference'],'rick-strategy-v1')
    def test_scope_doug_has_no_unearned_opportunity(self):
        self.packet()
        with self.assertRaises(ValueError):build_context(self.w,f.DOUG)
        p=build_context(self.w,f.DOUG,'first','battle-only-fixture');self.assertEqual(p['modelInput']['evidence'],[]);self.assertEqual(p['modelInput']['privateEpisodes'],[])
    def test_unexposed_janice_and_brock(self):
        self.checkpoint(False)
        b=build_context(self.w,f.BROCK,'first');self.assertEqual(b['modelInput']['identityPolicy']['theme']['maximumSupport'],0)
        self.assertTrue(b['modelInput']['identityPolicy']['signatureLineages']);self.assertIn('theme_identity',b['modelInput']['capabilities']);validate(fallback(b),b)
        future=copy.deepcopy(b);future['modelInput']['identityPolicy']['theme']['maximumSupport']=1
        self.assertEqual(future['modelInput']['companions'],b['modelInput']['companions']);validate(fallback(future),future)
        self.checkpoint(True)
        j=build_context(self.w,f.JANICE,'first','battle-only-fixture');self.assertEqual(j['modelInput']['evidence'],[])
    def test_persona_influence_without_opponent_assumptions(self):
        p=self.packet();a=fallback(p);different=copy.deepcopy(p);different['modelInput']['behavior']['setupPatience']='weak';b=fallback(different)
        self.assertNotEqual(a['approach'],b['approach']);self.assertEqual(a['assumptions'][0]['kind'],'UNKNOWN')
    def test_reject_candidate_unknown_tags_wrong_actor(self):
        p=self.packet();base=fallback(p)
        for key,value in [('candidateID','candidate:7'),('actor','janice'),('branch','wrong')]:
            bad={**base,key:value}
            with self.assertRaises(ValidationError):validate(bad,p)
        bad=copy.deepcopy(base);bad['priorities']=['choose_candidate_7']
        with self.assertRaises(ValidationError):validate(bad,p)
    def test_resource_and_acquisition_impossible(self):
        p=self.packet()
        for tag in ('consider_acquisition','use_healing'):
            bad=fallback(p);bad['priorities']=[tag]
            with self.assertRaises(ValueError):validate(bad,p)
    def test_foreign_hidden_frequency_assumptions_rejected(self):
        p=self.packet();bad=fallback(p);bad['assumptions']=[{'kind':'observed_species','basis':'direct','confidence':'strong','evidenceRefs':['foreign']}]
        with self.assertRaises(ValueError):validate(bad,p)
        for kind in ('hidden_party','always_bulbasaur','tackle_frequency'):
            bad['assumptions'][0]['kind']=kind
            with self.assertRaises(ValidationError):validate(bad,p)
    def test_direct_vs_reported_and_future_uncertainty(self):
        p=self.packet();p=copy.deepcopy(p);p['modelInput']['evidence']=[{'reference':'exposed','mode':'reported','claim':{'type':'POKEMON_SEEN','speciesID':1},'attribution':{'author':'rick'}}]
        bad=fallback(p);bad['assumptions']=[{'kind':'observed_species','basis':'reported','confidence':'moderate','evidenceRefs':['exposed']}];validate(bad,p)
        bad['assumptions'][0]['basis']='direct'
        with self.assertRaises(ValueError):validate(bad,p)
        bad['assumptions'][0].update(kind='possible_species_return',basis='interpretation',confidence='strong')
        with self.assertRaises(ValueError):validate(bad,p)
        bad['assumptions'][0]['confidence']='weak';validate(bad,p)
    def test_mock_durable_replay_and_idempotency(self):
        p=self.packet();before=self.w.preparation_state();job=self.w.begin_strategy(f.RICK);provider=FixtureProvider(fallback(p));result=run_job(self.w,job,provider)
        again=self.w.begin_strategy(f.RICK);self.assertEqual(again['status'],'recorded');self.assertEqual(run_job(self.w,again,provider),result);self.assertEqual(provider.calls,1);self.assertEqual(before,self.w.preparation_state())
        self.w.close();self.w=StrategyStore(self.path,f.BUILD,f.TAG);self.assertEqual(self.w.recorded_strategy(f.RICK)['decision'],result)
    def test_three_invalid_attempts_fallback(self):
        p=self.packet();job=self.w.begin_strategy(f.RICK);provider=FixtureProvider({'invalid':True});result=run_job(self.w,job,provider)
        self.assertEqual(result['source'],'fallback');self.assertEqual(provider.calls,3);validate(fallback(p),p)
    def test_provider_timeout_fallback(self):
        self.packet();job=self.w.begin_strategy(f.RICK);provider=FixtureProvider(error='request_deadline');r=run_job(self.w,job,provider)
        self.assertEqual(r['source'],'fallback');self.assertEqual(provider.calls,3)
    def test_before_after_pair_restore_and_late_rejection(self):
        p=self.packet();before=self.save;job=self.w.begin_strategy(f.RICK);result=run_job(self.w,job,FixtureProvider(fallback(p)));self.checkpoint(True);after=self.save
        self.w.restore(before);self.assertEqual(self.w.strategy_state()['postures'],{});self.assertIsNone(self.w.recorded_strategy(f.RICK))
        with self.assertRaises(ValueError):self.w.finish_strategy(job['jobID'],fallback(p),'mock',{})
        self.w.restore(after);self.assertEqual(self.w.recorded_strategy(f.RICK)['decision'],result)
        self.assertNotEqual(self.w.recorded_strategy(f.RICK)['currentContextID'],result['contextID'])
    def test_active_job_revoked_restore(self):
        p=self.packet();job=self.w.begin_strategy(f.RICK);self.w.restore(self.save)
        self.assertFalse(self.w.job_current(job['jobID']))
        with self.assertRaises(ValueError):self.w.finish_strategy(job['jobID'],fallback(p),'mock',{})
    def test_save_barrier(self):
        p=self.packet();job=self.w.begin_strategy(f.RICK);intent=self.w.begin_save(self.nonce,self.save)
        with self.assertRaises(ValueError):self.w.finish_strategy(job['jobID'],fallback(p),'mock',{})
        self.w.abandon_save(intent)
    def test_old_writer_refused(self):
        with self.assertRaises(ValueError):PrepStore(self.path,f.BUILD,f.TAG)
    def test_regrant_same_semantic_job_preserves_attempts(self):
        self.packet();job=self.w.begin_strategy(f.RICK);self.w.count_attempt(job['jobID'],job['packet']['contextID']);self.checkpoint(True);self.w.restore(self.save)
        resumed=self.w.begin_strategy(f.RICK);self.assertEqual(resumed['jobID'],job['jobID']);self.assertNotEqual(resumed['packet']['contextID'],job['packet']['contextID'])
        self.assertEqual(self.w._one('SELECT attempts FROM strategy_jobs WHERE id=?',(job['jobID'],))['attempts'],1)
        with self.assertRaises(ValueError):self.w.finish_strategy(job['jobID'],fallback(job['packet']),'mock',{},job['packet']['contextID'])
        self.w.finish_strategy(resumed['jobID'],fallback(resumed['packet']),'mock',{},resumed['packet']['contextID'])
    def test_new_branch_does_not_inherit_future_posture(self):
        p=self.packet();before=self.save;job=self.w.begin_strategy(f.RICK);result=run_job(self.w,job,FixtureProvider(fallback(p)));self.w.restore(before)
        future=self.w.begin_strategy(f.RICK);self.assertNotEqual(future['jobID'],job['jobID']);self.assertNotEqual(future['packet']['scope']['branch'],result['scope']['branch'])
        self.assertEqual(self.w.strategy_state()['postures'],{})
    def test_budget_exhausted_restart_falls_back_without_provider(self):
        self.packet();job=self.w.begin_strategy(f.RICK)
        for _ in range(3):self.w.count_attempt(job['jobID'],job['packet']['contextID'])
        provider=FixtureProvider(error='unreachable');result=run_job(self.w,job,provider);self.assertEqual(provider.calls,0);self.assertEqual(result['source'],'fallback')
    def test_budget_persistent_per_job_and_global_closed(self):
        path=Path(self.tmp.name)/'budget.json'
        with LiveBudget(path) as budget:
            for _ in range(3):budget.charge('a','free')
            with self.assertRaises(ProviderError):budget.charge('a','free')
        with LiveBudget(path) as budget:
            for i in range(7):budget.charge(str(i),'free')
            with self.assertRaises(ProviderError):budget.charge('last','free')
            budget.close()
        with LiveBudget(path) as budget:
            with self.assertRaises(ProviderError):budget.charge('new','free')
    def test_route_requires_zero_price_tools_and_availability(self):
        row={'id':'test:free','pricing':{'prompt':'0','completion':'0'},'supported_parameters':['tools','tool_choice','max_tokens']}
        endpoint={'model_id':'test:free','provider_name':'Test','pricing':row['pricing'],'supported_parameters':row['supported_parameters'],'supports_tool_choice':{'function':True},'status':0,'uptime_last_5m':100}
        cat={'data':[row]};ends={'data':{'endpoints':[endpoint]}};qualify_route('test:free',cat,ends)
        for key,value in [('status',-2),('pricing',{'prompt':'1','completion':'0'}),('supports_tool_choice',{'function':False}),('supported_parameters',[])]:
            modified=copy.deepcopy(ends);modified['data']['endpoints'][0][key]=value
            with self.assertRaises(ProviderError):qualify_route('test:free',cat,modified)
    def test_deadline_prevents_attempt(self):
        self.packet();job=self.w.begin_strategy(f.RICK);provider=FixtureProvider(error='bad');r=run_job(self.w,job,provider,limits=Limits(job_seconds=1));self.assertEqual(provider.calls,0);self.assertEqual(r['source'],'fallback')

    def test_upstream_backoff_stops_after_three_unchanged_requests(self):
        from unittest.mock import patch
        self.packet();job=self.w.begin_strategy(f.RICK);provider=FixtureProvider(error='provider_error_502')
        with patch('strategy.runtime.time.sleep') as sleep:r=run_job(self.w,job,provider)
        self.assertEqual(provider.calls,3);self.assertEqual([c.args[0] for c in sleep.call_args_list],[5,10]);self.assertEqual(r['source'],'fallback');self.assertEqual(r['diagnostics']['backoffSeconds'],[5,10])

    def test_client_and_rate_errors_stop_without_rapid_retry(self):
        from unittest.mock import patch
        self.packet()
        for code in ('http_400','provider_error_429'):
            job=self.w.begin_strategy(f.RICK,provider_binding={'provider':'fixture','model':code+':free','adapterVersion':1});provider=FixtureProvider(error=code)
            with patch('strategy.runtime.time.sleep') as sleep:r=run_job(self.w,job,provider)
            self.assertEqual(provider.calls,1);sleep.assert_not_called();self.assertEqual(r['source'],'fallback');self.assertEqual(r['diagnostics']['failures'],[code])
