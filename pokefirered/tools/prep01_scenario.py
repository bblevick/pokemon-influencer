#!/usr/bin/env python3
"""Reviewed native save/default Fight sequence; existing mandatory recap settlement stays offline in the host."""
import argparse,json,time
import re
from prep01_input import segment
from prep01 import ROOT,E,open_store,save_identity

def paired_intent(w,intent,save):
 r=w._one('SELECT status,checkpoint FROM save_intents WHERE id=?',(intent,))
 if not r or r['status']!='paired':return None
 cp=w.get_save_checkpoint(save.fingerprint)
 return cp if cp and cp['id']==r['checkpoint'] and cp['kind']=='normal_save' else None

def normal_save(label,cursor,resume=False):
 if not re.fullmatch('[a-z0-9-]{1,32}',label):raise ValueError('validate lowercase screenshot prefix before arming save')
 cfg=json.loads((ROOT/'.local/prep01-launch.json').read_text())
 with open_store(cfg['database']) as w:
  save=save_identity(cfg['save']);pending=w.pending_save()
  if resume:
   if not pending or (pending['nonce'],pending['branch'],pending['cursor'],pending['old_fingerprint'])!=(cfg['nonce'],w.get_active_branch(),w.get_current_world_cursor(),save.fingerprint):raise ValueError('incompatible pending save intent')
   intent=pending['id']
  else:intent=w.begin_save(cfg['nonce'],save)
 segment(label+'-prompt',['key 3 8 30']+['key 7 6 10']*((4-cursor)%8)+['key 0 8 60'])
 segment(label+'-overwrite',['a 4','key 9 0 240'])
 segment(label+'-complete',['key 0 8 300','key 9 0 300'])
 deadline=time.monotonic()+15
 while time.monotonic()<deadline:
  with open_store(cfg['database']) as w:
   cp=paired_intent(w,intent,save_identity(cfg['save']))
   if cp:return cp
  time.sleep(.2)
 raise TimeoutError('native save did not produce a validated world pair; intent '+intent)

def battle(label,steps):
 if not re.fullmatch('[a-z0-9-]{1,32}',label):raise ValueError('lowercase screenshot prefix required')
 cfg=json.loads((ROOT/'.local/prep01-launch.json').read_text())
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
 if not re.fullmatch('[a-z0-9-]{1,32}',label):raise ValueError('lowercase screenshot prefix required')
 cfg=json.loads((ROOT/'.local/prep01-launch.json').read_text())
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
 p=argparse.ArgumentParser();p.add_argument('command',choices=['save','battle','encounter']);p.add_argument('--label',required=True);p.add_argument('--steps',type=int,default=60);p.add_argument('--menu-cursor',type=int,choices=range(8),default=0);p.add_argument('--resume-intent',action='store_true');a=p.parse_args();assert 1<=a.steps<=60
 print(json.dumps(normal_save(a.label,a.menu_cursor,a.resume_intent) if a.command=='save' else battle(a.label,a.steps) if a.command=='battle' else encounter(a.label,a.steps),indent=2))
