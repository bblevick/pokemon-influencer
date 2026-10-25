#!/usr/bin/env python3
"""Pure production request preparation using recorded GET metadata; no network."""
import json,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from campaign.expansion import ExpansionStore
from strategy.provider import OpenRouterProvider,Limits
from roster.hashes import digest
E=ROOT/'evidence/phase6/campaign_expansion01_gate_repair';OLD=ROOT/'evidence/phase6/campaign_expansion01'
def main():
 route=json.loads((E/'current-strategy-route.json').read_text());route['checkedAtUnix']=time.time();binding={'provider':'openrouter_chat','model':route['model'],'adapterVersion':6}
 provider=OpenRouterProvider(binding,'unused-offline',route,None,None,system_prompt=(ROOT/'prompts/strategy_scouting_v3.txt').read_text())
 historic={x['actor']:x['context'] for x in map(json.loads,(OLD/'causal-trace.jsonl').read_text().splitlines()) if x['event']=='trainer-context'};out={};contexts={}
 with ExpansionStore(ROOT/'.local/campaign_expansion01_gate_repair/world.sqlite3',OLD/'manifest-native.json') as w:
  for i in [117,106,107,108]:
   actor='trainer:fr:trainer:%04d'%i
   if actor in historic:context=historic[actor];source='immutable historical production context; opportunity consumed'
   else:context=w.context_packet(actor,'first',provider_binding=binding);source='current isolated C1 production context; future natural eligibility not battle completion'
   body,encoded=provider.prepare_request(context['modelInput'],None,Limits(attempts=1),text=True)
   assert not {'tools','tool_choice','response_format'}&body.keys();facts=context['modelInput']['authorizedSocialEvidence']['authorizedFacts'];assert all(f['mode']=='delivered' for f in facts)
   assert not context['modelInput']['privateEpisodes'];assert context['modelInput']['opponentCurrentLead']=='UNKNOWN'
   (E/f'strategy-{i}-request.json').write_text(json.dumps(body,indent=2)+'\n');(E/f'strategy-{i}-context.json').write_text(json.dumps(context,indent=2)+'\n');contexts[str(i)]=context
   out[str(i)]={'contextID':context['contextID'],'source':source,'requestSHA256':digest(body),'encodedBytes':len(encoded),'authorizedFacts':len(facts),'opponentCurrentLead':'UNKNOWN','existingLock':bool(w.locked_preparation(actor)),'privateEpisodesExcluded':True,'providerRequestShape':'ordinary text; metadata snapshot is not future availability guarantee'}
  (E/'offline-preflight.json').write_text(json.dumps(out,indent=2)+'\n')
 def compare(a,b,path=''):
  if isinstance(a,dict) and isinstance(b,dict):
   return sum((compare(a.get(k),b.get(k),path+'/'+k) for k in sorted(set(a)|set(b))),[])
  if a==b:return []
  return [{'path':path,'sally':a,'greg':b}]
 (E/'sally-greg-diff.json').write_text(json.dumps(compare(contexts['117'],contexts['106']),indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
