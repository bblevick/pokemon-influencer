#!/usr/bin/env python3
"""Generic ROM qualification rows; zero permanent RAM permitted."""
import sys,json,shutil,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from roster.extract import file_hash
from phase1_events_build import symbols
from world.saves import layout_from_build
import system1_01a_build as base
E=ROOT/'evidence/phase6/campaign_expansion01';OLD=ROOT/'.local/battle-end01-external-v2';DEST=ROOT/'.local/campaign-expansion01-native'
def ram(elf):
 rows=[]
 for line in subprocess.check_output(['arm-none-eabi-nm','-S','--defined-only',str(elf)],text=True).splitlines():
  p=line.split()
  if len(p)==4 and (0x02000000<=int(p[0],16)<0x02040000 or 0x03000000<=int(p[0],16)<0x03008000):rows.append((p[3],int(p[0],16),int(p[1],16)))
 return sorted(rows)
def main():
 E.mkdir(parents=True,exist_ok=True)
 if DEST.exists():raise ValueError('refuse overwrite native build')
 content=json.loads((ROOT/'config/campaign_content.json').read_text());ids=sorted([414]+[t['sourceTrainer'] for t in content['participation'].values()])
 shutil.copytree(OLD,DEST,ignore=shutil.ignore_patterns('.git','build','pokefirered.gba','*.elf','*.map','*.sav','*.ss*'))
 p=DEST/'src/pi_battle.c';s=p.read_text()
 start=s.index('static bool8 QualifiedTrainer(void)');end=s.index('static bool8 Supported(void)',start)
 s=s[:start]+'''/* Qualification is ROM data generated from reviewed content, no per-trainer RAM. */
static bool8 AuthoredTrainer(u16 trainer)
{
 switch(trainer) {
#define PI_TRAINER_CASE(id) case id: return TRUE;
 PI_CAMPAIGN_TRAINERS(PI_TRAINER_CASE)
#undef PI_TRAINER_CASE
 default: return FALSE;
 }
}
static bool8 QualifiedTrainer(void)
{
 return AuthoredTrainer(gTrainerBattleOpponent_A)
  || (gTrainerBattleOpponent_A == 102 && gPiPreparation.state == 3);
}
void PiBattle_PartyConstructed(u16 trainer)
{
 if (AuthoredTrainer(trainer) && (gBattleTypeFlags & BATTLE_TYPE_TRAINER)
  && !(gBattleTypeFlags & ~(BATTLE_TYPE_TRAINER|BATTLE_TYPE_IS_MASTER)))
  gPiPreparation.installations++;
}
'''+s[end:]
 before='#ifdef PI_CAMPAIGN_BROCK\n if (gTrainerBattleOpponent_A == 414) armed = TRUE;\n#endif'
 if s.count(before)!=1:raise ValueError('ambiguous activation')
 p.write_text(s.replace(before,' if (AuthoredTrainer(gTrainerBattleOpponent_A)) armed = TRUE;'))
 tag=int(hashlib.sha256(json.dumps([file_hash(p),content,ids],sort_keys=True).encode()).hexdigest()[:8],16)
 (DEST/'include/pi_build.h').write_text('#define PI_BUILD_TAG %du\n#define PI_CAMPAIGN_BROCK 1\n#define PI_CAMPAIGN_TRAINERS(X) %s\n'%(tag,' '.join('X(%d)'%n for n in ids)))
 argv=['make','-j8','rom','PI_BRIDGE=1','PI_BRIDGE_TEST=0','PI_EVENTS=1','PI_UI=1','PI_UI_TEST=1','GAME_VERSION=FIRERED','GAME_REVISION=0','GAME_LANGUAGE=ENGLISH','MODERN=0']
 with (E/'native-build.log').open('w') as f:
  f.write(json.dumps({'argv':argv,'cwd':str(DEST)})+'\n');f.flush();r=subprocess.run(argv,cwd=DEST,stdout=f,stderr=subprocess.STDOUT);f.write('\nEXIT_CODE='+str(r.returncode)+'\n')
 if r.returncode:raise ValueError('native build failed')
 old=json.loads((ROOT/'evidence/phase4/battle_end01/manifest-external.json').read_text());base.E=E;base.OLD=OLD;base.DEST=DEST;base.finalize(old['preparation_sources'],tag)
 m=json.loads((E/'manifest-native.json').read_text());syms=symbols(DEST/'pokefirered.elf')
 before,after=ram(OLD/'pokefirered.elf'),ram(DEST/'pokefirered.elf')
 report={'beforeEnd':old['allocation_end'],'afterEnd':syms['__pi_mailbox_end']['address'],'beforeRemaining':old['ewram_remaining'],'afterRemaining':0x02040000-syms['__pi_mailbox_end']['address'],'allRAMSymbolsIdentical':before==after,'addedRAMRecords':[x for x in after if x not in before],'removedRAMRecords':[x for x in before if x not in after],'nativeDeltaBytes':sum(x[2] for x in after)-sum(x[2] for x in before),'saveLayoutIdentical':layout_from_build(OLD/'pokefirered.gba')==layout_from_build(DEST/'pokefirered.gba'),'metric':'all defined EWRAM/IWRAM symbol (name,address,size) tuples and linker __pi_mailbox_end; no stack/heap peak claim'}
 (E/'native-memory.json').write_text(json.dumps(report,indent=2)+'\n')
 if before!=after or report['beforeEnd']!=report['afterEnd'] or not report['saveLayoutIdentical']:raise ValueError('STOP native memory/layout regression')
 # Start from actual current finalized ELF values, retain accepted ABI contracts.
 for key in ('battle_abi','battle_end_revision','terminalRetention','lifecycle_checks'):m[key]=old[key]
 m.update(battle_control=syms['gPiBattle'],qualified_trainers=sorted([102]+ids),allocation_end=report['afterEnd'],ewram_remaining=report['afterRemaining'],campaign_content_sha256=file_hash(ROOT/'config/campaign_content.json'),campaign_profile='data-driven-authored-singles-v1',battle_scope='existing generic authored singles; no new items/modes')
 m['battle_sources']={p:file_hash(DEST/p) for p in old['battle_sources']}
 m['preparation_sources']={p:file_hash(DEST/p) for p in old['preparation_sources']}
 (E/'manifest-native.json').write_text(json.dumps(m,indent=2)+'\n')
 print(json.dumps({'ROM':m['rom_sha256'],'qualified':m['qualified_trainers'],'memory':report}))
if __name__=='__main__':main()
