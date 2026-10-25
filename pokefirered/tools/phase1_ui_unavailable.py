#!/usr/bin/env python3
"""Live field progress with an absent, silent or disconnecting local host."""
import argparse,json,time,subprocess
from phase1_ui_input import send,wait_shot,ROOT,E
from phase1_ui_scenario import mode,records

def run(which):
 if which=='absent':
  ps=subprocess.check_output(['ps','-axo','pid,command'],text=True)
  processes=[s for s in ps.splitlines() if any(x.endswith('/python') or x.endswith('/python3') for x in s.split()[1:2]) and 'tools/phase1_ui_host.py' in s.split()]
  if processes:raise RuntimeError('Stop the fixture host before absent scenario')
 else:mode(which)
 start=len(records('host.jsonl'));start_emu=len(records('emulator.jsonl'));send('sample','uisample','ui 1','key 9 0 420',f'shot {which}-idle')
 wait_shot(which+'-idle')
 send('sample','uisample','key 4 8 8','key 4 16 30',f'shot {which}-moved');wait_shot(which+'-moved')
 send('sample','uisample','key 5 8 8','key 5 16 30',f'shot {which}-returned');wait_shot(which+'-returned');send('sample')
 report={'scenario':which,'scope':'real native input with no UI lock; transport terminal failures not canonical events','host_trace_since_start':records('host.jsonl')[start:],'emulator_trace_tail':records('emulator.jsonl')[start_emu:]}
 (E/(which+'-availability.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'scenario':which,'ran':True}))
 mode('normal')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('scenario',choices=['absent','timeout','disconnect','oversized-wire']);a=p.parse_args();run(a.scenario)
