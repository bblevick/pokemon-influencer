"""Closed provider-neutral intent and local evidence/capability validation."""
from __future__ import annotations
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from roster.extract import digest
ROOT=Path(__file__).resolve().parents[1]
SCHEMA=json.loads((ROOT/'schemas/strategy/posture.schema.json').read_text())
PRIORITIES=['preserve_partners','control_status','speed_control','offensive_coverage','conserve_resources','preserve_theme','flexible_approach','consider_acquisition','use_healing']
CAPABILITY={'control_status':'status_options_available','speed_control':'speed_control_available','offensive_coverage':'offensive_coverage_available','consider_acquisition':'acquisition_available','use_healing':'healing_items_available','preserve_theme':'theme_identity'}

def validate(posture,packet):
    Draft202012Validator(SCHEMA).validate(posture)
    evidence={x['reference']:x for x in packet['modelInput']['evidence']}
    caps=set(packet['modelInput']['capabilities'])
    for tag in posture['priorities']:
        if tag in CAPABILITY and CAPABILITY[tag] not in caps:raise ValueError('impossible_priority:'+tag)
    for a in posture['assumptions']:
        if a['kind']=='UNKNOWN':
            if a['evidenceRefs'] or a['confidence']!='weak' or a['basis']!='unknown':raise ValueError('unknown_not_evidence')
            continue
        if not a['evidenceRefs'] or any(ref not in evidence for ref in a['evidenceRefs']):raise ValueError('foreign_evidence')
        rows=[evidence[ref] for ref in a['evidenceRefs']]
        expected={'observed_species':'POKEMON_SEEN','possible_species_return':'POKEMON_SEEN','observed_move':'MOVE_REVEALED','prior_battle_result':'TRAINER_BATTLE_RESULT'}[a['kind']]
        if any(r['claim']['type']!=expected for r in rows):raise ValueError('evidence_kind_mismatch')
        if a['kind']=='possible_species_return':
            if a['basis']!='interpretation' or a['confidence']=='strong':raise ValueError('future_opponent_not_guaranteed')
        elif a['basis'] not in ('direct','reported') or any(r['mode']!=a['basis'] for r in rows):raise ValueError('misattributed_evidence')
        elif a['basis']=='reported' and a['confidence']=='strong':raise ValueError('reported_not_direct_certainty')
    return json.loads(json.dumps(posture))

def normalize(posture):
    summary='Approach: '+posture['approach']+'. Priorities: '+', '.join(posture['priorities'])+'. '
    summary+='Opponent knowledge: '+(', '.join(x['kind']+' ('+x['basis']+', '+x['confidence']+')' for x in posture['assumptions']) or 'UNKNOWN')+'.'
    return {**posture,'summary':summary}

def fallback(packet):
    p=packet['modelInput'];caps=p['capabilities'];b=p['behavior']
    priorities=['preserve_partners','conserve_resources']
    if 'theme_identity' in caps:priorities.append('preserve_theme')
    if b['setupPatience']=='strong' and 'speed_control_available' in caps:priorities.append('speed_control')
    posture={'schemaVersion':2,'approach':'patient_control' if b['setupPatience']=='strong' else 'balanced',
      'priorities':priorities,'principles':['retain_identity','respect_limits','adapt_to_revealed_evidence'],
      'behavior':{'aggression':b['aggression'],'riskTolerance':'weak' if b['caution']=='strong' else 'moderate','switchFlexibility':b['strategyFlexibility'],'resourceConservation':b['resourceConservation'],'setupPatience':b['setupPatience']},
      'assumptions':[{'kind':'UNKNOWN','basis':'unknown','confidence':'weak','evidenceRefs':[]}]}
    return validate(posture,packet)
