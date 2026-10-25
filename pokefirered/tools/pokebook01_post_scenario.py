#!/usr/bin/env python3
"""Actual post-battle read-only/privacy/cleanup/paired-save assertions."""
import json,shutil,time
from pokebook01 import ROOT,E,open_store
from hermes01 import snapshot,JANICE,DOUG
from pokebook01_viewer_scenario import public,cycles
from pokebook01_scenario import normal_save

def run():
 with open_store(ROOT/'.local/pokebook01/world.sqlite3') as w:
  assert len(w.social_state()['posts'])==1
  before=snapshot(w)
  assert before['playerFollowerCount']==1
  assert not before['trainerPackets'][JANICE]['reportedClaims']
  (E/'native-records-before-view.json').write_text(json.dumps(before,indent=2)+'\n')
 public('accepted-public',4);cycles('accepted-repeat',5)
 with open_store(ROOT/'.local/pokebook01/world.sqlite3') as w:
  after=snapshot(w);keys=['canonicalSHA256','memorySHA256','socialSHA256','puppeteerSHA256','counts','trainerPackets']
  assert all(before[k]==after[k] for k in keys)
  (E/'native-read-only.json').write_text(json.dumps({'allUnchanged':True,'checkedKeys':keys,'hashes':{k:after[k] for k in keys[:4]},'janiceReportedClaims':after['trainerPackets'][JANICE]['reportedClaims'],'dougReportedClaims':after['trainerPackets'][DOUG]['reportedClaims'],'posts':1,'followers':1},indent=2)+'\n')
  post=next(iter(w.social_state()['posts']));w.tick(1)
  assert not w.trainer_packet(JANICE)['reportedClaims']
  (E/'native-unread.json').write_text(json.dumps(snapshot(w),indent=2)+'\n')
  w.for_social_actor(JANICE).expose(post)
  assert len(w.trainer_packet(JANICE)['reportedClaims'])==2 and not w.trainer_packet(DOUG)['reportedClaims']
  assert 'moveID' not in json.dumps(w.trainer_packet(JANICE))
  (E/'native-exposure.json').write_text(json.dumps(snapshot(w),indent=2)+'\n')
  job=w._one("SELECT * FROM puppeteer_jobs WHERE status='completed'")
  packet=w._battle_evidence(json.loads(job['scope']))['evidence']
  battle=next(iter(w.state()['battles'].values()))
  detail={'viewerSummarizes':False,'hermesSourceModified':False,'privateEvidenceCount':len(packet),'privateEvidenceTypes':[p['claim']['type'] for p in packet],'turns':battle['turn'],'canonicalRecords':w.get_current_world_cursor(),'limitation':'Accepted Hermes bundle deduplicates facts/caps64references; not a complete chronological transcript. UI does not shorten/replace it.'}
  (E/'recap-detail-preserved.json').write_text(json.dumps(detail,indent=2)+'\n')
 cp=normal_save('accepted-s2',7)
 shutil.copy2(ROOT/'.local/pokebook01/pokefirered.sav',ROOT/'.local/pokebook01/S2.sav')
 (E/'checkpoint-S2.json').write_text(json.dumps(cp,indent=2)+'\n')
 with open_store(ROOT/'.local/pokebook01/world.sqlite3') as w:(E/'native-records-S2.json').write_text(json.dumps(snapshot(w),indent=2)+'\n')
 print(json.dumps(cp,indent=2))
if __name__=='__main__':run()
