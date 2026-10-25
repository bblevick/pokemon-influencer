"""Executable host-only envelopes and complete opening-package validation.

No opponent facts, model ranking, RNG, selected candidate or installation.
"""
from __future__ import annotations
from dataclasses import dataclass,replace,asdict
from copy import deepcopy
from pathlib import Path
from itertools import product
import json
from jsonschema import Draft202012Validator,ValidationError
from roster.domain import Step,Companion
from roster.extract import digest,canonical,file_hash
from content.policy import OpeningContent
ROOT=Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class PreparationEnvelope:
    encoded: str
    trusted_state: object
    content: object
    def packet(self):return json.loads(self.encoded)


def schema_validate(kind,packet):
    Draft202012Validator(json.loads((ROOT/f'schemas/prep/{kind}.schema.json').read_text())).validate(packet)


def validator_identity():
    return digest({name:file_hash(ROOT/name) for name in ('prep/domain.py','prep/store.py','prep/progression.py','prep/companions.py','content/policy.py','content/adaptation.py','roster/domain.py','schemas/prep/candidate.schema.json','schemas/prep/envelope.schema.json')})


def resolve_preparation_envelope(store,actor,stage='forest-post-boulder-1'):
    try:state=store.trusted_state(actor)
    except ValueError as e:return {'status':'blocked','reason':str(e)}
    opportunity=store.get_preparation_opportunity(actor,stage)
    if not opportunity or opportunity['status']!='available':return {'status':'blocked','reason':'preparation_opportunity_unavailable'}
    resolved=store.content.resolve(state,stage)
    if resolved['status']!='permitted':return {'status':'blocked','reason':resolved['reason']}
    content=store.content;config=json.loads((ROOT/'config/preparation_generation.json').read_text())
    view=store._one('SELECT * FROM prep_view');s=store.preparation_state()
    owned=dict(state.context.inventory);reservations=[r for r in s['reservations'].values() if r['actor']==actor]
    available=dict(owned)
    for reservation in reservations:
        for item,quantity in reservation['costs']:
            available[item]=available.get(item,0)-quantity
    if any(n<0 for n in available.values()):return {'status':'blocked','reason':'resource_reservations_exceed_owned_stock'}
    companions=[];options=[]
    for c in state.context.companions:
        original=next(p for p in content.pack['trainers'][actor]['originals'] if p['baselineKey']==c.origin)
        companions.append({**asdict(c),'fixedIV':original['fixedIV'],'ivSource':original['ivSource'],'active':True})
        v=content.roster_view(state,stage,c.lineage)
        options.append({'lineage':c.lineage,'retainedMoves':[m for m in c.moves if m],
            'futurePaths':[p.packet() for p in v.move_paths(c.lineage) if p.status=='allowed' and p.ids.get('method')!='retained'],
            'evolutionTargets':[x[2] for x in v.cat.lookup('species',c.species)['evolutions'] if x[0]],
            'evolutionProofRequired':True})
    p={'schemaVersion':1,'generatorVersion':config['version'],
       'scope':{**asdict(state.context.scope),'prepCutoff':view['cutoff'],'opportunityID':opportunity['opportunityID'],
                'activation':digest(s['activation']),'memoryCutoff':store._one('SELECT cutoff FROM memory_view')['cutoff'],
                'socialCutoff':store._one('SELECT cutoff FROM social_view')['cutoff'],
                'puppeteerCutoff':store._one('SELECT cutoff FROM puppeteer_view')['cutoff']},
       'identity':{'actor':actor,'worldTrainerID':content.pack['trainers'][actor]['worldTrainerID'],
                   'sourceVariant':content.pack['trainers'][actor]['qualifiedVariant'],'kind':stage},
       'rules':{'contentSHA256':content.hash,'contentVersion':content.pack['version'],'catalogSHA256':content.cat.hash,
                'sourceCommit':content.pack['sourceCommit'],'romSHA256':store.build,
                'adaptationRulesSHA256':content.adaptation.hash,'generationSHA256':digest(config),
                'validatorSHA256':validator_identity()},
       'progression':{**resolved['progression'],'earnedOpportunityAllowance':resolved['earnedOpportunityAllowance'],
           'earnedOpportunityIDs':[opportunity['opportunityID']] if resolved['earnedOpportunityAllowance'] else [],
           'appliedOpportunityIDs':sorted(state.consumed_opportunities)},'levels':resolved['levels'],'companions':companions,
       'moveOptions':options,'budgets':resolved['budgets'],
       'acquisition':{'allowance':resolved['budgets']['catchBudget'],'profile':content.adaptation_profile(state,stage),
                      'originWeights':content.adaptation.rules['originWeights'],'eligibleOrigins':{},
                      'originSamplerImplemented':False,'laterCandidateGenerationGate':'PREP-ACQ-01',
                      'activeCapacity':len(companions),'reserveCapacity':0},
       'resources':{'owned':list(state.context.inventory),'available':[[item,n] for item,n in sorted(available.items())],'reserved':reservations,
                    'initialization':s['actors'][actor]['resources'],'restock':False},
       'identityPolicy':{'retainedLineages':resolved['retainedLineages'],'signatureLineages':resolved['signatureLineages'],'theme':resolved['theme']},
       'evidence':{'nativeReceiptIDs':resolved['evidenceRefs'],'opportunityReceipt':opportunity.get('earnedReceipt'),
                   'pairedCheckpoint':resolved['checkpoint'],'trustedStateSHA256':digest([companions,resolved['currentInventory'],resolved['scope']])},
       'generation':config,'knowledgeBoundary':'actor own state and canonical progression only; no player/opponent state or briefing',
       'expiry':'any scope/cutoff/ownership/resource/opportunity change'}
    p=json.loads(json.dumps(p));p['envelopeSHA256']=digest(p);p['envelopeID']='envelope:'+p['envelopeSHA256']
    schema_validate('envelope',p)
    if len(canonical(p))>config['maximumEnvelopeBytes']:return {'status':'blocked','reason':'envelope_byte_limit'}
    return PreparationEnvelope(json.dumps(p,sort_keys=True),state,content)


