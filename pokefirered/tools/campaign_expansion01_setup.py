#!/usr/bin/env python3
"""Preserve accepted checkpoint; SQLite backup API creates separate expansion copy."""
import sys,json,sqlite3,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from campaign.expansion import ExpansionStore
from roster.extract import file_hash
from world.saves import fingerprint,layout_from_build
E=ROOT/'evidence/phase6/campaign_expansion01';PRIVATE=ROOT/'.local/campaign_expansion01';MANIFEST=E/'manifest-native.json'
def main():
 PRIVATE.mkdir(parents=True,exist_ok=True);db=PRIVATE/'world.sqlite3';battery=PRIVATE/'pokefirered.sav';source=ROOT/'.local/vertical_slice01/world.sqlite3';save=ROOT/'.local/vertical_slice01/final-success.sav'
 if db.exists() or battery.exists():raise ValueError('refuse overwrite campaign copy')
 if any(p.stat().st_size for p in ROOT.glob('.local/vertical_slice01/world.sqlite3-wal')):raise ValueError('accepted source WAL exists; require closed known-good source')
 protected={str(p.relative_to(ROOT)):file_hash(p) for p in (source,save,ROOT/'pokefirered.gba',ROOT/'evidence/phase4/vertical_slice01/requests.json',ROOT/'config/opening_content.json',ROOT/'config/model_profiles.yaml')}
 m=json.loads(MANIFEST.read_text());identity=fingerprint(save.read_bytes(),layout_from_build(ROOT/m['rom_path']))
 src=sqlite3.connect('file:'+str(source)+'?mode=ro',uri=True);dst=sqlite3.connect(db)
 try:src.backup(dst)
 finally:dst.close();src.close()
 shutil.copy2(save,battery);shutil.copy2(save,PRIVATE/'C0.sav')
 with ExpansionStore(db,MANIFEST) as w:
  cp=w.get_save_checkpoint(identity.fingerprint)
  if cp['id']!='b67c97e6-46b4-410f-87c3-6a1ebb696fa0':raise ValueError('wrong accepted checkpoint')
  w.restore(identity)
  sally=w.trainer_packet('trainer:fr:trainer:0117')
  before={'checkpoint':cp,'Sally':sally,'preparationHash':w.verify_preparation_replay() if hasattr(w,'verify_preparation_replay') else None}
 (E/'starting-state.json').write_text(json.dumps(before,indent=2)+'\n');(E/'protected.json').write_text(json.dumps(protected,indent=2)+'\n')
 print(json.dumps({'copied':str(db),'checkpoint':cp['id'],'sourceUnchanged':file_hash(source)==protected[str(source.relative_to(ROOT))],'SallyReportedClaims':len(sally['reportedClaims'])}))
if __name__=='__main__':main()
