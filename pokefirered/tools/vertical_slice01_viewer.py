#!/usr/bin/env python3
"""Replay a native checkpoint viewer milestone and assert all-layer immutability.

Requires an already restored/Continued normal paired battery, offline host,
loaded pinned Lua script, ordinary field and explicit current Start cursor.
This is not a new-game or live-model acceptance runner.
"""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from vertical_slice01_host import E,PRIVATE,open_store
from vertical_slice01_input import segment
from vertical_slice01_verify import verify
METHODS=('verify_replay','verify_memory_replay','verify_social_replay','verify_puppeteer_replay','verify_strategy_replay','verify_decision_replay','verify_virality_replay')
def snapshot():
 cfg=json.loads((PRIVATE/'launch.json').read_text())
 with open_store(cfg['database']) as w:
  if w.pending_save() or any(not b['ended'] for b in w.state()['battles'].values()):raise ValueError('ordinary paired field required')
  return {m:getattr(w,m)() for m in METHODS}
def viewer(stage,cursor,label=None):
 if stage!='CLOSEOUT':verify(stage)
 before=snapshot();requests=(E/'requests.json').read_bytes()
 label=label or ('closeout-viewer' if stage=='CLOSEOUT' else 'restore-'+stage.lower()+'-viewer')
 segment(label+'-home',['key 3 8 30']+['key 7 6 10']*((7-cursor)%8)+['key 0 8 120'])
 segment(label+'-feed',['key 0 8 120'])
 if stage!='S0':
  segment(label+'-rick',['key 0 8 120'])
  segment(label+'-feed-return',['key 1 8 90'])
 if stage in ('S3','CLOSEOUT'):
  segment(label+'-brock',['key 7 6 20','key 7 6 20','key 0 8 120'])
  segment(label+'-brock-return',['key 1 8 90'])
 segment(label+'-home-return',['key 1 8 90'])
 segment(label+'-followers',['key 7 6 20','key 0 8 120'])
 segment(label+'-field',['key 1 8 60','key 1 8 120','key 1 8 90'])
 after=snapshot()
 assert before==after and requests==(E/'requests.json').read_bytes()
 result={'stage':stage,'sevenHashesUnchanged':True,'requestLedgerUnchanged':True,'workflow':'native Feed/Post/Followers keys over restored paired battery; no inference','hashes':after}
 (E/(label+'-proof.json' if stage=='CLOSEOUT' else label+'.json')).write_text(json.dumps(result,indent=2)+'\n')
 if stage!='CLOSEOUT':verify(stage)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['S0','S1','S2','S3','CLOSEOUT']);p.add_argument('--menu-cursor',type=int,choices=range(8),required=True)
 p.add_argument('--label')
 a=p.parse_args();print(json.dumps(viewer(a.stage,a.menu_cursor,a.label)))
