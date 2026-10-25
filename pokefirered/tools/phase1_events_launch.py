#!/usr/bin/env python3
"""Prepare a pinned ROM + trusted generated Lua launcher; one manual script-load step."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import subprocess
from phase1_events_host import verify
ROOT=Path(__file__).resolve().parents[1]

def lua(value):
    if value is None:return 'nil'
    if isinstance(value,bool):return 'true' if value else 'false'
    if isinstance(value,(int,float)):return str(value)
    if isinstance(value,str):return json.dumps(value,ensure_ascii=True)
    if isinstance(value,dict):return '{'+','.join('['+lua(k)+']='+lua(v) for k,v in value.items())+'}'
    if isinstance(value,list):return '{'+','.join(map(lua,value))+'}'
    raise TypeError(type(value))

def prepare(start=False):
    m=json.loads((ROOT/'evidence/phase1/bridge02/manifest-enabled.json').read_text());verify(m)
    private=ROOT/'.local/phase1-events-emulator';private.mkdir(parents=True,exist_ok=True)
    screenshots=ROOT/'evidence/private/bridge02';screenshots.mkdir(parents=True,exist_ok=True)
    # Save fixture copies remain local; never start from the Phase 0 file directly.
    save=private/'pokefirered.sav'
    if not save.exists():shutil.copy2(ROOT/'.local/emulator-test/pokefirered.sav',save)
    cfg={'manifest':'evidence/phase1/bridge02/manifest-enabled.json','port':18772,'nonce':secrets.randbelow(0xffffffff)+1,
         'token':secrets.token_hex(16),'checkpoint':str(private/'scenario-checkpoint.ss0'),'log':str(ROOT/'evidence/phase1/bridge02/emulator.jsonl'),'screenshots':str(screenshots)}
    cpath=ROOT/'.local/phase1-events-launch.json';cpath.write_text(json.dumps(cfg,indent=2)+'\n');cpath.chmod(0o600)
    # Binary checksum kept as escaped bytes; only generated trusted local Lua, never network eval.
    binary='"'+''.join('\\%03d'%x for x in bytes.fromhex(m['rom_sha256']))+'"'
    prefix='PI_MANIFEST='+lua(m)+'\nPI_MANIFEST.rom_sha256_binary='+binary+'\nPI_CONFIG='+lua(cfg)+'\n'
    path=ROOT/'.local/events-bridge-run.lua'
    path.write_text(prefix+(ROOT/'bridge/events_mgba.lua').read_text()+'\n'+(ROOT/'bridge/emulator_smoke.lua').read_text()+'\n'+(ROOT/'bridge/events_emulator_smoke.lua').read_text());path.chmod(0o600)
    argv=[str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA'),'-C','hwaccelVideo=0','-C','savegamePath='+str(private),str(ROOT/m['rom_path'])]
    plan={'emulator_argv':argv,'manual_step':'Tools > Scripting > File > Load script: '+str(path),'host_argv':['.venv/bin/python','tools/phase1_events_host.py','--seconds','120'],'script_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'test_harness_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['bridge/emulator_smoke.lua','bridge/events_emulator_smoke.lua']},'manifest':cfg['manifest'],'emulator_version':m['emulator']['version'],'token_redacted':True}
    (ROOT/'evidence/phase1/bridge02/launch.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(plan,indent=2),flush=True)
    if start:subprocess.run(argv,cwd=ROOT,check=True,restore_signals=False)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--start',action='store_true');a=p.parse_args();prepare(a.start)
