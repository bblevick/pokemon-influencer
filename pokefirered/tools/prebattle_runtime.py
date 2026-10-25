#!/usr/bin/env python3
"""Generic managed offline continuation qualification over existing launch APIs.

No inference services or tactical provider are constructed. No encounter is
triggered. This tool is not the persistence mechanism; that lives in the store.
"""
import argparse,json,sys,time,os,shutil,uuid,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from campaign.scripted import ScriptedStore
from world.saves import fingerprint,layout_from_build
from bridge.managed import atomic

def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['prepare','host','input','stop','restart-host'])
    p.add_argument('--private',type=Path,required=True)
    p.add_argument('--evidence',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--continuation');p.add_argument('--seconds',type=int,default=900)
    p.add_argument('--label');p.add_argument('inputs',nargs='*')
    a=p.parse_args();a.private=a.private.resolve();a.evidence=a.evidence.resolve();a.manifest=a.manifest.resolve()
    if not 1<=a.seconds<=3600:raise ValueError('bounded host lifetime required')
    m=json.loads(a.manifest.read_text());screens=ROOT/'evidence/private'/a.private.name;screens.mkdir(exist_ok=True)
    def store(path):return ScriptedStore(path,a.manifest)
    def save(path):return fingerprint(Path(path).read_bytes(),layout_from_build(ROOT/m['rom_path']))
    bindings=dict(ROOT=ROOT,PRIVATE=a.private,E=a.evidence,CONFIG=a.private/'launch.json',SCREENS=screens,
                  manifest=lambda:m,open_store=store,save_identity=save)
    def bind(module):
        for k,v in bindings.items():setattr(module,k,v)
    if a.command=='prepare':
        if not a.continuation:raise ValueError('explicit continuation required')
        if (a.private/'launch.json').exists():
            shutil.copy2(a.private/'launch.json',a.private/('retired-launch-'+str(uuid.uuid4())+'.json'))
        import strategy01_launch as launch
        bind(launch);launch.prepare(manifest_path=a.manifest,continuation_id=a.continuation)
        cfg=json.loads((a.private/'launch.json').read_text())
        cfg['continuity']={k:str(a.private/n) for k,n in dict(inbox='inbox.sqlite3',native='native-proof.json',host='host-health.json',permit='input-permit.txt',owner='native-owner.json',stopped='native-stopped.json',command='supervisor-command.json').items()}
        cfg['continuity'].update(console=str(a.evidence/'host-console.log'),supervisorLog=str(a.evidence/'supervisor.jsonl'),telemetry=str(a.evidence/'native-host-telemetry.jsonl'))
        cfg['managedHostArgv']=[str(ROOT/'.venv/bin/python'),str(Path(__file__).resolve()),'host','--private',str(a.private),'--evidence',str(a.evidence),'--manifest',str(a.manifest),'--seconds',str(a.seconds)]
        # Video synchronization supplies normal frame pacing while avoiding the
        # retained macOS audio-producer wait. No turbo/fast-forward setting.
        cfg['emulatorArgv']=[str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA'),'-C','hwaccelVideo=0','-C','audioSync=0','-C','videoSync=1','-C','fpsTarget=59.7275','-C','savegamePath='+str(a.private),str(ROOT/m['rom_path'])]
        atomic(a.private/'launch.json',json.dumps(cfg,indent=2)+'\n')
        atomic(cfg['continuity']['command'],'null\n')
        from phase1_events_launch import lua
        script=a.private/'run.lua'
        script.write_text(script.read_text()+'\nPI_CONFIG.continuity='+lua(cfg['continuity'])+'\n'+(ROOT/'bridge/continuity_mgba.lua').read_text())
        with (a.evidence/'prepared-launches.jsonl').open('a') as f:
            f.write(json.dumps({'nonce':cfg['nonce'],'origin':cfg['origin'],'continuationID':a.continuation,
                'emulatorArgv':cfg['emulatorArgv'],'managedHostArgv':cfg['managedHostArgv'],
                'scriptSHA256':hashlib.sha256(script.read_bytes()).hexdigest()})+'\n')
    elif a.command=='host':
        import strategy01_host as host
        bind(host);host.run(a.seconds,services=None,battle_handler=None)
    elif a.command=='input':
        import strategy01_input as driver
        bind(driver);driver.retained.E=a.evidence
        if not a.label:raise ValueError('input label required')
        print(driver.segment(a.label,a.inputs))
    else:
        import uuid
        cfg=json.loads((a.private/'launch.json').read_text())
        command={'id':str(uuid.uuid4()),'nonce':cfg['nonce'],'command':a.command}
        if a.command=='restart-host':command['seconds']=a.seconds
        healthy=False
        if a.command=='stop':
            try:
                h=json.loads(Path(cfg['continuity']['host']).read_text())
                healthy=h['nonce']==cfg['nonce'] and h['state']=='CONNECTED' and h.get('nativeProgress') and time.time()-h['at']<=1
            except (OSError,ValueError,KeyError):pass
        atomic(cfg['continuity']['command'],json.dumps(command)+'\n')
        if a.command=='stop' and cfg.get('prebattleContinuation'):
            deadline=time.monotonic()+15
            while True:
                health=json.loads(Path(cfg['continuity']['host']).read_text())
                try:os.kill(health['pid'],0);alive=True
                except ProcessLookupError:alive=False
                if not alive and health['state'].startswith('CLOSED'):break
                if time.monotonic()>deadline:raise ValueError('managed shutdown unconfirmed; continuation session remains unsettled')
                time.sleep(.1)
            if not healthy:raise ValueError('no advancing pre-stop witness; continuation requires explicit revalidation')
            native=json.loads(Path(cfg['continuity']['native']).read_text())
            with store(cfg['database']) as w:w.settle_continuation_session(cfg['origin'],save(cfg['save']),native)
            print('Managed session settled without gameplay or inference.')

if __name__=='__main__':main()
