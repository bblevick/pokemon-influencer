"""Scoped SYSTEM1-01B experiment; same native adapter, killable off-writer worker."""
import json,time,os,fcntl,subprocess,sys,hashlib
from pathlib import Path
from strategy.provider import ProviderError
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/phase4/system1_01b';PRIVATE=ROOT/'.local/system1_01b';LEDGER=E/'requests.json';ROUTE=PRIVATE/'route.json'
class BattleBudget:
 def __init__(self,path):self.path=Path(path)
 def __enter__(self):
  self.lock=self.path.with_suffix('.lock').open('a');fcntl.flock(self.lock,fcntl.LOCK_EX);return self
 def __exit__(self,*args):self.lock.close()
 def read(self):return json.loads(self.path.read_text()) if self.path.exists() else {'version':1,'maximumAttempts':30,'closed':False,'attempts':[]}
 def write(self,value):
  temp=self.path.with_suffix('.tmp');
  with temp.open('w') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  os.replace(temp,self.path);self.path.chmod(0o600)
 def charge(self,job,model):
  v=self.read()
  if v.get('maximumAttempts')!=30 or v['closed'] or len(v['attempts'])>=30 or any(a['jobID']==job for a in v['attempts']):raise ProviderError('battle_budget_closed_exhausted_or_duplicate')
  v['attempts'].append({'jobID':job,'requestedModel':model,'startedAtUnix':time.time()});self.write(v);return len(v['attempts'])
 def finish(self,job,outcome):
  v=self.read()
  for a in v['attempts']:
   if a['jobID']==job:a['workerOutcome']=outcome
  self.write(v)
 def close(self):v=self.read();v['closed']=True;self.write(v)
class LiveBattleProvider:
 def decide(self,state,question,choices):
  with BattleBudget(LEDGER) as b:
   if b.read()['closed']:return None
  # Exact bounded text already filtered by BATTLE-01. No DB/ROM/player-memory access.
  job='battle:'+hashlib.sha256(json.dumps([state,question,choices],sort_keys=True).encode()).hexdigest()
  payload=json.dumps({'state':state,'question':question,'choices':choices,'jobID':job})
  started=time.monotonic()
  try:r=subprocess.run([sys.executable,str(ROOT/'tools/system1_01b_worker.py')],input=payload,capture_output=True,text=True,timeout=2.55,cwd=ROOT)
  except subprocess.TimeoutExpired:
   with BattleBudget(LEDGER) as b:
    b.finish(job,{'error':'battle_worker_hard_deadline','elapsedSeconds':time.monotonic()-started});b.close()
   raise ProviderError('battle_worker_hard_deadline') from None
  if r.returncode:
   # Only the worker's small symbolic error is used; never retain arbitrary stderr.
   try:reason=json.loads(r.stderr).get('error')
   except (ValueError,AttributeError):reason=None
   if not isinstance(reason,str) or not reason.startswith(('system1_','battle_','missing_','unqualified_')):reason='battle_worker_unavailable'
   with BattleBudget(LEDGER) as b:
    b.finish(job,{'error':reason,'elapsedSeconds':time.monotonic()-started});b.close()
   raise ProviderError(reason)
  try:return json.loads(r.stdout)
  except ValueError:
   with BattleBudget(LEDGER) as b:
    b.finish(job,{'error':'battle_worker_invalid_output','elapsedSeconds':time.monotonic()-started});b.close()
   raise ProviderError('battle_worker_invalid_output') from None
