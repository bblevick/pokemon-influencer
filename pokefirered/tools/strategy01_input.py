#!/usr/bin/env python3
"""B3 bounded native-input driver with independent Strategy evidence destinations."""
import argparse
import strategy01_transport_input as retained
from strategy01 import PRIVATE,CONFIG,SCREENS,ROOT,E
retained.E=E
# Keep the tested lock/transport/ambiguous-mutation rule unchanged.
send=retained.send
import time,json,re
def segment(label,commands):
 if not re.fullmatch('[a-z0-9-]{1,48}',label):raise ValueError('native screenshot label must be lowercase, bounded and path-free')
 send(*commands,'shot '+label);deadline=time.monotonic()+40
 path=SCREENS/f'{label}.png'
 while time.monotonic()<deadline:
  with (E/'emulator.jsonl').open() as f:f.seek(retained._shots[label]);lines=f.read().splitlines()
  if path.exists() and any(json.loads(x).get('event')=='sample' and json.loads(x).get('detail','').startswith(label+' ') for x in lines):return path
  time.sleep(.1)
 raise TimeoutError(label)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('commands',nargs='+');a=p.parse_args();print(segment(a.label,a.commands))
