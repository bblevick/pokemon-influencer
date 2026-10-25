#!/usr/bin/env python3
"""Actual actor-scoped channels + offline Strategy consumer preview; no inference."""
import sys,json,argparse,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rocket01 import generic
from strategy.social_context import build_social_evidence
from roster.extract import file_hash
from vertical_slice01_viewer import METHODS
MEMBER='trainer:fr:trainer:0352';LEADER='trainer:fr:trainer:0348'
p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('--battery',action='store_true');a=p.parse_args();E=generic.E;PRIVATE=generic.PRIVATE
if not a.label.replace('-','').isalnum() or len(a.label)>40:raise ValueError('label bound')
cfg=json.loads((PRIVATE/'launch.json').read_text());identity=generic.save_identity(cfg['save'])
with generic.open_store(cfg['database']) as w:
 cp=w.get_save_checkpoint(identity.fingerprint);actors={};raw={}
 for actor in (MEMBER,LEADER,'trainer:fr:trainer:0414','trainer:fr:trainer:0415','trainer:fr:trainer:0326','trainer:fr:trainer:0103'):
  actors[actor]=w.trainer_packet(actor);rows=[];after=0
  while True:
   page=w.for_actor(actor).records(after=after,limit=256);rows+=page['records']
   if not page['hasMore']:break
   after=page['records'][-1]['memoryCursor']
  raw[actor]=rows
 leader=build_social_evidence(w,LEADER)
 out={'campaign':w.campaign(),'checkpoint':cp,'save':identity.as_dict(),'hashes':{m:getattr(w,m)() for m in METHODS},'world':w.state(),'social':w.social_state(),'puppeteer':w.puppeteer_state(),'virality':w.virality_state(),'memos':w.memo_records(),'decisions':w.decision_state(),'actors':actors,'actorRecords':raw,'audit':w.battle_audit(),'lifecycle':w.decision_lifecycle(),'ledger':json.loads((E/'requests.json').read_text()),'leadershipStrategyKnowledgePreview':{'consumer':'strategy.social_context.build_social_evidence, production actor-first projection','modelCalled':False,'strategyJobCreated':False,'preparationEnvelopeQualified':False,'actorID':LEADER,'scope':leader['scope'],'PUBLIC_INFORMATION':[r for r in leader['authorizedFacts'] if r['evidenceQuality']['channel']=='pokebook'],'ROCKET_INTERNAL_INTELLIGENCE':[r for r in leader['authorizedFacts'] if r['evidenceQuality']['channel']=='ROCKET_INTEL'],'UNKNOWN':leader['unknowns'],'truncated':leader['truncated']}}
 if a.battery:
  if not cp or cp['kind']!='normal_save' or w.pending_save():raise ValueError('normal paired battery required')
  target=PRIVATE/(a.label+'.sav')
  if target.exists():raise ValueError('refuse overwrite retained battery')
  shutil.copy2(cfg['save'],target);out['batterySHA256']=file_hash(target)
(E/(a.label+'.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'label':a.label,'checkpoint':cp['id'] if cp else None,'cursor':out['campaign']['cursor'],'calls':len(out['ledger']['attempts'])}))
