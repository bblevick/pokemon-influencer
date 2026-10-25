#!/usr/bin/env python3
"""Read-only actual closeout state/save evidence; no fabricated events."""
import argparse,json,sys,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from vertical_slice01_host import E,PRIVATE,open_store,save_identity
from prep.progression import read_boulder
from vertical_slice01_verify import BROCK,SALLY
from vertical_slice01_viewer import METHODS

def capture(label,battery=False):
 if not re.fullmatch('[a-z0-9-]{1,48}',label):raise ValueError('evidence_label')
 cfg=json.loads((PRIVATE/'launch.json').read_text());identity=save_identity(cfg['save'])
 with open_store(cfg['database']) as w:
  cp=w.get_save_checkpoint(identity.fingerprint)
  out={'campaign':w.campaign(),'checkpoint':cp,'save':identity.as_dict(),'hashes':{m:getattr(w,m)() for m in METHODS},'world':w.state(),'social':w.social_state(),'puppeteer':w.puppeteer_state(),'virality':w.virality_state(),'memos':w.memo_records(),'decisions':w.decision_state(),'brock':w.trainer_packet(BROCK),'sally':w.trainer_packet(SALLY),'boulder':read_boulder(Path(cfg['save']).read_bytes(),w.build),'audit':w.battle_audit(),'lifecycle':w.decision_lifecycle(),'chargedRequests':len(json.loads((E/'requests.json').read_text())['attempts'])}
  if battery:
   if not cp or cp['kind']!='normal_save' or w.pending_save():raise ValueError('normal_paired_battery_required')
   target=PRIVATE/(label+'.sav')
   if target.exists():raise ValueError('refuse overwrite retained battery')
   shutil.copy2(cfg['save'],target)
 (E/(label+'.json')).write_text(json.dumps(out,indent=2)+'\n')
 return {'label':label,'checkpoint':cp['id'] if cp else None,'branch':out['campaign']['active_branch'],'memos':[(m['strategyID'],m['source']) for m in out['memos']],'chargedRequests':out['chargedRequests']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('--battery',action='store_true');a=p.parse_args();print(json.dumps(capture(a.label,a.battery)))
