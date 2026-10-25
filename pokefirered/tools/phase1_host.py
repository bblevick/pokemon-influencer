#!/usr/bin/env python3
"""Local bounded PING responder. Only host process makes blocking connects."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bridge.protocol import Decoder,Message,Responder
ROOT=Path(__file__).resolve().parents[1]

def verify(manifest):
    if manifest['schema_version']!=1 or manifest['protocol_version']!=1 or manifest['bridge_version']!=1 or not manifest['target']['bridge_enabled']:raise ValueError('manifest incompatible')
    rom=ROOT/manifest['rom_path']
    if hashlib.sha256(rom.read_bytes()).hexdigest()!=manifest['rom_sha256']:raise ValueError('ROM hash mismatch')
    elf=rom.with_suffix('.elf');mp=rom.with_suffix('.map')
    if hashlib.sha256(elf.read_bytes()).hexdigest()!=manifest['elf_sha256'] or hashlib.sha256(mp.read_bytes()).hexdigest()!=manifest['map_sha256']:raise ValueError('ELF/map hash mismatch')
    from phase1_build import symbols
    actual=symbols(elf)
    if actual['gPiMailbox']!={'address':manifest['mailbox']['address'],'size':manifest['mailbox']['size']} or actual['gPiBuildTag']['address']!=manifest['build_tag_address']:raise ValueError('mailbox/tag symbol mismatch')
    if hashlib.sha256((ROOT/'bridge/mgba.lua').read_bytes()).hexdigest()!=manifest['overlay_sha256']['bridge/mgba.lua']:raise ValueError('bridge hash mismatch')

def run(config,mode='normal',limit=15):
    cfg=json.loads(Path(config).read_text());m=json.loads((ROOT/cfg['manifest']).read_text());verify(m)
    log=ROOT/'evidence/phase1'/f'host-{mode}.jsonl'
    def record(event,**data):
        with log.open('a') as f:f.write(json.dumps({'event':event,**data})+'\n')
    deadline=time.monotonic()+limit
    sock=None
    while time.monotonic()<deadline:
        try:sock=socket.create_connection(('127.0.0.1',cfg['port']),timeout=.25);break
        except (OSError,TimeoutError):time.sleep(.1)
    if sock is None:record('unavailable');return 2
    with sock:
        sock.settimeout(.25)
        hello=Message(0,cfg['nonce'],0,0,m['build_tag'],0,cfg['token'].encode()+bytes.fromhex(m['rom_sha256']))
        sock.sendall(hello.encode());decoder=Decoder();responder=None
        record('connected',mode=mode)
        while time.monotonic()<deadline:
            try:data=sock.recv(128)
            except socket.timeout:continue
            if not data:record('disconnected');return 0 if mode=='disconnect' else 3
            for message in decoder.feed(data):
                if responder is None:
                    if message.kind!=3 or message.sequence or message.nonce!=cfg['nonce'] or message.tag!=m['build_tag'] or message.typ or message.payload:raise ValueError('HELLO_ACK mismatch')
                    responder=Responder(cfg['nonce'],message.generation,m['build_tag']);record('hello',generation=message.generation)
                    continue
                started=time.monotonic();response=responder.handle(message)
                record('request',sequence=message.sequence,nonce=message.nonce,generation=message.generation,payload=message.payload.decode())
                if mode=='disconnect':record('intentional-disconnect');return 0
                if mode=='silent':record('intentional-no-response');continue
                if mode=='delayed':time.sleep(1.5)
                if mode=='stale':response=Message(2,response.nonce,response.generation,response.sequence-1,response.tag,2,b'PONG')
                wire=response.encode()
                if mode=='fragmented':
                    for i in range(0,len(wire),3):sock.sendall(wire[i:i+3]);time.sleep(.001)
                else:sock.sendall(wire)
                record('response',sequence=response.sequence,payload=response.payload.decode(),host_elapsed_ms=(time.monotonic()-started)*1000)
                if mode=='duplicate':sock.sendall(wire);record('duplicate-response',sequence=response.sequence)
        record('host-deadline');return 0
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',default='.local/phase1-launch.json');p.add_argument('--mode',choices=['normal','disconnect','silent','delayed','stale','fragmented','duplicate'],default='normal');p.add_argument('--seconds',type=float,default=15);a=p.parse_args()
    try:raise SystemExit(run(ROOT/a.config,a.mode,a.seconds))
    except (ValueError,OSError) as e:raise SystemExit(str(e))
