#!/usr/bin/env python3
"""Fresh paired launch's native Continue/view path and history assertions."""
import argparse,json
from pokebook01 import ROOT,E,open_store
from hermes01 import snapshot,JANICE
from pokebook.viewer import Viewer
from pokebook01_input import segment
from pokebook01_viewer_scenario import open_view,public

def run(stage):
 segment('restore-'+stage.lower()+'-continue',['a 6','key 9 0 240'])
 segment('restore-'+stage.lower()+'-quest',['key 0 8 360'])
 segment('restore-'+stage.lower()+'-field',['key 1 8 180','a 3','key 9 0 180'])
 with open_store(ROOT/'.local/pokebook01/world.sqlite3') as w:
  before=snapshot(w);v=Viewer(w);s=v.open(9999)
  if stage=='S1':
   assert (s['posts'],s['followers'])==(0,0) and not before['puppeteer']['episodes'] and not before['trainerPackets'][JANICE]['reportedClaims']
  else:
   paired=json.loads((E/'native-records-S2.json').read_text())
   assert all(before[k]==paired[k] for k in ('canonicalSHA256','memorySHA256','socialSHA256','puppeteerSHA256','counts'))
   for actor,packet in paired['trainerPackets'].items():
    q=before['trainerPackets'][actor]
    assert {k:z for k,z in packet.items() if k!='cutoffs'}=={k:z for k,z in q.items() if k!='cutoffs'}
    assert q['cutoffs']['socialEpoch']>packet['cutoffs']['socialEpoch']
 if stage=='S1':
  open_view('paired-early-home',0);segment('paired-early-feed',['key 0 8 120'])
  segment('paired-early-followers',['key 1 8 90','key 7 6 12','key 0 8 120'])
  segment('paired-early-field',['key 1 8 90','key 1 8 90','key 1 8 90'])
 else:public('paired-late',0)
 with open_store(ROOT/'.local/pokebook01/world.sqlite3') as w:
  after=snapshot(w)
  assert all(before[k]==after[k] for k in ('canonicalSHA256','memorySHA256','socialSHA256','puppeteerSHA256','counts','trainerPackets'))
  result={'posts':s['posts'],'followers':s['followers'],'janiceClaims':len(after['trainerPackets'][JANICE]['reportedClaims']),'scopeRevoked':before['trainerPackets'][JANICE]['cutoffs']['socialEpoch']>json.loads((E/'native-records-S2.json').read_text())['trainerPackets'][JANICE]['cutoffs']['socialEpoch'],'hashesEqual':True,'snapshot':after,'workflow':'fresh managed OS-process paired normal Continue; native controls; all browsing histories unchanged'}
  assert result['scopeRevoked']
  (E/('restored-'+stage+'.json')).write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['S1','S2']);run(p.parse_args().stage)
