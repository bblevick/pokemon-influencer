#!/usr/bin/env python3
"""Explicit stored/layout fixtures through native controls; no history writes."""
import json,subprocess,sys,time
from pokebook01 import ROOT,E,open_store
from hermes01 import snapshot
from pokebook01_viewer_scenario import public,open_view
from pokebook01_input import segment

def run():
 with open_store(ROOT/'.local/pokebook01/world.sqlite3') as w:before=snapshot(w)
 for mode in ('stored-hermes','layout'):
  fixture='stored-hermes-public-fixture.json' if mode=='stored-hermes' else 'layout-public-fixture.json'
  with (E/(mode+'-host.log')).open('w') as log:
   host=subprocess.Popen([sys.executable,'tools/pokebook01_host.py','--seconds','180','--stored-output-fixture',str(E/fixture)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
   try:
    time.sleep(.4)
    if host.poll() is not None:raise RuntimeError('fixture host did not start')
    if mode=='stored-hermes':public('stored-hermes',7)
    else:
     open_view('layout-home',7);segment('layout-feed',['key 0 8 120'])
     segment('layout-page-1',['key 7 6 12','key 7 6 12','key 0 8 120'])
     for n in range(2,6):segment('layout-page-'+str(n),['key 4 8 120'])
     segment('layout-back-page',['key 5 8 120'])
     segment('layout-return-list',['key 1 8 90'])
     segment('layout-field',['key 1 8 90','key 1 8 90','key 1 8 90'])
   finally:
    if host.poll() is None:host.send_signal(2);host.wait(timeout=5)
 with open_store(ROOT/'.local/pokebook01/world.sqlite3') as w:
  after=snapshot(w);keys=['canonicalSHA256','memorySHA256','socialSHA256','puppeteerSHA256','counts','trainerPackets']
  assert all(before[k]==after[k] for k in keys)
  (E/'fixture-read-only.json').write_text(json.dumps({'allUnchanged':True,'keys':keys,'layoutRows':3,'selectedRow':3,'pages':5,'normalProductionPostCount':len(after['social']['posts'])},indent=2)+'\n')
if __name__=='__main__':run()
