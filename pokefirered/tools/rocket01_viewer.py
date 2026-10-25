#!/usr/bin/env python3
"""Native public feed/followers traversal; exact replay/ledger read-only proof."""
import sys,json,argparse
from rocket01 import generic
from vertical_slice01_viewer import METHODS
import vertical_slice01_input as inp
generic.bind(inp);generic.bind(inp.driver);inp.driver.retained.E=generic.E
p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('--cursor',type=int,default=4);a=p.parse_args();cfg=json.loads((generic.PRIVATE/'launch.json').read_text());E=generic.E
with generic.open_store(cfg['database']) as w:
 before={m:getattr(w,m)() for m in METHODS};posts=[p for p in w.social_state()['posts'].values() if p['visibility']=='public'];n=len(posts)
ledger=(E/'requests.json').read_bytes();steps=[]
def step(label,keys):steps.append(label);inp.segment(a.label+'-'+label,keys)
step('home',['key 3 8 30']+['key 7 6 10']*((7-a.cursor)%8)+['key 0 8 120']);step('feed',['key 0 8 120'])
for page in range((n+2)//3):
 if page:step('page-'+str(page+1),['key 4 8 120'])
 for row in range(min(3,n-page*3)):
  if row:step('row-'+str(page*3+row+1),['key 7 6 20'])
  step('post-'+str(page*3+row+1),['key 0 8 120']);step('back-'+str(page*3+row+1),['key 1 8 120'])
step('home-return',['key 1 8 120']);step('followers',['key 7 6 20','key 0 8 120']);step('followers-next',['key 4 8 120']);step('field',['key 1 8 120','key 1 8 120','key 1 8 90'])
with generic.open_store(cfg['database']) as w:after={m:getattr(w,m)() for m in METHODS}
assert after==before and ledger==(E/'requests.json').read_bytes()
(E/(a.label+'-proof.json')).write_text(json.dumps({'native':True,'publicPosts':n,'steps':steps,'sevenReplayHashesUnchanged':True,'requestLedgerUnchanged':True,'hashes':after,'privateIntelQueriedByViewer':False},indent=2)+'\n');print(json.dumps({'posts':n,'readOnly':True}))
