#!/usr/bin/env python3
"""Attach observed provider/native receipts to new charges; preserve original66."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT)]
from campaign.budget import CampaignBudget
E=ROOT/'evidence/phase4/vertical_slice01'
def main():
 old=json.loads((E/'final-original66.json').read_text())
 snapshots=[json.loads((E/(n+'.json')).read_text()) for n in ('final-a1-current','final-a2-loss','final-success')]
 winner=snapshots[-1]['campaign']['active_branch'];native=[r for d in snapshots for r in d['lifecycle']]
 job=next(json.loads(line)['result'] for line in reversed((E/'causal-trace.jsonl').read_text().splitlines()) if json.loads(line)['event']=='hermes-finished')
 reqs={r['liveAttempt']:r for r in job['requests']};receipts=[]
 with CampaignBudget(E/'requests.json') as budget:
  rows=budget.read()['attempts'][66:]
  for a in rows:
   if a['role']=='battle':
    r=a['response']['result'];terminal=next(n for n in native if n['session']==a['scope']['nonce'] and n['nativeRequest']==a['scope']['request'] and n['stage']=='EXECUTED')
    out={'httpStatus':a['response']['httpStatus'],'servingModel':r['model'],'provider':r['provider'],'usage':r['usage'],'choiceID':r['answers']['preparation']['choice'],'nativeDisposition':terminal['stage'],'nativeLifecycleID':terminal['lifecycleID'],'timelineDisposition':'winning_active' if a['scope']['branch']==winner else 'abandoned_player_loss','evidence':'provider response plus actual canonical-backed native lifecycle'}
   elif a['role']=='puppeteer':
    t=reqs[a['attempt']];assert t['sha256']==a['requestHash'];r=t['response']
    out={'servingModel':r['model'],'provider':r['provider'],'usage':r['usage'],'latencySeconds':t['latencySeconds'],'jobID':job['jobID'],'producer':job['outcome']['producer'],'postID':job['outcome']['postID'],'evidence':'actual pinned Hermes runtime hosted response and committed result'}
   else:raise AssertionError('unauthorized new role')
   assert out['usage']['cost']==0
   budget.finish(a['attempt'],out);receipts.append({'attempt':a['attempt'],'role':a['role'],**out})
  budget.close();ledger=budget.read();assert ledger['attempts'][:66]==old['attempts']
 out={'historicalRequests':len(ledger['attempts']),'original66Unchanged':True,'closed':ledger['closed'],'newBattleRequests':sum(a['role']=='battle' for a in rows),'newHermesRequests':sum(a['role']=='puppeteer' for a in rows),'newStrategyRequests':0,'newPreparationRequests':0,'newActualCostUSD':sum(a['usage']['cost'] for a in receipts),'receipts':receipts,'battleCallsRemaining':80-sum(a['role']=='battle' for a in rows),'hermesCallsRemaining':4-sum(a['role']=='puppeteer' for a in rows),'unusedAllowanceClosedAfterFirstSuccessfulBattle':True}
 (E/'final-accounting.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='receipts'}))
if __name__=='__main__':main()
