#!/usr/bin/env python3
"""Local durable evidence capture; no inference or domain mutations."""
import json,argparse,shutil,sqlite3
from rival01 import E,PRIVATE,open_store,save_identity
from rival01_prerequisites import METHODS,protected
p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('--battery',action='store_true');a=p.parse_args()
if not a.label.replace('-','').isalnum() or len(a.label)>32:raise ValueError('bounded local evidence label')
cfg=json.loads((PRIVATE/'launch.json').read_text());identity=save_identity(cfg['save'])
with open_store(cfg['database']) as w:
 cp=w.get_save_checkpoint(identity.fingerprint)
 actors=['trainer:fr:trainer:0326','trainer:fr:trainer:0352','trainer:fr:trainer:0348','trainer:fr:trainer:0103','trainer:fr:trainer:0415']
 out={'campaign':w.campaign(),'checkpoint':cp,'save':identity.as_dict(),'hashes':{m:getattr(w,m)() for m in METHODS},'world':w.state(),'social':w.social_state(),'puppeteer':w.puppeteer_state(),'virality':w.virality_state(),'memos':w.memo_records(),'decisions':w.decision_state(),'actors':{actor:w.trainer_packet(actor) for actor in actors},'actorRecords':{actor:w.for_actor(actor).records(limit=256) for actor in actors},'audit':w.battle_audit(),'lifecycle':w.decision_lifecycle(),'ledger':json.loads((E/'requests.json').read_text()),'protected':protected(),'pendingSave':w.pending_save()}
 if a.battery:
  if not cp or cp['kind']!='normal_save' or w.pending_save() or cp['cursor']!=w.campaign()['cursor']:raise ValueError('current normal settled pair required')
  target=PRIVATE/(a.label+'.sav');db=PRIVATE/(a.label+'.sqlite3')
  if target.exists() or db.exists():raise ValueError('refuse overwrite evidence pair')
  shutil.copy2(cfg['save'],target);dst=sqlite3.connect(db);w.db.backup(dst);dst.close();out['retainedPair']={'save':str(target),'database':str(db)}
(E/(a.label+'.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'label':a.label,'checkpoint':cp['id'] if cp else None,'cursor':out['campaign']['cursor'],'attempts':len(out['ledger']['attempts']),'battles':[{k:b.get(k) for k in ('battleID','sourceTrainerID','trainerID','ended','outcome')} for b in out['world']['battles'].values() if not b['ended']]}))
