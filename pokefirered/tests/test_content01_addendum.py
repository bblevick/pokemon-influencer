"""Later content expressiveness fixtures, not approved balance/live acquisitions."""
import unittest,copy,json
from dataclasses import replace
from content.policy import OpeningContent
from content.adaptation import AdaptationRules
from roster.domain import Step
from tools.content01 import scenario

class AdaptationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.opening=OpeningContent.load();cls.rules=cls.opening.adaptation

    def inputs(self, limit=1, **overrides):
        state=scenario(self.opening,102,'forest-post-boulder-1')
        ctx=replace(state.context,inventory=((4,3),),permissions=frozenset(['capture:land']),milestones=frozenset(['scenario:later-stage']))
        p=self.opening.adaptation_profile(state,'forest-post-boulder-1')
        # All later values here are expressly hypothetical. No production profile
        # or approved campaign probability/spacing/cap is created by this fixture.
        p.update(scenarioOnly=True,stage='scenario:later-stage',opportunityOrdinal=3,
                 acquisitionLimit=limit,partyLimit=6,acquisitionLevelCap=14,
                 requires=['scenario:later-stage'],balance={'acquisitionProbability':1.0,'minimumOpportunitySpacing':1,'campaignAcquisitionCap':10})
        p.update(overrides)
        return ctx,p

    def resolve(self,ctx,p,**kw):
        return self.rules.resolve(self.opening.cat,ctx,p,campaign_acquisitions=0,**kw)

    def test_opening_zero_and_later_one_two(self):
        state=scenario(self.opening,102,'forest-post-boulder-1')
        p=self.opening.adaptation_profile(state,'forest-post-boulder-1')
        r=self.rules.resolve(self.opening.cat,state.context,p)
        self.assertEqual(r['reason'],'zero_opportunity_acquisition_allowance')
        for limit in [1,2]:
            ctx,p=self.inputs(limit);r=self.resolve(ctx,p)
            self.assertEqual(r['status'],'permitted');self.assertEqual(r['remainingAllowance'],limit)
            self.assertTrue(r['keepExistingAllowed']);self.assertFalse(r['selectionImplemented']);self.assertFalse(r['fully_legal'])
        self.assertEqual(self.opening.pack['defaults']['catchBudget'],0)

    def test_first_ordinal_cannot_catch(self):
        ctx,p=self.inputs(opportunityOrdinal=1)
        with self.assertRaises(ValueError):self.resolve(ctx,p)

    def test_unqualified_later_stays_inactive(self):
        ctx,p=self.inputs(qualified=False)
        r=self.resolve(ctx,p);self.assertEqual(r['reason'],'later_profile_inactive_unqualified')
        self.assertNotEqual(r['status'],'unsupported_implementation')

    def test_no_inherited_old_balance_or_unlimited_growth(self):
        ctx,p=self.inputs();p['balance']={k:None for k in p['balance']}
        self.assertEqual(self.resolve(ctx,p)['reason'],'later_balance_unresolved')
        self.assertEqual({k:v['status'] for k,v in self.rules.rules['laterBalance'].items()},dict.fromkeys(p['balance'],'unresolved'))
        self.assertNotIn('capture_attempt_probability',p)

    def test_resources_and_capacity_bound_two_allowance(self):
        ctx,p=self.inputs(2)
        self.assertEqual(self.resolve(replace(ctx,inventory=((4,1),)),p)['remainingAllowance'],1)
        self.assertEqual(self.resolve(replace(ctx,inventory=()),p)['status'],'prohibited_by_policy')
        p['partyLimit']=3
        self.assertEqual(self.resolve(ctx,p)['remainingAllowance'],1)
        p['partyLimit']=2
        self.assertEqual(self.resolve(ctx,p)['status'],'prohibited_by_policy')
        self.assertEqual(ctx.inventory,((4,3),))

    def test_spacing_history_and_campaign_cap_are_explicit(self):
        ctx,p=self.inputs(2);p['balance']['minimumOpportunitySpacing']=2
        r=self.rules.resolve(self.opening.cat,ctx,p,campaign_acquisitions=1,last_acquisition_ordinal=2)
        self.assertEqual(r['reason'],'acquisition_spacing')
        self.assertEqual(self.rules.resolve(self.opening.cat,ctx,p,campaign_acquisitions=1)['reason'],'acquisition_spacing_history_required')
        p['balance']['campaignAcquisitionCap']=1
        r=self.rules.resolve(self.opening.cat,ctx,p,campaign_acquisitions=1,last_acquisition_ordinal=1)
        self.assertEqual(r['status'],'prohibited_by_policy')

    def test_habitat_stage_and_travel_filtering(self):
        ctx,p=self.inputs()
        no_stage=replace(ctx,milestones=frozenset())
        self.assertEqual(self.resolve(no_stage,p)['reason'],'named_stage_evidence_required')
        r=self.resolve(ctx,p)
        self.assertEqual(set(r['eligibleOrigins']),{'native'})
        self.assertEqual(r['conditionalOriginWeights'],{'native':1.0})
        self.assertTrue(all(x['map']=='MAP_VIRIDIAN_FOREST' for x in r['eligibleOrigins']['native']))
        r=self.resolve(ctx,p,grants=frozenset(['travel.forest.route2']))
        self.assertEqual(r['conditionalOriginWeights'],{'native':0.8,'nearby':0.2})
        self.assertTrue(all(x['map']=='MAP_ROUTE2' for x in r['eligibleOrigins']['nearby']))

    def test_accessible_and_exceptional_are_separate_grants(self):
        ctx,p=self.inputs()
        p['regions']['MAP_MT_MOON_1F']={'tier':'accessible','requires':['npc:travel:moon'],'acquisitionPermission':'npc:acquire:moon'}
        p['regions']['MAP_SAFARI_ZONE_CENTER']={'tier':'exceptional','requires':['npc:travel:safari'],'acquisitionPermission':'story:acquire:safari'}
        r=self.resolve(ctx,p);self.assertFalse(r['separatelyPermittedOrigins'])
        grants=frozenset(['npc:travel:moon','npc:acquire:moon','npc:travel:safari','story:acquire:safari'])
        p['acquisitionLevelCap']=40
        r=self.resolve(ctx,p,grants=grants)
        self.assertEqual(set(r['separatelyPermittedOrigins']),{'accessible','exceptional'})
        self.assertNotIn('accessible',r['conditionalOriginWeights'])
        self.assertNotIn('exceptional',r['eligibleOrigins'])
        self.assertTrue(all(x['map']=='MAP_MT_MOON_1F' for x in r['separatelyPermittedOrigins']['accessible']))

    def test_empty_pool_never_invents_or_widens(self):
        ctx,p=self.inputs(allowedSpecies=[7]) # Squirtle: no eligible source wild route.
        r=self.resolve(ctx,p,grants=frozenset(['travel.forest.route2']))
        self.assertEqual(r['reason'],'no_eligible_origin_no_access_widening');self.assertFalse(r['separatelyPermittedOrigins'])
        self.assertEqual(r['remainingAllowance'],0)

    def test_species_identity_permissions_and_levels(self):
        ctx,p=self.inputs(allowedSpecies=[10],acquisitionLevelCap=2)
        self.assertEqual(self.resolve(ctx,p)['status'],'prohibited_by_policy')
        p['acquisitionLevelCap']=14;r=self.resolve(ctx,p)
        self.assertEqual({x['species'] for pool in r['eligibleOrigins'].values() for x in pool},{10})
        self.assertEqual(self.resolve(replace(ctx,permissions=frozenset()),p)['reason'],'capture_permission_required')
        lineages=[c.lineage for c in ctx.companions]
        p['signatureLineages']=[lineages[1]]
        self.assertFalse(self.rules.identity(p,lineages,[lineages[0],'new']))
        self.assertTrue(self.rules.identity(p,lineages,lineages+['new']))
        self.assertFalse(self.rules.identity(p,lineages,lineages+['new']*2))

    def test_evolution_preserves_original_lineage(self):
        ctx,p=self.inputs();c=ctx.companions[0]
        evolved=replace(c,species=14,level=7,history=(Step('level',13,7),Step('evolution',14,7)))
        ctx=replace(ctx,companions=(evolved,ctx.companions[1]))
        self.assertEqual(self.resolve(ctx,p)['status'],'permitted')
        self.assertEqual(evolved.lineage,c.lineage)

    def test_configurable_move_limits_and_weighting(self):
        ctx,p=self.inputs(aggregateMoveChanges=3,originWeights={'native':0.7,'nearby':0.3})
        r=self.resolve(ctx,p,grants=frozenset(['travel.forest.route2']))
        self.assertEqual(r['aggregateMoveChanges'],3)
        self.assertEqual(r['conditionalOriginWeights'],{'native':0.7,'nearby':0.3})
        state=scenario(self.opening,102,'forest-post-boulder-1')
        pack=copy.deepcopy(self.opening.pack);pack['version']+=1;pack['defaults']['aggregateMoveChanges']=3
        tuned=OpeningContent(pack,self.opening.data,self.opening.basis,self.opening.registry)
        self.assertEqual(tuned.resolve(state,'forest-post-boulder-1')['budgets']['aggregateMoveChanges'],3)
        self.assertEqual(self.opening.resolve(state,'forest-post-boulder-1')['budgets']['aggregateMoveChanges'],2)

    def test_fixture_profile_cannot_activate_live_state(self):
        ctx,p=self.inputs()
        with self.assertRaises(ValueError):self.resolve(replace(ctx,fixture=False),p)

    def test_versions_purity_and_locked_history_inputs(self):
        ctx,p=self.inputs();before=copy.deepcopy((ctx,p))
        old=self.resolve(ctx,p)
        p2=copy.deepcopy(p);p2['version']+=1;p2['acquisitionLimit']=2
        new=self.resolve(ctx,p2)
        self.assertNotEqual(old['profileSHA256'],new['profileSHA256'])
        self.assertEqual((ctx,p),before);self.assertEqual(old,self.resolve(ctx,p))
        self.assertEqual(self.rules.rules['updatesApplyTo'],'future uncommitted opportunities only')

if __name__=='__main__':unittest.main()
