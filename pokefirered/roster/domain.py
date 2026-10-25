"""Pure internal queries. Only a trusted world adapter supplies Context/history.

Model-facing callers get a bound View and lookup IDs, never constructors or
inventory/history writers. This ticket has no world adapter or persistence.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from collections import Counter
import json
from copy import deepcopy
from typing import Literal
from .extract import digest, initial_moves, file_hash
from pathlib import Path

@dataclass(frozen=True)
class Scope:
    campaign: str
    branch: str
    actor: str
    restore_epoch: int
    cutoff: int

@dataclass(frozen=True)
class Step:
    kind: str
    species: int
    level: int
    value: int = 0
    slot: int = 0

@dataclass(frozen=True)
class Companion:
    lineage: str
    actor: str
    origin: str  # exact trainer:slot baseline key or exact source encounter route
    origin_kind: Literal['baseline', 'wild']
    origin_level: int
    species: int
    level: int
    moves: tuple[int, ...]
    history: tuple[Step, ...] = ()
    held_item: int = 0

@dataclass(frozen=True)
class Context:
    scope: Scope
    companions: tuple[Companion, ...]
    milestones: frozenset[str]
    earned_epochs: tuple[str, ...]
    applied_epochs: tuple[str, ...]
    inventory: tuple[tuple[int, int], ...]
    permissions: frozenset[str]
    acquisitions: int | None = None
    opportunity_acquisitions: int | None = None
    last_capture_epoch: int | None = None
    fixture: bool = False

@dataclass(frozen=True)
class Result:
    status: Literal['allowed','blocked','unqualified']
    code: str
    ids: dict
    prerequisites: tuple[str, ...]
    resources: dict
    provenance: dict
    fully_legal: bool = False  # an element query is never a whole-package approval
    def packet(self): return json.loads(json.dumps(asdict(self)))

class Catalog:
    def __init__(self, data, policy):
        self.data=deepcopy(data); self.policy=deepcopy(policy)
        body={k:v for k,v in self.data.items() if k!='catalogSHA256'}
        if digest(body)!=self.data['catalogSHA256']: raise ValueError('catalog digest mismatch')
        self.hash=self.data['catalogSHA256'];self.policy_hash=digest(self.policy)
        self.constants=self.data['constants']
        self.routes={r['routeID']:r for r in self.data['encounters']}
        self.trainers={t['id']:t for t in self.data['trainers']}
    def lookup(self, kind: str, number: int):
        if kind not in ('species','moves','items') or type(number)!=int or number<=0: raise ValueError('invalid ID')
        table=self.data[kind]
        if number>=len(table): raise ValueError('unknown ID')
        row=table[number]
        if kind=='items' and row['unused']: raise ValueError('unused item')
        if kind=='species' and (number>=self.constants['SPECIES_EGG'] or self.constants['SPECIES_OLD_UNOWN_B']<=number<=self.constants['SPECIES_OLD_UNOWN_Z']): raise ValueError('non-playable species')
        return deepcopy(row)
    def own_baseline(self, actor, variant):
        t=self.trainers.get(variant)
        if t is None or t['actorID']!=actor: raise ValueError('cross-actor variant')
        return deepcopy(t)
    def bind(self, context: Context): return View(self,context)

class View:
    def __init__(self, catalog: Catalog, context: Context):
        self.cat=catalog; self.ctx=context
        if not isinstance(context,Context) or not isinstance(context.scope,Scope) or not context.scope.campaign or not context.scope.branch or type(context.scope.restore_epoch)!=int or type(context.scope.cutoff)!=int or context.scope.restore_epoch<0 or context.scope.cutoff<0: raise ValueError('missing active scope')
        if context.scope.actor not in {t['actorID'] for t in catalog.data['trainers']}: raise ValueError('unknown actor')
        if len({c.lineage for c in context.companions})!=len(context.companions): raise ValueError('duplicate lineage')
        inventory=dict(context.inventory)
        if len(inventory)!=len(context.inventory) or any(type(n)!=int or n<0 for n in inventory.values()):raise ValueError('invalid finite stock')
        for item in inventory: catalog.lookup('items',item)
        if any(not isinstance(e,str) or not e for e in context.earned_epochs+context.applied_epochs):raise ValueError('missing earned epoch identity')
        if any(n is not None and (type(n)!=int or n<0) for n in (context.acquisitions,context.opportunity_acquisitions,context.last_capture_epoch)):raise ValueError('invalid acquisition history')
        if len(set(context.earned_epochs))!=len(context.earned_epochs) or not set(context.applied_epochs)<=set(context.earned_epochs):raise ValueError('invalid epochs')
        self.profile=catalog.policy['actors'].get(context.scope.actor)
        if catalog.policy.get('fixtureOnly') and not context.fixture:raise ValueError('fixture policy denied to live context')
        self.inventory=inventory
        self.owned={c.lineage:c for c in context.companions}
        for c in context.companions: self._verify_history(c)
    def result(self,status,code,ids=None,prerequisites=(),resources=None,sources=()):
        return Result(status,code,ids or {},tuple(prerequisites),resources or {},{'catalogSHA256':self.cat.hash,'policySHA256':self.cat.policy_hash,'catalogVersion':1,'validatorVersion':1,'validatorSHA256':file_hash(Path(__file__)),'policyVersion':self.cat.policy['version'],'scope':asdict(self.ctx.scope),'contextSHA256':digest(asdict_context(self.ctx)),'fixture':self.ctx.fixture,'sourceFiles':list(sources)})
    def _verify_history(self,c):
        if c.actor!=self.ctx.scope.actor:raise ValueError('cross-actor companion')
        if c.origin_kind=='baseline':
            try: trainer,slot=map(int,c.origin.split(':')); t=self.cat.own_baseline(c.actor,trainer); p=t['party'][slot]
            except (ValueError,IndexError):raise ValueError('invalid baseline origin') from None
            if p['baselineKey']!=c.origin or c.origin_level!=p['level']:raise ValueError('baseline provenance mismatch')
            species,level,moves=p['species'],p['level'],list(p['moves'])
        elif c.origin_kind=='wild':
            route=self.cat.routes.get(c.origin)
            if not route or not route['minLevel']<=c.origin_level<=route['maxLevel']:raise ValueError('invalid wild origin')
            species,level=route['species'],c.origin_level; moves=initial_moves(self.cat.lookup('species',species)['learnset'],level)
        else:raise ValueError('unsupported origin')
        for step in c.history:
            if step.kind=='level':
                if step.species!=species or not level<step.level<=100:raise ValueError('invalid recorded growth')
                level=step.level
            elif step.kind=='evolution':
                transitions=self.cat.lookup('species',species)['evolutions']
                if step.level!=level or not any(m==self.cat.constants['EVO_LEVEL'] and p<=level and t==step.species for m,p,t in transitions):raise ValueError('unsupported recorded evolution')
                species=step.species
            elif step.kind=='level_move':
                if step.species!=species or step.level!=level or [level,step.value] not in self.cat.lookup('species',species)['learnset']:raise ValueError('invalid recorded move path')
                if not 0<=step.slot<4 or step.value in moves:raise ValueError('invalid recorded move slot')
                moves[step.slot]=step.value
            else:raise ValueError('unsupported recorded history method')
        if (species,level,tuple(moves))!=(c.species,c.level,c.moves):raise ValueError('unverified companion snapshot')
        self.cat.lookup('species',species)
        if c.held_item: self.cat.lookup('items',c.held_item)
    def baseline(self,variant):
        return self.cat.own_baseline(self.ctx.scope.actor,variant)
    def _companion(self,lineage):
        if lineage not in self.owned:raise ValueError('unknown owned lineage')
        return self.owned[lineage]
    def _stage(self):
        if not self.profile or not self.profile.get('stages'):return None
        eligible=[s for s in self.profile['stages'] if set(s['requires'])<=self.ctx.milestones]
        return max(eligible,key=lambda s:s['cap']) if eligible else None
    def growth(self,lineage,level):
        c=self._companion(lineage)
        if type(level)!=int or not c.level<=level<=100:return self.result('blocked','invalid_level',{'lineage':lineage,'level':level})
        if level==c.level:return self.result('allowed','owned_level_retained',{'lineage':lineage,'level':level},sources=('src/data/trainer_parties.h',))
        stage=self._stage()
        if stage is None:return self.result('unqualified','missing_trainer_stage_target',{'lineage':lineage},('CONTENT-01 stage target/cap and named milestones',))
        epochs=len(set(self.ctx.earned_epochs)-set(self.ctx.applied_epochs))
        gain=self.cat.policy['adaptation']['max_level_gain_per_earned_epoch_per_pokemon']*epochs
        cap=min(stage['cap'],stage['target'],c.level+gain)
        return self.result('allowed' if level<=cap else 'blocked','earned_growth' if level<=cap else 'stage_or_epoch_limit',{'lineage':lineage,'level':level,'maximum':max(c.level,cap)},('unapplied earned epochs','named stage milestones'),{'trainingEpochs':sorted(set(self.ctx.earned_epochs)-set(self.ctx.applied_epochs))})
    def acquisition(self,route_id):
        route=self.cat.routes.get(route_id)
        if route is None:return self.result('blocked','unknown_or_other_version_route',{'routeID':route_id})
        ids={'routeID':route_id,'species':route['species'],'map':route['map'],'method':route['method']}
        if route['method']!='land_mons':return self.result('unqualified','unsupported_acquisition_method',ids,(route['equipment'] or route['method'],),sources=('src/data/wild_encounters.json',))
        if not self.profile:return self.result('unqualified','missing_actor_region_profile',ids,('CONTENT-01',))
        region=self.profile['regions'].get(route['map'])
        if region is None:return self.result('blocked','off_region_no_explicit_permission',ids,('authored accessible/exceptional route grant; unsupported until qualified',))
        if not set(region['requires'])<=self.ctx.milestones:return self.result('blocked','inaccessible_map',ids,tuple(region['requires']))
        if 'capture:land' not in self.ctx.permissions:return self.result('blocked','capture_permission_missing',ids,('capture:land',))
        a=self.cat.policy['adaptation'];n=len(self.ctx.earned_epochs)
        if n<a['first_capture_eligible_epoch']:return self.result('blocked','first_epoch_no_capture',ids)
        if self.ctx.acquisitions is None or self.ctx.opportunity_acquisitions is None:return self.result('unqualified','missing_acquisition_history',ids)
        if self.ctx.opportunity_acquisitions>=a['max_new_acquisitions_per_opportunity']:return self.result('blocked','opportunity_acquisition_limit',ids)
        if self.ctx.acquisitions>=a['max_campaign_acquisitions_per_trainer']:return self.result('blocked','campaign_acquisition_limit',ids)
        if self.ctx.acquisitions and self.ctx.last_capture_epoch is None:return self.result('unqualified','missing_capture_spacing_history',ids)
        if self.ctx.last_capture_epoch is not None and n-self.ctx.last_capture_epoch<a['min_earned_epochs_between_successful_acquisitions']:return self.result('blocked','capture_spacing',ids)
        stage=self._stage()
        if stage is None:return self.result('unqualified','missing_trainer_stage_target',ids,('CONTENT-01',))
        if route['minLevel']>min(stage['target'],stage['cap']):return self.result('blocked','encounter_above_stage',ids)
        if self.inventory.get(self.cat.constants['ITEM_POKE_BALL'],0)<1:return self.result('blocked','resource_deficit',ids,resources={str(self.cat.constants['ITEM_POKE_BALL']):1})
        return self.result('allowed','eligible_attempt_not_capture_success',dict(ids,tier=region['tier'],levelRange=[route['minLevel'],min(route['maxLevel'],stage['cap'],stage['target'])]),('active addition limit/party capacity require PREP-01 whole-package validation','actual single seeded attempt (probability from policy)/result remains game authority','new initial moves charged to acquisition budget; no reserve/replacement by default'),{str(self.cat.constants['ITEM_POKE_BALL']):1},('src/data/wild_encounters.json',))
    def acquisition_routes(self,species):
        self.cat.lookup('species',species)
        return tuple(self.acquisition(r['routeID']) for r in self.cat.data['encounters'] if r['species']==species)
    def move(self,lineage,move,method='retained',level=None,item=None):
        c=self._companion(lineage);self.cat.lookup('moves',move); ids={'lineage':lineage,'move':move,'method':method}
        if method=='retained':return self.result('allowed' if move in c.moves else 'blocked','verified_retention' if move in c.moves else 'not_currently_retained',ids,sources=('src/data/trainer_parties.h','src/pokemon.c'))
        if method!='retained' and move in c.moves:return self.result('blocked','already_known_not_new_acquisition',ids)
        if method=='level_up':
            if type(level)!=int:return self.result('blocked','missing_learning_level',ids)
            if level<=c.level:return self.result('blocked','past_level_is_not_free_relearn',ids)
            if [level,move] not in self.cat.lookup('species',c.species)['learnset']:return self.result('blocked','no_current_species_level_path',ids,sources=('src/data/pokemon/level_up_learnsets.h',))
            g=self.growth(lineage,level)
            if g.status!='allowed':return g
            if 'learn:level' not in self.ctx.permissions:return self.result('blocked','learning_permission_missing',ids,('learn:level',))
            return self.result('allowed','future_level_acquisition',dict(ids,level=level),('move slot choice','aggregate two-slot change budget in PREP-01'),sources=('src/data/pokemon/level_up_learnsets.h','src/pokemon.c'))
        if method in ('tm','hm'):
            if type(item)!=int:return self.result('blocked','missing_machine',ids)
            machine=self.cat.lookup('items',item);ids['item']=item
            hm=item>=self.cat.constants['ITEM_HM01']
            if item==self.cat.constants['ITEM_HM08']:return self.result('unqualified','Dive_acquisition_not_qualified',ids)
            if machine['machineMove']!=move or (method=='hm')!=hm:return self.result('blocked','wrong_machine',ids)
            index=item-self.cat.constants['ITEM_TM01']
            if not 0<=index<58 or not int(self.cat.lookup('species',c.species)['tmhmMask'],16)&(1<<index):return self.result('blocked','machine_incompatible',ids)
            if f'learn:{method}' not in self.ctx.permissions:return self.result('blocked','machine_permission_missing',ids)
            if self.inventory.get(item,0)<1:return self.result('blocked','resource_deficit',ids,resources={str(item):1})
            return self.result('allowed','machine_acquisition',ids,('owned machine','aggregate slot budget; HM forgetting requires audited deleter'),{str(item):{'ownedRequired':1,'consume':0 if hm else 1}},('src/data/pokemon/tmhm_learnsets.h','src/party_menu.c','src/data/items.json'))
        return self.result('unqualified','unsupported_move_acquisition',ids)
    def move_paths(self,lineage):
        c=self._companion(lineage); results=[self.move(lineage,m) for m in c.moves if m]
        results += [self.move(lineage,m,'level_up',level=l) for l,m in self.cat.lookup('species',c.species)['learnset'] if l>c.level]
        for item in self.cat.data['items']:
            if item['machineMove']:results.append(self.move(lineage,item['machineMove'],'hm' if item['id']>=self.cat.constants['ITEM_HM01'] else 'tm',item=item['id']))
        return tuple(results)
    def evolution(self,lineage,target,level=None):
        c=self._companion(lineage);self.cat.lookup('species',target);ids={'lineage':lineage,'fromSpecies':c.species,'toSpecies':target}
        rows=[(m,p) for m,p,t in self.cat.lookup('species',c.species)['evolutions'] if t==target and m]
        if not rows:return self.result('blocked','not_direct_evolution',ids)
        if c.held_item==self.cat.constants['ITEM_EVERSTONE']:return self.result('blocked','everstone',ids)
        if target>self.cat.constants['SPECIES_MEW'] and 'pokedex.national' not in self.ctx.milestones:return self.result('blocked','national_dex_gate',ids,('pokedex.national',),sources=('src/evolution_scene.c',))
        m,p=rows[0]
        if m==self.cat.constants['EVO_LEVEL']:
            if type(level)!=int or level<=c.level or level<p:return self.result('blocked','level_evolution_threshold_or_trigger',ids,(f'new leveling event at level >= {p}',))
            g=self.growth(lineage,level)
            if g.status!='allowed':return g
            if 'evolve:level' not in self.ctx.permissions:return self.result('blocked','evolution_permission_missing',ids)
            return self.result('allowed','level_evolution_eligible',dict(ids,level=level),('preserve lineage and fixed identity','learning at evolution level separately queried'),sources=('src/data/pokemon/evolution.h','src/pokemon.c'))
        if m==self.cat.constants['EVO_ITEM']:
            if 'evolve:item' not in self.ctx.permissions:return self.result('blocked','evolution_permission_missing',ids,resources={str(p):1})
            if self.inventory.get(p,0)<1:return self.result('blocked','resource_deficit',ids,resources={str(p):1})
            if not self._stage():return self.result('unqualified','missing_trainer_stage_target',ids)
            return self.result('allowed','item_evolution_eligible',ids,('preserve lineage','actual item use downstream'),{str(p):1},('src/pokemon.c','src/data/pokemon/evolution.h'))
        return self.result('unqualified','unsupported_evolution_method',dict(ids,method=m,param=p))
    def evolution_paths(self,lineage,level=None):
        c=self._companion(lineage)
        return tuple(self.evolution(lineage,target,level=level) for method,param,target in self.cat.lookup('species',c.species)['evolutions'] if method)
    def allocations(self,allocations:tuple[tuple[str,int,int],...]):
        used=Counter(); ids={'allocations':[list(a) for a in allocations]}
        for category,item,n in allocations:
            if type(n)!=int or n<=0:return self.result('blocked','invalid_quantity',ids)
            definition=self.cat.lookup('items',item)
            if category not in ('held','battle_bag','teaching','evolution','capture'):return self.result('blocked','unknown_resource_category',ids)
            if category=='held' and definition['holdEffect']=='HOLD_EFFECT_NONE':return self.result('blocked','not_supported_held_effect',ids)
            if category=='battle_bag':return self.result('unqualified','NPC_item_execution_not_qualified',ids)
            if category=='teaching' and not definition['machineMove']:return self.result('blocked','not_machine_resource',ids)
            if category=='evolution' and not any(m==self.cat.constants['EVO_ITEM'] and p==item for s in self.cat.data['species'] for m,p,t in s['evolutions']):return self.result('blocked','not_evolution_resource',ids)
            if category=='capture' and item!=self.cat.constants['ITEM_POKE_BALL']:return self.result('unqualified','capture_resource_not_qualified',ids)
            if f'allocate:{category}' not in self.ctx.permissions:return self.result('blocked','allocation_permission_missing',ids)
            # HMs are reusable teaching equipment; reservation still prevents assigning
            # the same physical held/consumable item twice. A category conflict fails.
            if category=='teaching' and item>=self.cat.constants['ITEM_HM01']:
                used[item]=max(used[item],1)
            else:used[item]+=n
        deficits={str(i):n-self.inventory.get(i,0) for i,n in used.items() if n>self.inventory.get(i,0)}
        return self.result('blocked' if deficits else 'allowed','resource_deficit' if deficits else 'finite_allocation',ids,resources={'required':dict(used),'deficits':deficits})
    def theme(self,species:tuple[int,...]):
        for s in species:self.cat.lookup('species',s)
        theme=self.profile.get('theme') if self.profile else None
        if not theme or theme.get('mixedSupportLimit') is None:return self.result('unqualified','missing_gym_support_bounds',{'species':list(species)})
        count=sum(theme['primaryType'] not in self.cat.lookup('species',s)['types'] for s in species)
        return self.result('allowed' if count<=theme['mixedSupportLimit'] else 'blocked','theme_element_validated' if count<=theme['mixedSupportLimit'] else 'gym_theme_support_limit',{'species':list(species),'supportCount':count},('signature/lineage/acquisition/level/resource/whole-package validation separately required',))
    def identity(self,lineages:tuple[str,...],species:tuple[int,...]):
        ids={'lineages':list(lineages),'species':list(species)}
        if len(lineages)!=len(species) or len(set(lineages))!=len(lineages) or len(lineages)>self.cat.policy['adaptation']['engine_party_size_limit']:return self.result('blocked','invalid_identity_shape',ids)
        if not set(self.owned)<=set(lineages):return self.result('blocked','original_lineage_removal',ids)
        for s in species:self.cat.lookup('species',s)
        if not self.profile:return self.result('unqualified','missing_identity_profile',ids)
        signatures=set(self.profile.get('signatureLineages',[]))
        if not signatures<=set(lineages):return self.result('blocked','signature_removed',ids)
        theme=self.profile.get('theme')
        if theme:
            if theme.get('mixedSupportLimit') is None:return self.result('unqualified','missing_gym_support_bounds',ids,('CONTENT-01 authored first-Gym profile',))
            if sum(theme['primaryType'] not in self.cat.lookup('species',s)['types'] for s in species)>theme['mixedSupportLimit']:return self.result('blocked','gym_theme_support_limit',ids)
        if set(lineages)!=set(self.owned):return self.result('unqualified','new_lineage_requires_acquisition_and_PREP_validation',ids)
        # Identity-only projection does not bless arbitrary species transitions.
        for lineage,s in zip(lineages,species):
            if s!=self.owned[lineage].species:return self.result('unqualified','species_transition_requires_separate_evolution_proof',ids)
        return self.result('allowed','identity_preserved',ids,('all other preparation constraints checked separately',))

def asdict_context(context):
    d=asdict(context)
    d['milestones']=sorted(context.milestones);d['permissions']=sorted(context.permissions)
    return d

def validate_moveset(view: View, lineage: str, proposed: tuple[int,...], proofs: dict[int,dict]) -> Result:
    """Validate only slots/paths/edit budget; not a complete preparation package."""
    c=view._companion(lineage)
    if len(proposed)!=4 or any(type(m)!=int or m<0 for m in proposed):return view.result('blocked','invalid_move_slots')
    nonzero=[m for m in proposed if m]
    if not nonzero and proposed!=c.moves:return view.result('blocked','no_usable_move')
    if len(nonzero)!=len(set(nonzero)):return view.result('blocked','duplicate_moves')
    # HM deletion is a separate acquisition resource/service; never free forgetting.
    hm_moves=set(view.cat.data['machineMoves'][view.cat.constants['NUM_TECHNICAL_MACHINES']:-1])  # native IsMoveHm excludes eighth HM (Dive)
    if any(m in hm_moves and m not in proposed for m in c.moves):return view.result('unqualified','HM_deletion_not_qualified')
    edits=sum(a!=b for a,b in zip(c.moves,proposed))
    if edits>view.cat.policy['adaptation']['max_move_slot_changes_per_opportunity']:return view.result('blocked','move_change_budget')
    allocations=[]
    for move in nonzero:
        view.cat.lookup('moves',move)
        if move in c.moves:continue
        proof=proofs.get(move)
        if not proof or set(proof)-{'method','level','item'}:return view.result('blocked','missing_or_unknown_move_path')
        result=view.move(lineage,move,**proof)
        if result.status!='allowed':return result
        if proof.get('method') in ('tm','hm'):allocations.append(('teaching',proof['item'],1))
    if allocations:
        result=view.allocations(tuple(allocations))
        if result.status!='allowed':return result
    return view.result('allowed','move_element_validated',{'lineage':lineage,'moves':list(proposed),'changedSlots':edits},('PREP-01 aggregate edits across all companions','hypothetical growth/evolution/commit not executed'))
