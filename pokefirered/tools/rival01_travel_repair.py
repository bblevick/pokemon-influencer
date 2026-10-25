#!/usr/bin/env python3
"""Isolated, zero-inference continuity qualification; never adopts Rival content."""
import argparse,hashlib,json,os,shutil,sqlite3,sys,uuid
from pathlib import Path
os.environ['POKEINFLUENCER_EXPERIMENT']='rival01'
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
TRIAL=os.environ.get('POKEINFLUENCER_CONTINUITY_TRIAL','')
if TRIAL and (not TRIAL.isalnum() or len(TRIAL)>24):raise ValueError('invalid isolated trial label')
E=ROOT/'evidence/phase8/rival01-travel-repair';PRIVATE=ROOT/('.local/rival01-travel-repair'+('-'+TRIAL if TRIAL else ''))
SCREENS=ROOT/'evidence/private/rival01-travel-repair'
if TRIAL:E=E/TRIAL;SCREENS=SCREENS/TRIAL
CONFIG=PRIVATE/'launch.json';M=E/'manifest-native.json'
from campaign.scripted import ScriptedStore
from world.saves import fingerprint,layout_from_build
from world.store import dump
def manifest():return json.loads(M.read_text())
def open_store(path):return ScriptedStore(path,M)
def save_identity(path):return fingerprint(Path(path).read_bytes(),layout_from_build(ROOT/manifest()['rom_path']))
def bind(module):
 for name,value in {'E':E,'PRIVATE':PRIVATE,'CONFIG':CONFIG,'SCREENS':SCREENS,'manifest':manifest,'open_store':open_store,'save_identity':save_identity}.items():setattr(module,name,value)
def seed():
 E.mkdir(exist_ok=True);PRIVATE.mkdir(exist_ok=True);SCREENS.mkdir(parents=True,exist_ok=True)
 if (PRIVATE/'world.sqlite3').exists() or (PRIVATE/'pokefirered.sav').exists():raise ValueError('do not overwrite isolated qualification')
 src=sqlite3.connect('file:'+str(ROOT/'.local/rocket01/post-rocket-pair.sqlite3')+'?mode=ro',uri=True)
 dst=sqlite3.connect(PRIVATE/'world.sqlite3');src.backup(dst);dst.close();src.close()
 shutil.copy2(ROOT/'.local/rocket01/post-rocket-pair.sav',PRIVATE/'pokefirered.sav')
 shutil.copy2(ROOT/'evidence/phase8/rival01/manifest-native.json',M)
