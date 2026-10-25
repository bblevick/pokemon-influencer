#!/usr/bin/env python3
"""Supported fresh-process launcher; manual native File > Load once."""
import argparse,json,hashlib,secrets,shutil,subprocess
from phase1_events_launch import lua
from phase1_ui_build import ROOT,E,verify_ui

def prepare(start=False):
 m=json.loads((E/'manifest-enabled.json').read_text());verify_ui(m)
 for file,digest in m['ui_harness_sha256'].items():
  if hashlib.sha256((ROOT/file).read_bytes()).hexdigest()!=digest:raise ValueError('UI harness changed')
 private=ROOT/'.local/phase1-ui-emulator';private.mkdir(exist_ok=True)
 screenshots=ROOT/'evidence/private/bridge03';screenshots.mkdir(parents=True,exist_ok=True)
 save=private/'pokefirered.sav'
 if not save.exists():shutil.copy2(ROOT/'.local/phase1-events-emulator/pre-rick-final-build.sav',save)
 cfg={'manifest':'evidence/phase1/bridge03/manifest-enabled.json','port':18772,'nonce':secrets.randbelow(0xffffffff)+1,'token':secrets.token_hex(16),'checkpoint':str(private/'scenario-checkpoint.ss0'),'log':str(E/'emulator.jsonl'),'screenshots':str(screenshots)}
 p=ROOT/'.local/phase1-ui-launch.json';p.write_text(json.dumps(cfg,indent=2)+'\n');p.chmod(0o600)
 binary='"'+''.join('\\%03d'%x for x in bytes.fromhex(m['rom_sha256']))+'"'
 prefix='PI_MANIFEST='+lua(m)+'\nPI_MANIFEST.rom_sha256_binary='+binary+'\nPI_CONFIG='+lua(cfg)+'\n'
 test=(ROOT/'bridge/events_emulator_smoke.lua').read_text()
 test=test.replace("elseif cmd=='sample' then", "elseif cmd=='ui' then assert(a=='1' or a=='2');table.insert(PI_TEST.queue,{ui=tonumber(a)})\n  elseif cmd=='uisample' then PI.log('ui-diagnostic',string.format('state=%d request=%d command=%d result=%d choice=%d run=%d',PI_UI.read('state'),PI_UI.read('request_id'),PI_UI.read('command_id'),PI_UI.read('result'),PI_UI.read('choice_id'),PI_UI.read('run_generation')))\n  elseif cmd=='sample' then")
 test=test.replace("assert(emu:loadStateFile(PI.cfg.checkpoint,C.SAVESTATE.ALL));", "assert(emu:loadStateFile(PI.cfg.checkpoint,C.SAVESTATE.ALL));PI_UI.boundary('managed rollback');")
 harness=(ROOT/'bridge/emulator_smoke.lua').read_text().replace('if item.shot then', "if item.ui then PI_UI.write('trigger',item.ui)\n elseif item.shot then")
 sources=['bridge/ui_transport_mgba.lua','bridge/ui_mgba.lua','bridge/emulator_smoke.lua']
 script=ROOT/'.local/ui-bridge-run.lua';script.write_text(prefix+'\n'.join(harness if x=='bridge/emulator_smoke.lua' else (ROOT/x).read_text() for x in sources)+'\n'+test);script.chmod(0o600)
 argv=[str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA'),'-C','hwaccelVideo=0','-C','savegamePath='+str(private),str(ROOT/m['rom_path'])]
 report={'argv':argv,'manifest':cfg['manifest'],'script':str(script),'script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'manual_step':'Tools > Scripting > File > Load once in a fresh process','credentials_used':False,'token_redacted':True}
 (E/'launch.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
 if start:subprocess.run(argv,cwd=ROOT,check=True,restore_signals=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--start',action='store_true');a=p.parse_args();prepare(a.start)
