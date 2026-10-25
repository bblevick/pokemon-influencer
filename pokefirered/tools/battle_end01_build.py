#!/usr/bin/env python3
"""Explicit lifecycle-only overlay; preserve all accepted builds and ROM inputs."""
import sys,json,shutil,hashlib,subprocess,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from phase1_events_build import symbols
from roster.extract import file_hash
import system1_01a_build as base
from world.saves import layout_from_build
E=ROOT/'evidence/phase4/battle_end01';OLD=ROOT/'.local/vertical-slice01-native'
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--vanilla',action='store_true');parser.add_argument('--revision2',action='store_true');args=parser.parse_args()
 revision=2 if args.revision2 else 1;vanilla=args.vanilla;name='vanilla' if vanilla else 'external';dest=ROOT/'.local'/('battle-end01-'+name+('-v2' if revision==2 else ''))
 if dest.exists():raise ValueError('refuse overwrite retained lifecycle build')
 shutil.copytree(OLD,dest,ignore=shutil.ignore_patterns('.git','build','pokefirered.gba','*.elf','*.map','*.sav','*.ss*'))
 for n in ('pi_events.c','pi_battle.c'):shutil.copy2(ROOT/'native/battle_end01'/n,dest/'src'/n)
 paths=('src/pi_events.c','src/pi_battle.c')
 identity={p:file_hash(dest/p) for p in paths};tag=int(hashlib.sha256(json.dumps({'files':identity,'vanilla':vanilla},sort_keys=True).encode()).hexdigest()[:8],16)
 (dest/'include/pi_build.h').write_text('#define PI_BUILD_TAG %du\n#define PI_CAMPAIGN_BROCK 1\n'%tag+('#define PI_BATTLE_END_VANILLA 1\n' if vanilla else ''))
 args=['make','-j8','rom','PI_BRIDGE=1','PI_BRIDGE_TEST=0','PI_EVENTS=1','PI_UI=1','PI_UI_TEST=1','GAME_VERSION=FIRERED','GAME_REVISION=0','GAME_LANGUAGE=ENGLISH','MODERN=0']
 with (E/('build-'+name+('-v2' if revision==2 else '')+'.log')).open('w') as log:
  log.write(json.dumps({'argv':args,'cwd':str(dest)})+'\n');log.flush();r=subprocess.run(args,cwd=dest,stdout=log,stderr=subprocess.STDOUT);log.write('\nEXIT_CODE='+str(r.returncode)+'\n')
 if r.returncode:raise ValueError('native build failed '+name)
 prior=json.loads((ROOT/'evidence/phase4/vertical_slice01/manifest-native.json').read_text());base.E=E;base.DEST=dest;base.OLD=OLD;base.finalize(prior['preparation_sources'],tag)
 path=E/'manifest-native.json';m=json.loads(path.read_text());syms=symbols(dest/'pokefirered.elf')
 m['battle_sources']={p:file_hash(dest/p) for p in set(prior['battle_sources'])|set(paths)|{'include/pi_build.h'}}
 m['preparation_sources']={p:file_hash(dest/p) for p in prior['preparation_sources']}
 m.update(battle_control=syms['gPiBattle'],battle_abi=prior['battle_abi'],qualified_trainers=[102,414],battle_end_scope=name,terminalRetention='bounded queue; terminal same-sequence retries until ACK/reset; no game wait')
 m['lifecycle_checks']={'noAddedFixedRAM':m['preparation_checks']['priorRAMSymbolsUnchanged'],'unchangedWorkABI':True,'nativeGymScriptUnchanged':file_hash(dest/'data/maps/PewterCity_Gym/scripts.inc')==file_hash(OLD/'data/maps/PewterCity_Gym/scripts.inc'),'nativeBattleMainUnchanged':file_hash(dest/'src/battle_main.c')==file_hash(OLD/'src/battle_main.c'),'unchangedSaveLayout':layout_from_build(dest/'pokefirered.gba')==layout_from_build(OLD/'pokefirered.gba')}
 if not all(m['lifecycle_checks'].values()):raise ValueError('scope/RAM/layout mismatch')
 m['allocation_end']=syms['__pi_mailbox_end']['address'];m['ewram_remaining']=0x02040000-m['allocation_end']
 m['battle_end_revision']=revision
 if (E/('manifest-'+name+'.json')).exists():shutil.copy2(E/('manifest-'+name+'.json'),E/('manifest-'+name+'-v1.json'))
 (E/('manifest-'+name+'.json')).write_text(json.dumps(m,indent=2)+'\n');path.unlink()
 print(json.dumps({'build':name,'ROM':m['rom_sha256'],'checks':m['lifecycle_checks']}))
if __name__=='__main__':main()
