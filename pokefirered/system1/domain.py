"""Facts + exact subjective memo + source-derived legal choices, never scores."""
import json,re,math
from pathlib import Path
from roster.extract import digest,canonical
from prep.domain import resolve_preparation_bundle,resolve_preparation_envelope,validate_preparation_candidate
from strategy.memo import validate_text
ROOT=Path(__file__).resolve().parents[1]
QUESTION='Choose the supplied legal preparation that best realizes this trainer\'s subjective StrategyMemo given personality, authorized evidence, identity and finite resources. Interpret wishes semantically: exact realization, close legal substitute, same tactical function, partial realization, then best overall fit. Never invent options. Unavailable wishes do not change facts or legality. Return one supplied choice; do not resample.'

def symbol(cat,kind,number):
    if not number:return 'None'
    # MOVE_EFFECT_* also starts MOVE_ in the legacy catalog. Restrict names to
    # the actual source moves.h namespace rather than selecting the first alias.
    if kind=='moves':allowed=set(re.findall(r'^#define\s+(MOVE_\w+)\s', (ROOT/'include/constants/moves.h').read_text(),re.M))
    else:allowed=set(cat.lookup(kind,number)['symbols'])
    names=[s for s in cat.lookup(kind,number)['symbols'] if s in allowed]
    if not names:raise ValueError('unqualified_source_name')
    return names[0].split('_',1)[1].replace('_',' ').title()

def describe(store,envelope,candidate):
    cat=store.content.cat;current={p['lineage']:p for p in envelope['companions']};rows=[]
    constants=store.content.data['constants']
    for lineage in candidate['order']:
        p=next(x for x in candidate['party'] if x['lineage']==lineage);sp=cat.lookup('species',p['species']);moves=[]
        for m in p['moves']:
            if not m:moves.append({'id':0,'name':'None'});continue
            r=cat.lookup('moves',m)
            effect=sorted(k for k,v in constants.items() if k.startswith('EFFECT_') and v==r['effect'])
            moves.append({'id':m,'name':symbol(cat,'moves',m),**{k:r[k] for k in ('type','power','accuracy','pp','priority','target')},'effect':effect or [r['effect']]})
        old=current[lineage]
        rows.append({'lineage':lineage,'species':symbol(cat,'species',p['species']),'speciesID':p['species'],'level':p['level'],'types':sp['types'],'baseStatsHPAtkDefSpeedSpAtkSpDef':sp['stats'],'moves':moves,'heldItem':symbol(cat,'items',p['heldItem']),'heldItemID':p['heldItem'],'changes':{'originalSpeciesID':old['species'],'originalLevel':old['level'],'changedMoveSlots':[i for i,(a,b) in enumerate(zip(old['moves'],p['moves'])) if a!=b]},'signature':lineage in envelope['identityPolicy']['signatureLineages'],'retainedOriginal':lineage in envelope['identityPolicy']['retainedLineages']})
    lines=[]
    for p in rows:
        moves='; '.join(f"{m['id']} {m['name']}"+(f" type={m['type']} power={m['power']} acc={m['accuracy']} pp={m['pp']} priority={m['priority']} target={m['target']} effect={m['effect']}" if m['id'] else '') for m in p['moves'])
        lines.append(f"{p['lineage']}: {p['speciesID']} {p['species']} L{p['level']} types={p['types']} baseStatsHPAtkDefSpeedSpAtkSpDef={p['baseStatsHPAtkDefSpeedSpAtkSpDef']}; moves=[{moves}]; held={p['heldItemID']} {p['heldItem']}; changedSlots={p['changes']['changedMoveSlots']}; original={p['retainedOriginal']} signature={p['signature']}")
    lines.append(f"Battle items={candidate['battleItems']}; resource costs={candidate['resourceCosts']}; available={envelope['resources']['available']}; acquisitions={candidate['acquisitionCount']}; capabilities={candidate['descriptors']}")
    return '\n'.join(lines)

def build_request(store,actor,stage='forest-post-boulder-1'):
    bundle=resolve_preparation_bundle(store,actor,stage)
    if bundle['status']!='resolved':raise ValueError('preparation_unavailable')
    records=[m for m in store.memo_records() if m['actor']==actor]
    if not records:raise ValueError('missing_strategy_memo')
    memo=records[-1];validate_text(memo['strategyText'])
    current=store.recorded_strategy(actor,stage,memo['scope']['strategyPurpose'],memo['scope']['providerConfiguration'])
    if not current or current['decision']['strategyID']!=memo['strategyID']:raise ValueError('stale_strategy_memo')
    env=bundle['envelope'];brief=store.trainer_packet(actor);options={c['candidateID']:describe(store,env,c) for c in bundle['candidateSet']['candidates']}
    facts={'trainer':brief['trainer'],'personality':brief['persona'],'authoredBehavior':store.context_packet(actor,stage,memo['scope']['strategyPurpose'],memo['scope']['providerConfiguration'])['modelInput']['behavior'],'stage':stage,'opportunity':env['scope']['opportunityID'],'levels':env['levels'],'budgets':env['budgets'],'identityPolicy':env['identityPolicy'],'resources':env['resources']['available']}
    state='TRAINER FACTS\n'+json.dumps(facts,sort_keys=True)+'\nAUTHORIZED OPPONENT KNOWLEDGE\n'+json.dumps({k:brief[k] for k in ('directObservations','reportedClaims','retainedEpisodes','unknowns')},sort_keys=True)+'\nSTRATEGY MEMO — SUBJECTIVE\n'+memo['strategyText']+'\nLEGAL PREPARATION OPTIONS\nOnly the supplied criteria describe legal options. Numeric type/effect identifiers refer to the pinned FireRed catalog; move names are qualified against moves.h. Memo wishes do not grant moves or species.'
    if len(state.encode())>24576:raise ValueError('decision_state_bound')
    r={'schemaVersion':1,'actor':actor,'stage':stage,'scope':{**env['scope'],'system1Epoch':store._one('SELECT epoch FROM preparation_decision_view')['epoch']},'memo':memo,'memoSHA256':digest(memo['strategyText']),'bundle':bundle,'state':state,'question':QUESTION,'choices':options,'fallbackCandidateID':bundle['candidateSet']['fallbackCandidateID']}
    r['requestID']='prep-decision:'+digest(r);return r

from .validation import validate_decision

def candidate_for(request,choice):
    return next(c for c in request['bundle']['candidateSet']['candidates'] if c['candidateID']==choice)

def revalidate(store,request,result):
    validate_decision(result,request['choices'])
    fresh=build_request(store,request['actor'],request['stage'])
    if fresh['requestID']!=request['requestID']:raise ValueError('stale_preparation_decision')
    env=resolve_preparation_envelope(store,request['actor'],request['stage']);c=candidate_for(request,result['choiceID']);proof=validate_preparation_candidate(env,c,store)
    if not proof['valid']:raise ValueError('candidate_revalidation:'+proof['reason'])
    return c,proof

def debit_stock(stock,costs):
    out=dict(stock)
    if len(dict(costs))!=len(costs):raise ValueError('duplicate_resource_cost')
    for item,n in costs:
        if type(item)!=int or item<=0 or type(n)!=int or n<=0 or out.get(item,0)<n:raise ValueError('finite_resource_deficit')
        out[item]-=n
    return [[k,v] for k,v in sorted(out.items()) if v]
