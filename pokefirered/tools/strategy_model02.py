#!/usr/bin/env python3
"""Explicit <=4 free text qualification requests; synthetic evidence only, no game store."""
import argparse,json,time,sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from strategy.provider import OpenRouterProvider,LiveBudget,Limits,preflight_text
from strategy.memo import validate_text
from strategy.diagnostics import failure_diagnostics
from roster.hashes import digest
E=ROOT/'evidence/phase3/strategy_model02';P=ROOT/'.local/strategy_model02';MODEL='google/gemma-4-31b-it:free'
class QualificationBudget(LiveBudget):
 def __init__(self,path):super().__init__(path,4)
def qualification_packet():
 packet=json.loads((ROOT/'evidence/phase6/campaign_expansion01_gate_repair/strategy-107-context.json').read_text())['modelInput']
 def fictional(value):
  if isinstance(value,dict):return {k:fictional(v) for k,v in value.items()}
  if isinstance(value,list):return [fictional(v) for v in value]
  if isinstance(value,str):return value.replace('trainer:fr:trainer:0107','fixture:trainer:avery').replace('fr:trainer:0107','fixture:avery').replace('JAMES','AVERY')
  return value
 packet=fictional(packet);packet['qualificationNotice']='Synthetic trainer Avery; no active campaign job. Retained public claims/legality shape exercise the existing prompt. Output is subjective strategy prose, never canon or a candidate selection.'
 return packet
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['smoke','fixture','close']);p.add_argument('--retry',action='store_true');p.add_argument('--candidate',choices=['primary','secondary'],default='primary');a=p.parse_args();E.mkdir(parents=True,exist_ok=True);P.mkdir(parents=True,exist_ok=True);ledger=E/'requests.json'
 model=MODEL if a.candidate=='primary' else 'qwen/qwen3.8-27b:free'
 label=('secondary-' if a.candidate=='secondary' else '')+a.command+('-retry' if a.retry else '')
 if a.candidate=='secondary':
  assert json.loads((E/'smoke.json').read_text())['status']=='blocked' and json.loads((E/'smoke-retry.json').read_text())['status']=='blocked'
 if a.retry:
  prior=json.loads((E/('smoke.json')).read_text());assert a.command=='smoke' and a.candidate=='primary' and prior['diagnostics']['retryable']
 with QualificationBudget(ledger) as budget:
  if not ledger.exists():
   value=budget.read();value['authorization']={'source':'3e7d2a32-5892-4d6d-b627-688a60baa67c','models':[MODEL,'qwen/qwen3.8-27b:free'],'maximumGenerationRequests':4,'scope':'Strategy smoke and synthetic memo only; secondary only after primary concrete disqualification'};budget.write(value)
  if a.command=='close':budget.close();print(json.dumps({'closed':True,'requests':len(budget.read()['attempts'])}));return
  if any(r['jobID']=='strategy-model02-'+label for r in budget.read()['attempts']):raise ValueError('qualification job already attempted; no automatic retry')
  if a.command=='fixture':
   smoke_path=E/('secondary-smoke.json' if a.candidate=='secondary' else 'smoke.json')
   smoke=json.loads(smoke_path.read_text())
   if smoke['status']!='accepted' and a.candidate=='primary':smoke=json.loads((E/'smoke-retry.json').read_text())
   assert smoke['status']=='accepted'
 # Only use existing credential loader; explicit candidate binding, never echo credentials.
 from strategy.provider import live_configuration
 _,key=live_configuration();binding={'provider':'openrouter_chat','model':model,'adapterVersion':6}
 job='strategy-model02-'+label;route=preflight_text(model);(E/(label+'-route.json')).write_text(json.dumps(route,indent=2)+'\n');provider=OpenRouterProvider(binding,key,route,ledger,job,budget_class=QualificationBudget,system_prompt=(ROOT/'prompts/strategy_scouting_v3.txt').read_text());start=time.monotonic()
 try:
  if a.command=='smoke':text,diagnostics=provider.smoke(Limits(attempts=1,output_tokens=128))
  else:
   packet=qualification_packet()
   (E/'synthetic-context.json').write_text(json.dumps(packet,indent=2)+'\n');body,encoded=provider.prepare_request(packet,None,Limits(attempts=1),text=True);assert not {'tools','tool_choice','response_format'}&body.keys();(E/'synthetic-request.json').write_text(json.dumps(body,indent=2)+'\n')
   text,diagnostics=provider.complete(packet,Limits(attempts=1));diagnostics['serializedBytes']=len(encoded)
  validate_text(text)
  result={'status':'accepted','jobID':job,'binding':binding,'strategyText':text,'diagnostics':diagnostics,'storageValidator':'strategy.memo.validate_text; exact validator called by MemoStore.finish_memo','campaignCommitted':False,'textSHA256':digest(text),'recordedAtUnix':time.time()}
 except Exception as error:result={'status':'blocked','jobID':job,'binding':binding,'diagnostics':failure_diagnostics(error,job=job,binding=binding,stage='qualification',elapsed=round(time.monotonic()-start,6)),'campaignCommitted':False}
 (E/(label+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
