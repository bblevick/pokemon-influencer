"""Pure production policy resolution. No world connection, grant issuer or writer.

TrustedState must be assembled by the future active WORLD/PREP adapter, not
from model prose or player/NPC submissions. Schema/hash checks do not authenticate
it. Scenarios exercise this contract without claiming a live progression hook.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, replace, asdict
from pathlib import Path
import json
from jsonschema import Draft202012Validator
from .adaptation import AdaptationRules
from roster.domain import Catalog, Context, Scope, Step
from roster.extract import digest, file_hash

ROOT = Path(__file__).resolve().parents[1]
STATUSES = ('permitted', 'prohibited_by_policy', 'unsupported_implementation', 'missing_trusted_state')

@dataclass(frozen=True)
class ProgressionEvidence:
    scope: Scope
    rom_sha256: str
    source_commit: str
    flags: tuple[tuple[str, bool], ...]
    evidence_refs: tuple[str, ...]
    paired_checkpoint: str
    activation: str

@dataclass(frozen=True)
class TrustedState:
    context: Context
    progression: ProgressionEvidence | None
    defeated_actors: frozenset[str] | None
    consumed_opportunities: frozenset[str] | None
    inventory_initialized: bool
    travel_grants: frozenset[str] = frozenset()

class OpeningContent:
    def __init__(self, pack, catalog, basis_policy, registry):
        self.pack = deepcopy(pack)
        self.data = deepcopy(catalog)
        self.basis = deepcopy(basis_policy)
        self.registry = deepcopy(registry)
        self.hash = digest(self.pack)
        self.cat = Catalog(catalog, basis_policy)
        self.adaptation = AdaptationRules.load()
        self.validate()

    @classmethod
    def load(cls, root=ROOT):
        read = lambda p: json.loads((root / p).read_text())
        return cls(read('config/opening_content.json'), read('config/roster_catalog.json'),
                   read('config/roster_policy.json'), read('config/trainer_registry.json'))

    def validate(self):
        schema = json.loads((ROOT / 'schemas/content/pack.schema.json').read_text())
        Draft202012Validator(schema).validate(self.pack)
        p = self.pack
        if p['catalogSHA256'] != self.cat.hash or p['sourceCommit'] != self.data['sourceCommit']:
            raise ValueError('incompatible catalog/source')
        if p['registrySHA256'] != file_hash(ROOT / 'config/trainer_registry.json') or self.registry != json.loads((ROOT / 'config/trainer_registry.json').read_text()):
            raise ValueError('incompatible registry')
        if p['basisPolicySHA256'] != digest(self.basis):
            raise ValueError('incompatible inherited restraint policy')
        required_sources = {'include/constants/flags.h','data/maps/PewterCity_Gym/scripts.inc','data/maps/ViridianForest/scripts.inc','data/scripts/trainers.inc','src/vs_seeker.c'}
        if set(p['sourceEvidence']) != required_sources:
            raise ValueError('missing/unqualified source evidence')
        if any(file_hash(ROOT / path) != sha for path, sha in p['sourceEvidence'].items()):
            raise ValueError('stale progression/map source evidence')
        if p['milestone']['flags'] != {'FLAG_DEFEATED_BROCK': 0x4B0, 'FLAG_BADGE01_GET': 0x820}:
            raise ValueError('wrong pinned Boulder identities')
        if p['adaptationRulesSHA256'] != self.adaptation.hash:
            raise ValueError('incompatible shared adaptation rules')
        d = p['defaults']
        if d['levelGainPerOpportunity'] != self.basis['adaptation']['max_level_gain_per_earned_epoch_per_pokemon']:
            raise ValueError('unapproved restraint change')
        if d['catchBudget'] or d['activeAdditions'] or d['reserveAdditions'] or d['replacements'] or d['restock']:
            raise ValueError('opening slice cannot create ownership/resources')
        for actor, t in p['trainers'].items():
            native = self.cat.own_baseline(actor, t['sourceTrainer'])
            if t['qualifiedVariant'] != t['sourceTrainer'] or t['originals'] != native['party']:
                raise ValueError('source baseline mismatch')
            registry = self.registry['trainers'][t['worldTrainerID']]
            if t['sourceVariants'] != [r['sourceID'] for r in registry['sourceRecords']] or native['worldTrainerID'] != t['worldTrainerID']:
                raise ValueError('identity/variant mismatch')
            expected_map_evidence = registry['mapReferences'] or ['src/vs_seeker.c:Janice MAP_ROUTE3','data/scripts/trainers.inc:Route3_EventScript_Janice']
            if t['mapEvidence'] != expected_map_evidence:
                raise ValueError('map reference provenance mismatch')
            if t['sourceTrainer'] != 414 and t['signatureOrigins']:
                raise ValueError('no ordinary signature invented in this pack')
            origins = {row['baselineKey']: row for row in native['party']}
            if set(t['retainedOrigins']) != set(origins) or not set(t['signatureOrigins']) <= set(origins):
                raise ValueError('retention/signature mismatch')
            if t['resources']['owner'] != actor or t['resources']['initialBattleItems'] != native['battleItems'] or t['resources']['initialHeldItems'] != {key: row['heldItem'] for key, row in origins.items()}:
                raise ValueError('source resource mismatch')
            if any(native['battleItems']) or any(row['heldItem'] for row in native['party']) or t['resources']['initialStock'] or any(row['quantity'] for row in t['resources']['categories']):
                raise ValueError('unapproved opening resource grant')
            expected_home = {102:'MAP_VIRIDIAN_FOREST',103:'MAP_VIRIDIAN_FOREST',116:'MAP_ROUTE3',414:'MAP_PEWTER_CITY_GYM'}[t['sourceTrainer']]
            expected_regions = {expected_home, 'MAP_ROUTE2'} if t['sourceTrainer'] in (102,103) else {expected_home}
            if t['homeMap'] != expected_home or set(t['regions']) != expected_regions:
                raise ValueError('unapproved territory expansion')
            if len(set(row['category'] for row in t['resources']['categories'])) != 7:
                raise ValueError('missing/duplicate resource category')
            if t['homeMap'] not in t['regions'] or t['regions'][t['homeMap']]['tier'] != 'native':
                raise ValueError('missing home territory')
            for region, binding in t['regions'].items():
                if binding != ({'tier':'native','requires':[]} if region == expected_home else {'tier':'nearby','requires':['travel.forest.route2']}):
                    raise ValueError('unapproved region access predicate')
                if binding['tier'] == 'nearby' and not binding['requires']:
                    raise ValueError('nearby is not unconditional travel permission')
            expected_stages = {'first','forest-post-boulder-1'} if t['sourceTrainer'] in (102,103) else {'first'}
            if set(t['stages']) != expected_stages:
                raise ValueError('unsupported stage expansion')
            for stage, s in t['stages'].items():
                expected_predicate = ('own_prior_defeat_and_boulder_and_unconsumed' if stage != 'first' else {102:'not_previously_defeated',103:'not_previously_defeated',116:'boulder_required',414:'boulder_absent'}[t['sourceTrainer']])
                expected_ceiling = 14 if stage != 'first' or t['sourceTrainer'] in (116,414) else max(row['level'] for row in origins.values())
                if s['stageCeiling'] != expected_ceiling:
                    raise ValueError('unapproved opening stage ceiling')
                if s['predicate'] != expected_predicate:
                    raise ValueError('incorrect progression eligibility')
                expected_gain = d['levelGainPerOpportunity'] if stage == 'forest-post-boulder-1' else 0
                if s['gain'] != expected_gain or set(s['targets']) != set(origins):
                    raise ValueError('missing/stacked training target')
                if any(target != origins[key]['level'] + expected_gain or target > s['stageCeiling'] for key,target in s['targets'].items()):
                    raise ValueError('target disagrees with baseline/epoch/ceiling')
            theme = t['theme']
            if theme:
                for species in theme['supportSpecies']: self.cat.lookup('species',species)
                if not set(theme['coreOrigins']) <= set(origins) or theme['minimumCore'] > len(theme['coreOrigins']) or theme['maximumSupport'] > theme['maximumActive'] - theme['minimumCore']:
                    raise ValueError('inconsistent Gym core/support bounds')
                if theme['primaryType'] not in self.cat.lookup('species',origins['414:1']['species'])['types']:
                    raise ValueError('signature theme mismatch')
                if t['signatureOrigins'] != ['414:1'] or set(theme['coreOrigins']) != {'414:0','414:1'} or theme['primaryType'] != 5 or theme['minimumCore'] != 2 or theme['supportLevelCap'] != 14 or theme['maximumActive'] != 2 or theme['maximumSupport'] != 0 or theme['supportSpecies'] or theme['supportAcquisition']:
                    raise ValueError('opening Brock bounds require separate approval to expand')
            elif t['sourceTrainer'] == 414: raise ValueError('missing Gym bounds')

    def _packet(self, status, code, state, stage, **extra):
        return {'schemaVersion':1, 'status':status, 'reason':code,
                'scope':asdict(state.context.scope), 'stage':stage,
                'packID':self.pack['packID'], 'packVersion':self.pack['version'],
                'packSHA256':self.hash, 'catalogSHA256':self.cat.hash,
                'scenario':state.context.fixture, 'fully_legal':False, **extra}

    def opportunity_id(self, scope, stage):
        # Trigger order/evidence receipt IDs do not create extra opportunities.
        # Branch/restore/activation changes invalidate capability, not logical
        # opportunity identity. Branch-scoped consumption receipts inherited at a
        # fork therefore cannot grant this first opportunity twice.
        return 'opening:' + digest({'campaign':scope.campaign,'actor':scope.actor,'stage':stage})

    def resolve(self, state: TrustedState, stage='first', variant=None):
        ctx = state.context
        self.cat.bind(ctx)  # validate actual supplied individual/history/resource snapshot
        actor = ctx.scope.actor
        t = self.pack['trainers'].get(actor)
        result = lambda status, reason, **kw: self._packet(status, reason, state, stage, **kw)
        if t is None or stage not in t['stages']:
            return result('unsupported_implementation','outside_qualified_opening_slice',fallback='authored-baseline')
        if variant is not None and variant != t['qualifiedVariant']:
            return result('unsupported_implementation','source_variant_not_qualified',fallback='authored-baseline')
        if not state.inventory_initialized or state.defeated_actors is None or state.consumed_opportunities is None:
            return result('missing_trusted_state','active_ownership_inventory_defeat_opportunity_state_required')
        origins = {c.origin:c for c in ctx.companions if c.origin_kind == 'baseline'}
        if len(ctx.companions) != len(t['originals']) or set(origins) != set(t['retainedOrigins']):
            return result('prohibited_by_policy','all_original_individuals_required_no_additions')
        if any(c.held_item for c in ctx.companions):
            return result('prohibited_by_policy','no_opening_held_item_entitlement')
        if stage == 'first' and any(c.level != row['level'] or c.species != row['species'] for row in t['originals'] for c in ctx.companions if c.origin == row['baselineKey']):
            return result('prohibited_by_policy','first_levels_and_companions_are_source_fixed')
        # Validate Gym current species independently from acquisition permission.
        if t['theme']:
            theme = t['theme']
            core = sum(theme['primaryType'] in self.cat.lookup('species',c.species)['types'] for c in ctx.companions if c.origin in theme['coreOrigins'])
            support = sum(theme['primaryType'] not in self.cat.lookup('species',c.species)['types'] for c in ctx.companions)
            if core < theme['minimumCore'] or support > theme['maximumSupport']:
                return result('prohibited_by_policy','gym_core_or_support_limit')
        e = state.progression
        required_flags = self.pack['milestone']['flags']
        if e is None:
            return result('missing_trusted_state','trusted_boulder_flag_snapshot_required',requiredFlags=required_flags)
        if (e.scope != ctx.scope or e.rom_sha256 != self.pack['romSHA256'] or e.source_commit != self.pack['sourceCommit'] or not e.paired_checkpoint or not e.activation or not e.evidence_refs):
            return result('missing_trusted_state','stale_or_unpaired_progression_evidence')
        flags = dict(e.flags)
        if len(flags) != len(e.flags) or any(type(v) is not bool for v in flags.values()) or set(flags) != set(required_flags):
            return result('missing_trusted_state','exact_native_flag_values_required')
        if len(set(flags.values())) != 1:
            return result('missing_trusted_state','inconsistent_native_boulder_flags')
        boulder = all(flags.values())
        rule = t['stages'][stage]
        predicate = rule['predicate']
        if stage == 'first' and actor in state.defeated_actors:
            return result('prohibited_by_policy','first_encounter_already_defeated')
        if predicate == 'boulder_required' and not boulder:
            return result('prohibited_by_policy','boulder_required_for_janice_opening')
        if predicate == 'boulder_absent' and boulder:
            return result('unsupported_implementation','brock_later_encounter_not_qualified',fallback='authored-baseline')
        if stage != 'first' and (not boulder or actor not in state.defeated_actors):
            return result('prohibited_by_policy','prior_own_defeat_and_boulder_required')
        opportunity = self.opportunity_id(ctx.scope,stage)
        if opportunity in state.consumed_opportunities or opportunity in ctx.applied_epochs:
            return result('prohibited_by_policy','opportunity_already_consumed',opportunityID=opportunity)
        targets = {c.lineage:{'origin':c.origin,'originalLevel':next(p['level'] for p in t['originals'] if p['baselineKey']==c.origin),'target':rule['targets'][c.origin], 'stageCeiling':rule['stageCeiling'], 'current':c.level, 'maximum':max(c.level,min(rule['targets'][c.origin],rule['stageCeiling'],c.level+rule['gain']))} for c in ctx.companions}
        return result('permitted','concrete_opening_policy',opportunityID=opportunity,
            progression={'namedStage':'after-boulder' if boulder else 'before-boulder','milestoneID':self.pack['milestone']['id'],'flags':flags},
            activation=e.activation, checkpoint=e.paired_checkpoint,evidenceRefs=list(e.evidence_refs),
            levels=targets,retainedLineages=[origins[k].lineage for k in t['retainedOrigins']],
            signatureLineages=[origins[k].lineage for k in t['signatureOrigins']],theme=deepcopy(t['theme']),
            budgets=deepcopy(self.pack['defaults']),regions=deepcopy(t['regions']),
            startingResourceDefinition=deepcopy(t['resources']),currentInventory=[list(x) for x in ctx.inventory],
            earnedOpportunityAllowance=1 if rule['gain'] else 0,
            runtimeGates=['trusted paired native flag exporter','durable companion/resource/opportunity issuer',
                          'PREP aggregate envelope/candidates and one-time commit','safe encounter installation and actual consumption'])

    def roster_view(self, state, stage, lineage):
        """Internal PREP substrate adapter, fixed policy and one earned allowance.

        Single-lineage scalar target adapts existing ROSTER API without weakening
        its source queries. Complete candidates/aggregate validation still PREP.
        """
        resolved = self.resolve(state,stage)
        if resolved['status'] != 'permitted': raise ValueError(resolved['reason'])
        target = resolved['levels'][lineage]
        t = self.pack['trainers'][state.context.scope.actor]
        policy = deepcopy(self.basis)
        policy['version'] = self.pack['version']
        policy['contentPackSHA256'] = self.hash
        policy['adaptation']['max_move_slot_changes_per_opportunity'] = resolved['budgets']['aggregateMoveChanges']
        policy['actors'] = {state.context.scope.actor:{'sourceTrainer':t['sourceTrainer'],
            'regions':deepcopy(t['regions']), 'signatureLineages':resolved['signatureLineages'],
            'theme':None if not t['theme'] else {'primaryType':t['theme']['primaryType'],'mixedSupportLimit':t['theme']['maximumSupport']},
            'stages':[{'requires':[], 'target':target['target'], 'cap':target['stageCeiling']}]}}
        ctx = state.context
        epochs = (resolved['opportunityID'],) if resolved['earnedOpportunityAllowance'] else ()
        permissions = frozenset({'learn:level','evolve:level'}) if epochs else frozenset()
        adapted = replace(ctx,milestones=state.travel_grants,earned_epochs=epochs,
                          applied_epochs=(),permissions=permissions)
        return Catalog(self.data,policy).bind(adapted)

    def resource(self, state, stage, category, item, quantity=1):
        r = self.resolve(state,stage)
        if r['status'] != 'permitted': return r
        self.cat.lookup('items',item)
        if type(quantity) is not int or quantity <= 0:
            return self._packet('prohibited_by_policy','invalid_resource_quantity',state,stage)
        categories = {x['category']:x for x in r['startingResourceDefinition']['categories']}
        if category not in categories:
            return self._packet('unsupported_implementation','unknown_resource_category',state,stage)
        # All initial categories are explicitly zero. Positive trusted current stock
        # cannot create an unapproved teaching/evolution/bag entitlement.
        return self._packet('prohibited_by_policy','zero_opening_resource_entitlement',state,stage)

    def acquisition(self, state, stage, route_id):
        r = self.resolve(state,stage)
        if r['status'] != 'permitted': return r
        route = self.cat.routes.get(route_id)
        if route is None:
            return self._packet('prohibited_by_policy','unknown_or_other_version_route',state,stage)
        if route['map'] not in r['regions']:
            return self._packet('prohibited_by_policy','off_region_no_acquisition_grant',state,stage)
        if route['method'] not in r['budgets']['methods']:
            return self._packet('unsupported_implementation','unsupported_acquisition_method',state,stage)
        required = set(r['regions'][route['map']]['requires'])
        if not required <= state.travel_grants:
            return self._packet('missing_trusted_state','trainer_travel_grant_required',state,stage)
        shared = self.adaptation.resolve(self.cat,state.context,self.adaptation_profile(state,stage),grants=state.travel_grants)
        if shared['reason'] == 'zero_opportunity_acquisition_allowance':
            return self._packet('prohibited_by_policy','zero_first_opportunity_catch_budget',state,stage)
        return self._packet(shared['status'],shared['reason'],state,stage)

    def adaptation_profile(self, state, stage):
        """Opening override of the shared configurable policy contract.

        Later qualified content can use AdaptationRules with another versioned
        profile; this opening loader never activates those profiles.
        """
        r = self.resolve(state,stage)
        if r['status'] != 'permitted': raise ValueError(r['reason'])
        return {'version':self.pack['version'],'actor':state.context.scope.actor,
            'stage':stage,'qualified':True,'scenarioOnly':False,'opportunityOrdinal':1,
            'aggregateMoveChanges':r['budgets']['aggregateMoveChanges'],
            'acquisitionLimit':r['budgets']['catchBudget'],'partyLimit':len(r['retainedLineages']),
            'originalLineages':r['retainedLineages'],'signatureLineages':r['signatureLineages'],
            'originWeights':deepcopy(self.adaptation.rules['originWeights']),
            'requires':[], 'regions':{key:{**value,'acquisitionPermission':''} for key,value in r['regions'].items()},
            'allowedSpecies':[], 'methods':r['budgets']['methods'],
            'acquisitionLevelCap':max(x['stageCeiling'] for x in r['levels'].values()),
            'captureItem':self.cat.constants['ITEM_POKE_BALL'],'captureCostPerAttempt':1,
            'balance':{'acquisitionProbability':None,'minimumOpportunitySpacing':None,'campaignAcquisitionCap':None}}

    def development(self, state, stage, paths):
        """Check hypothetical sequential level/evolution/learning paths only.

        Not a full candidate validator: no party/order/item installation or spend.
        Skipping elective native learning is permitted. Each new learned slot,
        including at evolution, costs one aggregate change; changes never reset
        between intermediate species. Models do not get Context/Step constructors.
        """
        r = self.resolve(state,stage)
        if r['status'] != 'permitted': return r
        changed = 0
        current = state
        base_views = {lineage:self.roster_view(state,stage,lineage) for lineage in paths if lineage in r['levels']}
        for lineage, steps in paths.items():
            if lineage not in r['levels']: return self._packet('prohibited_by_policy','unowned_lineage',state,stage)
            for step in steps:
                base_view = base_views[lineage]
                view = base_view.cat.bind(replace(base_view.ctx,companions=current.context.companions))
                c = view.owned[lineage]
                if step.kind == 'level': proof = view.growth(lineage,step.level) if step.species == c.species else None
                elif step.kind == 'evolution':
                    proof = view.evolution(lineage,step.species,level=c.level)
                    # Existing ROSTER future evolution expects a NEW leveling trigger;
                    # replay query from the previous individual just before that step.
                    original = next(x for x in state.context.companions if x.lineage==lineage)
                    if step.level == c.level and len(c.history)>len(original.history) and c.history[-1].kind == 'level':
                        previous = c.history[-1]
                        old_level = c.origin_level
                        for h in c.history[:-1]:
                            if h.kind == 'level': old_level = h.level
                        before = replace(c,level=old_level,history=c.history[:-1])
                        before_ctx = replace(current.context,companions=tuple(before if x.lineage==lineage else x for x in current.context.companions))
                        proof = base_view.cat.bind(replace(base_view.ctx,companions=before_ctx.companions)).evolution(lineage,step.species,level=previous.level)
                    else: proof = None
                elif step.kind == 'level_move':
                    changed += 1
                    if changed > r['budgets']['aggregateMoveChanges']:
                        return self._packet('prohibited_by_policy','aggregate_move_change_limit',state,stage)
                    valid = (step.species == c.species and step.level == c.level and 0<=step.slot<4 and step.value not in c.moves and [step.level,step.value] in view.cat.lookup('species',c.species)['learnset'])
                    # Learning must follow an actual growth trigger in this proposed path;
                    # no free replay of an existing old history or current level.
                    original = next(x for x in state.context.companions if x.lineage==lineage)
                    valid = valid and len(c.history)>len(original.history) and step.level > original.level and r['earnedOpportunityAllowance'] == 1
                    proof = view.result('allowed' if valid else 'blocked','exact_growth_learning_path' if valid else 'not_new_level_move')
                else: proof = None
                if proof is None or proof.status != 'allowed':
                    return self._packet('prohibited_by_policy','unsupported_or_infeasible_development_path',state,stage,element=None if proof is None else proof.packet())
                moves = list(c.moves)
                if step.kind == 'level_move': moves[step.slot] = step.value
                updated = replace(c,species=step.species,level=step.level,moves=tuple(moves),history=c.history+(step,))
                next_ctx = replace(current.context,companions=tuple(updated if x.lineage==lineage else x for x in current.context.companions))
                current = replace(current,context=next_ctx)
                self.cat.bind(next_ctx)  # narrow mechanical history replay
        return self._packet('permitted','partial_development_feasibility',state,stage,moveChanges=changed,notSelected=True)
