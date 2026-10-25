#!/usr/bin/env python3
"""Retained native normal-save and explicit navigation evidence, no game writes."""
import sys,argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from vertical_slice01_host import E,PRIVATE,open_store,save_identity
from vertical_slice01_input import segment
import strategy01_scenario as retained
retained.E=E;retained.PRIVATE=PRIVATE;retained.CONFIG=PRIVATE/'launch.json';retained.open_store=open_store;retained.save_identity=save_identity;retained.segment=segment
def battle(label,steps=40):
 cfg=json.loads((PRIVATE/'launch.json').read_text())
 with open_store(cfg['database']) as w:
  active=[b for b in w.state()['battles'].values() if not b['ended']]
  if len(active)!=1:raise ValueError('one real native active battle required')
  bid=active[0]['battleID']
 for i in range(steps):
  with open_store(cfg['database']) as w:
   row=w.get_battle(bid)
   if row['ended']:return row
  segment(label+'-'+str(i),['a 30','key 9 0 30'])
 raise TimeoutError('native battle input bound; inspect state before further input')

def escape(label,steps=6):
 cfg=json.loads((PRIVATE/'launch.json').read_text())
 with open_store(cfg['database']) as w:
  active=[b for b in w.state()['battles'].values() if not b['ended']]
  if len(active)!=1 or active[0]['sourceTrainerID']!=0:raise ValueError('one real native wild battle required')
  bid=active[0]['battleID']
 for i in range(steps):
  with open_store(cfg['database']) as w:
   row=w.get_battle(bid)
   if row['ended']:return row
  # Native UI only: settle entrance animation, leave move menu if open,
  # clamp the command cursor to Run, submit and advance the result text.
  segment(label+'-'+str(i),['key 9 0 360','key 1 8 30','key 4 8 20','key 7 8 20','key 0 8 180','key 0 8 120'])
 raise TimeoutError('native wild escape bound')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['save','battle','escape']);p.add_argument('--label',required=True);p.add_argument('--steps',type=int,default=40);p.add_argument('--menu-cursor',type=int,default=0);p.add_argument('--resume-intent',action='store_true');a=p.parse_args()
 print(json.dumps(retained.normal_save(a.label,a.menu_cursor,resume=a.resume_intent) if a.command=='save' else escape(a.label,min(a.steps,6)) if a.command=='escape' else battle(a.label,a.steps),indent=2))
