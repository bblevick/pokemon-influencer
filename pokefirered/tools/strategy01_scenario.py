#!/usr/bin/env python3
"""Reviewed native save/default Fight sequence; existing mandatory recap settlement stays offline in the host."""
import argparse,json,time
import re
from strategy01_input import segment
from strategy01 import PRIVATE,CONFIG,SCREENS,ROOT,E,open_store,save_identity

def paired_intent(w,intent,save):
 r=w._one('SELECT status,checkpoint FROM save_intents WHERE id=?',(intent,))
 if not r or r['status']!='paired':return None
 cp=w.get_save_checkpoint(save.fingerprint)
 return cp if cp and cp['id']==r['checkpoint'] and cp['kind']=='normal_save' else None

def normal_save(label,cursor,resume=False):
 if not re.fullmatch('[a-z0-9-]{1,32}',label):raise ValueError('validate lowercase screenshot prefix before arming save')
 cfg=json.loads((CONFIG).read_text())
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

def continue_save(label):
 # Stable fresh native Continue path; avoids re-interacting with Brock afterward.
 return segment(label,['a 6','key 9 0 240','key 0 8 360','key 1 8 180','key 9 0 180'])

def continue_from_reviewed_title(label):
 # Precondition: native screenshot shows PRESS START. A-only startup is not
 # reliable across the intro/title lifecycle. Do not use this from field/menu.
 return segment(label,['key 3 8 120','key 0 8 360','key 1 8 180','key 9 0 180'])

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['save','continue','continue-title']);p.add_argument('--label',required=True);p.add_argument('--menu-cursor',type=int,choices=range(8),default=0);p.add_argument('--resume-intent',action='store_true');a=p.parse_args()
 print(json.dumps(normal_save(a.label,a.menu_cursor,a.resume_intent) if a.command=='save' else str(continue_from_reviewed_title(a.label) if a.command=='continue-title' else continue_save(a.label)),indent=2))
