#!/usr/bin/env python3
"""Live catalog-selected qualification, bounded ledger; no active game store access."""
import sys,json,time,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from strategy.provider import LiveBudget,OpenRouterProvider,Limits,live_configuration,preflight_text
from strategy.diagnostics import failure_diagnostics
from strategy.memo import validate_text
from roster.hashes import digest
from strategy_model02 import qualification_packet
E=ROOT/'evidence/phase3/strategy_model03'
class Budget(LiveBudget):
 def __init__(self,path):super().__init__(path,6)
 def charge(self,job,model):
  if sum(a['requestedModel']==model for a in self.read()['attempts'])>=2:raise ValueError('two requests per selected model maximum')
  return super().charge(job,model)
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['smoke','fixture','close']);a=p.parse_args();model=json.loads((E/'ranking.json').read_text())['selected'];ledger=E/'requests.json';label=('contingency-' if json.loads((E/'ranking.json').read_text()).get('previousSelectedSecondary') else '')+a.command;job='strategy-model03-'+label
 with Budget(ledger) as b:
  if not ledger.exists():
   v=b.read();v['authorization']={'source':'f63d85f4-520a-47f1-a021-ed97428a4395','maximumRequests':6,'maximumCandidateModels':3,'maximumRequestsPerModel':2,'scope':'metadata-qualified preferred Ling/LingFin or one ranked explicit free contingency; no campaign/Mercury/Hermes'};b.write(v)
  if a.command=='close':b.close();print(json.dumps({'closed':True,'requests':len(b.read()['attempts'])}));return
  if any(r['jobID']==job for r in b.read()['attempts']):raise ValueError('qualification job already attempted')
 if a.command=='fixture':assert json.loads((E/(label.replace('fixture','smoke')+'.json')).read_text())['status']=='accepted'
 _,key=live_configuration();binding={'provider':'openrouter_chat','model':model,'adapterVersion':6};start=time.monotonic()
 try:
  route=preflight_text(model);(E/(label+'-route.json')).write_text(json.dumps(route,indent=2)+'\n');provider=OpenRouterProvider(binding,key,route,ledger,job,budget_class=Budget,system_prompt=(ROOT/'prompts/strategy_scouting_v3.txt').read_text())
  if a.command=='smoke':text,diagnostics=provider.smoke(Limits(attempts=1,output_tokens=128))
  else:
   packet=qualification_packet();body,encoded=provider.prepare_request(packet,None,Limits(attempts=1),text=True);assert not {'tools','tool_choice','response_format'}&body.keys();(E/'synthetic-context.json').write_text(json.dumps(packet,indent=2)+'\n');(E/'synthetic-request.json').write_text(json.dumps(body,indent=2)+'\n')
   text,diagnostics=provider.complete(packet,Limits(attempts=1));diagnostics['serializedBytes']=len(encoded)
  validate_text(text);result={'status':'accepted','binding':binding,'jobID':job,'strategyText':text,'diagnostics':diagnostics,'textSHA256':digest(text),'promptVersion':3 if a.command=='fixture' else 'transport-smoke','recordedAtUnix':time.time(),'syntheticOnly':True,'campaignCommitted':False,'storageValidator':'strategy.memo.validate_text; exact MemoStore.finish_memo text validator'}
 except Exception as error:result={'status':'blocked','binding':binding,'jobID':job,'diagnostics':failure_diagnostics(error,job=job,binding=binding,stage=a.command,elapsed=round(time.monotonic()-start,6)),'campaignCommitted':False}
 (E/(label+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
