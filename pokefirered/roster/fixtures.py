"""Explicit hypothetical trusted snapshots, never active campaign grants."""
from dataclasses import replace
from copy import deepcopy
from .domain import Scope,Context,Companion,Step
RICK='trainer:fr:trainer:0102'
def baseline(cat,actor=RICK,variant=102):
    return tuple(Companion(f'{actor}:baseline:{variant}:{p["slot"]}',actor,p['baselineKey'],'baseline',p['level'],p['species'],p['level'],tuple(p['moves']),held_item=p['heldItem']) for p in cat.own_baseline(actor,variant)['party'])
def context(cat,**kw):
    data=dict(scope=Scope('fixture-campaign','fixture-branch',RICK,0,0),companions=baseline(cat),milestones=frozenset(),earned_epochs=(),applied_epochs=(),inventory=(),permissions=frozenset(),fixture=True,acquisitions=0,opportunity_acquisitions=0)
    data.update(kw);return Context(**data)
def policy(base,cat,target=14,cap=14,stage="boulder"):
    p=deepcopy(base);p['fixtureOnly']=True;p['fixtureExplanation']='Unbound CONTENT-01 fields supplied for host qualification only; not approved campaign grants.'
    p['actors'][RICK]['stages']=[{'requires':['badge.'+stage],'target':target,'cap':cap}]
    p['actors'][RICK]['signatureLineages']=[f'{RICK}:baseline:102:1']
    return p
def butterfly(cat,level=13):
    c=baseline(cat)[1];s=cat.constants
    steps=[Step('level',s['SPECIES_CATERPIE'],7),Step('evolution',s['SPECIES_METAPOD'],7),Step('level',s['SPECIES_METAPOD'],10),Step('evolution',s['SPECIES_BUTTERFREE'],10),Step('level_move',s['SPECIES_BUTTERFREE'],10,s['MOVE_CONFUSION'],2)]
    if level>10:steps.append(Step('level',s['SPECIES_BUTTERFREE'],level))
    return replace(c,species=s['SPECIES_BUTTERFREE'],level=level,moves=(s['MOVE_TACKLE'],s['MOVE_STRING_SHOT'],s['MOVE_CONFUSION'],0),history=tuple(steps))
