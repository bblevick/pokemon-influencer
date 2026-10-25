#!/usr/bin/env python3
"""Explicit isolated copy of accepted Save20; original campaign never opened writable."""
import sys,json,sqlite3,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from rival01_prerequisites import protected,METHODS
from campaign.scripted import ScriptedStore
from campaign.budget import CampaignBudget
from world.saves import fingerprint,layout_from_build
E=ROOT/'evidence/phase8/rival01';P=ROOT/'.local/rival01'
def main():
 if P.exists() or (E/'requests.json').exists():raise ValueError('refuse reseeding existing Rival run')
 before=protected();preflight=json.loads((E/'preflight.json').read_text());assert preflight['productionGameplayMayStart']
 P.mkdir();shutil.copy2(ROOT/'evidence/phase8/rival01-prerequisites/manifest-native.json',E/'manifest-native.json');manifest=json.loads((E/'manifest-native.json').read_text());assert hashlib.sha256((ROOT/manifest['rom_path']).read_bytes()).hexdigest()==manifest['rom_sha256']
 src=sqlite3.connect('file:'+str(ROOT/'.local/rocket01/post-rocket-pair.sqlite3')+'?mode=ro',uri=True);dst=sqlite3.connect(P/'world.sqlite3');src.backup(dst);dst.close();src.close();shutil.copy2(ROOT/'.local/rocket01/post-rocket-pair.sav',P/'pokefirered.sav')
 with ScriptedStore(P/'world.sqlite3',E/'manifest-native.json') as w:
  identity=fingerprint((P/'pokefirered.sav').read_bytes(),layout_from_build(ROOT/manifest['rom_path']));cp=w.get_save_checkpoint(identity.fingerprint);assert cp['id']=='fc2eb9f8-d613-4f48-aebf-b2ffa2c44824';assert w.campaign()['cursor']==443
  hashes={m:getattr(w,m)() for m in METHODS}
 with CampaignBudget(E/'requests.json') as b:b.authorize_rival()
 assert protected()==before
 (E/'r0-baseline.json').write_text(json.dumps({'protected':before,'checkpoint':cp,'nativeSave':identity.as_dict(),'projectionHashes':hashes,'romSHA256':manifest['rom_sha256'],'permanentEWRAMDelta':0,'headroomBytes':4,'hostedAttempts':0},indent=2)+'\n')
 print(json.dumps({'checkpoint':cp['id'],'projectionHashes':hashes,'hostedAttempts':0}))
if __name__=='__main__':main()
