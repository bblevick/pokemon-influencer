#!/usr/bin/env python3
"""Pinned collision walking; bounded normal Run for incidental wild battles only."""
import json,sys,argparse,time
import rival01 as generic
import vertical_slice01_input as inp
import prep01_route as route
generic.bind(inp);generic.bind(inp.driver);inp.driver.retained.E=generic.E
route.segment=inp.segment;route.E=generic.E;route.open_store=generic.open_store
p=argparse.ArgumentParser();p.add_argument('map');p.add_argument('x',type=int);p.add_argument('y',type=int);p.add_argument('--label',required=True);a=p.parse_args();history=[]
for n in range(16):
 out=route.walk(a.map,(a.x,a.y),a.label+'-'+str(n),config_path=generic.PRIVATE/'launch.json');history.append(out)
 if out['status']=='blocked-native':
  inp.segment(f'{a.label}-transition-review-{n}',['key 9 0 120'])
  with generic.open_store(generic.PRIVATE/'world.sqlite3') as w:
   if any(not b['ended'] for b in w.state()['battles'].values()):out['status']='battle'
 if out['status']!='battle':break
 with generic.open_store(generic.PRIVATE/'world.sqlite3') as w:
  active=[b for b in w.state()['battles'].values() if not b['ended']]
  if len(active)!=1 or active[0]['sourceTrainerID']!=0:break
  bid=active[0]['battleID']
 # Cursor-aware ordinary Run driver, explicitly armed only after host wild check.
 offset=(generic.E/'emulator.jsonl').stat().st_size
 inp.segment(f'{a.label}-wild-{n}',['a 30']);confirmed=False
 deadline=time.monotonic()+40
 while time.monotonic()<deadline:
  with generic.open_store(generic.PRIVATE/'world.sqlite3') as w:
   if w.get_battle(bid)['ended']:break
  if not confirmed:
   with (generic.E/'emulator.jsonl').open() as f:f.seek(offset);terminal=any(json.loads(line).get('event')=='wild-run-terminal' for line in f)
   if terminal:
    inp.segment(f'{a.label}-wild-confirm-{n}',['a 3','key 9 0 240']);confirmed=True
  time.sleep(.2)
 else:raise TimeoutError('ordinary Run failed; review native screen')
 inp.segment(f'{a.label}-wild-ended-{n}',['key 9 0 90'])
else:raise TimeoutError('route encounter bound reached')
(generic.E/(a.label+'-travel.json')).write_text(json.dumps(history,indent=2)+'\n');print(json.dumps(out))
