#!/usr/bin/env python3
"""Single local writer: commit before event ACK, existing offline mandatory recaps, read-only viewer queries. No inference worker is launched."""
import argparse,json,socket,sys,time,os,signal,fcntl,subprocess
from strategy01 import PRIVATE,CONFIG,SCREENS,ROOT,E,manifest,open_store,save_identity
from bridge.events_wire import Message,Decoder
from pokebook.viewer import Viewer
from pokebook.wire import respond,REQUEST
import struct
from phase1_events_host import append
from world.receipts import read_receipts
from world.save_recovery import receipt_disposition
from world.restart import recover_durable_work
from bridge.continuity import Inbox
from bridge.managed import Health,native_witness

def run(seconds,services=None,battle_handler=None):
 mode='offline'
 cfg=json.loads((CONFIG).read_text());m=manifest();end=time.monotonic()+seconds;receipts=Path(cfg['receipts']);offset=0
 health=Health(cfg);inbox=Inbox(cfg['continuity']['inbox']) if cfg.get('continuity') else None
 lock=(PRIVATE/'host.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 def stop(signum,frame):
  nonlocal end
  end=0
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 with open_store(cfg['database']) as w:
  worker=None;worker_job=None;viewer=Viewer(w)
  def log(event,**data):append(E/'host.jsonl',{'event':event,**data})
  recovery_done=False;waiting_intent=None
  def recover_work():
   nonlocal recovery_done,waiting_intent
   if recovery_done:return
   recovery=recover_durable_work(w)
   if recovery['status']=='waiting_save':
    if waiting_intent!=recovery['intent']:
     waiting_intent=recovery['intent'];log('restart-work-waiting',prerequisite='validated native save callback',intent=waiting_intent)
    return
   for operation in recovery['operations']:log('restart-work-disposition',**operation)
   if battle_handler is not None and hasattr(battle_handler,'recover'):battle_handler.recover(w)
   recovery_done=True
  def generation():
   nonlocal worker,worker_job
   if services is not None:
    services.tick(w);return
   if worker is not None:
    if worker.poll() is None:return
    log('worker-ended',jobID=worker_job,exit=worker.returncode);w.recover_job(worker_job,'worker_exit');worker=None
   if w.pending_save() or w.campaign()['pending_fork'] or w.campaign()['status'] not in ('paired','imported'):return
   o=next((o for o in w.puppeteer_state()['obligations'].values() if o['status']!='PUBLISHED'),None)
   if not o:return
   job=w.begin_job(o['obligationID'],mode);worker_job=job['jobID']
   if mode=='offline':log('recap-settled',outcome=w.fallback(worker_job));return
  def saves():
   nonlocal offset
   if not receipts.exists():return
   records,offset=read_receipts(receipts,offset)
   for receipt in records:
    if receipt['nonce']!=cfg['nonce']:continue
    intent=w.pending_save()
    if not intent:
     known=w.get_save_checkpoint(save_identity(cfg['save']).fingerprint)
     log('historical-or-paired-save-update' if known else 'unpaired-save-update',receipt=receipt);continue
    disposition=receipt_disposition(intent,receipt)
    if disposition!='candidate_requires_full_validation':
     log('save-callback-disposition',intent=intent['id'],disposition=disposition,receipt=receipt);continue
    try:
     # Callback follows native dirty-data sync. Require two stable content reads.
     with open(cfg['save'],'r+b') as battery:os.fsync(battery.fileno())
     one=save_identity(cfg['save']);two=save_identity(cfg['save'])
     if one.fingerprint!=two.fingerprint:raise ValueError('persisted save still changing')
     checkpoint=w.finish_save_with_progression(intent['id'],cfg['save'],receipt)
     append(E/'pairings.jsonl',{'checkpoint':checkpoint,'receipt':receipt});log('save-paired',checkpointID=checkpoint['id'])
    except ValueError as error:log('pairing-refused',reason=str(error),intent=intent['id'])
  # Finish a valid durable native save before recovering tactical/job writes.
  saves()
  recover_work()
  log('host-open',campaign=w.campaign(),stateSHA256=w.verify_replay(),memorySHA256=w.verify_memory_replay(),socialSHA256=w.verify_social_replay())
  health.publish(w,'OPEN')
  while time.monotonic()<end:
   try:
    with socket.create_connection(('127.0.0.1',cfg['port']),timeout=.3) as sock:
     sock.settimeout(.2);decoder=Decoder();runid=0
     sock.sendall(Message(0,cfg['nonce'],0,0,m['build_tag'],0,cfg['token'].encode()+bytes.fromhex(m['rom_sha256'])).encode())
     while time.monotonic()<end:
      saves();recover_work();health.publish(w,'CONNECTED' if runid else 'CONNECTING')
      if battle_handler is not None and not w.pending_save():battle_handler.tick(w,sock)
      generation()
      # Poll tactical work closely; slow providers never block event/UI progress.
      sock.settimeout(.01 if battle_handler is not None and battle_handler.job is not None else .2)
      try:data=sock.recv(256)
      except socket.timeout:continue
      if not data:break
      for msg in decoder.feed(data):
       if not runid:
        if msg.kind!=3 or msg.typ or msg.sequence or msg.nonce!=cfg['nonce'] or msg.tag!=m['build_tag'] or msg.generation!=1:raise ValueError('unmanaged HELLO/run; fresh paired battery launch required')
        w._launch(msg.nonce,msg.generation);runid=msg.generation;log('hello',nonce=msg.nonce,run=runid);continue
       if (msg.nonce,msg.generation,msg.tag)!=(cfg['nonce'],runid,m['build_tag']):raise ValueError('wrong identity')
       if msg.kind==1 and msg.typ==3:
        if inbox is not None:
         witness=native_witness(cfg,w,msg)
         identity=inbox.stage(w,msg,witness)
         result=inbox.apply(w,identity,witness)
        else:result=w.ingest(msg)
        if battle_handler is not None and hasattr(battle_handler,'observe_event'):battle_handler.observe_event(msg,w)
        # SQLite is the authority; evidence sinks are secondary diagnostic copies.
        append(E/'deliveries.jsonl',{'wireHex':msg.encode().hex(),'result':result,'campaign':w.campaign()})
        health.publish(w,'CONNECTED')  # Publish durable cut before native ACK can advance.
        if battle_handler is None or not hasattr(battle_handler,'before_event_ack') or battle_handler.before_event_ack(msg,w,sock,result):
         sock.sendall(Message(2,msg.nonce,msg.generation,msg.sequence,msg.tag,4,b'').encode())
       elif battle_handler is not None and msg.kind in (8,10,12):battle_handler.receive(msg,w,sock)
       elif msg.kind==1 and msg.typ==5:
        before=[w.verify_replay(),w.verify_memory_replay(),w.verify_social_replay(),w.verify_puppeteer_replay()]
        try:
         if len(msg.payload)!=24 or REQUEST.unpack(msg.payload)[2]!=msg.sequence:raise ValueError('viewer request correlation')
         body=respond(viewer,msg.payload)
        except ValueError as error:
         log('viewer-rejected',reason=str(error));continue
        command=msg.sequence # ROM request IDs increase across host restarts.
        sock.sendall(Message(4,msg.nonce,msg.generation,command,msg.tag,6,body).encode())
        after=[w.verify_replay(),w.verify_memory_replay(),w.verify_social_replay(),w.verify_puppeteer_replay()]
        if before!=after:raise ValueError('viewer changed durable history')
        log('viewer-response',requestHex=msg.payload.hex(),responseHex=body.hex(),historySHA256=before)
       elif msg.kind==5 and msg.typ==7:
        sock.sendall(Message(6,msg.nonce,msg.generation,msg.sequence,msg.tag,8,b'').encode())
        log('viewer-terminal',payload=msg.payload.hex())
       else:raise ValueError('unexpected world inbound')
   except OSError as error:
    if battle_handler is not None:battle_handler.disconnected()
    log('connection-ended',reason=str(error))
   except ValueError as error:
    w.suspend(str(error));log('world-suspended',reason=str(error));end=0
   saves();generation();health.publish(w,'RECONNECTING');time.sleep(.1)
  # Stop the whole owned native process before retiring the canonical writer.
  # This also freezes ongoing scripts/battles, not just automated button input.
  health.close(w)
  if worker is not None and worker.poll() is None:
   w.recover_job(worker_job,'host_shutdown');worker.terminate()
   try:worker.wait(timeout=5)
   except subprocess.TimeoutExpired:worker.kill();worker.wait(timeout=3)
  if services is not None:services.close(w)
  if battle_handler is not None:battle_handler.close()
  saves();log('host-close',campaign=w.campaign(),stateSHA256=w.verify_replay(),scopedReplayStatus='revoked' if w.campaign()['status']=='incomplete' else 'active')
  if inbox is not None:inbox.close()
from pathlib import Path
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,default=1800);a=p.parse_args()
 run(a.seconds)
