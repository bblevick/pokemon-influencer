#!/usr/bin/env python3
"""Bounded ordinary native Run path for incidental cave wild encounters."""
import sys,json,argparse
from rocket01 import generic
import vertical_slice01_input as inp
generic.bind(inp);generic.bind(inp.driver);inp.driver.retained.E=generic.E
p=argparse.ArgumentParser();p.add_argument('--label',required=True);a=p.parse_args()
with generic.open_store(generic.PRIVATE/'world.sqlite3') as w:
 active=[b for b in w.state()['battles'].values() if not b['ended']]
 if len(active)!=1 or active[0]['sourceTrainerID']!=0:raise ValueError('one real native wild encounter required')
 bid=active[0]['battleID']
for i in range(3):
 inp.segment(a.label+'-intro-'+str(i),['a 1','key 0 0 360'])
 inp.segment(a.label+'-run-'+str(i),['key 1 8 90','key 4 8 20','key 7 8 20','key 0 8 240','key 0 8 240','key 0 0 180'])
 with generic.open_store(generic.PRIVATE/'world.sqlite3') as w:
  row=w.get_battle(bid)
  if row['ended']:print(json.dumps(row));break
else:raise TimeoutError('wild Run path bound; review native screen')
