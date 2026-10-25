#!/usr/bin/env python3
import subprocess,tempfile,sys,re,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def function(s,name):
 start=re.search(r'^(?:static\s+)?\w+\s+'+name+r'\([^;]*?\)\s*\{',s,re.M).start();bracket=s.index('{',start);depth=1;i=bracket+1
 while depth:
  if s[i]=='{':depth+=1
  if s[i]=='}':depth-=1
  i+=1
 return s[start:i]
def main():
 manifest=Path(sys.argv[sys.argv.index('--manifest')+1]) if '--manifest' in sys.argv else ROOT/'evidence/phase4/battle01/manifest-native.json'
 metadata=json.loads(manifest.read_text());build=(ROOT/metadata['rom_path']).parent;source=(build/'src/battle_util.c').read_text();helpers='\n'.join(function(source,n) for n in ('GetImprisonedMovesCount','CheckMoveLimitations','AreAllMovesUnusable'));overlay=(build/'src/pi_battle.c').read_text();rules=overlay[overlay.index('bool8 PiBattle_SwitchAllowed'):overlay.index('static void Capture')];lifecycle='\n'.join(function(overlay,n) for n in (('AuthoredTrainer',) if 'static bool8 AuthoredTrainer' in overlay else ())+ (('QualifiedTrainer',) if 'static bool8 QualifiedTrainer' in overlay else ())+('Supported','Hash','Capture','Execute','PiBattle_Select','PiBattle_Move'));harness=(( '#include \"pi_build.h\"\n' if metadata.get('campaign_profile') else '')+(ROOT/'tests/battle01_native_harness.c').read_text()).replace('/* ENGINE_HELPERS inserted by Python from the actual pinned battle_util.c. */',helpers).replace('/* PROJECT_RULES inserted from the actual compiled overlay through Capture boundary. */',rules).replace('/* LIFECYCLE inserted from the actual project wrapper. */',lifecycle)
 if metadata.get('campaign_profile'):
  checks=''.join('reset();gPiBattle.pointer=1;gPiPreparation.state=0;gTrainerBattleOpponent_A=%d;assert(Supported());'%n for n in metadata['qualified_trainers'] if n!=102)
  checks+='gTrainerBattleOpponent_A=105;assert(!Supported());gTrainerBattleOpponent_A=117;gBattleTypeFlags=BATTLE_TYPE_TRAINER|BATTLE_TYPE_DOUBLE;assert(!Supported());'
  harness=harness.replace('puts("native legality',checks+'puts("native legality')
 if metadata.get('qualified_trainers')==[102,414]:
  harness=harness.replace('puts("native legality', 'reset();gPiBattle.pointer=1;gTrainerBattleOpponent_A=414;gPiPreparation.state=0;assert(Supported());gTrainerBattleOpponent_A=103;assert(!Supported());gTrainerBattleOpponent_A=414;gBattleTypeFlags=BATTLE_TYPE_TRAINER|BATTLE_TYPE_DOUBLE;assert(!Supported());puts("native legality')
 with tempfile.TemporaryDirectory() as t:
  src=Path(t)/'test.c';exe=Path(t)/'test';src.write_text(harness);subprocess.run(['clang',*(['-DPI_CAMPAIGN_BROCK=1'] if metadata.get('qualified_trainers')==[102,414] else []),'-Wno-pointer-to-int-cast','-Wno-int-to-pointer-cast','-I'+str(build/'include'),'-I'+str(build/'src'),'-I'+str(ROOT/'native/battle01'),'-I'+str(ROOT/'native/system1_01a'),str(src),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