def envelope_intact(envelope):
    p=envelope.packet()
    try:schema_validate('envelope',p)
    except (ValidationError,TypeError,ValueError):return False
    body={k:v for k,v in p.items() if k not in ('envelopeID','envelopeSHA256')}
    return digest(body)==p['envelopeSHA256'] and p['envelopeID']=='envelope:'+p['envelopeSHA256'] and p['rules']['validatorSHA256']==validator_identity()


def current_envelope(store,envelope):
    if not envelope_intact(envelope):return False
    p=envelope.packet();fresh=resolve_preparation_envelope(store,p['identity']['actor'],p['identity']['kind'])
    return isinstance(fresh,PreparationEnvelope) and fresh.packet()['envelopeSHA256']==p['envelopeSHA256']


def _replay(c,steps):
    c=replace(c)
    for s in steps:
        moves=list(c.moves)
        if s.kind=='level_move':moves[s.slot]=s.value
        c=replace(c,species=s.species,level=s.level,moves=tuple(moves),history=c.history+(s,))
    return c


def validate_preparation_candidate(envelope,candidate,store=None):
    def rejected(reason,**kw):return {'valid':False,'reason':reason,**kw}
    try:schema_validate('candidate',candidate)
    except (ValidationError,TypeError,ValueError):return rejected('candidate_schema')
    if not envelope_intact(envelope):return rejected('envelope_integrity_or_version')
    p=envelope.packet();content=envelope.content;state=envelope.trusted_state
    if len(canonical(candidate))>p['generation']['maximumCandidateBytes']:return rejected('candidate_byte_limit')
    if digest(content.pack)!=p['rules']['contentSHA256']:return rejected('changed_content_snapshot')
    if store is not None and not current_envelope(store,envelope):return rejected('stale_envelope_generation')
    if candidate['envelopeID']!=p['envelopeID']:return rejected('wrong_envelope')
    core={k:v for k,v in candidate.items() if k not in ('candidateID','validation','descriptors')}
    if candidate['candidateID']!='candidate:'+digest(core):return rejected('candidate_digest_mismatch')
    if candidate['acquisitionCount'] or candidate['resourceCosts'] or any(candidate['battleItems']):return rejected('opening_acquisition_or_resource_prohibited')
    originals={c.lineage:c for c in state.context.companions}
    if len(candidate['party'])!=len(originals) or {c['lineage'] for c in candidate['party']}!=set(originals):return rejected('original_or_signature_retention')
    if sorted(candidate['order'])!=sorted(originals) or len(candidate['order'])!=len(originals):return rejected('party_order_invalid')
    if p['identity']['kind']=='first' and candidate['order']!=list(originals):return rejected('authored_first_party_order')
    if set(candidate['paths'])!=set(originals):return rejected('path_coverage')
    paths={k:[Step(**x) for x in v] for k,v in candidate['paths'].items()}
    try:proof=content.development(state,p['identity']['kind'],paths)
    except ValueError as e:return rejected('invalid_development_history',detail=str(e))
    if proof['status']!='permitted':return rejected(proof['reason'],proof=proof)
    for row in candidate['party']:
        c=originals[row['lineage']];expected=_replay(c,paths[c.lineage]);baseline=next(x for x in content.pack['trainers'][c.actor]['originals'] if x['baselineKey']==c.origin)
        required={'lineage':c.lineage,'origin':c.origin,'species':expected.species,'level':expected.level,
                  'moves':list(expected.moves),'heldItem':c.held_item,'fixedIV':baseline['fixedIV'],'ivSource':baseline['ivSource']}
        if row!=required:return rejected('package_and_legality_path_disagree')
        if row['heldItem'] or row['level']>p['levels'][c.lineage]['maximum']:return rejected('resource_or_level_cap')
    if p['identityPolicy']['theme']:
        theme=p['identityPolicy']['theme'];types=[content.cat.lookup('species',x['species'])['types'] for x in candidate['party']]
        if sum(theme['primaryType'] not in t for t in types)>theme['maximumSupport'] or len(types)>theme['maximumActive']:return rejected('gym_theme_or_support')
    result={'valid':True,'scope':'complete opening host package, not native installed team','electiveMoveChanges':proof['moveChanges'],
            'contentSHA256':content.hash,'catalogSHA256':content.cat.hash,'validatorSHA256':p['rules']['validatorSHA256'],
            'pathProof':proof['reason'],'resourcesRevalidatedAtCommitRequired':True}
    if candidate['validation'] and candidate['validation']!=result:return rejected('validation_metadata_mismatch')
    descriptors=describe_candidate(content,candidate,result)
    if candidate['descriptors'] and candidate['descriptors']!=descriptors:return rejected('descriptor_metadata_mismatch')
    return result


