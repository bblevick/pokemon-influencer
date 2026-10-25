#!/usr/bin/env python3
"""Sequential localhost HELLO/close probe; no inference, gameplay or RAM edits."""
import argparse,json,socket,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bridge.events_wire import Message,Decoder
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=16);a=p.parse_args();assert 1<=a.count<=128
cfg=json.loads((root/'.local/phase1-events-launch.json').read_text());m=json.loads((root/cfg['manifest']).read_text());runs=[]
for i in range(a.count):
 with socket.create_connection(('127.0.0.1',cfg['port']),timeout=2) as s:
  s.settimeout(2);d=Decoder()
  s.sendall(Message(0,cfg['nonce'],0,0,m['build_tag'],0,cfg['token'].encode()+bytes.fromhex(m['rom_sha256'])).encode())
  while True:
   messages=d.feed(s.recv(256))
   if messages:
    msg=messages[0];assert msg.kind==3 and msg.nonce==cfg['nonce'] and msg.tag==m['build_tag'];runs.append(msg.generation);break
 time.sleep(.1)
r={'connections':a.count,'runs':runs,'runUnchanged':len(set(runs))==1,'session':cfg['nonce'],'romSHA256':m['rom_sha256'],'passed':len(set(runs))==1,'scope':'live loopback authenticated reconnects; emulator needs previously loaded script; token omitted'}
(root/'evidence/phase1/bridge02/reconnect-probe.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
