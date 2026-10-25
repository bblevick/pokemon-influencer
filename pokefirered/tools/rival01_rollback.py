#!/usr/bin/env python3
"""Save20 rollback binding; supervised runtime only, travel offline by default."""
import os,sys,json,sqlite3,shutil,hashlib,uuid,argparse
from pathlib import Path
os.environ['POKEINFLUENCER_EXPERIMENT']='rival01';os.environ['POKEINFLUENCER_RIVAL_ROLLBACK']='1'
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
import rival01 as r
from bridge.managed import atomic
from world.store import dump
P=r.PRIVATE;E=r.E
def seed():
 if P.exists() or E.exists():raise ValueError('refuse overwriting rollback run')
 E.mkdir(parents=True);P.mkdir()
 preserved=json.loads((ROOT/'evidence/phase8/rival01-travel-repair/preserved-inventory.json').read_text())
 for path in ['evidence/phase8/rival01-travel-repair/verification.json','evidence/phase8/rival01-travel-repair/native-static-verification.json']:
  file=ROOT/path;preserved[path]={'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
 for path,value in preserved.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==value['sha256']
 (E/'preserved-inventory.json').write_text(json.dumps(preserved,indent=2)+'\n')
 src=sqlite3.connect('file:'+str(ROOT/'.local/rocket01/post-rocket-pair.sqlite3')+'?mode=ro',uri=True);dst=sqlite3.connect(P/'world.sqlite3');src.backup(dst);src.close();dst.close()
 shutil.copy2(ROOT/'.local/rocket01/post-rocket-pair.sav',P/'pokefirered.sav')
 shutil.copy2(ROOT/'evidence/phase8/rival01/manifest-native.json',E/'manifest-native.json')
 # Carry forward the entire unused original allowance, never reset a spent ledger.
 old=json.loads((ROOT/'evidence/phase8/rival01/requests.json').read_text());assert old['closed'] and not old['attempts']
 old['rollbackContinuation']={'source':'e5440ab0-70d5-4651-969d-17a52f31cf00','originalLedger':'evidence/phase8/rival01/requests.json','originalSHA256':preserved['evidence/phase8/rival01/requests.json']['sha256'],'baseAttempts':0,'travelInferencePermitted':False}
 (E/'requests.json').write_text(json.dumps(old,indent=2)+'\n')
 from rival01_prerequisites import METHODS
 with r.open_store(P/'world.sqlite3') as w:
  identity=r.save_identity(P/'pokefirered.sav');cp=w.get_save_checkpoint(identity.fingerprint)
  assert cp['id']=='fc2eb9f8-d613-4f48-aebf-b2ffa2c44824' and w.campaign()['cursor']==443
  (E/'save20-branch-manifest.json').write_text(json.dumps({'checkpoint':cp,'save':identity.as_dict(),'hashes':{m:getattr(w,m)() for m in METHODS},'rollbackNotRecovery':True,'abandonedBranch':'481b8552-6800-493e-b254-33baf7c77b41','calls':0},indent=2)+'\n')
def launch(args):
 live='--live' in args
 if live and not (E/'gate-a-accepted.json').exists():raise ValueError('travel checkpoint/reload/context/route gates required before live mode')
 if (P/'launch.json').exists():shutil.copy2(P/'launch.json',P/('retired-launch-'+str(uuid.uuid4())+'.json'))
 sys.argv=[sys.argv[0],'launch',*['--rival-ready' for x in args if x=='--rival-ready']];r.main()
 cfg=json.loads((P/'launch.json').read_text())
 cfg['continuity']={k:str(P/name) for k,name in {'inbox':'inbox.sqlite3','native':'native-proof.json','host':'host-health.json','permit':'input-permit.txt','owner':'native-owner.json','stopped':'native-stopped.json','command':'supervisor-command.json'}.items()}
 cfg['continuity'].update(console=str(E/'host-console.log'),supervisorLog=str(E/'supervisor.jsonl'))
 cfg['managedHostEnv']={'POKEINFLUENCER_RIVAL_ROLLBACK':'1','POKEINFLUENCER_EXPERIMENT':'rival01'}
 cfg['managedHostArgv']=[str(ROOT/'.venv/bin/python'),str(Path(__file__).resolve()),'host','--seconds','900']+(['--live','--continue-authorized-run'] if live else [])
 cfg['emulatorArgv']=[str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA'),'-C','hwaccelVideo=0','-C','savegamePath='+str(P),str(ROOT/r.manifest()['rom_path'])]
 atomic(P/'launch.json',json.dumps(cfg,indent=2)+'\n')
 command=Path(cfg['continuity']['command'])
 if command.exists():shutil.copy2(command,P/('retired-command-'+str(uuid.uuid4())+'.json'))
 atomic(command,'null\n')
 from phase1_events_launch import lua
 script=P/'run.lua';script.write_text(script.read_text()+'\nPI_CONFIG.continuity='+lua(cfg['continuity'])+'\n'+(ROOT/'bridge/continuity_mgba.lua').read_text())
 (E/'managed-launch.json').write_text(dump({'nonce':cfg['nonce'],'origin':cfg['origin'],'script':str(script),'scriptSHA256':hashlib.sha256(script.read_bytes()).hexdigest(),'romSHA256':r.manifest()['rom_sha256'],'live':live,'rollbackNotRecovery':True})+'\n')
def main():
 command=sys.argv[1];args=sys.argv[2:]
 if command=='seed':seed()
 elif command=='launch':launch(args)
 elif command=='control':
  p=argparse.ArgumentParser();p.add_argument('action',choices=['stop','restart-host']);p.add_argument('--seconds',type=int);a=p.parse_args(args)
  if a.seconds is not None and (a.action!='restart-host' or not 1<=a.seconds<=3600):raise ValueError('bounded restart lifetime only')
  cfg=json.loads((P/'launch.json').read_text());command={'id':str(uuid.uuid4()),'nonce':cfg['nonce'],'command':a.action}
  if a.seconds is not None:command['seconds']=a.seconds
  atomic(cfg['continuity']['command'],dump(command)+'\n')
 else:r.main()
if __name__=='__main__':main()
