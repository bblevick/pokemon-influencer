"""Filter through actor APIs before context construction, never canonical retrieval."""
from __future__ import annotations
import json
from pathlib import Path
from roster.extract import digest,canonical
from jsonschema import Draft202012Validator
from prep.domain import resolve_preparation_bundle
ROOT=Path(__file__).resolve().parents[1]

def label(cat,kind,number):
    if not number:return 'NONE'
    return cat.lookup(kind,number)['symbols'][0].split('_',1)[1].replace('_',' ').title()

def configuration_identity():
    return digest({p:(ROOT/p).read_text() for p in ('config/strategy_behavior.json','config/model_profiles.yaml','prompts/strategy01.txt','schemas/strategy/posture.schema.json','schemas/strategy/context.schema.json','schemas/strategy/behavior.schema.json')})

def build_context(store,actor,stage='forest-post-boulder-1',purpose='preparation',provider_binding=None,context_transform=None):
    if purpose not in ('preparation','battle-only-fixture','preparation-live-acceptance'):raise ValueError('unknown_strategy_purpose')
    bundle=resolve_preparation_bundle(store,actor,stage)
    if bundle['status']!='resolved':raise ValueError('strategy_preparation_unavailable:'+bundle.get('reason','blocked'))
    e=bundle['envelope'];candidates=bundle['candidateSet']['candidates'];brief=store.trainer_packet(actor);cat=store.content.cat
    profiles=json.loads((ROOT/'config/strategy_behavior.json').read_text());Draft202012Validator(json.loads((ROOT/'schemas/strategy/behavior.schema.json').read_text())).validate(profiles);behavior=profiles['actors'].get(actor,profiles['default'])
    evidence=[]
    for mode,groups in [('direct',brief['directObservations']),('reported',brief['reportedClaims'])]:
        for group in groups:
            claim=group['claim']
            if claim['type'] not in ('POKEMON_SEEN','MOVE_REVEALED','TRAINER_BATTLE_RESULT'):continue
            row={'reference':group['evidenceIDs'][0],'mode':mode,'claim':claim,'attribution':group.get('attribution'),'labels':{}}
            for key,kind in [('speciesID','species'),('moveID','moves')]:
                if key in claim:row['labels'][key]=label(cat,kind,claim[key])
            evidence.append(row)
    caps=['preserve_partners','no_acquisition_available' if not e['acquisition']['allowance'] else 'acquisition_available']
    if not e['resources']['available']:caps.append('zero_healing_items')
    # Derive effect availability from validated candidates, not an unrestricted catalog prompt.
    moves=[cat.lookup('moves',m) for candidate in candidates for p in candidate['party'] for m in p['moves'] if m]
    if any(c['descriptors']['evolvedCompanions'] for c in candidates):caps.append('evolution_possible')
    if any(m['power']==0 for m in moves):caps.append('status_options_available')
    if any('MOVE_STRING_SHOT' in m['symbols'] for m in moves):caps.append('speed_control_available')
    if len({m['type'] for m in moves if m['power']})>1:caps.append('offensive_coverage_available')
    if e['identityPolicy']['signatureLineages']:caps.append('signature_must_be_retained')
    if e['identityPolicy']['theme']:caps.append('theme_identity')
    companions=[{'lineage':p['lineage'],'speciesID':p['species'],'species':label(cat,'species',p['species']),'level':p['level'],'moveIDs':p['moves'],'moves':[label(cat,'moves',m) for m in p['moves']],'heldItem':p['held_item']} for p in e['companions']]
    trainer={**brief['trainer'],'classID':cat.own_baseline(actor,store.content.pack['trainers'][actor]['sourceTrainer'])['class']}
    model={'schemaVersion':1,'trainer':trainer,'persona':brief['persona'],'behaviorVersion':profiles['version'],'behavior':behavior,
      'evidence':evidence,'privateEpisodes':brief['retainedEpisodes'],'authorizedDirectorNotes':[],
      'unknowns':brief['unknowns']+['action order and frequency','current or future opponent party'],
      'evidenceLimitation':'fact-deduplicated, not chronological; no frequency inference',
      'companions':companions,'resources':{'available':e['resources']['available'],'restock':False},
      'identityPolicy':e['identityPolicy'],'preparation':{'stage':stage,'levels':e['levels'],'moveChangeBudget':e['budgets']['aggregateMoveChanges'],'acquisitionAllowance':e['acquisition']['allowance'],'eligibleOrigins':e['acquisition']['eligibleOrigins'],'originWeights':e['acquisition']['originWeights'],'activeCapacity':len(companions),'reserveCapacity':0,'theme':e['identityPolicy']['theme']},'capabilities':sorted(caps),'truncated':brief['truncated']}
    # Episode summaries are actor-private, factual and deduplicated; exclude publication IDs and internal retrieval scope.
    model['privateEpisodes']=[{k:p[k] for k in ('episodeID','summary','sourceEvidenceIDs','visibility')} for p in brief['retainedEpisodes']]
    original_model=model
    if context_transform is not None:model=context_transform(model,e['scope']['opportunityID'])
    if len(canonical(model))>24576:raise ValueError('strategy_input_byte_limit')
    scope={**e['scope'],'strategyPurpose':purpose,'envelopeID':e['envelopeID'],'personaVersion':profiles['version'],'configurationSHA256':configuration_identity(),'promptVersion':1,'strategySchemaVersion':2,'providerConfiguration':provider_binding or {'provider':'offline','model':'strategy-fallback-v1','adapterVersion':1}}
    v=store._one('SELECT * FROM strategy_view') if getattr(store,'_strategy_ready',False) else None
    scope['strategyEpoch']=v['epoch'] if v else 0
    material=digest([model,scope['opportunityID'],purpose,configuration_identity(),scope['providerConfiguration']])
    packet={'schemaVersion':1,'scope':scope,'modelInput':model,'materialContextSHA256':material,'candidateCount':len(candidates)}
    packet['contextID']='strategy-context:'+digest(packet)
    Draft202012Validator(json.loads((ROOT/'schemas/strategy/context.schema.json').read_text())).validate({**packet,'modelInput':original_model} if context_transform is not None else packet)
    return packet
