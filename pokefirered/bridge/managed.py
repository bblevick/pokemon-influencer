"""Managed local-process identity and fail-closed native lifetime.

SIGSTOP freezes the whole owned emulator, including an ongoing battle/script.
No GBA memory, save, input or RNG is changed. Only explicit managed resumption
may use SIGCONT; historical battery restores require a fresh process instead.
"""
import json
import os
import signal
import subprocess
import time
from pathlib import Path
from bridge.continuity import NativeWitness
from world.store import WorldError, dump

def atomic(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('w') as f:
        f.write(value)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

def process_identity(pid):
    p = subprocess.run(['ps', '-p', str(pid), '-o', 'lstart=', '-o', 'command='],
                       capture_output=True, text=True)
    if p.returncode or not p.stdout.strip():
        raise WorldError('owned native process unavailable')
    return str(pid) + ':' + p.stdout.strip()

def owned(cfg):
    owner = json.loads(Path(cfg['continuity']['owner']).read_text())
    actual = process_identity(owner['pid'])
    if actual != owner['identity'] or owner['nonce'] != cfg['nonce']:
        raise WorldError('native process ownership/launch changed')
    # The private launch tool establishes this owner from the exact launched argv.
    return owner

def freeze(cfg, reason):
    atomic(cfg['continuity']['permit'], 'STOPPED\n')
    owner = owned(cfg)
    os.kill(owner['pid'], signal.SIGSTOP)
    atomic(cfg['continuity']['stopped'], dump({'reason': reason, 'at': time.time(),
           'nonce': cfg['nonce'], 'processIdentity': owner['identity']}) + '\n')

def native_witness(cfg, w, message, maximum_age=2):
    owner = owned(cfg)
    path = Path(cfg['continuity']['native'])
    if time.time() - path.stat().st_mtime > maximum_age:
        raise WorldError('native witness stale; managed revalidation required')
    p = json.loads(path.read_text())
    # Telemetry is sampled every ten frames. Wait outside any game transaction
    # for the sample containing this actual transport event, within its deadline.
    deadline = time.monotonic() + .25
    while p['eventCounter'] < message.sequence and time.monotonic() < deadline:
        time.sleep(.005)
        p = json.loads(path.read_text())
    physical = json.loads(Path(cfg['manifest']).read_text())
    if (p['build'], p['nonce'], p['run'], p['origin']) != (
        physical['rom_sha256'], cfg['nonce'], message.generation, cfg['origin']):
        raise WorldError('native telemetry launch mismatch')
    launch = w._launch(message.nonce, message.generation)
    return NativeWitness(w.build, p['nonce'], p['run'], p['origin'],
                         launch['loaded_fingerprint'], owner['identity'], p['frame'],
                         p['eventCounter'], p['ack'], p['drops'], True,
                         p['build'], physical['build_tag'])

class Health:
    def __init__(self, cfg):
        self.cfg = cfg
        self.enabled = bool(cfg.get('continuity'))
        self.first_frame = None
        self.last_frame = None
        self.last_advance = 0
    def publish(self, w, state):
        if not self.enabled:
            return
        c = w.campaign()
        stream = w._one('SELECT last FROM streams WHERE nonce=? AND run=1', (self.cfg['nonce'],))
        packet = {'pid': os.getpid(), 'at': time.time(),
               'nonce': self.cfg['nonce'], 'campaign': c['id'], 'branch': c['active_branch'],
               'cursor': c['cursor'], 'lastSequence': stream['last'] if stream else 0,
               'status': c['status'], 'state': state}
        try:
            path = Path(self.cfg['continuity']['native'])
            native = json.loads(path.read_text())
            manifest = json.loads(Path(self.cfg['manifest']).read_text())
            valid = ((native['nonce'],native['origin'],native['run'],native['build']) ==
                     (self.cfg['nonce'],self.cfg['origin'],1,manifest['rom_sha256']) and
                     native['authenticated'] and time.time()-path.stat().st_mtime <= 1 and
                     native['drops'] == 0 and native['ack'] <= packet['lastSequence'] and
                     native['eventCounter'] <= packet['lastSequence']+4)
            if valid:
                frame = native['frame']
                if self.last_frame is not None and frame < self.last_frame:
                    valid = False
                elif self.last_frame is None or frame > self.last_frame:
                    if self.first_frame is None:self.first_frame = frame
                    self.last_frame = frame;self.last_advance = time.time()
                    trace = self.cfg['continuity'].get('telemetry')
                    if trace:
                        with Path(trace).open('a') as f:
                            f.write(dump({**packet,'native':native})+'\n')
                packet.update(nativeFrame=frame,firstNativeFrame=self.first_frame,
                              nativeProgress=bool(valid and frame>self.first_frame and
                                                  time.time()-self.last_advance<=1))
        except (FileNotFoundError,ValueError,KeyError,TypeError):
            pass
        atomic(self.cfg['continuity']['host'], dump(packet) + '\n')
    def close(self, w):
        if not self.enabled:
            return
        self.publish(w, 'CLOSED')
        try:
            freeze(self.cfg, 'managed host closed; native continuation requires revalidation')
        except WorldError:
            # Process absence/replacement never authorizes signalling another PID.
            atomic(self.cfg['continuity']['permit'], 'STOPPED\n')
            self.publish(w, 'CLOSED_NATIVE_UNAVAILABLE')
