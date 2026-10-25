#!/usr/bin/env python3
"""Ordinary native button traversal with read-only snapshot assertions."""
import os
os.environ['POKEINFLUENCER_EXPERIMENT']='campaign_expansion01';os.environ['POKEINFLUENCER_CAMPAIGN_FINAL']='1'
import json,sys,argparse
from campaign_expansion01 import E,PRIVATE,open_store,bind
from vertical_slice01_viewer import METHODS
import vertical_slice01_input as inp
bind(inp);bind(inp.driver);inp.driver.retained.E=E
p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('--cursor',type=int,default=7);p.add_argument('--posts',type=int,required=True);p.add_argument('--fixture',action='store_true');a=p.parse_args()
cfg=json.loads((PRIVATE/'launch.json').read_text())
def snap():
 with open_store(cfg['database']) as w:return {m:getattr(w,m)() for m in METHODS}
before=snap();ledger=(E/'requests.json').read_bytes();steps=[]
def step(label,keys):
 steps.append(label);inp.segment(a.label+'-'+label,keys)
step('home',['key 3 8 30']+['key 7 6 10']*((7-a.cursor)%8)+['key 0 8 120'])
step('feed-1',['key 0 8 120'])
for page in range((a.posts+2)//3):
 if page:step('feed-'+str(page+1),['key 4 8 120'])
 for row in range(min(3,a.posts-page*3)):
  if row:step('select-'+str(page*3+row+1),['key 7 6 20'])
  step('post-'+str(page*3+row+1),['key 0 8 120'])
  if a.fixture and page*3+row+1==a.posts:
   step('text-next',['key 4 8 120']);step('text-back',['key 5 8 120'])
  step('return-'+str(page*3+row+1),['key 1 8 120'])
for page in range((a.posts+2)//3-1,0,-1):step('previous-'+str(page),['key 5 8 120'])
step('home-return',['key 1 8 120'])
step('followers-1',['key 7 6 20','key 0 8 120'])
step('followers-2',['key 4 8 120'])
step('followers-back',['key 5 8 120'])
step('field',['key 1 8 120','key 1 8 120','key 1 8 90'])
step('reopen',['key 3 8 30','key 0 8 120'])
step('reopened-feed',['key 0 8 120'])
step('closed',['key 1 8 120','key 1 8 120','key 1 8 90'])
after=snap();assert after==before and ledger==(E/'requests.json').read_bytes()
(E/'kent-resolution'/f'{a.label}-proof.json').write_text(json.dumps({'label':a.label,'fixture':a.fixture,'expectedPosts':a.posts,'screenshots':steps,'sevenHashesUnchanged':True,'requestLedgerUnchanged':True,'hashes':after},indent=2)+'\n')
