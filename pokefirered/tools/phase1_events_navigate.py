#!/usr/bin/env python3
"""Test-only source-map route planner. Issues normal buttons; no RAM writes.
Stops after one straight segment. Obstacles/NPCs/scripts/encounters need review.
Never used to construct NPC observations.
"""
import argparse, heapq, json, re, struct, subprocess, sys
from pathlib import Path
from phase1_events_scenario import segment
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('map');p.add_argument('x',type=int);p.add_argument('y',type=int);p.add_argument('--label',required=True);a=p.parse_args()
subprocess.run([sys.executable,'tools/phase1_events_input.py','sample'],cwd=ROOT,check=True)
rows=[json.loads(x) for x in (ROOT/'evidence/phase1/bridge02/emulator.jsonl').read_text().splitlines()]
s=next(r['detail'] for r in reversed(rows) if r['event']=='persist')
v={k:int(n) for k,n in re.findall(r'(\w+)=(\d+)',s)}
nonce=json.loads((ROOT/'.local/phase1-events-launch.json').read_text())['nonce']
records=[json.loads(x) for x in (ROOT/'evidence/phase1/bridge02/events.jsonl').read_text().splitlines()]
records=[x for x in records if x['session']==nonce]
starts=[x for x in records if x['eventType']=='BATTLE_STARTED']
if starts:
 b=starts[-1];assert any(x['eventType']=='BATTLE_ENDED' and (x['run'],x['battleID'])==(b['run'],b['battleID']) for x in records),'Active recorded battle; finish it before source-map routing'
mapdef=json.loads((ROOT/'data/maps'/a.map/'map.json').read_text())
constants=(ROOT/'include/constants/map_groups.h').read_text()
m=re.search(r'#define '+mapdef['id']+r'\s+\((\d+) \| \((\d+) << 8\)\)',constants)
assert m and (v['mapnum'],v['mapgroup'])==tuple(map(int,m.groups())),s
layout=next(x for x in json.loads((ROOT/'data/layouts/layouts.json').read_text())['layouts'] if x.get('id')==mapdef['layout'])
w,h=layout['width'],layout['height'];tiles=struct.unpack('<'+str(w*h)+'H',(ROOT/layout['blockdata_filepath']).read_bytes())
start=(v['x'],v['y']);end=(a.x,a.y);todo=[(0,start)];cost={start:0};prev={}
while todo:
 c,q=heapq.heappop(todo)
 if q==end:break
 if c!=cost[q]:continue
 for dx,dy,key in [(1,0,4),(-1,0,5),(0,-1,6),(0,1,7)]:
  n=q[0]+dx,q[1]+dy
  if not(0<=n[0]<w and 0<=n[1]<h):continue
  tile=tiles[n[1]*w+n[0]]
  if (tile>>10)&3:continue
  d=c+(10 if tile&1023==13 else 1)
  if d<cost.get(n,10**9):cost[n]=d;prev[n]=(q,key);heapq.heappush(todo,(d,n))
assert end in cost,'no static route'
keys=[];q=end
while q!=start:q,k=prev[q];keys.append(k)
keys.reverse()
if not keys:print('target reached');sys.exit()
k=keys[0];count=next((i for i,x in enumerate(keys) if x!=k),len(keys));count=min(count,10)
print(json.dumps({'map':a.map,'start':start,'target':end,'straightTiles':count,'key':k}),flush=True)
segment(a.label,[f'key {k} {count*16} 180'])
subprocess.run([sys.executable,'tools/phase1_events_input.py','sample'],cwd=ROOT,check=True)
