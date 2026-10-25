#!/usr/bin/env python3
"""Single local HERMES writer; database commit precedes event ACK. Inference is a separate bounded worker outside ingestion/ACK."""
import argparse,json,socket,sys,time,os,signal,fcntl,subprocess
from hermes01 import ROOT,E,manifest,open_store,save_identity
from bridge.events_wire import Message,Decoder
from phase1_events_host import append
from world.receipts import read_receipts

def run(seconds,mode,live,experiment):
 cfg=json.loads((ROOT/'.local/hermes01-launch.json').read_text());m=manifest();end=time.monotonic()+seconds;receipts=Path(cfg['receipts']);offset=0
 lock=(ROOT/'.local/hermes01/host.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 def stop(signum,frame):
  nonlocal end
  end=0
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 with open_store(cfg['database']) as w:
  worker=None;worker_job=None
  for r in w.db.execute("SELECT id FROM puppeteer_jobs WHERE status='active'").fetchall():w.recover_job(r['id'],'host_restart')
  def log(event,**data):append(E/'host.jsonl',{'event':event,**data})
  def generation():
   nonlocal worker,worker_job
   if worker is not None:
    if worker.poll() is None:return
    log('worker-ended',jobID=worker_job,exit=worker.returncode);w.recover_job(worker_job,'worker_exit');worker=None
   if w.pending_save() or w.campaign()['pending_fork'] or w.campaign()['status'] not in ('paired','imported'):return
   o=next((o for o in w.puppeteer_state()['obligations'].values() if o['status']!='PUBLISHED'),None)
   if not o:return
   job=w.begin_job(o['obligationID'],mode);worker_job=job['jobID']
   if mode=='offline':log('recap-settled',outcome=w.fallback(worker_job));return
   argv=[sys.executable,str(ROOT/'scripts/run_hermes_fresh.py'),'--database',cfg['database'],'--job',worker_job,'--mode',mode]+['--experiment',experiment]+(['--live'] if live else [])
   out=(E/'live-worker.jsonl').open('a')
   try:worker=subprocess.Popen(argv,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
   finally:out.close()
   log('worker-launched',jobID=worker_job,pid=worker.pid,argv=argv)
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
    try:
     # Callback follows native dirty-data sync. Require two stable content reads.
     with open(cfg['save'],'r+b') as battery:os.fsync(battery.fileno())
     one=save_identity(cfg['save']);two=save_identity(cfg['save'])
     if one.fingerprint!=two.fingerprint:raise ValueError('persisted save still changing')
     checkpoint=w.finish_save(intent['id'],one,receipt)
     append(E/'pairings.jsonl',{'checkpoint':checkpoint,'receipt':receipt});log('save-paired',checkpointID=checkpoint['id'])
    except ValueError as error:log('pairing-refused',reason=str(error),intent=intent['id'])
  log('host-open',campaign=w.campaign(),stateSHA256=w.verify_replay(),memorySHA256=w.verify_memory_replay(),socialSHA256=w.verify_social_replay())
  while time.monotonic()<end:
   try:
    with socket.create_connection(('127.0.0.1',cfg['port']),timeout=.3) as sock:
     sock.settimeout(.2);decoder=Decoder();runid=0
     sock.sendall(Message(0,cfg['nonce'],0,0,m['build_tag'],0,cfg['token'].encode()+bytes.fromhex(m['rom_sha256'])).encode())
     while time.monotonic()<end:
      saves();generation()
      try:data=sock.recv(256)
      except socket.timeout:continue
      if not data:break
      for msg in decoder.feed(data):
       if not runid:
        if msg.kind!=3 or msg.typ or msg.sequence or msg.nonce!=cfg['nonce'] or msg.tag!=m['build_tag'] or msg.generation!=1:raise ValueError('unmanaged HELLO/run; fresh paired battery launch required')
        w._launch(msg.nonce,msg.generation);runid=msg.generation;log('hello',nonce=msg.nonce,run=runid);continue
       if (msg.nonce,msg.generation,msg.tag)!=(cfg['nonce'],runid,m['build_tag']):raise ValueError('wrong identity')
       if msg.kind==1 and msg.typ==3:
        result=w.ingest(msg)
        # SQLite is the authority; evidence sinks are secondary diagnostic copies.
        append(E/'deliveries.jsonl',{'wireHex':msg.encode().hex(),'result':result,'campaign':w.campaign()})
        sock.sendall(Message(2,msg.nonce,msg.generation,msg.sequence,msg.tag,4,b'').encode())
       elif msg.typ in (5,7):log('ui-idle',type=msg.typ) # No HERMES UI requests/commands.
       else:raise ValueError('unexpected world inbound')
   except OSError as error:log('connection-ended',reason=str(error))
   except ValueError as error:
    w.suspend(str(error));log('world-suspended',reason=str(error))
   saves();generation();time.sleep(.1)
  if worker is not None and worker.poll() is None:
   w.recover_job(worker_job,'host_shutdown');worker.terminate()
   try:worker.wait(timeout=5)
   except subprocess.TimeoutExpired:worker.kill();worker.wait(timeout=3)
  saves();log('host-close',campaign=w.campaign(),stateSHA256=w.verify_replay(),memorySHA256=w.verify_memory_replay(),socialSHA256=w.verify_social_replay())
from pathlib import Path
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,default=1800);p.add_argument('--mode',choices=['offline','mock','shadow','enabled-test'],default='offline');p.add_argument('--live',action='store_true');p.add_argument('--experiment',choices=['original','closeout'],default='original');a=p.parse_args()
 if a.live and a.mode not in ('shadow','enabled-test'):p.error('live requires explicit test mode')
 run(a.seconds,a.mode,a.live,a.experiment)
