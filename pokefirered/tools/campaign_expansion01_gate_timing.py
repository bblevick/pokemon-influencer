#!/usr/bin/env python3
"""Disposable native timing trials. No generation, no completion automation."""
import sys,json,argparse,time,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from campaign_expansion01_gate_native import base
from campaign.transport import CampaignHandler
import strategy01_host as host
class DelayedProvider:
 def __init__(self,case,delay):self.case=case;self.delay=delay;self.stop=threading.Event();self.first=True;self.index=0
 def decide_scoped(self,packet):
  if self.case=='matrix':
   if packet['nativeState']['phase']!='NORMAL_TURN':return {'choiceID':next(iter(packet['choices']))}
   sequence=[('before',1),('just-before',2.65),('just-after',2.85),('well-after',4),('never',None)]
   if self.index>=len(sequence):return None
   case,delay=sequence[self.index];self.index+=1
  else:
   if not self.first:return None
   self.first=False;case,delay=self.case,self.delay
  started=time.monotonic()
  def log(event,**extra):
   with (base.E/'timing-provider.jsonl').open('a') as f:f.write(json.dumps({'case':case,'event':event,'scope':packet['scope'],'timeMonotonic':time.monotonic(),**extra})+'\n')
  log('deterministic-provider-start')
  if delay is None:
   self.stop.wait();log('never-provider-stopped');return None
  if self.stop.wait(delay):log('provider-stopped');return None
  log('deterministic-provider-result',elapsed=time.monotonic()-started)
  return {'choiceID':next(iter(packet['choices'])),'diagnostics':{'provider':'deterministic-delayed-fixture','case':case}}
def main():
 p=argparse.ArgumentParser();p.add_argument('--case',choices=['before','just-before','just-after','well-after','never','matrix'],required=True);p.add_argument('--seconds',type=float,default=600);a=p.parse_args()
 provider=DelayedProvider(a.case,{'before':1,'just-before':2.65,'just-after':2.85,'well-after':4,'never':None,'matrix':None}[a.case]);base.bind(host)
 handler=CampaignHandler(base.manifest(),base.E,provider=provider,decision_seconds=2.75)
 try:host.run(a.seconds,battle_handler=handler,services=type('NoGeneration',(),{'tick':lambda s,w:None,'close':lambda s,w:None})())
 finally:provider.stop.set();handler.close()
if __name__=='__main__':main()
