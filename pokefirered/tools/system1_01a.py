#!/usr/bin/env python3
"""Explicit bounded native selection acceptance. Does not install a native team."""
import sys,json,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from system1.provider import configuration,preflight,NativeDecisionProvider,Budget,run_selection
from system1.store import PreparationDecisionStore
BUILD=json.loads((ROOT/'config/prep_save_layout.json').read_text())['romSHA256']
TAG=json.loads((ROOT/'evidence/phase2/pokebook01/manifest-enabled.json').read_text())['build_tag']
RICK='trainer:fr:trainer:0102'
E=ROOT/'evidence/phase3/system1_01a';PRIVATE=ROOT/'.local/system1_01a';BUDGET=PRIVATE/'live-budget.json'
def write(name,value):
    (E/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['smoke','select','commit','replay','close-budget']);a=p.parse_args()
    if a.command=='close-budget':
        with Budget(BUDGET) as b:b.close();write('closed-budget',b.read())
        return
    if a.command=='select':
        with PreparationDecisionStore(PRIVATE/'world.sqlite3',BUILD,TAG) as w:
            previous=w.begin_selection(RICK)
            if previous['status']!='active':
                write('selection-reuse',previous);print('Recorded preparation reused; no credentials or provider call.');return
    if a.command in ('smoke','select'):
        binding,key=configuration();route=preflight(binding['model']);write(a.command+'-preflight',{'binding':binding,'route':route})
        if a.command=='smoke':
            with Budget(BUDGET) as b:
                if b.read()['attempts'] or b.read()['closed']:raise ValueError('smoke already attempted or budget closed')
            result=NativeDecisionProvider(binding,key,route,BUDGET,'system1-smoke-v1').decide('A synthetic test. Choose the only option described as preserving the original partner.','Choose the original partner.',{'retain':'Retains original partner.','replace':'Replaces original partner.'})
            if result['choiceID']!='retain':raise ValueError('smoke task failed')
            write('smoke',{'status':'accepted','binding':binding,'result':result});print('Native smoke accepted.');return
        smoke=json.loads((E/'smoke.json').read_text())
        if smoke['status']!='accepted' or smoke['binding']!=binding:raise ValueError('matching native smoke required')
    with PreparationDecisionStore(PRIVATE/'world.sqlite3',BUILD,TAG) as w:
        if a.command=='select':
            job=w.begin_selection(RICK);write('rick-request',job);before=w.preparation_state();r=run_selection(w,job,NativeDecisionProvider(binding,key,route,BUDGET,job['request']['requestID']));write('selection',r);write('selection-purity',{'trainerStateUnchanged':before==w.preparation_state(),'nativeInstalled':False});print('Selection source:',r['source'],'choice:',r['result']['choiceID'])
        elif a.command=='commit':
            d=json.loads((E/'selection.json').read_text())
            if d['source']!='model':raise ValueError('actual model selection required for live commitment acceptance')
            r=w.commit_preparation(d['decisionID']);write('commitment',r);print('Host commitment locked. Native installation remains unrun.')
        else:
            c=w.locked_preparation(RICK);r={'stateSHA256':w.verify_decision_replay(),'lockedPreparation':c,'modelRequests':0,'nativeInstalled':False};write('host-replay',r);print('Exact durable host commitment:',bool(c))
if __name__=='__main__':main()