def launch():
 import strategy01_launch as module
 bind(module);module.prepare(manifest_path=M)
 cfg=json.loads(CONFIG.read_text());cfg['continuity']={
  key:str(PRIVATE/(name)) for key,name in {'inbox':'inbox.sqlite3','native':'native-proof.json',
  'host':'host-health.json','permit':'input-permit.txt','owner':'native-owner.json','stopped':'native-stopped.json',
  'command':'supervisor-command.json'}.items()}
 cfg['continuity'].update(console=str(E/'host-console.log'),supervisorLog=str(E/'supervisor.jsonl'))
 cfg['managedHostArgv']=[str(ROOT/'.venv/bin/python'),str(Path(__file__).resolve()),'host','--seconds','900']
 cfg['managedHostEnv']={'POKEINFLUENCER_CONTINUITY_TRIAL':TRIAL}
 from bridge.managed import atomic
 command_path=Path(cfg['continuity']['command'])
 if command_path.exists():shutil.copy2(command_path,PRIVATE/('retired-command-'+str(cfg['nonce'])+'.json'))
 atomic(command_path,'null\n')
 cfg['emulatorArgv']=[str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA'),'-C','hwaccelVideo=0','-C','savegamePath='+str(PRIVATE),str(ROOT/manifest()['rom_path'])]
 CONFIG.write_text(json.dumps(cfg,indent=2)+'\n')
 from phase1_events_launch import lua
 script=PRIVATE/'run.lua';script.write_text(script.read_text()+'\nPI_CONFIG.continuity='+lua(cfg['continuity'])+'\n'+(ROOT/'bridge/continuity_mgba.lua').read_text())
 (E/'managed-launch.json').write_text(dump({'nonce':cfg['nonce'],'origin':cfg['origin'],'script':str(script),'scriptSHA256':hashlib.sha256(script.read_bytes()).hexdigest(),'romSHA256':manifest()['rom_sha256'],'hostedInference':False})+'\n')
def capture(label):
 from rival01_prerequisites import METHODS
 cfg=json.loads(CONFIG.read_text())
 with open_store(PRIVATE/'world.sqlite3') as w:
  out={'campaign':w.campaign(),'checkpoint':w.get_save_checkpoint(save_identity(PRIVATE/'pokefirered.sav').fingerprint),'save':save_identity(PRIVATE/'pokefirered.sav').as_dict(),'hashes':{m:getattr(w,m)() for m in METHODS},'world':w.state(),'pendingSave':w.pending_save(),'obligations':w.puppeteer_state()['obligations'],'nativeTelemetry':json.loads(Path(cfg['continuity']['native']).read_text()),'memos':w.memo_records()}
 (E/(label+'.json')).write_text(json.dumps(out,indent=2)+'\n');print(dump({'label':label,'cursor':out['campaign']['cursor'],'saveCounter':out['save']['counter'],'drops':out['nativeTelemetry']['drops']}))
class ControlledAckLoss:
 """One declared transport-only fault in this isolated qualification writer."""
 job=None
 def tick(self,*args):pass
 def recover(self,*args):pass
 def disconnected(self):pass
 def close(self):pass
 def receive(self,*args):raise ValueError('no tactical provider in travel qualification')
 def before_event_ack(self,msg,w,sock,result):
  import signal
  from bridge.managed import freeze
  path=PRIVATE/'ack-fault.json'
  if not path.exists():return True
  fault=json.loads(path.read_text())
  if fault.get('consumed') or msg.sequence!=fault['sequence']:return True
  cfg=json.loads(CONFIG.read_text())
  if fault['nonce']!=msg.nonce:raise ValueError('test ACK fault launch mismatch')
  fault.update(consumed=True,wireHex=msg.encode().hex(),commitResult=result,campaign=w.campaign())
  path.write_text(dump(fault)+'\n');(E/'ack-loss-after-commit.json').write_text(dump(fault)+'\n')
  freeze(cfg,'declared isolated ACK loss after durable canonical commit')
  os.kill(os.getpid(),signal.SIGTERM)
  return False
def main():
 command=sys.argv[1];rest=sys.argv[2:]
 if command=='seed':seed()
 elif command=='launch':launch()
 elif command=='host':
  import strategy01_host as host
  bind(host);p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,default=900);a=p.parse_args(rest)
  # No provider scheduler or tactical provider is instantiated. This writer only
  # ingests native events, settles mandatory recaps offline and serves the viewer.
  host.run(a.seconds,battle_handler=ControlledAckLoss())
 elif command=='input':
  import strategy01_input as inp
  bind(inp);inp.retained.E=E
  p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('commands',nargs='+');a=p.parse_args(rest);print(inp.segment(a.label,a.commands))
 elif command=='save':
  import strategy01_input as inp
  bind(inp);inp.retained.E=E
  import strategy01_scenario as s
  bind(s);s.segment=inp.segment
  p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('--menu-cursor',type=int,default=0);a=p.parse_args(rest);print(dump(s.normal_save(a.label,a.menu_cursor)))
 elif command=='capture':capture(rest[0])
 elif command=='fault-ack':
  cfg=json.loads(CONFIG.read_text());sequence=int(rest[0])
  if not 1<=sequence<=0xffffffff:raise ValueError('sequence bound')
  (PRIVATE/'ack-fault.json').write_text(dump({'nonce':cfg['nonce'],'sequence':sequence,'consumed':False})+'\n')
 elif command=='control':
  from bridge.managed import atomic
  cfg=json.loads(CONFIG.read_text());p=argparse.ArgumentParser();p.add_argument('action',choices=['restart-host','stop']);p.add_argument('--seconds',type=int);a=p.parse_args(rest)
  if a.seconds is not None and not 1<=a.seconds<=3600:raise ValueError('bounded host lifetime')
  atomic(cfg['continuity']['command'],dump({'id':str(uuid.uuid4()),'nonce':cfg['nonce'],'command':a.action,'seconds':a.seconds})+'\n')
 else:raise ValueError('unsupported repair action')
if __name__=='__main__':main()
