#!/usr/bin/env python3
"""Controlled native proof; first launch explicitly continues only unsaved prep."""
import argparse,json,secrets,shutil,subprocess,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from system1.native import NativePreparationStore,encode_plan
from world.saves import fingerprint,layout_from_build
from phase1_events_launch import lua
from phase1_events_build import symbols
E=ROOT/'evidence/phase3/system1_01a';PRIVATE=ROOT/'.local/system1_01a';CONFIG=PRIVATE/'launch.json';SCREENS=ROOT/'evidence/private/system1_01a';MANIFEST=E/'manifest-native.json'
def open_store(path):return NativePreparationStore(path,MANIFEST)
def manifest():return json.loads(MANIFEST.read_text())
def save_identity(path):return fingerprint(Path(path).read_bytes(),layout_from_build(ROOT/manifest()['rom_path']))
def main():
 p=argparse.ArgumentParser();p.add_argument('--start',action='store_true');p.add_argument('--retry-unstarted-launch',action='store_true');p.add_argument('--continue-preparation',action='store_true');p.add_argument('--restore',type=Path);a=p.parse_args();m=manifest();SCREENS.mkdir(parents=True,exist_ok=True)
 if subprocess.run(['pgrep','-f','^'+str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA')],stdout=subprocess.DEVNULL).returncode==0:raise ValueError('stop task-local mGBA first')
 save=PRIVATE/'pokefirered.sav'
 if a.restore:shutil.copy2(a.restore,save)
 if not save.exists():shutil.copy2(ROOT/'.local/strategy01-memo/after-live-memo.sav',save)
 nonce=json.loads(CONFIG.read_text())['nonce'] if a.retry_unstarted_launch else secrets.randbelow(0xffffffff)+1
 with open_store(PRIVATE/'world.sqlite3') as w:
  if a.retry_unstarted_launch:
   if (E/'launches.jsonl').exists() or any('nativeDelivery' in p for p in w.decision_state().get('nativeProvenance',{}).values()):raise ValueError('only never-started launch recovery')
   origin=w._launch(nonce,1)['id']
  else:origin=w.resume_unpaired_preparation(nonce,save_identity(save)) if a.continue_preparation else w.authorize_launch(nonce,save_identity(save))
  commit=w.locked_preparation('trainer:fr:trainer:0102')
  if not commit:raise ValueError('no active locked preparation')
  packet=encode_plan(commit,nonce,1,1,m['build_tag']);compat=w.compatibility
 cfg={'manifest':str(MANIFEST),'port':18782,'nonce':nonce,'token':secrets.token_hex(16),'origin':origin,'database':str(PRIVATE/'world.sqlite3'),'save':str(save),'log':str(E/'emulator.jsonl'),'screenshots':str(SCREENS),'receipts':str(E/'save-receipts.jsonl')};CONFIG.write_text(json.dumps(cfg,indent=2)+'\n');CONFIG.chmod(0o600)
 syms=symbols(ROOT/m['rom_path'].replace('.gba','.elf'));m['diagnostic_symbols'].update({k:syms[k]['address'] for k in ('gHeap','gTasks','gWindows','gSprites','sPb','gPlayerAvatar','gObjectEvents','gEnemyParty')})
 binary='"'+''.join('\\%03d'%x for x in bytes.fromhex(m['rom_sha256']))+'"';prefix='PI_MANIFEST='+lua(m)+'\nPI_MANIFEST.rom_sha256_binary='+binary+'\nPI_CONFIG='+lua(cfg)+'\nPI_PREP_PACKET="'+''.join('\\%03d'%x for x in packet)+'"\n'
 # Reuse the tested receipt/input harness verbatim with isolated destinations.
 source=(ROOT/'tools/strategy01_launch.py').read_text();start=source.index(" harness=(ROOT/'bridge/emulator_smoke.lua')");end=source.index(" script=PRIVATE/",start)
 import ast
 tree=ast.parse(source);body=next(n.body for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare');assignments=[n for n in body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('harness','test') for t in n.targets)];namespace={'ROOT':ROOT};exec(compile(ast.Module(body=assignments,type_ignores=[]),'retained-harness','exec'),namespace);harness=namespace['harness'];test=namespace['test']
 test=test.replace("else error('unknown input command')end","elseif cmd=='prepared' then PI_PREP_publish()\n  else error('unknown input command')end")
 extension=(ROOT/'native/system1_01a/preparation_probe.lua').read_text();script=PRIVATE/'run.lua';script.write_text(prefix+'\n'+(ROOT/'bridge/ui_transport_mgba.lua').read_text()+'\n'+(ROOT/'bridge/ui_mgba.lua').read_text()+'\n'+harness+'\n'+test+'\n'+extension);script.chmod(0o600)
 argv=[str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA'),'-C','hwaccelVideo=0','-C','savegamePath='+str(PRIVATE),str(ROOT/m['rom_path'])]
 r={'argv':argv,'origin':origin,'nonce':nonce,'script':str(script),'scriptSHA256':hashlib.sha256(script.read_bytes()).hexdigest(),'save':save_identity(save).as_dict(),'compatibility':compat,'workflow':'explicit prep-only continuation' if a.continue_preparation else 'ordinary paired restore; no inference'}
 with (E/'launches.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
 print(json.dumps(r,indent=2),flush=True)
 if a.start:subprocess.run(argv,cwd=ROOT,check=True,restore_signals=False)
if __name__=='__main__':main()
