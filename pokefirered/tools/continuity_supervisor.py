#!/usr/bin/env python3
"""Owned host/emulator lifecycle guard; no models, gameplay edits or UI driving."""
import argparse,json,os,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from bridge.managed import atomic,freeze,process_identity,owned
from world.store import dump

def read(path):
    try:return json.loads(Path(path).read_text())
    except (FileNotFoundError,ValueError):return None

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True,type=Path);a=p.parse_args()
    cfg=json.loads(a.config.read_text());c=cfg['continuity'];stop=False;host=None;emu=None;paused=False;active=False
    def log(event,**data):
        with Path(c['supervisorLog']).open('a') as f:f.write(dump({'event':event,'at':time.time(),**data})+'\n')
    def shutdown(signum,frame):
        nonlocal stop
        stop=True
    signal.signal(signal.SIGTERM,shutdown);signal.signal(signal.SIGINT,shutdown)
    def start_host():
        stream=Path(c['console']).open('a')
        child=subprocess.Popen(cfg['managedHostArgv'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,
                               env={**os.environ,**cfg.get('managedHostEnv',{})})
        stream.close();log('host-start',pid=child.pid);return child
    def pause(reason):
        nonlocal paused
        if not paused:
            freeze(cfg,reason);paused=True;log('native-frozen',reason=reason,pid=emu.pid)
    atomic(c['permit'],'STOPPED\n')
    host=start_host();last_command=None;started=time.monotonic()
    try:
        # Host must reach its bounded connection loop before any native process.
        deadline=time.monotonic()+15
        while True:
            h=read(c['host'])
            if host.poll() is not None:raise ValueError('host exited during startup')
            if h and h['pid']==host.pid and h['nonce']==cfg['nonce'] and time.time()-h['at']<=1 and h['state'] in ('CONNECTING','RECONNECTING'):break
            if time.monotonic()>=deadline:raise ValueError('host startup readiness deadline')
            time.sleep(.02)
        emu=subprocess.Popen(cfg['emulatorArgv'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        atomic(c['owner'],dump({'pid':emu.pid,'identity':process_identity(emu.pid),'nonce':cfg['nonce']})+'\n')
        physical=json.loads(Path(cfg['manifest']).read_text())['rom_sha256']
        while not stop and emu.poll() is None:
            h=read(c['host']);n=read(c['native']);command=read(c['command'])
            if command and command.get('id')!=last_command:
                last_command=command['id']
                if command.get('nonce')!=cfg['nonce']:raise ValueError('supervisor command wrong launch')
                if command['command']=='stop':stop=True;continue
                if command['command']=='restart-host':
                    if not paused or host.poll() is None:raise ValueError('restart requires paused native and stopped host')
                    owned(cfg)
                    if not n or n['drops'] or n['nonce']!=cfg['nonce'] or n['run']!=1:
                        raise ValueError('native continuity unproven; restore known pair')
                    if command.get('seconds') is not None:
                        seconds=command['seconds']
                        if type(seconds)!=int or not 1<=seconds<=3600:raise ValueError('bounded host lifetime')
                        argv=list(cfg['managedHostArgv']);index=argv.index('--seconds');argv[index+1]=str(seconds);cfg['managedHostArgv']=argv
                    host=start_host()
                    # Native retries have a finite frame budget. Keep the core
                    # frozen until this replacement writer has opened its DB
                    # and reached its connection loop; spawning is not readiness.
                    deadline=time.monotonic()+15
                    while not stop:
                        ready=read(c['host'])
                        if host.poll() is not None:raise ValueError('replacement host exited before readiness')
                        if (ready and ready['pid']==host.pid and ready['nonce']==cfg['nonce'] and
                            time.time()-ready['at']<=1 and ready['status'] in ('paired','imported') and
                            ready['state'] in ('CONNECTING','RECONNECTING','CONNECTED')):break
                        if time.monotonic()>=deadline:raise ValueError('replacement host readiness timed out; native remains frozen')
                        time.sleep(.02)
                    if stop:continue
                    owned(cfg)
                    os.kill(emu.pid,signal.SIGCONT);paused=False;active=False;started=time.monotonic()
                    log('explicit-reconnect',pid=host.pid)
                else:raise ValueError('unknown supervisor command')
            if paused:
                time.sleep(.02);continue
            if host.poll() is not None:
                pause('canonical host process exited');continue
            healthy=bool(h and h['pid']==host.pid and h['nonce']==cfg['nonce'] and
                         time.time()-h['at']<=1 and h['status'] in ('paired','imported'))
            native=bool(n and n['nonce']==cfg['nonce'] and n['origin']==cfg['origin'] and n['build']==physical and n['run']==1 and n['authenticated'] and
                        time.time()-Path(c['native']).stat().st_mtime<=1 and n['drops']==0)
            if n and n['drops']:
                pause('native dropped-event counter; no automatic continuation');continue
            if healthy and native and h['state']=='CONNECTED' and h.get('nativeProgress') and h.get('nativeFrame',-1)<=n['frame']:
                if n['ack']>h['lastSequence'] or n['eventCounter']>h['lastSequence']+4:
                    pause('native/host causal high-water mismatch');continue
                if not active:
                    atomic(c['permit'],f"{cfg['nonce']}:1:ACTIVE\n");active=True;log('input-lease-active')
            elif active or (time.monotonic()-started>600):
                pause('host/transport lifetime unavailable');continue
            time.sleep(.02)
    finally:
        atomic(c['permit'],'STOPPED\n')
        if emu and emu.poll() is None:
            os.kill(emu.pid,signal.SIGCONT);emu.terminate()
            try:emu.wait(timeout=5)
            except subprocess.TimeoutExpired:emu.kill();emu.wait()
        if host and host.poll() is None:
            host.terminate()
            try:host.wait(timeout=5)
            except subprocess.TimeoutExpired:host.kill();host.wait()
        log('supervisor-closed',hostExit=host.poll() if host else None,emulatorExit=emu.poll() if emu else None)

if __name__=='__main__':main()
