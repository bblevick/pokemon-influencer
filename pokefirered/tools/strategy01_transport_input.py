#!/usr/bin/env python3
"""Retained bounded input driver. Never retry an ambiguous mutation."""
import argparse,json,socket,time,fcntl
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/phase3/strategy01'
_shots={}
def send(*commands):
 with (ROOT/'.local/phase1-events-gameplay.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  deadline=time.monotonic()+5
  while True:
   sock=None
   try:
    sock=socket.create_connection(('127.0.0.1',18783),timeout=2);sock.settimeout(3)
    sock.sendall(b'sample\n')
    if sock.recv(128).strip()!=b'OK':raise ConnectionError('read-only readiness')
    break
   except OSError as error:
    if sock:sock.close()
    with (E/'input-commands.jsonl').open('a') as f:f.write(json.dumps({'command':'read-only readiness sample','error':str(error),'time':time.time()})+'\n')
    if time.monotonic()>deadline:raise
    time.sleep(.1)
  with sock:
   for command in commands:
    if len(command)>96 or '\n' in command:raise ValueError('bounds')
    if command.startswith('shot '):_shots[command[5:]]=(E/'emulator.jsonl').stat().st_size
    try:
     sock.sendall((command+'\n').encode('ascii'));response=sock.recv(128).decode().strip()
    except OSError as error:
     with (E/'input-commands.jsonl').open('a') as f:f.write(json.dumps({'command':command,'error':str(error),'retried':False,'time':time.time()})+'\n')
     raise
    with (E/'input-commands.jsonl').open('a') as f:f.write(json.dumps({'command':command,'response':response,'time':time.time()})+'\n')
    print(command+': '+response,flush=True)
    if response!='OK':raise ValueError('test input rejected')
def wait_shot(name,seconds=30):
 path=ROOT/'evidence/private/strategy01'/f'{name}.png';deadline=time.monotonic()+seconds
 while True:
  complete=path.exists()
  if name in _shots:
   with (E/'emulator.jsonl').open() as f:f.seek(_shots[name]);lines=f.read().splitlines()
   complete=complete and any(json.loads(x).get('event')=='sample' and json.loads(x).get('detail','').startswith(name+' ') for x in lines)
  if complete:return path
  if time.monotonic()>deadline:raise TimeoutError('queued screenshot '+name)
  time.sleep(.1)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('commands',nargs='+');a=p.parse_args();send(*a.commands)
