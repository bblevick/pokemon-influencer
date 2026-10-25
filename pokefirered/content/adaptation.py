"""Configurable pure policy prerequisites, not acquisition execution or selection.

Internal trusted host input. Scenario-only profiles cannot bind live Context.
No RNG draw, complete candidate generator, ledger writer or resource spender.
"""
from __future__ import annotations
import json
from copy import deepcopy
from pathlib import Path
from jsonschema import Draft202012Validator
from roster.extract import digest
ROOT=Path(__file__).resolve().parents[1]

class AdaptationRules:
    def __init__(self, rules):
        self.rules=deepcopy(rules)
        Draft202012Validator(json.loads((ROOT/'schemas/content/adaptation.schema.json').read_text())).validate(rules)
        if abs(sum(rules['originWeights'].values())-1)>1e-9:raise ValueError('origin weights must sum to one')
        self.hash=digest(rules)

    @classmethod
    def load(cls):return cls(json.loads((ROOT/'config/adaptation_rules.json').read_text()))

    def validate_profile(self, p):
        Draft202012Validator(json.loads((ROOT/'schemas/content/adaptation-profile.schema.json').read_text())).validate(p)
        if abs(sum(p['originWeights'].values())-1)>1e-9:raise ValueError('profile origin weights must sum to one')
        if p['partyLimit']>self.rules['enginePartyLimit']:raise ValueError('native active-party limit')
        if not set(p['signatureLineages'])<=set(p['originalLineages']):raise ValueError('signature must be original owned partner')
        if p['opportunityOrdinal']==1 and p['acquisitionLimit']!=self.rules['firstEarnedOpportunityAcquisitionLimit']:
            raise ValueError('first earned preparation has no catch')
        if p['acquisitionLimit'] and p['acquisitionLimit'] not in self.rules['laterOpportunityAllowanceChoices']:
            raise ValueError('unsupported acquisition allowance')

    def identity(self, profile, existing_lineages, proposed_lineages):
        self.validate_profile(profile)
        existing=set(existing_lineages);proposed=set(proposed_lineages)
        if len(proposed)!=len(proposed_lineages):return False
        return (set(profile['originalLineages'])<=existing and
                set(profile['originalLineages'])<=proposed and
                set(profile['signatureLineages'])<=proposed and
                existing<=proposed and len(proposed)<=profile['partyLimit'])

    def resolve(self, catalog, context, profile, *, acquired_this_opportunity=0,
                campaign_acquisitions=None, last_acquisition_ordinal=None, grants=frozenset()):
        """Return eligible source origin references and finite acquisition allowance.

        All profile/stage/current-state inputs are trusted adapter capabilities,
        not model submissions. Qualified scenario fixtures prove expressiveness
        only. Null balance entries mean unresolved, never unlimited/default25%.
        """
        self.validate_profile(profile)
        catalog.bind(context)
        catalog.lookup('items',profile['captureItem'])
        for species in profile['allowedSpecies']:catalog.lookup('species',species)
        known_maps={row['map'] for row in catalog.data['encounters']}
        if not set(profile['regions'])<=known_maps|{'MAP_PEWTER_CITY_GYM'}:raise ValueError('unknown acquisition territory')
        def result(status, reason, **fields):
            return {'status':status,'reason':reason,'fully_legal':False,
                    'rulesSHA256':self.hash,'balanceVersion':self.rules['balanceVersion'],
                    'profileSHA256':digest(profile),'scope':context.scope.__dict__,
                    'scenario':context.fixture,**fields}
        if profile['actor']!=context.scope.actor:raise ValueError('cross-actor adaptation profile')
        if profile['scenarioOnly'] and not context.fixture:raise ValueError('scenario profile cannot activate gameplay')
        if not profile['qualified']:return result('prohibited_by_policy','later_profile_inactive_unqualified')
        if not set(profile['requires'])<=context.milestones:return result('missing_trusted_state','named_stage_evidence_required')
        if not self.identity(profile,[c.lineage for c in context.companions],[c.lineage for c in context.companions]):
            return result('prohibited_by_policy','original_signature_or_capacity_constraint')
        limit=profile['acquisitionLimit']
        base={'aggregateMoveChanges':profile['aggregateMoveChanges'],'acquisitionLimit':limit,
              'remainingAllowance':0,'eligibleOrigins':{},'conditionalOriginWeights':{},
              'separatelyPermittedOrigins':{},'selectionImplemented':False,'keepExistingAllowed':True}
        if limit==0:return result('prohibited_by_policy','zero_opportunity_acquisition_allowance',**base)
        balance=profile['balance']
        if any(v is None for v in balance.values()):
            return result('missing_trusted_state','later_balance_unresolved',**base)
        if type(acquired_this_opportunity)!=int or acquired_this_opportunity<0:raise ValueError('invalid opportunity acquisition history')
        if campaign_acquisitions is None or type(campaign_acquisitions)!=int or campaign_acquisitions<0:
            return result('missing_trusted_state','campaign_acquisition_history_required',**base)
        if acquired_this_opportunity>campaign_acquisitions:raise ValueError('inconsistent acquisition counts')
        if campaign_acquisitions and (type(last_acquisition_ordinal)!=int or last_acquisition_ordinal<1):
            return result('missing_trusted_state','acquisition_spacing_history_required',**base)
        if last_acquisition_ordinal is not None and profile['opportunityOrdinal']-last_acquisition_ordinal<balance['minimumOpportunitySpacing']:
            return result('prohibited_by_policy','acquisition_spacing',**base)
        available=min(limit-acquired_this_opportunity,
                      balance['campaignAcquisitionCap']-campaign_acquisitions,
                      profile['partyLimit']-len(context.companions),
                      catalog.policy['adaptation']['engine_party_size_limit']-len(context.companions),
                      dict(context.inventory).get(profile['captureItem'],0)//profile['captureCostPerAttempt'])
        if balance['acquisitionProbability']==0 or available<=0:
            return result('prohibited_by_policy','finite_resource_capacity_or_balance_limit',**base)
        if 'capture:land' not in context.permissions:
            return result('prohibited_by_policy','capture_permission_required',**base)
        # Only the currently qualified mechanical method is land acquisition.
        # Further method solvers remain unsupported even if a profile names them.
        if profile['methods']!=['land_mons']:
            return result('unsupported_implementation','acquisition_method_solver_not_qualified',**base)
        catalog.lookup('items',profile['captureItem'])
        if profile['captureItem']!=catalog.constants['ITEM_POKE_BALL']:
            return result('unsupported_implementation','capture_equipment_solver_not_qualified',**base)
        pools={tier:[] for tier in ('native','nearby','accessible','exceptional')}
        for route in catalog.data['encounters']:
            region=profile['regions'].get(route['map'])
            if not region or route['method'] not in profile['methods']:continue
            if not set(region['requires'])<=grants:continue
            if region['tier'] in ('accessible','exceptional') and not region['acquisitionPermission']:continue
            if region['acquisitionPermission'] and region['acquisitionPermission'] not in grants:continue
            if route['minLevel']>profile['acquisitionLevelCap']:continue
            if profile['allowedSpecies'] and route['species'] not in profile['allowedSpecies']:continue
            pools[region['tier']].append({'routeID':route['routeID'],'map':route['map'],'species':route['species'],
                'levels':[route['minLevel'],min(route['maxLevel'],profile['acquisitionLevelCap'])]})
        ordinary={tier:pool for tier,pool in pools.items() if tier in profile['originWeights'] and pool and profile['originWeights'][tier]>0}
        total=sum(profile['originWeights'][tier] for tier in ordinary)
        weights={tier:profile['originWeights'][tier]/total for tier in ordinary} if total else {}
        base.update(remainingAllowance=max(0,available),eligibleOrigins=ordinary,
            conditionalOriginWeights=weights,separatelyPermittedOrigins={tier:pools[tier] for tier in ('accessible','exceptional') if pools[tier]})
        if not ordinary and not base['separatelyPermittedOrigins']:
            base['remainingAllowance']=0
            return result('prohibited_by_policy','no_eligible_origin_no_access_widening',**base)
        return result('permitted','partial_acquisition_attempt_policy',**base,
            probability=balance['acquisitionProbability'],resourcesPerAttempt={str(profile['captureItem']):profile['captureCostPerAttempt']})
