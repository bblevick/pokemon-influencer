#!/usr/bin/env python3
"""Add a reviewed ROM qualification row; no combat changes or fixed RAM."""
import sys,json,shutil,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from content.scripted import ScriptedContent
from roster.extract import file_hash
from phase1_events_build import symbols
from world.saves import layout_from_build
from campaign_expansion01_build import ram
import system1_01a_build as base
E=ROOT/'evidence/phase8/rival01-prerequisites';OLD=ROOT/'.local/rocket01-native';DEST=ROOT/'.local/scripted-prereq-native'
def main():
 E.mkdir(parents=True,exist_ok=True)
 reuse='--incremental' in sys.argv
 if DEST.exists() and not reuse:raise ValueError('refuse overwrite native build')
 if reuse and file_hash(DEST/'src/pi_battle.c')!=file_hash(OLD/'src/pi_battle.c'):raise ValueError('incremental source mismatch')
 c=ScriptedContent.load();ids=sorted([414]+[n for p in c.extension['participation'].values() for n in p.get('qualifiedSourceIDs',[p['sourceTrainer']])]);old=json.loads((ROOT/'evidence/phase7/rocket01/manifest-native.json').read_text())
 if not reuse:shutil.copytree(OLD,DEST,ignore=shutil.ignore_patterns('.git','build','pokefirered.gba','*.elf','*.map','*.sav','*.ss*'))
 tag=int(hashlib.sha256(json.dumps([old['rom_sha256'],c.hash,ids]).encode()).hexdigest()[:8],16)
 (DEST/'include/pi_build.h').write_text('#define PI_BUILD_TAG %du\n#define PI_CAMPAIGN_BROCK 1\n#define PI_CAMPAIGN_TRAINERS(X) %s\n'%(tag,' '.join('X(%d)'%n for n in ids)))
 argv=['make','-j8','rom','PI_BRIDGE=1','PI_BRIDGE_TEST=0','PI_EVENTS=1','PI_UI=1','PI_UI_TEST=1','GAME_VERSION=FIRERED','GAME_REVISION=0','GAME_LANGUAGE=ENGLISH','MODERN=0']
 with (E/'native-build.log').open('w') as f:
  f.write(json.dumps({'argv':argv,'cwd':str(DEST)})+'\n');f.flush();r=subprocess.run(argv,cwd=DEST,stdout=f,stderr=subprocess.STDOUT);f.write('\nEXIT_CODE='+str(r.returncode)+'\n')
 if r.returncode:raise ValueError('native build failed')
 base.E=E;base.OLD=OLD;base.DEST=DEST;base.finalize(old['preparation_sources'],tag)
 m=json.loads((E/'manifest-native.json').read_text());syms=symbols(DEST/'pokefirered.elf');before,after=ram(OLD/'pokefirered.elf'),ram(DEST/'pokefirered.elf')
 report={'beforeEnd':old['allocation_end'],'afterEnd':syms['__pi_mailbox_end']['address'],'beforeRemaining':old['ewram_remaining'],'afterRemaining':0x02040000-syms['__pi_mailbox_end']['address'],'allRAMSymbolsIdentical':before==after,'addedRAMRecords':[x for x in after if x not in before],'removedRAMRecords':[x for x in before if x not in after],'nativeDeltaBytes':sum(x[2] for x in after)-sum(x[2] for x in before),'saveLayoutIdentical':layout_from_build(OLD/'pokefirered.gba')==layout_from_build(DEST/'pokefirered.gba'),'changedNativeFiles':['include/pi_build.h'],'combatSourceIdentical':file_hash(OLD/'src/pi_battle.c')==file_hash(DEST/'src/pi_battle.c'),'metric':'defined EWRAM/IWRAM name,address,size tuples; linker end; no stack/heap peak claim'}
 (E/'native-memory.json').write_text(json.dumps(report,indent=2)+'\n')
 if before!=after or report['beforeEnd']!=report['afterEnd'] or report['afterRemaining']<4 or not report['saveLayoutIdentical'] or not report['combatSourceIdentical']:raise ValueError('STOP native RAM/layout/combat regression')
 for key in ('battle_abi','battle_end_revision','terminalRetention','lifecycle_checks'):m[key]=old[key]
 m.update(battle_control=syms['gPiBattle'],qualified_trainers=sorted([102]+ids),allocation_end=report['afterEnd'],ewram_remaining=report['afterRemaining'],campaign_content_sha256=file_hash(ROOT/'config/campaign_content.json'),rocket_content_sha256=file_hash(ROOT/'config/rocket_content.json'),scripted_content_sha256=file_hash(ROOT/'config/scripted_encounters.json'),campaign_profile='data-driven-scripted-singles-v1',battle_scope='isolated scripted constructor qualification; no production encounter result')
 for key in ('battle_sources','preparation_sources'):m[key]={p:file_hash(DEST/p) for p in old[key]}
 (E/'manifest-native.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({'ROM':m['rom_sha256'],'qualified':m['qualified_trainers'],'memory':report}))
if __name__=='__main__':main()
