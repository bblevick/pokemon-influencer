#!/usr/bin/env python3
"""Explicit acceptance overlay; all old root source/catalog/builds stay unchanged."""
import sys,json,shutil,subprocess,hashlib,struct,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
import phase1_events_build as b
from roster.extract import file_hash
from world.saves import layout_from_build
E=ROOT/'evidence/phase3/system1_01a';DEST=ROOT/'.local/system1-01a-native';OLD=ROOT/'.local/pokebook01-enabled'
def main():
 if DEST.exists() and (DEST/'pokefirered.gba').exists():raise ValueError('refuse overwrite existing acceptance ROM')
 # Copy accepted isolated source/tools only; do not copy proprietary ROM/save files.
 shutil.copytree(OLD,DEST,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git','build','pokefirered.gba','*.elf','*.map','*.sav','*.ss*'))
 for n in ('pi_preparation.c','pi_preparation.h'):shutil.copy2(ROOT/'native/system1_01a'/n,DEST/('src' if n.endswith('.c') else 'include')/n)
 patches={
 'src/main.c':[('#include "global.h"','#include "global.h"\n#include "pi_preparation.h"'),('    PiBridge_Init();','    PiBridge_Init();\n    PiPreparation_Init();')],
 'src/overworld.c':[('#include "global.h"','#include "global.h"\n#include "pi_preparation.h"'),('static void DoCB1_Overworld(u16 newKeys, u16 heldKeys)\n{\n    struct FieldInput fieldInput;','static void DoCB1_Overworld(u16 newKeys, u16 heldKeys)\n{\n    struct FieldInput fieldInput;\n    if (PiPreparation_Field()) return;')],
 'src/battle_main.c':[('#include "global.h"','#include "global.h"\n#include "pi_preparation.h"'),('    u32 nameHash = 0;','    u8 preparedCount = PiPreparation_CreateParty(party, trainerNum);\n    u32 nameHash = 0;'),('    if (trainerNum == TRAINER_SECRET_BASE)','    if (preparedCount) return preparedCount;\n    if (trainerNum == TRAINER_SECRET_BASE)')],
 'ld_script.ld':[('        __pi_mailbox_end = .;','        KEEP(src/pi_preparation.o(pi_mailbox_data));\n        __pi_mailbox_end = .;')]}
 for path,replacements in patches.items():
  p=DEST/path;s=p.read_text()
  for before,after in replacements:
   if s.count(before)!=1:raise ValueError('ambiguous source patch '+path)
   s=s.replace(before,after)
  p.write_text(s)
 files={str(p.relative_to(DEST)):file_hash(p) for p in [*(DEST/n for n in patches),DEST/'src/pi_preparation.c',DEST/'include/pi_preparation.h']}
 tag=int(hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()[:8],16);(DEST/'include/pi_build.h').write_text('#define PI_BUILD_TAG %du\n'%tag)
 args=['make','-j8','rom','PI_BRIDGE=1','PI_BRIDGE_TEST=0','PI_EVENTS=1','PI_UI=1','PI_UI_TEST=1','GAME_VERSION=FIRERED','GAME_REVISION=0','GAME_LANGUAGE=ENGLISH','MODERN=0']
 with (E/'native-build.log').open('w') as log:
  log.write(json.dumps({'argv':args,'cwd':str(DEST)})+'\n');log.flush();r=subprocess.run(args,cwd=DEST,stdout=log,stderr=subprocess.STDOUT);log.write('EXIT_CODE='+str(r.returncode)+'\n')
 if r.returncode:raise ValueError('native build failed; inspect log')
 finalize(files,tag)
def finalize(files,tag):
 m=json.loads((ROOT/'evidence/phase2/pokebook01/manifest-enabled.json').read_text());syms=b.symbols(DEST/'pokefirered.elf');rom=(DEST/'pokefirered.gba').read_bytes();oldsyms=b.symbols(OLD/'pokefirered.elf')
 def ram_records(elf):
  rows=[]
  for line in subprocess.check_output(['arm-none-eabi-nm','-S','--defined-only',str(elf)],text=True).splitlines():
   parts=line.split()
   if len(parts)==4:
    address,size=int(parts[0],16),int(parts[1],16)
    if 0x02000000<=address<0x02040000 or 0x03000000<=address<0x03008000:rows.append((parts[3],address,size))
  return rows
 new_ram=set(ram_records(DEST/'pokefirered.elf'))
 changed=[v for v in ram_records(OLD/'pokefirered.elf') if v not in new_ram]

 m.update(rom_path=str((DEST/'pokefirered.gba').relative_to(ROOT)),rom_sha256=file_hash(DEST/'pokefirered.gba'),rom_crc32=f'{zlib.crc32(rom)&0xffffffff:08x}',build_tag=tag,build_tag_address=syms['gPiBuildTag']['address'],elf_sha256=file_hash(DEST/'pokefirered.elf'))
 m['mailbox']['address']=syms['gPiMailbox']['address'];m['mailbox']['end']=syms['__pi_mailbox_end']['address'];m['ui_mailbox']['address']=syms['gPiUi']['address'];m['preparation_mailbox']=syms['gPiPreparation'];m['preparation_sources']=files
 m['preparation_checks']={'priorRAMSymbolsUnchanged':not changed,'changed':changed,'size168':syms['gPiPreparation']['size']==168,'saveSectionSizesUnchanged':list(layout_from_build(DEST/'pokefirered.gba'))==list(layout_from_build(OLD/'pokefirered.gba')),'ewramRemaining':0x02040000-syms['__pi_mailbox_end']['address']}
 (E/'manifest-native.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(m['preparation_checks']))
 if not all(m['preparation_checks'][k] for k in ('priorRAMSymbolsUnchanged','size168','saveSectionSizesUnchanged')):raise ValueError('native static acceptance failed')
if __name__=='__main__':main()
