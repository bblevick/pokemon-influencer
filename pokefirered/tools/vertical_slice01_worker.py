#!/usr/bin/env python3
"""Fresh bounded HTTP-only worker. No DB, ROM, tool or conversation access."""
import sys,json,re,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from campaign.provider import LEDGER,BattleBudget,StrategyBudget,scoped_battle_budget
from system1.provider import NativeDecisionProvider,configuration
from strategy.provider import OpenRouterProvider,Limits
from campaign.context import PROMPT

def main():
 p=json.loads(sys.stdin.read(65537));role=sys.argv[1]
 if role=='battle':
  binding,key=configuration();provider=NativeDecisionProvider(binding,key,p['route'],LEDGER,p['jobID'],request_seconds=2.35,budget_class=scoped_battle_budget(p['auditScope']) if p.get('auditScope') else BattleBudget)
  result=provider.decide(p['state'],p['question'],p['choices'])
 elif role=='strategy':
  from strategy.provider import live_configuration as strategy_configuration
  binding,key=strategy_configuration()
  provider=OpenRouterProvider(binding,key,p['route'],LEDGER,p['jobID'],budget_class=StrategyBudget,system_prompt=PROMPT.read_text())
  text,diagnostics=provider.complete(p['modelInput'],Limits(attempts=1));result={'strategyText':text,'diagnostics':diagnostics}
 else:raise ValueError('unknown role')
 print(json.dumps(result))
if __name__=='__main__':
 try:main()
 except Exception as error:
  # Only symbolic adapter/validation codes: never echo provider prose or keys.
  code=str(error)
  detail={'error':type(error).__name__,'code':code if re.fullmatch(r'[a-z][a-z0-9_]{0,95}',code) else 'unspecified','role':sys.argv[1],'time':time.time()}
  from strategy.diagnostics import failure_diagnostics
  detail['diagnostics']=failure_diagnostics(error,stage='worker')
  from campaign.provider import E
  with (E/'worker-errors.jsonl').open('a') as f:f.write(json.dumps(detail)+'\n')
  print(json.dumps(detail),file=sys.stderr);sys.exit(1)
