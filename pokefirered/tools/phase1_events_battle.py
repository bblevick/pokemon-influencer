#!/usr/bin/env python3
"""Bounded test player uses default Fight/Tackle by normal A input only.
Requires reviewed active encounter and default menus; not a game AI/provider.
RNG, animations and idle time mean this is a scenario helper, not golden path.
"""
import argparse,json
from pathlib import Path
from phase1_events_scenario import segment,task_lock
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('--steps',type=int,default=30);a=p.parse_args();assert 1<=a.steps<=40
guard=task_lock();guard.__enter__()
log=ROOT/'evidence/phase1/bridge02/events.jsonl'
rows=[json.loads(x) for x in log.read_text().splitlines()]
start=next(x for x in reversed(rows) if x['eventType']=='BATTLE_STARTED');identity=start['session'],start['run'],start['battleID']
for i in range(a.steps):
 rows=[json.loads(x) for x in log.read_text().splitlines()]
 ends=[x for x in rows if (x['session'],x['run'],x['battleID'])==identity and x['eventType']=='BATTLE_ENDED']
 if ends:print(json.dumps({'completed':True,'identity':identity,'end':ends[-1]}));break
 segment(a.label+'-'+str(i),['key 0 90 180'])
else:raise SystemExit('No accepted battle end within input bound; review live state/failure')
