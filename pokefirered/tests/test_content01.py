import copy
import json
import unittest
from dataclasses import replace
from pathlib import Path
from jsonschema import Draft202012Validator, ValidationError
from content.policy import OpeningContent, TrustedState, ProgressionEvidence, ROOT
from roster.domain import Context, Scope, Step, Companion
from roster.fixtures import baseline
from roster.extract import digest, initial_moves

class ContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = OpeningContent.load()
        cls.schema = json.loads((ROOT/'schemas/content/resolved.schema.json').read_text())

    def state(self, number=102, boulder=True, defeated=True, **kw):
        actor = f'trainer:fr:trainer:{number:04d}'
        scope = Scope('scenario-campaign','scenario-branch',actor,2,9)
        ctx = Context(scope,baseline(self.content.cat,actor,number),frozenset(),(),(),(),frozenset(),0,0,None,True)
        e = ProgressionEvidence(scope,self.content.pack['romSHA256'],self.content.pack['sourceCommit'],
            (('FLAG_DEFEATED_BROCK',boulder),('FLAG_BADGE01_GET',boulder)),
            ('scenario:paired-native-flags',),'scenario:checkpoint','scenario:activation')
        s = TrustedState(ctx,e,frozenset([actor]) if defeated else frozenset(),frozenset(),True)
        return replace(s,**kw)

    def resolve(self,s,stage='forest-post-boulder-1',**kw):
        r = self.content.resolve(s,stage,**kw)
        Draft202012Validator(self.schema).validate(r)
        return r

    def alter(self, change):
        pack=copy.deepcopy(self.content.pack);change(pack)
        return OpeningContent(pack,self.content.data,self.content.basis,self.content.registry)

    def test_all_qualified_stages(self):
        for n,stages in [(102,['first','forest-post-boulder-1']),(103,['first','forest-post-boulder-1']),(116,['first']),(414,['first'])]:
            for stage in stages:
                state=self.state(n,boulder=n!=414,defeated=stage!='first')
                r=self.resolve(state,stage)
                self.assertEqual(r['status'],'permitted');self.assertFalse(r['fully_legal']);self.assertTrue(r['scenario'])
                self.assertEqual([x['target'] for x in r['levels'].values()], [p['level']+(4 if stage!='first' else 0) for p in self.content.pack['trainers'][state.context.scope.actor]['originals']])
                self.assertEqual(r['budgets']['catchBudget'],0)

    def test_zero_not_missing(self):
        r=self.resolve(self.state());self.assertEqual(r['status'],'permitted')
        self.assertTrue(all(x['quantity']==0 for x in r['startingResourceDefinition']['categories']))
        self.assertEqual(self.resolve(self.state(inventory_initialized=False))['status'],'missing_trusted_state')
        with self.assertRaises(ValidationError):self.alter(lambda p:p['defaults'].pop('tmhmStock'))

    def test_catalog_guard(self):
        with self.assertRaises(ValueError):self.alter(lambda p:p.update(catalogSHA256='0'*64))
        with self.assertRaises(ValueError):self.alter(lambda p:p.update(sourceCommit='0'*40))

    def test_variants(self):
        s=self.state(116,defeated=False)
        self.assertEqual(self.resolve(s,'first',variant=507)['status'],'unsupported_implementation')
        self.assertEqual(self.content.pack['trainers'][s.context.scope.actor]['sourceVariants'],[116,507,508])

    def test_missing_flags(self):
        s=self.state();self.assertEqual(self.resolve(replace(s,progression=None))['reason'],'trusted_boulder_flag_snapshot_required')
        e=replace(s.progression,flags=(('FLAG_BADGE01_GET',True),))
        self.assertEqual(self.resolve(replace(s,progression=e))['status'],'missing_trusted_state')

    def test_boulder_and_prior_win_gates(self):
        for n in [102,103]:
            self.assertEqual(self.resolve(self.state(n,boulder=False))['status'],'prohibited_by_policy')
            self.assertEqual(self.resolve(self.state(n,defeated=False))['status'],'prohibited_by_policy')
        self.assertEqual(self.resolve(self.state(116,boulder=False,defeated=False),'first')['status'],'prohibited_by_policy')
        self.assertEqual(self.resolve(self.state(414,defeated=False),'first')['status'],'unsupported_implementation')

    def test_consumed_and_no_stack(self):
        s=self.state();r=self.resolve(s);oid=r['opportunityID']
        self.assertEqual(self.resolve(replace(s,consumed_opportunities=frozenset([oid])))['reason'],'opportunity_already_consumed')
        ctx=replace(s.context,earned_epochs=('extra1','extra2','extra3','extra4'),permissions=frozenset(['learn:tm','capture:land']))
        rr=self.resolve(replace(s,context=ctx));self.assertEqual(r,rr)
        view=self.content.roster_view(replace(s,context=ctx),'forest-post-boulder-1',ctx.companions[0].lineage)
        self.assertEqual(view.growth(ctx.companions[0].lineage,11).status,'blocked')

    def test_order_duplicate_and_restart_identity(self):
        s=self.state();r=self.resolve(s)
        e=replace(s.progression,evidence_refs=('scenario:boulder-then-win','scenario:duplicate-win'))
        self.assertEqual(r['opportunityID'],self.resolve(replace(s,progression=e))['opportunityID'])
        ctx=replace(s.context,scope=replace(s.context.scope,restore_epoch=3))
        e=replace(e,scope=ctx.scope,activation='scenario:fresh-worker')
        self.assertEqual(r['opportunityID'],self.resolve(replace(s,context=ctx,progression=e))['opportunityID'])

    def test_earlier_restore_and_branch(self):
        s=self.state();early=self.state(boulder=False,defeated=False)
        self.assertNotEqual(self.resolve(early)['status'],'permitted')
        scope=replace(s.context.scope,branch='other-branch')
        stale=replace(s,context=replace(s.context,scope=scope))
        self.assertEqual(self.resolve(stale)['reason'],'stale_or_unpaired_progression_evidence')
        fork=replace(stale,progression=replace(s.progression,scope=scope))
        self.assertEqual(self.resolve(s)['opportunityID'],self.resolve(fork)['opportunityID'])
        consumed=replace(fork,consumed_opportunities=frozenset([self.resolve(s)['opportunityID']]))
        self.assertEqual(self.resolve(consumed)['reason'],'opportunity_already_consumed')

    def test_social_permissions_no_authority(self):
        s=self.state(boulder=False,defeated=False)
        s=replace(s,context=replace(s.context,milestones=frozenset(['badge.boulder','rick_won','post:brock_defeated'])))
        self.assertNotEqual(self.resolve(s)['status'],'permitted')
        s=self.state();r=self.resolve(s)
        s=replace(s,context=replace(s.context,permissions=frozenset(['learn:tm','evolve:item','capture:land']),milestones=frozenset(['post:future'])))
        self.assertEqual(self.resolve(s),r)

    def test_first_levels_no_learning_growth_grant(self):
        for n in [102,103,116,414]:
            s=self.state(n,boulder=n!=414,defeated=False);r=self.resolve(s,'first')
            for c in s.context.companions:
                view=self.content.roster_view(s,'first',c.lineage)
                self.assertEqual(view.growth(c.lineage,c.level+1).status,'blocked')
                self.assertEqual(r['levels'][c.lineage]['target'],c.origin_level)

    def test_source_baselines_identity_inventory(self):
        for n in [102,103,116,414]:
            s=self.state(n,boulder=n!=414,defeated=False);r=self.resolve(s,'first')
            self.assertEqual(len(r['retainedLineages']),len(s.context.companions))
            self.assertEqual(r['startingResourceDefinition']['initialBattleItems'],[0]*4)
            self.assertTrue(all(c.held_item==0 for c in s.context.companions))
        s=self.state(414,boulder=False,defeated=False)
        self.assertEqual(self.resolve(s,'first')['signatureLineages'],[s.context.companions[1].lineage])

    def test_identity_retention_and_duplicate_origins(self):
        s=self.state();ctx=replace(s.context,companions=s.context.companions[:1])
        self.assertEqual(self.resolve(replace(s,context=ctx))['reason'],'all_original_individuals_required_no_additions')
        copied=replace(s.context.companions[0],lineage='fake-copy')
        ctx=replace(s.context,companions=s.context.companions+(copied,))
        self.assertEqual(self.resolve(replace(s,context=ctx))['status'],'prohibited_by_policy')

    def test_targets_and_no_delevel(self):
        s=self.state();c=s.context.companions[0]
        c=replace(c,level=12,history=(Step('level',c.species,12),))
        ctx=replace(s.context,companions=(c,s.context.companions[1]))
        r=self.resolve(replace(s,context=ctx));self.assertEqual(r['levels'][c.lineage]['maximum'],12)
        v=self.content.roster_view(replace(s,context=ctx),'forest-post-boulder-1',c.lineage)
        self.assertEqual(v.growth(c.lineage,12).status,'allowed');self.assertEqual(v.growth(c.lineage,13).status,'blocked')

    def test_local_routes_no_catch(self):
        s=self.state();land=next(x for x in self.content.data['encounters'] if x['map']=='MAP_VIRIDIAN_FOREST')
        self.assertEqual(self.content.acquisition(s,'forest-post-boulder-1',land['routeID'])['reason'],'zero_first_opportunity_catch_budget')
        near=next(x for x in self.content.data['encounters'] if x['map']=='MAP_ROUTE2' and x['method']=='land_mons')
        self.assertEqual(self.content.acquisition(s,'forest-post-boulder-1',near['routeID'])['reason'],'trainer_travel_grant_required')
        granted=replace(s,travel_grants=frozenset(['travel.forest.route2']))
        self.assertEqual(self.content.acquisition(granted,'forest-post-boulder-1',near['routeID'])['reason'],'zero_first_opportunity_catch_budget')

    def test_offregion_and_version(self):
        s=self.state()
        for mapname in ['MAP_MT_MOON_1F','MAP_DIGLETTS_CAVE_B1F','MAP_SAFARI_ZONE_CENTER']:
            route=next((x for x in self.content.data['encounters'] if x['map']==mapname),None)
            self.assertIsNotNone(route)
            self.assertEqual(self.content.acquisition(s,'forest-post-boulder-1',route['routeID'])['reason'],'off_region_no_acquisition_grant')
        self.assertEqual(self.content.acquisition(s,'forest-post-boulder-1','sRoute2_LeafGreen:land_mons:0')['reason'],'unknown_or_other_version_route')

    def test_methods_no_permission_union(self):
        s=self.state()
        route=next(x for x in self.content.data['encounters'] if x['method']!='land_mons')
        self.assertNotEqual(self.content.acquisition(s,'forest-post-boulder-1',route['routeID'])['status'],'permitted')
        self.assertIn('trade',self.content.pack['defaults']['unsupportedMethods'])
        self.assertEqual(self.content.pack['defaults']['exceptionalMaps'],[])

    def test_finite_zero_resources_and_no_restock(self):
        s=self.state();item=self.content.cat.constants['ITEM_POTION']
        s=replace(s,context=replace(s.context,inventory=((item,2),),permissions=frozenset(['allocate:battle_bag'])))
        for category in ['battle_bag','teaching','held','evolution','capture','tutor_relearner','exceptional']:
            r=self.content.resource(s,'forest-post-boulder-1',category,item)
            self.assertEqual(r['status'],'prohibited_by_policy')
        self.assertFalse(self.resolve(s)['budgets']['restock'])
        self.assertEqual(s.context.inventory,((item,2),))

    def test_retained_tm_not_teaching_inventory(self):
        s=self.state(414,boulder=False,defeated=False);c=s.context.companions[1]
        v=self.content.roster_view(s,'first',c.lineage)
        self.assertEqual(v.move(c.lineage,317).status,'allowed')
        self.assertEqual(self.content.resource(s,'first','teaching',self.content.cat.constants['ITEM_TM39'])['status'],'prohibited_by_policy')
        self.assertFalse(s.context.inventory)

    def test_production_roster_consumer(self):
        s=self.state();c=s.context.companions[0];v=self.content.roster_view(s,'forest-post-boulder-1',c.lineage)
        self.assertEqual(v.growth(c.lineage,10).status,'allowed')
        self.assertEqual(v.growth(c.lineage,11).status,'blocked')
        self.assertEqual(v.evolution(c.lineage,14,level=7).status,'allowed')
        self.assertFalse(v.evolution(c.lineage,14,level=7).fully_legal)
        self.assertEqual(v.move(c.lineage,106,'level_up',level=7).status,'blocked') # Weedle not Kakuna
        self.assertEqual(v.move(c.lineage,106,'relearner').status,'unqualified')

    def caterpie_path(self,c):
        return [Step('level',10,7),Step('evolution',11,7),Step('level',11,10),Step('evolution',12,10),Step('level_move',12,10,93,2)]

    def test_feasible_evolution_learning_not_selected(self):
        s=self.state();c=s.context.companions[1]
        result=self.content.development(s,'forest-post-boulder-1',{c.lineage:self.caterpie_path(c)})
        self.assertEqual(result['status'],'permitted');self.assertEqual(result['moveChanges'],1)
        self.assertTrue(result['notSelected']);self.assertEqual(s.context.companions[1].species,10)
        Draft202012Validator(self.schema).validate(result)

    def test_shared_two_move_budget_including_evolutions(self):
        s=self.state();a,b=s.context.companions
        weedle=[Step('level',13,7),Step('evolution',14,7),Step('level_move',14,7,106,2),Step('level',14,10),Step('evolution',15,10),Step('level_move',15,10,31,3)]
        # Two changes on Weedle alone permitted; third on Caterpie rejected.
        self.assertEqual(self.content.development(s,'forest-post-boulder-1',{a.lineage:weedle})['status'],'permitted')
        self.assertEqual(self.content.development(s,'forest-post-boulder-1',{a.lineage:weedle,b.lineage:self.caterpie_path(b)})['reason'],'aggregate_move_change_limit')

    def test_no_free_evolution_or_relearn(self):
        s=self.state();c=s.context.companions[1]
        self.assertEqual(self.content.development(s,'forest-post-boulder-1',{c.lineage:[Step('evolution',11,7)]})['status'],'prohibited_by_policy')
        path=self.caterpie_path(c)+[Step('level_move',12,10,33,0)]
        self.assertEqual(self.content.development(s,'forest-post-boulder-1',{c.lineage:path})['status'],'prohibited_by_policy')
        self.assertEqual(self.content.development(s,'forest-post-boulder-1',{c.lineage:[Step('level',10,11)]})['status'],'prohibited_by_policy')

    def test_gym_explicit_zero_and_future_support_fields(self):
        s=self.state(414,boulder=False,defeated=False);r=self.resolve(s,'first')
        self.assertEqual(r['theme']['maximumSupport'],0);self.assertEqual(r['theme']['maximumActive'],2)
        self.assertEqual(r['theme']['minimumCore'],2)
        schema=json.loads((ROOT/'schemas/content/pack.schema.json').read_text())
        prop=schema['properties']['trainers']['properties'][s.context.scope.actor]['properties']['theme']['anyOf'][0]['properties']['maximumSupport']
        self.assertNotIn('const',prop) # Schema supports explicitly approved future mixed-type bounds.
        with self.assertRaises(ValueError):self.alter(lambda p:p['trainers'][s.context.scope.actor]['theme'].update(maximumSupport=1))

    def test_brock_unapproved_support_is_rejected(self):
        state=self.state(414,boulder=False,defeated=False)
        route=next(x for x in self.content.data['encounters'] if x['map']=='MAP_ROUTE2' and x['species']==19 and x['method']=='land_mons')
        level=route['minLevel']
        moves=tuple(initial_moves(self.content.cat.lookup('species',19)['learnset'],level))
        support=Companion('scenario:unapproved-support',state.context.scope.actor,route['routeID'],'wild',level,19,level,moves)
        ctx=replace(state.context,companions=state.context.companions+(support,))
        self.assertEqual(self.resolve(replace(state,context=ctx),'first')['reason'],'all_original_individuals_required_no_additions')

    def test_crossfield_validation(self):
        actor=self.state().context.scope.actor
        changes=[lambda p:p['sourceEvidence'].clear(),lambda p:p['trainers'][actor]['stages']['forest-post-boulder-1']['targets'].update({'102:0':11}),lambda p:p['trainers'][actor]['stages']['first'].update(predicate='boulder_absent'),lambda p:p['trainers'][actor]['retainedOrigins'].pop(),lambda p:p['trainers'][actor]['regions'].update({'MAP_MT_MOON_1F':{'tier':'nearby','requires':[]}}),lambda p:p['trainers'][actor]['resources']['initialBattleItems'].__setitem__(0,13)]
        for change in changes:
            with self.assertRaises(ValueError):self.alter(change)

    def test_versions_and_purity(self):
        s=self.state();before=copy.deepcopy(s);r=self.resolve(s)
        p2=self.alter(lambda p:p.update(version=p['version']+1))
        self.assertNotEqual(r['packSHA256'],p2.resolve(s,'forest-post-boulder-1')['packSHA256'])
        for _ in range(3):self.assertEqual(r,self.resolve(s))
        self.assertEqual(s,before)
        self.assertEqual(self.content.pack['trainers'][s.context.scope.actor]['resources']['initialStock'],[])

    def test_scope_build_consistency(self):
        s=self.state()
        for field,value in [('rom_sha256','0'*64),('source_commit','0'*40),('paired_checkpoint',''),('activation',''),('evidence_refs',())]:
            self.assertEqual(self.resolve(replace(s,progression=replace(s.progression,**{field:value})))['status'],'missing_trusted_state')
        e=replace(s.progression,flags=(('FLAG_DEFEATED_BROCK',False),('FLAG_BADGE01_GET',True)))
        self.assertEqual(self.resolve(replace(s,progression=e))['reason'],'inconsistent_native_boulder_flags')

    def test_endgame_and_unconfigured_actor(self):
        self.assertEqual(self.resolve(self.state(),'cascade')['status'],'unsupported_implementation')
        actor='trainer:fr:trainer:0104';ctx=replace(self.state().context,scope=Scope('c','b',actor,0,0),companions=baseline(self.content.cat,actor,104))
        self.assertEqual(self.resolve(replace(self.state(),context=ctx),'first')['status'],'unsupported_implementation')

if __name__=='__main__':unittest.main()
