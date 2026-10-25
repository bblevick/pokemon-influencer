#!/usr/bin/env python3
"""Managed fresh OS-process battery launch; pinned accepted viewer ROM, separate private paths."""
import argparse,hashlib,json,secrets,shutil,subprocess,sys,re
from pathlib import Path
from phase1_events_launch import lua
from strategy01 import PRIVATE,CONFIG,SCREENS,ROOT,E,manifest,open_store,save_identity

def prepare(start=False,restore=None,launch_hook=None,manifest_path=None,continuation_id=None):
 m=manifest();private=PRIVATE;private.mkdir(exist_ok=True);E.mkdir(parents=True,exist_ok=True)
 save=private/'pokefirered.sav';screens=SCREENS;screens.mkdir(parents=True,exist_ok=True)
 # Caller must stop mGBA before restore; refuse to mutate a file held by mGBA.
 if subprocess.run(['pgrep','-f','^'+re.escape(str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA'))+r'(\s|$)'],stdout=subprocess.DEVNULL).returncode==0:raise ValueError('stop task-local mGBA before a fresh paired launch')
 if restore:
  with open_store(private/'world.sqlite3') as w:
   if not w.get_save_checkpoint(save_identity(restore).fingerprint):raise ValueError('unpaired restore refused before changing the current private battery')
  if save.exists():shutil.copy2(save,private/'before-managed-restore.sav')
  shutil.copy2(restore,save)
 if not save.exists():raise ValueError('explicit import/restore --save required; no silent seed')
 nonce=secrets.randbelow(0xffffffff)+1
 with open_store(private/'world.sqlite3') as w:
  if continuation_id:
   row=w._one('SELECT descriptor FROM prebattle_continuations WHERE id=?',(continuation_id,))
   if not row:raise ValueError('unknown prebattle continuation')
   d=json.loads(row['descriptor'])
   origin=w.authorize_continuation_launch(continuation_id,nonce,save_identity(save),d['actor'],d['nativeTrainer'],d['opportunityID'])
  else:origin=w.authorize_launch(nonce,save_identity(save))
  w.activate_preparation()
  # Initial explicitly imported lineage may activate once after selecting its
  # import checkpoint. Restored normal checkpoints never gain new history.
  cp=w.get_save_checkpoint(save_identity(save).fingerprint)
  if cp['kind']=='explicit_import' and not w.puppeteer_state()['activation']:w.activate_puppeteer()
  if launch_hook is not None:launch_hook(w,cp)
 cfg={'manifest':str(manifest_path or 'evidence/phase2/pokebook01/manifest-enabled.json'),'port':18782,'nonce':nonce,'token':secrets.token_hex(16),'origin':origin,'database':str(private/'world.sqlite3'),'save':str(save),'log':str(E/'emulator.jsonl'),'screenshots':str(screens),'receipts':str(E/'save-receipts.jsonl')}
 if continuation_id:cfg['prebattleContinuation']=continuation_id
 config=CONFIG;config.write_text(json.dumps(cfg,indent=2)+'\n');config.chmod(0o600)
 from phase1_events_build import symbols
 syms=symbols(ROOT/m['rom_path'].replace('.gba','.elf'))
 for name in ['gHeap','gTasks','gWindows','gSprites','sPb','gPlayerAvatar','gObjectEvents']:m['diagnostic_symbols'][name]=syms[name]['address']
 binary='"'+''.join('\\%03d'%x for x in bytes.fromhex(m['rom_sha256']))+'"'
 prefix='PI_MANIFEST='+lua(m)+'\nPI_MANIFEST.rom_sha256_binary='+binary+'\nPI_CONFIG='+lua(cfg)+'\n'
 harness=(ROOT/'bridge/emulator_smoke.lua').read_text().replace('18773','18783')
 # Observation-only lifecycle receipt from the existing callback; no bridge ABI,
 # writes, inference, socket connect or save implementation changes.
 harness=harness.replace("PI_TEST.savecb=callbacks:add('savedataUpdated',function()PI.log('savedataUpdated','actual battery write')end)",'''PI_TEST.savecb=callbacks:add('savedataUpdated',function()
 PI.log('savedataUpdated','Strategy persisted-save receipt')
 local f=assert(io.open(PI.cfg.receipts,'a'))
 f:write(string.format('{"event":"savedataUpdated","nonce":%d,"run":%d,"eventCounter":%d,"ack":%d,"depth":%d,"state":%d,"drops":%d,"counter":%d,"frame":%d}\\n',PI.cfg.nonce,PI.epoch,PI.read('event_counter'),PI.read('last_ack'),PI.read('queue_depth'),PI.read('state'),PI.read('drops'),emu:read32(PI.m.diagnostic_symbols.gSaveCounter),emu:currentFrame()))
 f:flush();f:close()
end)''')
 test=(ROOT/'bridge/events_emulator_smoke.lua').read_text().replace('18773','18783')
 # Arbitrary states and controller reset are deliberately not managed Strategy paths.
 test=test.replace("elseif cmd=='reset' then emu:reset()", "elseif cmd=='reset' then error('use fresh paired battery launch')")
 test=test.replace("elseif cmd=='checkpoint' then assert(emu:saveStateFile(PI.cfg.checkpoint,C.SAVESTATE.ALL));PI.log('checkpoint-test','explicit ALL; not host-paired')", "elseif cmd=='checkpoint' then error('Strategy supports normal saves only')")
 test=test.replace("elseif cmd=='reload' then assert(emu:loadStateFile(PI.cfg.checkpoint,C.SAVESTATE.ALL));PI.log('reload-test','explicit ALL; heartbeat regression detection only')", "elseif cmd=='reload' then error('Strategy supports fresh paired battery launch only')")
 script=PRIVATE/'run.lua' if PRIVATE.name!='strategy01' else ROOT/'.local/strategy01-run.lua';script.write_text(prefix+'\n'+(ROOT/'bridge/ui_transport_mgba.lua').read_text()+'\n'+(ROOT/'bridge/ui_mgba.lua').read_text()+'\n'+harness+'\n'+test+'\n'+(ROOT/'bridge/pokebook_resource_probe.lua').read_text()+'\n'+(ROOT/'bridge/prep_acceptance_probe.lua').read_text());script.chmod(0o600)
 argv=[str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA'),'-C','hwaccelVideo=0','-C','savegamePath='+str(private),str(ROOT/m['rom_path'])]
 report={'argv':argv,'origin':origin,'nonce':nonce,'romSHA256':m['rom_sha256'],'script':str(script),'scriptSHA256':hashlib.sha256(script.read_bytes()).hexdigest(),'save':save_identity(save).as_dict(),'workflow':'fresh OS process; native script load; normal battery Continue; no savestate','credentialsUsed':False}
 with (E/'launches.jsonl').open('a') as f:f.write(json.dumps(report)+'\n')
 print(json.dumps(report,indent=2),flush=True)
 if start:subprocess.run(argv,cwd=ROOT,check=True,restore_signals=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--start',action='store_true');p.add_argument('--save',type=Path);a=p.parse_args();prepare(a.start,a.save)
