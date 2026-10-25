#!/usr/bin/env python3
"""Local deterministic recorder. No .env, credentials, cloud, world state or AI."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bridge.events_wire import Decoder,Message
from bridge.events import Consumer
from phase1_events_build import symbols
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/phase1/bridge02'

def verify(m):
    if (m['schema_version'],m['protocol_version'],m['bridge_version'])!=(2,2,2) or not m['target']['bridge_enabled']:raise ValueError('manifest version')
    p=ROOT/m['rom_path']
    for file,key in [(p,'rom_sha256'),(p.with_suffix('.elf'),'elf_sha256'),(p.with_suffix('.map'),'map_sha256')]:
        if hashlib.sha256(file.read_bytes()).hexdigest()!=m[key]:raise ValueError('build hash mismatch')
    s=symbols(p.with_suffix('.elf'))
    if s['gPiMailbox']!={'address':m['mailbox']['address'],'size':m['mailbox']['size']}:raise ValueError('ELF mailbox mismatch')
    for file in ['bridge/events_mgba.lua','bridge/events_protocol.json']:
        if hashlib.sha256((ROOT/file).read_bytes()).hexdigest()!=m['overlay_sha256'][file]:raise ValueError('bridge/schema mismatch')

def append(path,record):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as f:
        f.write(json.dumps(record,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())

def run(config,seconds,mode):
    cfg=json.loads(Path(config).read_text());m=json.loads((ROOT/cfg['manifest']).read_text());verify(m)
    history=E/'events.jsonl';trace=E/('host-'+mode+'.jsonl');consumers={};faulted=False
    def log(event,**data):append(trace,{'event':event,**data})
    # Replay accepted bytes to recover dedupe after recorder restart. This is a
    # test log, not a branch-aware canonical world database or paired save.
    if history.exists():
        for line in history.read_text().splitlines():
            r=json.loads(line)
            if r['session']!=cfg['nonce'] or r['buildTag']!=m['build_tag']:continue
            wire=bytes.fromhex(r['wireHex']);msg=Message.decode(wire[2:]);key=msg.generation
            consumers.setdefault(key,Consumer(msg.nonce,key,msg.tag)).accept(msg)
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        try:
            with socket.create_connection(('127.0.0.1',cfg['port']),timeout=.3) as sock:
                sock.settimeout(.25);decoder=Decoder();consumer=None
                sock.sendall(Message(0,cfg['nonce'],0,0,m['build_tag'],0,cfg['token'].encode()+bytes.fromhex(m['rom_sha256'])).encode())
                log('connected')
                while time.monotonic()<deadline:
                    try:data=sock.recv(256)
                    except socket.timeout:continue
                    if not data:break
                    for msg in decoder.feed(data):
                        if consumer is None:
                            if msg.kind!=3 or msg.sequence or msg.nonce!=cfg['nonce'] or msg.tag!=m['build_tag'] or not msg.generation or msg.payload or msg.typ:raise ValueError('HELLO_ACK')
                            consumer=consumers.setdefault(msg.generation,Consumer(msg.nonce,msg.generation,msg.tag))
                            if len(consumers)>8:
                                oldest=next(iter(consumers));del consumers[oldest]
                            log('hello',session=msg.nonce,run=msg.generation,branch=f'transient:{msg.nonce}:{msg.generation}')
                            continue
                        record,ack=consumer.accept(msg)
                        if record is None:log('duplicate',sequence=msg.sequence,run=msg.generation)
                        else:
                            record['wireHex']=msg.encode().hex();record['romSHA256']=m['rom_sha256']
                            append(history,record)
                            sink='observations.jsonl' if record['recordClass']=='observation' else 'canonical-events.jsonl'
                            append(E/sink,record)
                            log('accepted',sequence=msg.sequence,run=msg.generation,battle=record['battleID'],turn=record['turnID'],eventType=record['eventType'],gap=record['sequenceGap'])
                        if not faulted and mode!='normal':
                            faulted=True;log('fault-injected',mode=mode,sequence=msg.sequence)
                            if mode=='drop-ack-once':continue
                            if mode=='disconnect-once':raise ConnectionError('intentional disconnect')
                            if mode=='stale-ack-once':
                                ack=Message(2,ack.nonce,ack.generation,ack.sequence-1,ack.tag,4,b'')
                        wire=ack.encode()
                        if mode=='fragmented':
                            for i in range(0,len(wire),3):sock.sendall(wire[i:i+3])
                        else:sock.sendall(wire)
                        if mode=='duplicate':sock.sendall(wire)
                        log('ack-sent',sequence=ack.sequence,run=ack.generation)
        except (OSError,TimeoutError,ValueError) as error:log('connection-ended',reason=str(error))
        time.sleep(.1) # Host process only; Lua never blocks connecting or waiting.
    log('host-deadline');return 0

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',default='.local/phase1-events-launch.json');p.add_argument('--seconds',type=float,default=120);p.add_argument('--mode',choices=['normal','drop-ack-once','disconnect-once','stale-ack-once','fragmented','duplicate'],default='normal');a=p.parse_args()
    raise SystemExit(run(ROOT/a.config,a.seconds,a.mode))
