#!/usr/bin/env python3
"""Isolated explicit Brock profile; native Gym script and constructors preserved."""
import sys,json,shutil,hashlib,subprocess,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
import system1_01a_build as base
from roster.extract import file_hash
from phase1_events_build import symbols
E=ROOT/'evidence/phase4/vertical_slice01';DEST=ROOT/'.local/vertical-slice01-native';OLD=ROOT/'.local/battle01-native-v3'

def main():
 E.mkdir(parents=True,exist_ok=True)
 if DEST.exists():raise ValueError('refuse overwrite of isolated vertical build')
 shutil.copytree(OLD,DEST,ignore=shutil.ignore_patterns('.git','build','pokefirered.gba','*.elf','*.map','*.sav','*.ss*'))
 for n in ('pi_battle.c','pi_battle.h'):shutil.copy2(ROOT/'native/battle01'/n,DEST/('src' if n.endswith('.c') else 'include')/n)
 p=DEST/'src/battle_main.c';s=p.read_text();before='    return gTrainers[trainerNum].partySize;'
 if s.count(before)!=1:raise ValueError('ambiguous trainer constructor return')
 p.write_text(s.replace(before,'    PiBattle_PartyConstructed(trainerNum);\n'+before))
 prior=json.loads((ROOT/'evidence/phase4/battle01/manifest-native.json').read_text())
 paths=set(prior['battle_sources'])|{'src/battle_main.c'}
 files={p:file_hash(DEST/p) for p in sorted(paths)}
 tag=int(hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()[:8],16)
 (DEST/'include/pi_build.h').write_text('#define PI_BUILD_TAG %du\n#define PI_CAMPAIGN_BROCK 1\n'%tag)
 args=['make','-j8','rom','PI_BRIDGE=1','PI_BRIDGE_TEST=0','PI_EVENTS=1','PI_UI=1','PI_UI_TEST=1','GAME_VERSION=FIRERED','GAME_REVISION=0','GAME_LANGUAGE=ENGLISH','MODERN=0']
 with (E/'native-build.log').open('w') as log:
  log.write(json.dumps({'argv':args,'cwd':str(DEST)})+'\n');log.flush();r=subprocess.run(args,cwd=DEST,stdout=log,stderr=subprocess.STDOUT);log.write('\nEXIT_CODE='+str(r.returncode)+'\n')
 if r.returncode:raise ValueError('vertical native build failed')
 base.E=E;base.DEST=DEST;base.OLD=OLD;base.finalize(prior['preparation_sources'],tag)
 path=E/'manifest-native.json';m=json.loads(path.read_text());syms=symbols(DEST/'pokefirered.elf')
 files['include/pi_build.h']=file_hash(DEST/'include/pi_build.h')
 m.update(battle_sources=files,battle_control=syms['gPiBattle'],qualified_trainers=[102,414],battle_scope='controlled prepared Rick and real authored first Brock singles; no new roster options')
 m['preparation_sources']={p:file_hash(DEST/p) for p in m['preparation_sources']}
 m['battle_abi']=list(struct.unpack_from('<9I',(DEST/'pokefirered.gba').read_bytes(),syms['gPiBattleAbi']['address']-0x08000000))
 script='data/maps/PewterCity_Gym/scripts.inc'
 if file_hash(DEST/script)!=file_hash(OLD/script):raise ValueError('Gym script changed')
 m['campaign_checks']={'nativeGymScriptUnchanged':True,'partyConstructorOnlyObservationHook':(DEST/'src/battle_main.c').read_text().replace('    PiBattle_PartyConstructed(trainerNum);\n','')==(OLD/'src/battle_main.c').read_text(),'constructorCounterSymbol':'gPiPreparation','constructorCounterOffset':64,'brockAuthoredParty':True,'inferenceDefault':'offline'}
 if not m['campaign_checks']['partyConstructorOnlyObservationHook']:raise ValueError('constructor changed')
 path.write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':main()
