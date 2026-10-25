#!/usr/bin/env python3
"""Explicit scoped Strategy CLI; normal host remains offline, no automatic jobs."""
import sys,json,argparse,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from strategy.store import StrategyStore
from strategy.context import build_context
from strategy.domain import fallback
from strategy.runtime import run_job
from strategy.provider import live_configuration,preflight,OpenRouterProvider,LiveBudget,ProviderError
from pokebook01 import manifest,save_identity
MEMO=os.environ.get('POKEINFLUENCER_STRATEGY_MEMO_ACCEPTANCE')=='1'
CLOSEOUT=os.environ.get('POKEINFLUENCER_STRATEGY_CLOSEOUT')=='1'
BACKUP=os.environ.get('POKEINFLUENCER_STRATEGY_BACKUP_ACCEPTANCE')=='1'
if sum((CLOSEOUT,BACKUP,MEMO))>1:raise ValueError('choose one Strategy acceptance namespace')
E=ROOT/('evidence/phase3/strategy01/memo' if MEMO else 'evidence/phase3/strategy01/backup' if BACKUP else 'evidence/phase3/strategy01/closeout' if CLOSEOUT else 'evidence/phase3/strategy01')
PRIVATE=ROOT/('.local/strategy01-memo' if MEMO else '.local/strategy01-backup' if BACKUP else '.local/strategy01-closeout' if CLOSEOUT else '.local/strategy01')
CONFIG=ROOT/('.local/strategy01-memo-launch.json' if MEMO else '.local/strategy01-backup-launch.json' if BACKUP else '.local/strategy01-closeout-launch.json' if CLOSEOUT else '.local/strategy01-launch.json')
SCREENS=ROOT/('evidence/private/strategy01-memo' if MEMO else 'evidence/private/strategy01-backup' if BACKUP else 'evidence/private/strategy01-closeout' if CLOSEOUT else 'evidence/private/strategy01')
def open_store(path):
 from strategy.memo import MemoStore
 m=manifest();return (MemoStore if MEMO else StrategyStore)(path,m['rom_sha256'],m['build_tag'])

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['context','generate','replay','preflight','close-budget']);p.add_argument('--database',default=str(PRIVATE/'world.sqlite3'));p.add_argument('--actor',default='trainer:fr:trainer:0102');p.add_argument('--stage',default='forest-post-boulder-1');p.add_argument('--purpose',choices=['preparation','battle-only-fixture','preparation-live-acceptance'],default='preparation');p.add_argument('--live',action='store_true');p.add_argument('--model-role',choices=['primary','backup','backup_backup','emergency'],default='primary');p.add_argument('--out',type=Path);a=p.parse_args();budget=PRIVATE/'live-budget.json'
 if a.command=='close-budget':
  with LiveBudget(budget) as b:b.close();r=b.read()
 elif a.command=='preflight':
  binding,key=live_configuration(a.model_role)
  try:r={'status':'qualified','binding':binding,'route':preflight(binding['model'])}
  except ProviderError as e:r={'status':'blocked','binding':binding,'reason':str(e)}
 elif a.command in ('context','replay'):
  # Replay never reads credentials or calls a provider; model binding supplied
  # by the immutable active record, not current hosted defaults.
  with open_store(a.database) as w:
   if a.command=='context':r=build_context(w,a.actor,a.stage,a.purpose)
   else:
    records=[r for r in w.strategy_state()['postures'].values() if r['actor']==a.actor]
    r={'stateSHA256':w.verify_strategy_replay(),'records':records,'modelRequests':0}
 else:
  raise ValueError('Structured Strategy generation retired by D32; use tools/strategy_memo01.py')
  binding=None;key=None;route=None;blocked=None
  if a.live:
   try:
    binding,key=live_configuration(a.model_role);route=preflight(binding['model'])
   except ProviderError as e:blocked=str(e)
  with open_store(a.database) as w:
   job=w.begin_strategy(a.actor,a.stage,a.purpose,provider_binding=binding)
   if job['status']=='recorded':r=job['decision']
   elif route:
    r=run_job(w,job,OpenRouterProvider(binding,key,route,budget,job['jobID']),source='model')
   else:r=w.finish_strategy(job['jobID'],fallback(job['packet']),'fallback',{'provider':'template','model':'strategy-fallback-v1','costUSD':0,'failure':blocked or 'offline_default','modelRequests':0},job['packet']['contextID'])
 if a.out:a.out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r,indent=2))
if __name__=='__main__':main()
