#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import strategy01_transport_input as retained
retained.E=ROOT/'evidence/phase4/battle01'
if __name__=='__main__':
 import time
 commands=sys.argv[1:];log=retained.E/'emulator.jsonl';offset=log.stat().st_size;retained.send(*commands)
 for command in commands:
  if command.startswith('shot '):
   name=command[5:];deadline=time.monotonic()+55
   while True:
    with log.open() as f:f.seek(offset);text=f.read()
    if '\"detail\":\"'+name+' state=' in text:break
    if time.monotonic()>deadline:raise TimeoutError('native screenshot receipt '+name)
    time.sleep(.1)