def describe_candidate(content,candidate,proof):
    party=candidate['party'];moves=[content.cat.lookup('moves',m) for x in party for m in x['moves'] if m]
    evolves=sum(any(x['kind']=='evolution' for x in path) for path in candidate['paths'].values())
    return {'retainsSignature':True,'evolvedCompanions':evolves,'electiveMoveChanges':proof['electiveMoveChanges'],
            'acquisitionCount':candidate['acquisitionCount'],'teamSize':len(party),
            'typeComposition':[content.cat.lookup('species',x['species'])['types'] for x in party],
            'moveTypes':sorted(set(m['type'] for m in moves)), 'nonDamagingMoveCount':sum(m['power']==0 for m in moves)}


def _individual_paths(envelope,c):
    p=envelope.packet();content=envelope.content
    v=content.roster_view(envelope.trusted_state,p['identity']['kind'],c.lineage)
    cap=p['levels'][c.lineage]['maximum'];budget=p['budgets']['aggregateMoveChanges'];bound=p['generation']['maximumIndividualPaths']
    paths=[()];front=[()];omitted=0
    for level in range(c.level+1,cap+1):
        next_front=[]
        for path in front:
            before=_replay(c,path);step=Step('level',before.species,level);grown=_replay(c,path+(step,))
            before_ctx=replace(v.ctx,companions=tuple(before if x.lineage==c.lineage else x for x in v.ctx.companions))
            bv=v.cat.bind(before_ctx)
            species_states=[(grown,path+(step,))]
            for method,param,target in v.cat.lookup('species',before.species)['evolutions']:
                if method and bv.evolution(c.lineage,target,level=level).status=='allowed':
                    ev=Step('evolution',target,level);species_states.append((_replay(grown,(ev,)),path+(step,ev)))
            for owned,new_path in species_states:
                next_front.append(new_path)
                changes=sum(x.kind=='level_move' for x in new_path)
                if changes>=budget:continue
                for learning_level,move in v.cat.lookup('species',owned.species)['learnset']:
                    if learning_level!=level or move in owned.moves:continue
                    for slot in range(4):
                        if slot and owned.moves[slot]==0 and owned.moves[slot-1]==0:continue
                        next_front.append(new_path+(Step('level_move',owned.species,level,move,slot),))
        # Structural categories round robin prevents skip-only paths starving evolution.
        groups={}
        for path in next_front:
            key=(any(x.kind=='evolution' for x in path),any(x.kind=='level_move' for x in path))
            groups.setdefault(key,[]).append(path)
        selected=[]
        while len(selected)<bound and any(groups.values()):
            for key in sorted(groups):
                if groups[key] and len(selected)<bound:selected.append(groups[key].pop(0))
        omitted+=sum(len(x) for x in groups.values());front=selected;paths+=front
    # Include unchanged and max-target structural variants preferentially.
    at_cap=[x for x in paths if x and x[-1].level==cap]
    intermediates=[x for x in paths if x and x[-1].level!=cap]
    return [()]+at_cap+intermediates,omitted


