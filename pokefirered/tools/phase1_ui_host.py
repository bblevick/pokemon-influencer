#!/usr/bin/env python3
"""Deterministic presentation fixtures plus separate B2 event/observation recorder."""
import argparse,json,socket,time,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bridge.events_wire import Message,Decoder
from bridge.events import Consumer
from bridge.ui import Command,Responses
from phase1_events_host import append
from phase1_ui_build import ROOT,E,verify_ui

def run(seconds):
 cfg=json.loads((ROOT/'.local/phase1-ui-launch.json').read_text());m=json.loads((ROOT/cfg['manifest']).read_text());verify_ui(m)
 deadline=time.monotonic()+seconds;commands={};requests={};responses=Responses();consumers={};counter=0;faulted=set()
 def log(event,**kw):append(E/'host.jsonl',{'event':event,**kw})
 # Restore this launch's fixture correlation/dedupe from accepted local bytes.
 # This is a test recorder, not durable world/save pairing.
 reqmeta={}
 history=E/'host.jsonl'
 if history.exists():
  for line in history.read_text().splitlines():
   row=json.loads(line)
   if row['event']=='ui-request':reqmeta[(row['run'],row['requestID'])]=row
   elif row['event']=='ui-command':
    msg=Message.decode(bytes.fromhex(row['wireHex'])[2:])
    if msg.nonce!=cfg['nonce'] or msg.tag!=m['build_tag']:continue
    key=(msg.generation,row['requestID']);meta=reqmeta[key];kind=meta['kind'];savedmode=row['mode']
    command=Command(row['commandID'],row['requestID'],kind,row['text'],((11,'YES'),(22,'NO')) if kind==2 else (),60 if savedmode=='ui-timeout' else 900)
    requests[key]=command;commands[(msg.generation,command.command_id)]=(command,savedmode);counter=max(counter,command.command_id)
 if len(requests)>256:raise ValueError('fixture log capacity; fresh launch required')
 responsefile=E/'ui-responses.jsonl'
 if responsefile.exists():
  for line in responsefile.read_text().splitlines():
   row=json.loads(line)
   if row['session']!=cfg['nonce'] or row['romSHA256']!=m['rom_sha256']:continue
   msg=Message.decode(bytes.fromhex(row['wireHex'])[2:]);entry=commands.get((msg.generation,msg.sequence))
   if entry:responses.accept(msg,entry[0],msg.nonce,msg.generation,msg.tag)
 eventfile=E/'events.jsonl'
 if eventfile.exists():
  for line in eventfile.read_text().splitlines():
   row=json.loads(line)
   if row['session']!=cfg['nonce'] or row['romSHA256']!=m['rom_sha256']:continue
   msg=Message.decode(bytes.fromhex(row['wireHex'])[2:]);consumers.setdefault(msg.generation,Consumer(msg.nonce,msg.generation,msg.tag)).accept(msg)
 log('fixture-log-restored',command_count=len(commands),response_count=len(responses.seen),next_command=counter+1)
 while time.monotonic()<deadline:
  try:
   with socket.create_connection(('127.0.0.1',cfg['port']),timeout=.3) as sock:
    sock.settimeout(.2);decoder=Decoder();run_id=0
    sock.sendall(Message(0,cfg['nonce'],0,0,m['build_tag'],0,cfg['token'].encode()+bytes.fromhex(m['rom_sha256'])).encode())
    while time.monotonic()<deadline:
     try:data=sock.recv(256)
     except socket.timeout:continue
     if not data:break
     for msg in decoder.feed(data):
      if not run_id:
       if msg.kind!=3 or msg.typ or msg.sequence or msg.nonce!=cfg['nonce'] or msg.tag!=m['build_tag'] or not msg.generation:raise ValueError('HELLO')
       run_id=msg.generation;consumers.setdefault(run_id,Consumer(msg.nonce,run_id,msg.tag));log('hello',session=msg.nonce,run=run_id);continue
      if (msg.nonce,msg.generation,msg.tag)!=(cfg['nonce'],run_id,m['build_tag']):raise ValueError('wrong transport identity')
      if msg.kind==1 and msg.typ==3:
       record,ack=consumers[run_id].accept(msg)
       if record:
        record['wireHex']=msg.encode().hex();record['romSHA256']=m['rom_sha256'];append(E/'events.jsonl',record)
        append(E/('observations.jsonl' if record['recordClass']=='observation' else 'canonical-events.jsonl'),record)
       sock.sendall(ack.encode());continue
      if msg.kind==1 and msg.typ==5:
       if len(msg.payload)!=8:raise ValueError('UI request length')
       ver,kind,req=struct.unpack('<HHI',msg.payload)
       if ver!=1 or kind not in (1,2) or req!=msg.sequence or not req:raise ValueError('UI request')
       key=(run_id,req)
       modefile=ROOT/'.local/ui-host-mode.json';mode=json.loads(modefile.read_text()).get('mode','normal') if modefile.exists() else 'normal'
       log('ui-request',requestID=req,kind=kind,run=run_id,mode=mode)
       if mode=='disconnect':raise ConnectionError('intentional after request')
       if mode=='timeout':continue
       if key in requests:command=requests[key]
       else:
        if len(requests)>=256:raise ValueError('bounded fixture host capacity')
        counter+=1
        command=Command(counter,req,kind,'Bridge test message received.' if kind==1 else 'Do you want to send this test response?',((11,'YES'),(22,'NO')) if kind==2 else (),60 if mode=='ui-timeout' else 900)
        requests[key]=command;commands[(run_id,command.command_id)]=(command,mode)
       out=command.message(msg.nonce,run_id,msg.tag);payload=bytearray(out.payload)
       if mode=='bad-schema':payload[0]=99
       elif mode=='bad-character':payload[20]=0xfc
       elif mode=='bad-terminator':payload[20]=0xff
       elif mode=='bad-length':payload[18]=48
       elif mode=='bad-count':payload[12]=4
       elif mode=='bad-id':payload[14:16]=b'\0\0'
       elif mode=='oversized':payload=bytearray(out.payload[:20]+b'\xbb'*49);payload[18]=49
       elif mode=='short':payload=payload[:8]
       if mode=='oversized-wire':
        sock.sendall(struct.pack('<H',133)+b'\0'*133);log('fault-sent',mode=mode,run=run_id);continue
       if mode=='stale':
        sock.sendall(Message(4,msg.nonce,run_id+1,out.sequence,msg.tag,6,out.payload).encode())
       out=Message(4,out.nonce,out.generation,out.sequence,out.tag,6,bytes(payload))
       sock.sendall(out.encode())
       if mode=='duplicate':sock.sendall(out.encode())
       log('ui-command',commandID=command.command_id,requestID=req,run=run_id,mode=mode,wireHex=out.encode().hex(),text=command.text)
      elif msg.kind==5 and msg.typ==7:
       entry=commands.get((run_id,msg.sequence))
       if entry is None:log('uncorrelated-terminal',run=run_id,wireHex=msg.encode().hex());continue
       command,mode=entry
       record=responses.accept(msg,command,msg.nonce,run_id,msg.tag)
       if record:
        record['wireHex']=msg.encode().hex();record['romSHA256']=m['rom_sha256'];append(E/'ui-responses.jsonl',record);log('ui-response',**record)
       else:log('ui-response-duplicate',commandID=msg.sequence,run=run_id)
       if mode=='duplicate-response' and (run_id,msg.sequence) not in faulted:
        faulted.add((run_id,msg.sequence));continue
       sock.sendall(Message(6,msg.nonce,run_id,msg.sequence,msg.tag,8,b'').encode())
      else:raise ValueError('unsupported host inbound type')
  except (OSError,ValueError) as e:log('connection-ended',reason=str(e))
  time.sleep(.1)
 log('host-deadline')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,default=120);a=p.parse_args();run(a.seconds)
