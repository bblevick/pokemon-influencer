#!/usr/bin/env python3
"""Reviewed native save/default Fight sequence, bounded and reusable. No AI."""
import argparse,json,time
import re
from memory01_input import segment
from memory01 import ROOT,E,open_store,save_identity

def normal_save(label,cursor):
 if not re.fullmatch('[a-z0-9_-]{1,32}',label):raise ValueError('validate lowercase screenshot prefix before arming save')
 cfg=json.loads((ROOT/'.local/memory01-launch.json').read_text())
 with open_store(cfg['database']) as w:intent=w.begin_save(cfg['nonce'],save_identity(cfg['save']))
 segment(label+'-prompt',['key 3 8 30']+['key 7 6 10']*((4-cursor)%7)+['key 0 8 60'])
 segment(label+'-overwrite',['a 4','key 9 0 240'])
 segment(label+'-complete',['key 0 8 300','key 9 0 300'])
 deadline=time.monotonic()+15
 while time.monotonic()<deadline:
  with open_store(cfg['database']) as w:
   cp=w.get_save_checkpoint(save_identity(cfg['save']).fingerprint)
   if cp and cp['kind']=='normal_save':return cp
  time.sleep(.2)
 raise TimeoutError('native save did not produce a validated world pair; intent '+intent)

def battle(label,steps):
 if not re.fullmatch('[a-z0-9_-]{1,32}',label):raise ValueError('lowercase screenshot prefix required')
 cfg=json.loads((ROOT/'.local/memory01-launch.json').read_text())
 with open_store(cfg['database']) as w:
  active=[b for b in w.state()['battles'].values() if not b['ended']]
  if len(active)!=1:raise ValueError('reviewed active encounter required')
  bid=active[0]['battleID']
 for i in range(steps):
  with open_store(cfg['database']) as w:
   b=w.get_battle(bid)
   if b['ended']:return b
  segment(label+'-'+str(i),['key 0 90 180'])
 raise TimeoutError('battle bound reached; inspect native screen, do not repeat blindly')
def encounter(label,steps):
 if not re.fullmatch('[a-z0-9_-]{1,32}',label):raise ValueError('lowercase screenshot prefix required')
 cfg=json.loads((ROOT/'.local/memory01-launch.json').read_text())
 with open_store(cfg['database']) as w:
  before=len(w.state()['battles'])
  if any(not b['ended'] for b in w.state()['battles'].values()):raise ValueError('ordinary field required')
 segment(label+'-grass',['key 5 8 8','key 5 16 180'])
 for i in range(steps):
  with open_store(cfg['database']) as w:
   if len(w.state()['battles'])>before:return {'campaign':w.campaign(),'battle':list(w.state()['battles'].values())[-1],'segments':i+1}
  key=6 if i%2==0 else 7
  segment(label+'-walk-'+str(i),[f'key {key} 8 8',f'key {key} 16 180'])
 raise TimeoutError('no encounter within reviewed Viridian Forest grass bound')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['save','battle','encounter']);p.add_argument('--label',required=True);p.add_argument('--steps',type=int,default=40);p.add_argument('--menu-cursor',type=int,choices=range(7),default=0);a=p.parse_args();assert 1<=a.steps<=40
 print(json.dumps(normal_save(a.label,a.menu_cursor) if a.command=='save' else battle(a.label,a.steps) if a.command=='battle' else encounter(a.label,a.steps),indent=2))