def generate_preparation_candidates(envelope):
    p=envelope.packet();state=envelope.trusted_state;content=envelope.content
    if p['acquisition']['allowance']!=0:raise ValueError('PREP-ACQ-01 gated: future origins/capture outcomes not qualified')
    config=p['generation'];originals=state.context.companions;options=[];omitted=0
    for c in originals:
        paths,n=_individual_paths(envelope,c);options.append(paths);omitted+=n
    # Baseline, then round-robin whole-package structural families; no strength score.
    lanes={};examined=0;pruned=[]
    def combinations():
        # Seed each companion's growth before the Cartesian search; product order
        # alone can exhaust the bound on the final companion and starve earlier ones.
        for i in range(max(map(len,options))):
            for slot,paths in enumerate(options):
                if i<len(paths):
                    row=[() for _ in originals];row[slot]=paths[i];yield tuple(row)
        yield from product(*options)
    combinations_seen=set()
    for combination in combinations():
        key=digest([[asdict(x) for x in path] for path in combination])
        if key in combinations_seen:continue
        combinations_seen.add(key)
        if examined>=config['maximumExaminedPackages']:pruned.append('whole-package examination bound reached');break
        examined+=1
        changes=sum(x.kind=='level_move' for path in combination for x in path)
        if changes>p['budgets']['aggregateMoveChanges']:continue
        shape=('evolution' if any(x.kind=='evolution' for path in combination for x in path) else 'learning' if changes else 'growth')
        lanes.setdefault(shape,[]).append(combination)
    candidates=[];seen=set();rejected=[]
    def package(paths,order=None):
        party=[];serialized={};evolves=0
        for c,path in zip(originals,paths):
            final=_replay(c,path);source=next(x for x in content.pack['trainers'][c.actor]['originals'] if x['baselineKey']==c.origin)
            party.append({'lineage':c.lineage,'origin':c.origin,'species':final.species,'level':final.level,'moves':list(final.moves),'heldItem':final.held_item,'fixedIV':source['fixedIV'],'ivSource':source['ivSource']})
            serialized[c.lineage]=[asdict(x) for x in path];evolves+=any(x.kind=='evolution' for x in path)
        body={'schemaVersion':1,'envelopeID':p['envelopeID'],'party':party,'order':order or [c.lineage for c in originals],
              'paths':serialized,'battleItems':[0,0,0,0],'resourceCosts':[],'acquisitionCount':0}
        structural=digest([party,body['order'],body['battleItems']])
        if structural in seen:return
        body['candidateID']='candidate:'+digest(body)
        body['validation']={};body['descriptors']={}
        proof=validate_preparation_candidate(envelope,body)
        if not proof['valid']:rejected.append({'reason':proof['reason']});return
        body['validation']=proof
        body['descriptors']=describe_candidate(content,body,proof)
        schema_validate('candidate',body)
        if len(canonical(body))>config['maximumCandidateBytes']:rejected.append({'reason':'candidate_byte_limit'});return
        seen.add(structural);candidates.append(body)
    package(tuple(() for c in originals))
    if len(originals)>1 and p['identity']['kind']!='first':package(tuple(() for c in originals),[c.lineage for c in reversed(originals)])
    while len(candidates)<config['maximumCandidates'] and any(lanes.values()):
        for shape in sorted(lanes):
            if lanes[shape] and len(candidates)<config['maximumCandidates']:package(lanes[shape].pop(0))
    if any(lanes.values()):pruned.append('configured maximum candidate count; remaining structural alternatives omitted')
    if not candidates:raise ValueError('no validated unchanged fallback')
    return {'envelopeID':p['envelopeID'],'generatorVersion':config['version'],'candidates':candidates,
            'fallbackCandidateID':candidates[0]['candidateID'],'examinedPackages':examined,
            'individualPathsPruned':omitted,'pruningReasons':pruned,'rejectedPackages':rejected,
            'selectedCandidateID':None,'sampling':'none'}


