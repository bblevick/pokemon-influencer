#!/usr/bin/env python3
"""Isolated BATTLE-01 overlay; preserves accepted root/ROM/save/catalog inputs."""
import sys,json,shutil,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
import system1_01a_build as base
from roster.extract import file_hash
from phase1_events_build import symbols
E=ROOT/'evidence/phase4/battle01';DEST=ROOT/'.local/battle01-native-v3';OLD=ROOT/'.local/system1-01a-native-v3'
def main():
 if (DEST/'pokefirered.gba').exists():raise ValueError('refuse existing build')
 shutil.copytree(OLD,DEST,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git','build','pokefirered.gba','*.elf','*.map','*.sav','*.ss*'))
 for n in ('pi_battle.c','pi_battle.h'):shutil.copy2(ROOT/'native/battle01'/n,DEST/('src' if n.endswith('.c') else 'include')/n)
 patches={
 'src/main.c':[('    PiPreparation_Init();','    PiPreparation_Init();\n    PiBattle_Init();')],
 'src/battle_main.c':[('    PiEvents_BattleStart();','    PiEvents_BattleStart();\n    PiBattle_Start();'),('    PiEvents_End();','    PiEvents_End();\n    PiBattle_End();'),('        PiEvents_Action(gBattlerByTurnOrder[gBattleStruct->savedTurnActionNumber],\n                        gActionsByTurnOrder[gBattleStruct->savedTurnActionNumber]);','    {\n        PiEvents_Action(gBattlerByTurnOrder[gBattleStruct->savedTurnActionNumber],\n                        gActionsByTurnOrder[gBattleStruct->savedTurnActionNumber]);\n        PiBattle_Resolved(gBattlerByTurnOrder[gBattleStruct->savedTurnActionNumber],\n                        gActionsByTurnOrder[gBattleStruct->savedTurnActionNumber]);\n    }')],
 'src/battle_script_commands.c':[('        PiEvents_Reveal();','        PiEvents_Reveal();\n        PiBattle_Reveal();')],
 'src/battle_controller_opponent.c':[('static void OpponentHandleChooseAction(void)\n{','static void OpponentHandleChooseAction(void)\n{\n    u8 external = PiBattle_Select(PB_NORMAL);\n    if (external == 1) return;\n    if (external == 2) { OpponentBufferExecCompleted(); return; }'),('    struct ChooseMoveStruct *moveInfo = (struct ChooseMoveStruct *)(&gBattleBufferA[gActiveBattler][4]);','    struct ChooseMoveStruct *moveInfo = (struct ChooseMoveStruct *)(&gBattleBufferA[gActiveBattler][4]);\n    if (PiBattle_Move()) { OpponentBufferExecCompleted(); return; }'),('    s32 chosenMonId;','    s32 chosenMonId;\n    u8 external = PiBattle_Select(PB_REPLACE);\n    if (external == 1) return;\n    if (external == 2) { OpponentBufferExecCompleted(); return; }')],
 'ld_script.ld':[('        __pi_mailbox_end = .;','        KEEP(src/pi_battle.o(pi_mailbox_data));\n        __pi_mailbox_end = .;')]}
 for path,replacements in patches.items():
  p=DEST/path;s=p.read_text()
  if path.endswith('.c'):s=s.replace('#include "global.h"','#include "global.h"\n#include "pi_battle.h"',1)
  for before,after in replacements:
   if s.count(before)!=1:raise ValueError('ambiguous '+path)
   s=s.replace(before,after)
  p.write_text(s)
 files={n:file_hash(DEST/n) for n in [*patches,'src/pi_battle.c','include/pi_battle.h']};tag=int(hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()[:8],16);(DEST/'include/pi_build.h').write_text('#define PI_BUILD_TAG %du\n'%tag)
 args=['make','-j8','rom','PI_BRIDGE=1','PI_BRIDGE_TEST=0','PI_EVENTS=1','PI_UI=1','PI_UI_TEST=1','GAME_VERSION=FIRERED','GAME_REVISION=0','GAME_LANGUAGE=ENGLISH','MODERN=0']
 with (E/'native-build.log').open('w') as log:r=subprocess.run(args,cwd=DEST,stdout=log,stderr=subprocess.STDOUT);log.write('\nEXIT_CODE='+str(r.returncode)+'\n')
 if r.returncode:raise ValueError('build failed')
 base.E=E;base.DEST=DEST;base.OLD=OLD;base.finalize(json.loads((ROOT/'evidence/phase3/system1_01a/manifest-native.json').read_text())['preparation_sources'],tag)
 p=E/'manifest-native.json';m=json.loads(p.read_text());syms=symbols(DEST/'pokefirered.elf');m['battle_sources']=files;m['battle_control']=syms['gPiBattle'];m['preparation_sources']={n:file_hash(DEST/n) for n in m['preparation_sources']};m['battle_scope']='controlled prepared Rick, ordinary single trainer, deterministic only';
 import struct
 address=syms['gPiBattleAbi']['address'];m['battle_abi']=list(struct.unpack_from('<9I',(DEST/'pokefirered.gba').read_bytes(),address-0x08000000));p.write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':main()
