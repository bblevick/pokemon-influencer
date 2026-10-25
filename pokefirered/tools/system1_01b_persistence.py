#!/usr/bin/env python3
"""Record/compare actual normal-save pairs; no inference or invented emulator results."""
import sys,json,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from system1_01b_launch import E,PRIVATE,open_store,save_identity
from roster.hashes import digest
def snapshot():
 with open_store(PRIVATE/'world.sqlite3') as w:
  s=save_identity(PRIVATE/'pokefirered.sav');cp=w.get_save_checkpoint(s.fingerprint)
  if not cp or cp['kind']!='normal_save':raise ValueError('actual normal pair required')
  lock=w.locked_preparation('trainer:fr:trainer:0102')
  return {'save':s.as_dict(),'checkpoint':cp,'audit':w.battle_audit(),'auditSHA256':digest(w.battle_audit()),'replays':{'world':w.verify_replay(),'memory':w.verify_memory_replay(),'social':w.verify_social_replay(),'puppeteer':w.verify_puppeteer_replay()},'commitment':lock['commitmentID'],'strategySHA256':hashlib.sha256(lock['strategyText'].encode()).hexdigest(),'requestCount':len(json.loads((E/'requests.json').read_text())['attempts']),'session':json.loads((PRIVATE/'launch.json').read_text())['nonce']}
if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ('before','after'):raise ValueError('before or after required')
 r=snapshot()
 if sys.argv[1]=='before':
  shutil.copy2(PRIVATE/'pokefirered.sav',PRIVATE/'completed-enabled-save20.sav');name='persistence-before.json'
 else:
  before=json.loads((E/'persistence-before.json').read_text())
  for k in ('save','checkpoint','audit','auditSHA256','replays','commitment','strategySHA256','requestCount'):
   if before[k]!=r[k]:raise ValueError('reload mismatch: '+k)
  name='fresh-reload.json'
 (E/name).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'record':name,'counter':r['save']['counter'],'requests':r['requestCount'],'auditCount':len(r['audit'])}))
