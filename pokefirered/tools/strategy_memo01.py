#!/usr/bin/env python3
"""Explicit text acceptance only; one smoke plus one legitimate memo, no auto retry."""
import sys,os,json,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['POKEINFLUENCER_STRATEGY_MEMO_ACCEPTANCE']='1'
from strategy01 import E,PRIVATE,open_store
from strategy.provider import live_configuration,preflight_text,OpenRouterProvider,LiveBudget,Limits,ProviderError
from strategy.memo import run_memo_job,validate_text
RICK='trainer:fr:trainer:0102'
def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['smoke','generate','replay','close-budget']);p.add_argument('--model-role',default='primary',choices=['primary','backup','backup_backup']);a=p.parse_args()
    E.mkdir(parents=True,exist_ok=True);PRIVATE.mkdir(parents=True,exist_ok=True);budget=PRIVATE/'live-budget.json'
    if a.command=='close-budget':
        with LiveBudget(budget,2) as b:b.close();r=b.read()
        (E/'closed-budget.json').write_text(json.dumps(r,indent=2)+'\n');return
    if a.command=='replay':
        with open_store(PRIVATE/'world.sqlite3') as w:r={'records':w.memo_records(),'stateSHA256':w.verify_strategy_replay(),'modelRequests':0}
    else:
        binding,key=live_configuration(a.model_role);binding['adapterVersion']=7
        if a.command=='generate':
            smoke=json.loads((E/'smoke.json').read_text())
            if smoke.get('status')!='accepted' or smoke['binding']!=binding:raise ValueError('matching successful smoke required')
        try:route=preflight_text(binding['model'])
        except (ValueError,OSError) as err:
            r={'status':'blocked','binding':binding,'reason':str(err) if isinstance(err,ProviderError) else type(err).__name__,'modelRequests':0}
            (E/(a.command+'.json')).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));return
        (E/(a.command+'-preflight.json')).write_text(json.dumps({'binding':binding,'route':route},indent=2)+'\n')
        if a.command=='smoke':
            with LiveBudget(budget,2) as b:
                if b.read()['attempts'] or b.read()['closed']:raise ValueError('smoke already attempted or window closed')
                b.write(b.read())
            try:
                text,d=OpenRouterProvider(binding,key,route,budget,'memo-smoke-v1').smoke(Limits(attempts=1,output_tokens=128))
                validate_text(text);r={'status':'accepted','binding':binding,'text':text,'diagnostics':d}
            except (ValueError,OSError) as err:r={'status':'blocked','binding':binding,'reason':str(err) if isinstance(err,ProviderError) else type(err).__name__}
        else:
            with open_store(PRIVATE/'world.sqlite3') as w:
                job=w.begin_strategy(RICK,purpose='preparation-live-acceptance',provider_binding=binding)
                (E/'rick-context.json').write_text(json.dumps(job,indent=2)+'\n')
                r=run_memo_job(w,job,OpenRouterProvider(binding,key,route,budget,job.get('jobID','recorded')),source='model')
    (E/(a.command+'.json')).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
