#!/usr/bin/env python3
"""Public exact-model route qualification; optional one tiny native smoke call."""
import sys,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from battle.live import E,PRIVATE,ROUTE,LEDGER,BattleBudget
from system1.provider import configuration,preflight,NativeDecisionProvider

def refresh():
 binding,key=configuration();route=preflight(binding['model']);p=ROUTE.with_suffix('.tmp');p.write_text(json.dumps(route,indent=2)+'\n');os.replace(p,ROUTE)
 (E/'preflight.json').write_text(json.dumps({'binding':binding,**route},indent=2)+'\n');return binding,key,route
if __name__=='__main__':
 binding,key,route=refresh();print(json.dumps({'model':binding['model'],'freeRoutes':len(route['endpoints']),'api':route['api']}))
 if '--smoke' in sys.argv:
  p=NativeDecisionProvider(binding,key,route,LEDGER,'synthetic-smoke-semantic-substitute',request_seconds=5,budget_class=BattleBudget)
  state='Fictional trainer wants Sleep Powder and patient status pressure, but Sleep Powder is unavailable. Only the supplied actions are legal. There is no private opponent information.'
  choices={'slow':'Use available String Shot to lower opponent Speed.','strike':'Use available Tackle for direct pressure.'}
  r=p.decide(state,'Choose one supplied legal action that best approximates the subjective intent. Impossible wishes grant no action. Do not explain, escalate or resample.',choices)
  (E/'smoke.json').write_text(json.dumps({'state':state,'choices':choices,'result':r},indent=2)+'\n');print(json.dumps({'smoke':'valid','choice':r['choiceID'],'latencySeconds':r['diagnostics']['latencySeconds'],'costUSD':r['diagnostics']['costUSD']}))
