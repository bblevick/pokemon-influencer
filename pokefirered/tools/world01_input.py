#!/usr/bin/env python3
"""B3 bounded native-input driver with independent WORLD evidence destinations."""
import argparse
import phase1_ui_input as retained
from world01 import ROOT,E
retained.E=E
# Keep the tested lock/transport/ambiguous-mutation rule unchanged.
send=retained.send
import time,json
def segment(label,commands):
 send(*commands,'shot '+label);deadline=time.monotonic()+40
 path=ROOT/'evidence/private/world01'/f'{label}.png'
 while time.monotonic()<deadline:
  with (E/'emulator.jsonl').open() as f:f.seek(retained._shots[label]);lines=f.read().splitlines()
  if path.exists() and any(json.loads(x).get('event')=='sample' and json.loads(x).get('detail','').startswith(label+' ') for x in lines):return path
  time.sleep(.1)
 raise TimeoutError(label)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('commands',nargs='+');a=p.parse_args();print(segment(a.label,a.commands))
