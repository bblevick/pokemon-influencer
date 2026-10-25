#!/usr/bin/env python3
"""Fresh main-thread HTTP worker; signal deadline, durable charge, no game tools."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from battle.live import BattleBudget,LEDGER,ROUTE
from system1.provider import NativeDecisionProvider,configuration
if __name__=='__main__':
 try:
  p=json.loads(sys.stdin.read(65537));binding,key=configuration();route=json.loads(ROUTE.read_text())
  provider=NativeDecisionProvider(binding,key,route,LEDGER,p['jobID'],request_seconds=2.35,budget_class=BattleBudget)
  result=provider.decide(p['state'],p['question'],p['choices']);print(json.dumps(result))
 except Exception as error:
  # Never print request headers, credentials, arbitrary HTTP transcripts or env.
  from battle.live import E
  reason=str(error) if type(error).__name__=='ProviderError' else type(error).__name__
  (E/'worker-last-error.json').write_text(json.dumps({'error':reason})+'\n')
  print(json.dumps({'error':reason}),file=sys.stderr);sys.exit(1)
