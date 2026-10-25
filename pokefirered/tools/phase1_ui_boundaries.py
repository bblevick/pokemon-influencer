#!/usr/bin/env python3
"""Live managed lifecycle tests; never repeat an ambiguous reset."""
import argparse,json,time,hashlib
from phase1_ui_input import send,wait_shot,ROOT,E
from phase1_ui_scenario import mode,records,scenario

def run(which,resume=False):
 mode('normal');start=len(records('ui-responses.jsonl'))
 if not resume:
  send('ui '+('1' if which=='rollback' else '2'),'key 9 0 180',f'shot {which}-pending')
  wait_shot(which+'-pending')
 trace=records('host.jsonl');command=[r for r in trace if r['event']=='ui-command'][-1]
 item={'scenario':which,'pending_command':command,'scope':'real final-ROM native UI + managed transient boundary; not durable save pairing'}
 if which=='rollback':
  send('checkpoint');cp=ROOT/'.local/phase1-ui-emulator/scenario-checkpoint.ss0'
  item['checkpoint']={'path':str(cp.relative_to(ROOT)),'sha256':hashlib.sha256(cp.read_bytes()).hexdigest()}
  send('key 0 8 30','shot rollback-old-ack');wait_shot('rollback-old-ack')
  send('reload','key 9 0 90','shot rollback-cleared','uisample','sample');wait_shot('rollback-cleared')
  scenario('after-rollback')
 else:
  if resume:item['reset_reply']='timeout; NOT retried';item['input_recovery']='initial new read-only socket reset; subsequent read-only sample succeeded'
  else:
   try:send('reset');item['reset_reply']='OK'
   except TimeoutError as e:item['reset_reply']='timeout; NOT retried';item['error']=str(e)
  # New read-only connection proves the native reset; queued shot shows title.
  send('sample','uisample','key 9 0 180','shot reset-cleared');wait_shot('reset-cleared')
  send('a 2','key 0 10 400','shot reset-continue');wait_shot('reset-continue')
  send('key 0 10 150','key 1 10 500','shot reset-field');wait_shot('reset-field')
  scenario('after-reset')
 item['responses_after_start']=records('ui-responses.jsonl')[start:]
 item['host_runs']=[r for r in records('host.jsonl') if r['event']=='hello']
 (E/(which+'-boundary.json')).write_text(json.dumps(item,indent=2)+'\n');print(json.dumps({'scenario':which,'reset_reply':item.get('reset_reply'),'completed':True}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('scenario',choices=['rollback','reset']);p.add_argument('--resume-reset',action='store_true');a=p.parse_args();assert not a.resume_reset or a.scenario=='reset';run(a.scenario,a.resume_reset)
