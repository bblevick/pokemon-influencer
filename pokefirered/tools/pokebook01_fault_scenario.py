#!/usr/bin/env python3
"""Sequential native presentation faults with no campaign mutation or inference."""
import argparse,json,subprocess,sys,time
from pokebook01 import ROOT,E
from pokebook01_input import segment
from pokebook01_viewer_scenario import open_view

def run(modes):
 results=[]
 for mode in modes:
  peer=None
  try:
   if mode!='absent':
    log=(E/('fault-'+mode+'.log')).open('w')
    peer=subprocess.Popen([sys.executable,'tools/pokebook01_fault_host.py',mode,'--seconds','40'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    time.sleep(.4)
   if mode=='late':
    segment('fault-late-loading',['key 3 8 45','key 0 8 40'])
    segment('fault-late-cancelled',['key 1 8 120'])
    segment('fault-late-field',['key 1 8 90'])
   else:
    open_view('fault-'+mode+'-home',7)
    if mode=='control':
     segment('fault-control-feed',['key 0 8 120'])
     segment('fault-control-reader',['key 0 8 240'])
    else:segment('fault-'+mode+'-result',['key 9 0 240'])
    segment('fault-'+mode+'-field',['key 1 8 90']*(4 if mode=='control' else 2))
   results.append({'mode':mode,'nativeExecuted':True,'peerExitAtEnd':peer.poll() if peer else None})
  finally:
   if peer and peer.poll() is None:peer.terminate();peer.wait(timeout=3)
   if peer:log.close()
 (E/'native-fault-scenarios.json').write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('modes',nargs='+',choices=['absent','oversized','silent','disconnect','late','schema','malformed','control','stale-view','stale-nonce','missing']);a=p.parse_args();run(a.modes)
