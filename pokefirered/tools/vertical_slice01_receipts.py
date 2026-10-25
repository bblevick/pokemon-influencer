#!/usr/bin/env python3
"""Reconcile existing provider receipts into a CLOSED charged ledger.

No request or charge is created. An absent receipt remains unknown/charged.
Previously settled outcomes are immutable; use only hash/attempt-matched audits.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from campaign.provider import E,LEDGER
from campaign.budget import CampaignBudget

def main():
 proofs={}
 for path in sorted((E/'hermes-jobs').glob('*.json')):
  audit=json.loads(path.read_text())
  for req in audit.get('requests',[]):
   if req.get('liveAttempt') and isinstance(req.get('response'),dict):
    proofs[req['liveAttempt']]=(audit,req,path)
 recorded=[]
 with CampaignBudget(LEDGER) as budget:
  ledger=budget.read()
  if not ledger['closed']:raise ValueError('receipt reconciliation requires closed ledger')
  for row in ledger['attempts']:
   if row['outcome'] is not None:continue
   response=row.get('response') or {}
   usage=(response.get('result') or {}).get('usage') or response.get('usage')
   outcome=None
   if isinstance(usage,dict):
    outcome={'audit':'requests.json response for this same immutable charged attempt','httpResponse':response.get('httpStatus')==200,'usage':usage,'receiptReconciled':True}
   elif row['attempt'] in proofs:
    audit,req,path=proofs[row['attempt']]
    if req['sha256']!=row['requestHash'] or audit['jobID']!=row['jobID']:raise ValueError('mismatched Hermes receipt')
    usage=req['response'].get('usage')
    if isinstance(usage,dict):outcome={'audit':str(path.relative_to(E)),'httpResponse':True,'usage':usage,'producer':audit['outcome'].get('producer'),'failures':audit.get('failures',[]),'receiptReconciled':True}
   if outcome is not None:
    budget.finish(row['attempt'],outcome);recorded.append(row['attempt'])
  result={'chargedAttempts':len(ledger['attempts']),'closed':True,'newRequests':0,'reconciledExistingReceipts':recorded,'unknownAttempts':[a['attempt'] for a in budget.read()['attempts'] if a['outcome'] is None and not a.get('response')]}
 (E/'closeout-receipt-reconciliation.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result))

if __name__=='__main__':main()
