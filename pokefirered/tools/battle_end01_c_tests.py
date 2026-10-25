#!/usr/bin/env python3
"""Compile actual overlay with explicit game stubs; not emulator evidence."""
import sys,subprocess,shutil,tempfile,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from battle01_c_tests import function
build=(ROOT/json.loads((ROOT/'evidence/phase4/battle_end01/manifest-external.json').read_text())['rom_path']).parent
with tempfile.TemporaryDirectory() as td:
 t=Path(td);(t/'constants').mkdir()
 for p in ('tests/c_stubs/global.h','tests/c_stubs/battle.h','tests/c_stubs/battle_anim.h','tests/c_stubs/battle_setup.h'):shutil.copy2(ROOT/p,t/Path(p).name)
 for p in ('include/pi_events.h','include/pi_build.h'):shutil.copy2(build/p,t/Path(p).name)
 shutil.copy2(build/'include/constants/battle.h',t/'constants/battle.h')
 for name,test,defines in (('terminal','tests/pi_terminal_test.c',[]),('retained-events','tests/pi_events_test.c',['-DPI_EVENTS_NATIVE_TEST=1']),('retained-observation','tests/pi_observation_test.c',[])):
  exe=t/name;subprocess.run(['clang','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-D__attribute__(x)=','-DPI_EVENTS=1',*defines,'-I'+str(t),str(ROOT/test),str(build/'src/pi_events.c'),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
 source=(build/'src/battle_util.c').read_text();overlay=(build/'src/pi_battle.c').read_text()
 helpers='\n'.join(function(source,n) for n in ('GetImprisonedMovesCount','CheckMoveLimitations','AreAllMovesUnusable'))
 rules=overlay[overlay.index('bool8 PiBattle_SwitchAllowed'):overlay.index('static void Capture')]
 names=('QualifiedTrainer','Supported','Hash','Capture','Execute','PiBattle_Select','PiBattle_Move','PiBattle_End')
 lifecycle='static int freed;static void Free(void *p){(void)p;freed++;}\n'+'\n'.join(function(overlay,n) for n in names)
 h=(ROOT/'tests/battle01_native_harness.c').read_text().replace('/* ENGINE_HELPERS inserted by Python from the actual pinned battle_util.c. */',helpers).replace('/* PROJECT_RULES inserted from the actual compiled overlay through Capture boundary. */',rules).replace('/* LIFECYCLE inserted from the actual project wrapper. */',lifecycle)
 h=h.replace('puts("native legality', '''reset();gPiBattle.state=1;gBattleOutcome=B_OUTCOME_WON;{u32 req=gPiBattle.request;assert(PiBattle_Select(PB_NORMAL)==0 && PiBattle_Select(PB_REPLACE)==0 && gPiBattle.request==req);}PiBattle_End();assert(gPiBattle.pointer==0 && gPiBattle.state==6 && freed==1);reset();gPiBattle.pointer=1;gPiBattle.state=4;fixtureWork.lastSource=1;PiBattle_End();assert(gPiBattle.state==7);reset();gPiBattle.pointer=1;gPiBattle.state=4;fixtureWork.lastSource=3;PiBattle_End();assert(gPiBattle.state==8);reset();gPiBattle.pointer=1;gPiBattle.state=5;fixtureWork.lastReason=2;PiBattle_End();assert(gPiBattle.state==9);reset();gPiBattle.pointer=1;gPiBattle.state=5;fixtureWork.lastReason=3;PiBattle_End();assert(gPiBattle.state==10);puts("PASS no terminal tactical request; stable copied controller disposition before heap free");puts("native legality''')
 sub=t/'battle-fixture';sub.mkdir();src=sub/'battle.c';src.write_text(h);exe=sub/'battle';subprocess.run(['clang','-DPI_CAMPAIGN_BROCK=1','-Wno-pointer-to-int-cast','-Wno-int-to-pointer-cast','-I'+str(build/'include'),'-I'+str(build/'src'),'-I'+str(ROOT/'native/battle01'),'-I'+str(ROOT/'native/system1_01a'),str(src),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