def resolve_future_acquisition_envelope(content,context,profile,**history):
    """Scenario-only future interface; never binds unqualified live content.

    Exact origin filtering is executable; origin draw, acquisition outcomes and
    complete acquisition packages remain the explicitly named PREP-ACQ-01 gate.
    """
    if not context.fixture or not profile.get('scenarioOnly'):raise ValueError('future qualification fixtures only')
    r=content.adaptation.resolve(content.cat,context,profile,**history)
    packet={'schemaVersion':1,'scenarioOnly':True,'scope':asdict(context.scope),
        'catalogSHA256':content.cat.hash,'profileSHA256':digest(profile),
        'rulesSHA256':content.adaptation.hash,'balanceVersion':content.adaptation.rules['balanceVersion'],
        'acquisitionLimit':profile['acquisitionLimit'],'constraintResult':r,
        'originSamplerImplemented':False,'completeCandidateGate':'PREP-ACQ-01',
        'selectedOrigin':None,'selectedCandidateID':None}
    packet['envelopeID']='acquisition-envelope:'+digest(packet)
    return packet


def resolve_preparation_bundle(store,actor,stage='forest-post-boulder-1'):
    """Separate hashes avoid circular envelope -> candidate -> envelope IDs."""
    envelope=resolve_preparation_envelope(store,actor,stage)
    if not isinstance(envelope,PreparationEnvelope):return envelope
    result=generate_preparation_candidates(envelope)
    return {'schemaVersion':1,'status':'resolved','envelope':envelope.packet(),
            'candidateSet':result,'candidateSetSHA256':digest(result),
            'selectedCandidateID':None,'commitment':None,'installed':False}
