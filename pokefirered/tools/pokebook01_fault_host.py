#!/usr/bin/env python3
"""Bounded presentation-only fault peer; never model/domain/event writes."""
import argparse,json,socket,time,struct
from pokebook01 import ROOT,E,manifest
from pokebook.wire import HEADER,REQUEST
from bridge.events_wire import Message,Decoder
from phase1_events_host import append

def run(mode,seconds):
 cfg=json.loads((ROOT/'.local/pokebook01-launch.json').read_text());m=manifest();end=time.monotonic()+seconds;sequence=0
 with socket.create_connection(('127.0.0.1',cfg['port']),timeout=2) as sock:
  sock.settimeout(.2);sock.sendall(Message(0,cfg['nonce'],0,0,m['build_tag'],0,cfg['token'].encode()+bytes.fromhex(m['rom_sha256'])).encode());decoder=Decoder();run=0
  while time.monotonic()<end:
   try:data=sock.recv(256)
   except socket.timeout:continue
   except ConnectionResetError:return # Expected oversized/stale frame rejection.
   if not data:break
   for msg in decoder.feed(data):
    if not run:
     if (msg.kind,msg.typ,msg.nonce,msg.tag)!=(3,0,cfg['nonce'],m['build_tag']):raise ValueError('HELLO')
     run=msg.generation;continue
    if msg.kind==5 and msg.typ==7:
     sock.sendall(Message(6,msg.nonce,msg.generation,msg.sequence,msg.tag,8,b'').encode());continue
    if msg.kind!=1 or msg.typ!=5:raise ValueError('fault peer refuses gameplay requests')
    ver,op,req,view,snap,post,page,_=REQUEST.unpack(msg.payload);sequence=msg.sequence
    body=HEADER.pack(2,op,req,view,1 if op==1 else snap,post,page,0)+(struct.pack('<I',0) if op==1 else b'')
    nonce=msg.nonce
    if mode=='silent':continue
    if mode=='disconnect':return
    if mode=='late':time.sleep(1.5)
    elif mode=='schema':body=b'\x03'+body[1:]
    elif mode=='malformed':body=body[:12]
    elif mode=='oversized':body+=bytes(97-len(body))
    elif mode=='control':
     if op==1:body=HEADER.pack(2,op,req,view,1,0,0,1)+struct.pack('<I',0)
     elif op==2:
      from bridge.ui import MAP
      label=bytes(MAP[c] for c in 'Fault fixture')
      body=HEADER.pack(2,op,req,view,snap,0,0,1)+struct.pack('<I',1)+label+b'\xff'+bytes(18-len(label))
     else:body=HEADER.pack(2,op,req,view,snap,post,page,1)+b'\xfc'
    elif mode=='stale-view':body=HEADER.pack(2,op,req,view+1,1 if op==1 else snap,post,page,0)+(struct.pack('<I',0) if op==1 else b'')
    elif mode=='stale-nonce':nonce^=1
    elif mode=='abandoned':
     launches=[json.loads(line) for line in (E/'launches.jsonl').read_text().splitlines()]
     nonce=launches[-2]['nonce']
     prior=[json.loads(line) for line in (E/'host.jsonl').read_text().splitlines()]
     real=json.loads((E/'native-records-before-view.json').read_text())
     hashes=[real[k] for k in ('canonicalSHA256','memorySHA256','socialSHA256','puppeteerSHA256')]
     body=next(bytes.fromhex(row['responseHex']) for row in prior if row['event']=='viewer-response' and row['historySHA256']==hashes and HEADER.unpack_from(bytes.fromhex(row['responseHex']))[1]==3)
    elif mode=='missing':body=HEADER.pack(2,op|512,req,view,snap,post,page,0)
    reply=Message(4,nonce,run,sequence,m['build_tag'],6,body)
    # Deliberately allow97byte frames only for this peer's wire-size test.
    if mode=='oversized':
     from bridge.events_wire import HEADER as WH,checksum
     raw=WH.pack(b'PI02',2,4,nonce,run,sequence,m['build_tag'],6,len(body),0,0,checksum(sequence,nonce,run,6,body))+body
     sock.sendall(struct.pack('<H',len(raw))+raw)
    else:sock.sendall(reply.encode())
    append(E/'faults.jsonl',{'mode':mode,'requestHex':msg.payload.hex(),'responseHex':body.hex(),'nonce':nonce,'delayedSeconds':1.5 if mode=='late' else 0})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['abandoned','oversized','silent','disconnect','late','schema','malformed','control','stale-view','stale-nonce','missing']);p.add_argument('--seconds',type=float,default=15);a=p.parse_args();run(a.mode,a.seconds)
