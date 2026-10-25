#!/usr/bin/env python3
"""Stop only task-local emulator and Strategy acceptance hosts; retain all data."""
import os,signal,subprocess,shlex,time,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def stop():
 stopped=[]
 for row in subprocess.check_output(['ps','-axo','pid=,args='],text=True).splitlines():
  pid,args=row.strip().split(' ',1)
  try:argv=shlex.split(args)
  except ValueError:continue
  is_emulator=argv and argv[0]==str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA')
  is_host=len(argv)>1 and Path(argv[0]).name.lower() in ('python','python3','python3.9') and argv[1]=='tools/strategy01_host.py'
  if is_emulator or is_host:
   os.kill(int(pid),signal.SIGTERM);stopped.append(int(pid))
 deadline=time.monotonic()+5
 while time.monotonic()<deadline:
  remaining=[]
  for pid in stopped:
   try:os.kill(pid,0);remaining.append(pid)
   except ProcessLookupError:pass
  if not remaining:return {'stoppedPIDs':stopped,'remaining':[],'deletedFiles':[]}
  time.sleep(.1)
 raise RuntimeError('task processes still exiting; inspect before restore')
if __name__=='__main__':print(json.dumps(stop()))
