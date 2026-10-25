#!/usr/bin/env python3
"""Bounded test-only route segments; abort on unexpected map or no progress."""
import argparse,json,subprocess,sys
from phase1_events_scenario import task_lock
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('map');p.add_argument('x');p.add_argument('y');p.add_argument('--label',required=True);p.add_argument('--segments',type=int,default=12);a=p.parse_args();assert 1<=a.segments<=20
guard=task_lock();guard.__enter__()
last=None
for i in range(a.segments):
 r=subprocess.run([sys.executable,'tools/phase1_events_navigate.py',a.map,a.x,a.y,'--label',a.label+'-'+str(i)],cwd=ROOT,capture_output=True,text=True)
 print(r.stdout,flush=True)
 if r.returncode:print(r.stderr,file=sys.stderr);raise SystemExit(r.returncode)
 if 'target reached' in r.stdout:break
 rows=[json.loads(x) for x in (ROOT/'evidence/phase1/bridge02/emulator.jsonl').read_text().splitlines()]
 now=next(x['detail'] for x in reversed(rows) if x['event']=='persist').split(' x=')[-1]
 if now==last:raise SystemExit('No progress; review script/battle/NPC/warp')
 last=now

else:raise SystemExit("Route segment bound reached; inspect current state")
