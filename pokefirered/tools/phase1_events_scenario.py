#!/usr/bin/env python3
"""Replay bounded normal-input segments; wait for real frame-queue completion."""
import argparse
from contextlib import contextmanager
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
LOG=ROOT/'evidence/phase1/bridge02/emulator.jsonl'

@contextmanager
def task_lock(path=None):
    path=path or ROOT/'.local/phase1-events-gameplay.lock'
    with path.open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Another gameplay scenario is running; wait for completion')
        try:yield
        finally:fcntl.flock(lock,fcntl.LOCK_UN)

def segment(name,commands,timeout=60):
    offset=LOG.stat().st_size if LOG.exists() else 0
    subprocess.run([sys.executable,str(ROOT/'tools/phase1_events_input.py'),*commands,'shot '+name],check=True,cwd=ROOT)
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        with LOG.open() as f:f.seek(offset);lines=f.read().splitlines()
        for line in lines:
            try:r=json.loads(line)
            except json.JSONDecodeError:continue
            if r.get('event')=='sample' and r.get('detail','').startswith(name+' '):
                print(json.dumps({'segment':name,'completedFrame':r['frame'],'sample':r['detail']}),flush=True)
                return r
        time.sleep(.1)
    raise TimeoutError('No completed screenshot/sample for '+name)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('commands',nargs='*');p.add_argument('--timeout',type=float,default=60);a=p.parse_args()
    with task_lock():segment(a.name,a.commands,a.timeout)
