#!/usr/bin/env python3
"""Managed continuous campaign launch from an explicit pre-Rick normal battery."""
import sys,json,argparse,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
import vertical_slice01_host as binding
from vertical_slice01_host import E,PRIVATE,manifest_path,manifest,open_store,save_identity
import strategy01_launch as retained

def main():
 p=argparse.ArgumentParser();p.add_argument('--seed',type=Path);p.add_argument('--restore',type=Path);p.add_argument('--start',action='store_true');p.add_argument('--manifest',type=Path);a=p.parse_args();binding.MANIFEST_OVERRIDE=a.manifest
 E.mkdir(parents=True,exist_ok=True);PRIVATE.mkdir(parents=True,exist_ok=True);screens=ROOT/'evidence/private/vertical_slice01';screens.mkdir(parents=True,exist_ok=True)
 db=PRIVATE/'world.sqlite3';save=PRIVATE/'pokefirered.sav'
 if a.seed:
  if db.exists() or save.exists():raise ValueError('refuse seed into existing campaign')
  source=a.seed.resolve();identity=save_identity(source)
  from prep.progression import read_boulder
  old=json.loads((ROOT/'config/prep_save_layout.json').read_text())
  if any(read_boulder(source.read_bytes(),old['romSHA256'])['flags'].values()):raise ValueError('seed already contains Boulder progression')
  shutil.copy2(source,save)
  from world.store import WorldStore
  from system1.native import verify_build
  proof,_=verify_build(ROOT/'evidence/phase3/system1_01a/manifest-native.json')
  with WorldStore(db,proof['baselineROM'],proof['baselineTag']) as w:w.import_save(identity)
  (E/'seed.json').write_text(json.dumps({'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'identity':identity.as_dict(),'workflow':'explicit imported pre-Rick normal battery; no fabricated prior host events'},indent=2)+'\n')
 for name,value in {'E':E,'PRIVATE':PRIVATE,'CONFIG':PRIVATE/'launch.json','SCREENS':screens,'manifest':manifest,'open_store':open_store,'save_identity':save_identity}.items():setattr(retained,name,value)
 def activate(w,cp):
  if cp['kind']=='explicit_import' and w.virality_state().get('activation') is None:w.activate_virality()
 retained.prepare(False,a.restore,launch_hook=activate,manifest_path=manifest_path())
 script=PRIVATE/'run.lua'
 text=script.read_text().replace('if PI_UI_receive and kind>=4 then','if PI_BATTLE_receive and kind>=8 then PI_BATTLE_receive(kind,nonce,gen,seq,typ,data);return end\n if PI_UI_receive and kind>=4 then')
 script.write_text(text)
 with script.open('a') as f:f.write('\n'+(ROOT/'bridge/campaign_constructor_receipt.lua').read_text()+'\n'+(ROOT/('native/battle_end01/transport.lua' if manifest().get('battle_end_revision') else 'native/battle01/transport.lua')).read_text())
 # Publish final, exact script hash after all lifecycle adapters are appended.
 (E/'script.json').write_text(json.dumps({'path':str(script),'sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'initialManualScriptLoadRequired':True},indent=2)+'\n')
 if a.start:
  import subprocess
  subprocess.run([str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA'),'-C','hwaccelVideo=0','-C','savegamePath='+str(PRIVATE),str(ROOT/manifest()['rom_path'])],cwd=ROOT,check=True)
if __name__=='__main__':main()
