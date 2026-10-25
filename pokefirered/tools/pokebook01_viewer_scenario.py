#!/usr/bin/env python3
"""Reviewed normal eight-item Start-menu viewer path; no direct screen invocation."""
import argparse,json,shutil
from pokebook01_input import segment
from pokebook01 import ROOT,E,open_store
from pokebook01_scenario import normal_save

def open_view(label,cursor=7,menu_open=False):
 commands=[] if menu_open else ['key 3 8 45']
 commands+=['key 7 6 12']*((7-cursor)%8)+['key 0 8 120']
 return segment(label,commands)
def empty(label,menu_open=False,cursor=7):
 with open_store(ROOT/'.local/pokebook01/world.sqlite3') as w:
  assert not w.social_state()['posts'] and w.puppeteer_state()['activation']
 open_view(label+'-home',cursor,menu_open)
 segment(label+'-feed',['key 0 8 120'])
 segment(label+'-followers',['key 1 8 45','key 7 6 12','key 0 8 120'])
 segment(label+'-field',['key 1 8 45','key 1 8 90','key 1 8 90'])
 checkpoint=normal_save(label+'-s1',7)
 shutil.copy2(ROOT/'.local/pokebook01/pokefirered.sav',ROOT/'.local/pokebook01/S1.sav')
 (E/'checkpoint-S1.json').write_text(json.dumps(checkpoint,indent=2)+'\n')
 return checkpoint

def public(label,cursor=4):
 open_view(label+'-home',cursor)
 segment(label+'-feed',['key 0 8 120'])
 segment(label+'-post',['key 0 8 120'])
 segment(label+'-followers',['key 1 8 90','key 1 8 60','key 7 6 12','key 0 8 120'])
 segment(label+'-field',['key 1 8 45','key 1 8 90','key 1 8 90'])

def cycles(label,count):
 for n in range(count):
  open_view(label+'-'+str(n)+'-open',7)
  segment(label+'-'+str(n)+'-closed',['key 1 8 120','key 1 8 90'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['empty','public','cycles']);p.add_argument('--label',required=True);p.add_argument('--menu-cursor',type=int,choices=range(8),default=4);p.add_argument('--menu-open',action='store_true');p.add_argument('--cycles',type=int,choices=range(1,11),default=5);a=p.parse_args()
 if a.stage=='empty':print(json.dumps(empty(a.label,a.menu_open,a.menu_cursor),indent=2))
 elif a.stage=='public':public(a.label,a.menu_cursor)
 else:cycles(a.label,a.cycles)
