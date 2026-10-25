#!/usr/bin/env python3
"""Isolated pinned-source BRIDGE-02 build; never overwrites the user's dump."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import zlib
import phase0
from generate_pi_events import generate, S
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/phase1/bridge02'
OVERLAY=['Makefile','ld_script.ld','src/main.c','src/pi_bridge.c','include/pi_protocol.h','include/pi_build.h','include/pi_events.h','src/pi_events.c','src/battle_main.c','src/battle_script_commands.c','include/pi_ui.h','src/pi_ui.c','src/overworld.c','src/text_printer.c']

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def symbols(elf):
    result={}
    for line in subprocess.check_output(['arm-none-eabi-nm','-S','--defined-only',str(elf)],text=True).splitlines():
        parts=line.split()
        if len(parts)==4: result[parts[3]]={'address':int(parts[0],16),'size':int(parts[1],16)}
        elif len(parts)==3:result[parts[2]]={'address':int(parts[0],16),'size':0}
    return result

def build(enabled, reuse=False, output_prefix="phase1-events", ui=False):
    if not output_prefix.replace("-", "").isalnum():raise ValueError("output prefix")
    E.mkdir(parents=True,exist_ok=True);fields,size=generate();phase0.doctor()
    mode='enabled' if enabled else 'disabled'
    # Stable output directory name helps repeatability of ELF/map paths.
    dest=ROOT/'.local'/f'{output_prefix}-{mode}'
    if reuse:
        for name in OVERLAY:
            if name != 'include/pi_build.h' and sha(ROOT/name) != sha(dest/name):
                raise SystemExit('Existing build source differs: '+name)
    else:
        if dest.exists():
            raise SystemExit(f'{dest} already exists; use its manifest or move aside for a fresh build')
        dest.mkdir()
        with tempfile.TemporaryFile() as archive:
            subprocess.run(['git','archive',phase0.LOCK['source']['commit']],cwd=ROOT,stdout=archive,check=True)
            archive.seek(0)
            import tarfile
            with tarfile.open(fileobj=archive) as t:t.extractall(dest,filter='data')
        src=Path(phase0.LOCK['toolchain']['binaries']['agbcc']['path']).parent
        install=dest/'tools/agbcc';(install/'bin').mkdir(parents=True);(install/'lib').mkdir()
        shutil.copytree(src/'libc/include',install/'include')
        for p in (src/'ginclude').iterdir():
            if p.is_file():shutil.copy2(p,install/'include'/p.name)
        for name in ['agbcc','old_agbcc','agbcc_arm']:shutil.copy2(src/name,install/'bin'/name)
        for name in ['libgcc.a','libc.a']:shutil.copy2(src/name,install/'lib'/name)
        for name in OVERLAY:shutil.copy2(ROOT/name,dest/name)
    identities={p:sha(ROOT/p) for p in OVERLAY+['bridge/events_protocol.json','bridge/events_mgba.lua']+(['bridge/ui_transport_mgba.lua','bridge/ui_mgba.lua','bridge/ui.py','bridge/ui_protocol.json','schemas/bridge/ui-command.schema.json','schemas/bridge/ui-response.schema.json'] if ui else [])}
    digest=hashlib.sha256(json.dumps({'pin':phase0.LOCK['source']['commit'],'files':identities,'enabled':enabled,'ui':ui},sort_keys=True).encode()).hexdigest()
    tag=int(digest[:8],16)
    if not reuse:
        (dest/'include/pi_build.h').write_text(f'/* Generated content identity; no timestamp. */\n#define PI_BUILD_TAG {tag}u\n')
        args=['make','-j8','rom',f'PI_BRIDGE={int(enabled)}','PI_BRIDGE_TEST=0',f'PI_EVENTS={int(enabled)}',f'PI_UI={int(ui and enabled)}',f'PI_UI_TEST={int(ui and enabled)}','GAME_VERSION=FIRERED','GAME_REVISION=0','GAME_LANGUAGE=ENGLISH','MODERN=0']
        with (E/f'build-{mode}.log').open('w') as log:
            log.write(json.dumps({'command':args,'cwd':str(dest)})+'\n');log.flush()
            p=subprocess.run(args,cwd=dest,stdout=log,stderr=subprocess.STDOUT)
            log.write(f'EXIT_CODE={p.returncode}\n')
        if p.returncode:raise SystemExit(f'build failed: evidence/phase1/build-{mode}.log')
    elf=dest/'pokefirered.elf';rom=dest/'pokefirered.gba';mp=dest/'pokefirered.map'
    syms=symbols(elf);data=rom.read_bytes();baseline=json.loads((ROOT/'evidence/phase0/baseline.json').read_text())
    base=symbols(ROOT/baseline['rom_path'].replace('.gba','.elf'))
    def ram_records(path):
        records=[]
        for line in subprocess.check_output(['arm-none-eabi-nm','-S','--defined-only',str(path)],text=True).splitlines():
            parts=line.split()
            if len(parts)==4:
                address,n=int(parts[0],16),int(parts[1],16)
                if 0x02000000<=address<0x02040000 or 0x03000000<=address<0x03008000:
                    records.append((parts[3],address,n))
            elif len(parts)==3:
                address=int(parts[0],16)
                if 0x02000000<=address<0x02040000 or 0x03000000<=address<0x03008000:
                    records.append((parts[2],address,0))
        return sorted(records)
    original_ram=ram_records(ROOT/baseline['rom_path'].replace('.gba','.elf'))
    new_ram=ram_records(elf)
    changed=[v for v in original_ram if v not in new_ram]
    # Existing allocator boundaries and heap/stack remain unchanged; EWRAM new section follows all prior data.
    checks={'original_ram_symbols_unchanged':not changed,'symbols_compared':len(original_ram),'changed':changed,
            'heap_start':syms['gHeap']['address'],'heap_end':syms['gHeap']['address']+0x1c000,
            'iwram_globals_end':syms['end']['address'],'user_stack_initial':0x03007e40,
            'stack_global_gap':0x03007e40-syms['end']['address']}
    mailbox=None
    if enabled:
        a=syms['gPiMailbox']['address'];n=syms['gPiMailbox']['size'];end=syms['__pi_mailbox_end']['address']
        overlaps=[k for k,address,length in original_ram if length and max(address,a)<min(address+length,a+n)]
        compiled=struct.unpack_from('<'+'I'*(1+len(fields)),data,syms['gPiCompiledLayout']['address']-0x08000000)
        checks.update(mailbox_aligned=a%4==0,mailbox_size=n==size,mailbox_inside_ewram=0x0201c000<=a<end<=0x02040000,
                      no_original_symbol_overlap=not overlaps,overlaps=overlaps,
                      compiled_layout_matches=list(compiled)==[size]+[x['offset'] for x in fields.values()],
                      compiled_build_tag=struct.unpack_from('<I',data,syms['gPiBuildTag']['address']-0x08000000)[0]==tag)
        mailbox={'symbol':'gPiMailbox','address':a,'size':n,'end':end,'region':'EWRAM','fields':fields}
    else:
        checks['disabled_matches_phase0']=sha(rom)==baseline['sha256']
    passed=all(v for k,v in checks.items() if k in ['original_ram_symbols_unchanged','mailbox_aligned','mailbox_size','mailbox_inside_ewram','no_original_symbol_overlap','compiled_layout_matches','compiled_build_tag','disabled_matches_phase0'])
    status=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)
    manifest={'project':'Pokemon Influencer','schema_version':2,'protocol_version':S['protocol_version'],'bridge_version':2,
              'source_commit':phase0.LOCK['source']['commit'],'worktree_dirty':bool(status),'overlay_sha256':identities,
              'build_tag':tag,'build_content_sha256':digest,'build_tag_address':syms.get('gPiBuildTag',{}).get('address'),
              'rom_path':str(rom.relative_to(ROOT)),'rom_sha256':sha(rom),'rom_sha1':hashlib.sha1(data).hexdigest(),
              'rom_crc32':f'{zlib.crc32(data):08x}','rom_size':len(data),'target':{'game':'FIRERED','language':'ENGLISH','revision':0,'modern':False,'bridge_enabled':enabled,'debug_ping':False},
              'diagnostic_symbols':{k:syms[k]['address'] for k in ['gSaveBlock1Ptr','gSaveCounter','gPlayerPartyCount','gPlayerParty','gBattleTypeFlags','gBattleOutcome','gBattleResults','gTrainerBattleOpponent_A','gBattleMons','gBattlerPartyIndexes']},'elf_sha256':sha(elf),'map_sha256':sha(mp),'mailbox':mailbox,'protocol':S,
              'bridge_harness_sha256':sha(ROOT/'bridge/emulator_smoke.lua'),'host_script_sha256':sha(ROOT/'tools/phase1_events_host.py'),'protocol_codec_sha256':sha(ROOT/'bridge/events.py'),'emulator':phase0.LOCK['emulator'],'allocation_checks':checks,'static_passed':passed, 'allocation_end':syms['__pi_mailbox_end']['address'], 'ewram_remaining':0x02040000-syms['__pi_mailbox_end']['address']}
    (E/f'manifest-{mode}.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if not passed:raise SystemExit('Static allocation/layout checks failed')
    print(json.dumps({'mode':mode,'rom_sha256':manifest['rom_sha256'],'mailbox':mailbox and {k:mailbox[k] for k in ['address','size','end']},'static_passed':passed, 'allocation_end':syms['__pi_mailbox_end']['address'], 'ewram_remaining':0x02040000-syms['__pi_mailbox_end']['address']},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--disabled',action='store_true');p.add_argument('--verify-existing',action='store_true');p.add_argument('--output-prefix',default='phase1-events');p.add_argument('--evidence-dir',default='evidence/phase1/bridge02');a=p.parse_args();E=ROOT/a.evidence_dir;build(not a.disabled,a.verify_existing,a.output_prefix)
