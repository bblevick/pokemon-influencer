#!/usr/bin/env python3
"""Fresh paired Save19/accepted BATTLE-01 ROM; no new roster or native build."""
import sys,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
import system1_01a_launch as retained
from battle.store import BattleStore
E=ROOT/'evidence/phase4/system1_01b';PRIVATE=ROOT/'.local/system1_01b';CONFIG=PRIVATE/'launch.json';SCREENS=ROOT/'evidence/private/system1_01b';MANIFEST=ROOT/'evidence/phase4/battle01/manifest-native.json'
def open_store(path):return BattleStore(path,MANIFEST)
def manifest():return json.loads(MANIFEST.read_text())
def save_identity(path):return retained.save_identity(path)
for n in ('E','PRIVATE','CONFIG','SCREENS','MANIFEST','open_store','manifest'):setattr(retained,n,globals()[n])
if __name__=='__main__':
 if not (PRIVATE/'pokefirered.sav').exists():shutil.copy2(ROOT/'.local/system1_01a/installed-save19.sav',PRIVATE/'pokefirered.sav')
 start='--start' in sys.argv
 if start:sys.argv.remove('--start')
 retained.main();p=PRIVATE/'run.lua';s=p.read_text().replace("elseif cmd=='prepared' then PI_PREP_publish()","elseif cmd=='prepared' then PI_BATTLE_arm();PI_PREP_publish()")
 s=s.replace('if PI_UI_receive and kind>=4 then','if PI_BATTLE_receive and kind>=8 then PI_BATTLE_receive(kind,nonce,gen,seq,typ,data);return end\n if PI_UI_receive and kind>=4 then');s+='\n'+(ROOT/'native/battle01/transport.lua').read_text();p.write_text(s)
 if start:subprocess.run([str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA'),'-C','hwaccelVideo=0','-C','savegamePath='+str(PRIVATE),str(ROOT/manifest()['rom_path'])],cwd=ROOT,check=True,restore_signals=False)
