#!/usr/bin/env python3
"""Actual active campaign proof; source-bound actor packets, no model calls."""
import sys,json,argparse,shutil
from pathlib import Path
from campaign_expansion01 import ROOT,E,PRIVATE,open_store,save_identity
from vertical_slice01_viewer import METHODS
from content.campaign import CampaignContent
from roster.extract import file_hash
p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('--battery',action='store_true');a=p.parse_args()
if not a.label.replace('-','').isalnum() or len(a.label)>40:raise ValueError('label bound')
cfg=json.loads((PRIVATE/'launch.json').read_text());identity=save_identity(cfg['save'])
with open_store(cfg['database']) as w:
 cp=w.get_save_checkpoint(identity.fingerprint)
 out={'campaign':w.campaign(),'checkpoint':cp,'save':identity.as_dict(),'hashes':{m:getattr(w,m)() for m in METHODS},'world':w.state(),'social':w.social_state(),'puppeteer':w.puppeteer_state(),'virality':w.virality_state(),'memos':w.memo_records(),'decisions':w.decision_state(),'actors':{actor:w.trainer_packet(actor) for actor in CampaignContent.load().extension['trainers']},'audit':w.battle_audit(),'lifecycle':w.decision_lifecycle(),'ledger':json.loads((E/'requests.json').read_text())}
 if a.battery:
  if not cp or cp['kind']!='normal_save' or w.pending_save():raise ValueError('actual normal paired battery required')
  target=PRIVATE/(a.label+'.sav')
  if target.exists():raise ValueError('retained battery exists')
  shutil.copy2(cfg['save'],target);out['batterySHA256']=file_hash(target)
(E/(a.label+'.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'label':a.label,'checkpoint':cp['id'] if cp else None,'cursor':w.get_current_world_cursor() if False else out['campaign']['cursor'],'calls':len(out['ledger']['attempts'])}))
