"""Serialized SQLite authority; append-only facts, transactional active projection.

Only managed fresh-process battery restores are authorized. A launch alias is a
trusted host identity, never a value supplied by the emulator or future NPCs.
"""
import copy,hashlib,json,sqlite3,time,uuid
from pathlib import Path
from bridge.events import Consumer,decode_event
from . import reducer
SCHEMA=1
ROOT=Path(__file__).resolve().parents[1]
def dump(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def uid():return str(uuid.uuid4())
class WorldError(ValueError):pass
MIGRATION_1=(Path(__file__).parent/'migrations/001.sql').read_text()
class WorldStore:
 def __init__(self,path,build,tag,registry=None):
  if len(build)!=64 or any(c not in '0123456789abcdef' for c in build):raise WorldError('ROM hash')
  self.build=build;self.tag=tag;self.registry=registry or json.loads((ROOT/'config/trainer_registry.json').read_text())
  catalog={k:v for k,v in self.registry.items() if k!='catalogSHA256'}
  if hashlib.sha256(dump(catalog).encode()).hexdigest()!=self.registry['catalogSHA256'] or self.registry['registryVersion']!=1:raise WorldError('trainer registry integrity/version')
  self.db=sqlite3.connect(path,timeout=2,isolation_level=None);self.db.row_factory=sqlite3.Row
  self.db.execute('PRAGMA foreign_keys=ON');self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL')
  if self._one("SELECT name FROM sqlite_master WHERE name='prep_version'") and not getattr(self,'_supports_preparation',False):
   self.close();raise WorldError('preparation-enabled database requires PrepStore writer')
  if self._one("SELECT name FROM sqlite_master WHERE name='strategy_version'") and not getattr(self,'_supports_strategy',False):
   self.close();raise WorldError('strategy-enabled database requires StrategyStore writer')
  if self._one("SELECT name FROM sqlite_master WHERE name='virality_version'") and not getattr(self,'_supports_virality',False):
   self.close();raise WorldError('virality-enabled database requires ViralityStore writer')
  version=self.db.execute('PRAGMA user_version').fetchone()[0]
  if self._one("SELECT name FROM sqlite_master WHERE name='memory_version'") and not getattr(self,'_supports_memory',False):
   self.close();raise WorldError('memory-enabled database requires MemoryStore writer')
  if version>SCHEMA:self.close();raise WorldError('database newer than supported software')
  if version not in (0,SCHEMA):self.close();raise WorldError('explicit migration required')
  if version==0:
   try:
    self.db.executescript('BEGIN IMMEDIATE;'+MIGRATION_1)
    meta={'build':build,'tag':tag,'protocol':2,'schema':SCHEMA,'reducer':reducer.VERSION,'registry':self.registry['catalogSHA256']}
    self.db.executemany('INSERT INTO metadata VALUES (?,?)',[(k,dump(v)) for k,v in meta.items()])
    for table in ('events','deliveries','observations','checkpoints'):
     for op in ('UPDATE','DELETE'):
      self.db.execute(f"CREATE TRIGGER immutable_{table}_{op} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'append-only table'); END")
    self.db.execute('PRAGMA user_version=1');self.db.execute('COMMIT')
   except Exception:self.db.execute('ROLLBACK');self.close();raise
  expected={'build':build,'tag':tag,'protocol':2,'schema':SCHEMA,'reducer':reducer.VERSION,'registry':self.registry['catalogSHA256']}
  actual={r['key']:json.loads(r['value']) for r in self.db.execute('SELECT * FROM metadata')}
  if actual!=expected:self.close();raise WorldError('incompatible database build/protocol/schema/reducer/registry')
 def close(self):self.db.close()
 def __enter__(self):return self
 def __exit__(self,*args):self.close()
 def _one(self,sql,args=()):return self.db.execute(sql,args).fetchone()
 def _tx(self,fn):
  if self._one("SELECT name FROM sqlite_master WHERE name='virality_version'") and not getattr(self,'_supports_virality',False):
   raise WorldError('virality-enabled database requires ViralityStore writer')
  if not getattr(self,'_supports_strategy',False) and self._one("SELECT name FROM sqlite_master WHERE name='strategy_version'"):
   raise WorldError('strategy-enabled database requires StrategyStore writer')
  if not getattr(self,'_supports_preparation',False) and self._one("SELECT name FROM sqlite_master WHERE name='prep_version'"):
   raise WorldError('preparation-enabled database requires PrepStore writer')
  if not getattr(self,'_supports_memory',False) and self._one("SELECT name FROM sqlite_master WHERE name='memory_version'"):
   raise WorldError('memory-enabled database requires MemoryStore writer')
  self.db.execute('BEGIN IMMEDIATE')
  try:result=fn();self.db.execute('COMMIT');return result
  except Exception:self.db.execute('ROLLBACK');raise
 def campaign(self,campaign=None):
  row=self._one('SELECT * FROM campaigns WHERE id=?',(campaign,)) if campaign else self._one('SELECT * FROM campaigns')
  if not row:raise WorldError('no active campaign; explicit import required')
  return dict(row)
 def get_active_branch(self):return self.campaign()['active_branch']
 def get_current_world_cursor(self):return self.campaign()['cursor']
 def state(self,campaign=None):
  c=self.campaign(campaign);return json.loads(self._one('SELECT state FROM projection WHERE campaign=?',(c['id'],))['state'])
 def get_trainer(self,world_id):
  registry=self.registry['trainers'].get(world_id)
  if registry is None:raise WorldError('unknown world trainer')
  return {'identity':copy.deepcopy(registry),'facts':self.state()['trainers'].get(world_id)}
 def get_trainer_encounters(self,world_id):
  f=self.get_trainer(world_id)['facts'];return [self.get_battle(b) for b in f['battleIDs']] if f else []
 def get_battle(self,battle):return self.state()['battles'].get(battle)
 def get_canonical_events(self,branch=None,cursor=None):
  c=self.campaign()
  if branch is None and cursor is None:cursor=c['cursor']
  branch=branch or c['active_branch'];b=self._one('SELECT * FROM branches WHERE id=?',(branch,))
  if b is None:raise WorldError('unknown branch')
  cursor=b['head'] if cursor is None else cursor
  if not 0<=cursor<=b['head']:raise WorldError('branch cursor bounds')
  prefix=self.get_canonical_events(b['parent'],min(cursor,b['fork_cursor'])) if b['parent'] else []
  rows=self.db.execute('SELECT * FROM events WHERE branch=? AND cursor<=? ORDER BY cursor',(branch,cursor))
  return prefix+[{'eventID':r['id'],'branchID':r['branch'],'cursor':r['cursor'],'origin':r['origin'],'battleID':r['battle'],'record':json.loads(r['record'])} for r in rows]
 def replay(self,branch=None,cursor=None):
  c=self.campaign();branch=branch or c['active_branch'];cursor=c['cursor'] if cursor is None and branch==c['active_branch'] else cursor
  s=reducer.empty()
  for e in self.get_canonical_events(branch,cursor):reducer.apply(s,e,self.registry)
  return s
 def verify_replay(self):
  s=self.replay()
  if s!=self.state():raise WorldError('projection/replay mismatch')
  return hashlib.sha256(dump(s).encode()).hexdigest()
 def _project(self,campaign,state):self.db.execute('INSERT OR REPLACE INTO projection VALUES (?,?)',(campaign,dump(state)))
 def _checkpoint(self,c,save,kind):
  old=self.get_save_checkpoint(save.fingerprint)
  if old:
   if (old['campaign'],old['branch'],old['cursor'])!=(c['id'],c['active_branch'],c['cursor']):raise WorldError('save fingerprint already paired to another history')
   return old['id']
  s=self.state(c['id']);cid=uid()
  self.db.execute('INSERT INTO checkpoints VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',(cid,c['id'],c['active_branch'],c['cursor'],save.fingerprint,dump(save.as_dict()),hashlib.sha256(dump(s).encode()).hexdigest(),self.build,SCHEMA,reducer.VERSION,kind,time.time()))
  return cid
 def import_save(self,save):
  def action():
   if self._one('SELECT id FROM campaigns'):raise WorldError('explicit import requires a new database; unrelated history cannot merge')
   campaign,branch=uid(),uid()
   self.db.execute('INSERT INTO campaigns VALUES (?,?,0,?,0)',(campaign,branch,'imported'))
   self.db.execute('INSERT INTO branches VALUES (?,?,NULL,0,0)',(branch,campaign));self._project(campaign,reducer.empty())
   self._checkpoint(self.campaign(campaign),save,'explicit_import')
   return self.campaign(campaign)
  return self._tx(action)
 def get_save_checkpoint(self,fingerprint):
  r=self._one('SELECT * FROM checkpoints WHERE fingerprint=?',(fingerprint,));return dict(r) if r else None
 def restore(self,save):
  def action():
   p=self.get_save_checkpoint(save.fingerprint)
   if not p:raise WorldError('unpaired save: explicit import into new database or restore known pair')
   if (p['build'],p['schema'],p['reducer'])!=(self.build,SCHEMA,reducer.VERSION):raise WorldError('incompatible pairing')
   c=self.campaign(p['campaign']);s=self.replay(p['branch'],p['cursor'])
   if hashlib.sha256(dump(s).encode()).hexdigest()!=p['state_sha256']:raise WorldError('checkpoint replay integrity')
   if self._one("SELECT name FROM sqlite_master WHERE name='prebattle_continuations'"):
    self.db.execute("UPDATE prebattle_continuations SET status='abandoned' WHERE status='valid'")
   # Any fresh emulator launch discards unsaved continuation, even at same cursor.
   head=self._one('SELECT head FROM branches WHERE id=?',(p['branch'],))['head']
   self.db.execute('UPDATE campaigns SET active_branch=?,cursor=?,status=?,pending_fork=? WHERE id=?',(p['branch'],p['cursor'],'paired',int(p['cursor']<head),c['id']))
   self.db.execute("UPDATE launches SET status='inactive' WHERE campaign=?",(c['id'],))
   self.db.execute("UPDATE save_intents SET status='incomplete' WHERE campaign=? AND status='pending'",(c['id'],))
   self._project(c['id'],s);return p
  return self._tx(action)
 def authorize_launch(self,nonce,save,origin=None):
  if type(nonce)!=int or not 0<nonce<=0xffffffff:raise WorldError('launch nonce')
  if self._one('SELECT id FROM launches WHERE nonce=?',(nonce,)):raise WorldError('nonce reuse')
  p=self.restore(save);origin=origin or uid()
  def action():
   self.db.execute('INSERT INTO launches VALUES (?,?,?,?,?)',(origin,nonce,p['campaign'],save.fingerprint,'active'));return origin
  return self._tx(action)
 def _launch(self,nonce,run):
  l=self._one('SELECT * FROM launches WHERE nonce=?',(nonce,))
  if not l or l['status']!='active' or run!=1:raise WorldError('unmanaged launch/reset: fresh paired battery launch required')
  if self.campaign(l['campaign'])['status'] not in ('paired','imported'):raise WorldError('world is suspended; restore a known pair')
  return l
 def suspend(self,reason):
  def action():
   c=self.campaign();self.db.execute("UPDATE campaigns SET status='incomplete' WHERE id=?",(c['id'],))
   self.db.execute('INSERT INTO outbox VALUES (?,?,?,?)',(uid(),'world_suspended',dump({'reason':reason}),'pending'))
  self._tx(action)
 def ingest(self,message):
  def action():
   if type(message.nonce)!=int or not message.nonce or type(message.generation)!=int or not message.generation or message.tag!=self.tag:raise WorldError('transport identity/build')
   r=decode_event(message);launch=self._launch(message.nonce,message.generation);c=self.campaign(launch['campaign'])
   delivery=f'{self.build}:{message.nonce}:{message.generation}:{message.sequence}'
   wire=message.encode().hex();old=self._one('SELECT * FROM deliveries WHERE identity=?',(delivery,))
   if old:
    if old['wire']!=wire:raise WorldError('conflicting duplicate transport event')
    return {'duplicate':True,'eventID':old['event'],'observationID':old['observation']}
   if self._one("SELECT id FROM save_intents WHERE campaign=? AND status='pending'",(c['id'],)):raise WorldError('gameplay during pending save barrier')
   stream=self._one('SELECT * FROM streams WHERE nonce=? AND run=?',(message.nonce,message.generation))
   consumer=Consumer(message.nonce,message.generation,self.tag)
   if stream:
    st=json.loads(stream['state']);consumer.last=stream['last'];consumer.battles={int(k):v for k,v in st.items()}
   # A dropped transport record prevents a complete authoritative timeline.
   if message.sequence!=consumer.last+1:raise WorldError('out-of-order/gap: world suspended, restore a known pair')
   record,_=consumer.accept(message)
   if record['streamIncomplete']:raise WorldError('incomplete stream')
   if record['eventType']=='BATTLE_STARTED' and record['payload']['battleFlags'] & ~(4|8):raise WorldError('unsupported battle mode')
   origin=f'{launch["id"]}:{message.generation}:{message.sequence}'
   normalized={k:v for k,v in record.items() if k not in ('session','branch')};oid=hashlib.sha256(origin.encode()).hexdigest()
   existing=self._one('SELECT * FROM events WHERE origin=?',(origin,)) if record['recordClass']=='canonical_event' else self._one('SELECT * FROM observations WHERE origin=?',(origin,))
   event_id=observation_id=None
   if existing:
    saved=json.loads(existing['record']);saved={k:v for k,v in saved.items() if k not in ('session','branch')}
    if saved!=normalized:raise WorldError('conflicting canonical origin')
    if record['recordClass']=='canonical_event':
     if existing['id'] not in {x['eventID'] for x in self.get_canonical_events(c['active_branch'],c['cursor'])}:raise WorldError('origin belongs to inactive future')
     event_id=existing['id']
    else:observation_id=existing['id']
   else:
    if record['recordClass']=='canonical_event' and self._one("SELECT name FROM sqlite_master WHERE name='prebattle_continuations'"):
     if record['eventType']=='BATTLE_STARTED':self.db.execute("UPDATE prebattle_continuations SET status='consumed' WHERE status='valid'")
     elif record['eventType']=='BATTLE_ENDED':self.db.execute("UPDATE prebattle_continuations SET status='completed' WHERE status='consumed'")
    if c['pending_fork']:
     if record['eventType']!='BATTLE_STARTED':raise WorldError('divergence must begin a fresh battle, not restored queued records')
     branch=uid();self.db.execute('INSERT INTO branches VALUES (?,?,?,?,?)',(branch,c['id'],c['active_branch'],c['cursor'],c['cursor']))
     self.db.execute('UPDATE campaigns SET active_branch=?,pending_fork=0 WHERE id=?',(branch,c['id']));c=self.campaign(c['id'])
    if record['recordClass']=='canonical_event':
     event_id=oid;cursor=c['cursor']+1;bid=hashlib.sha256(f'{launch["id"]}:{message.generation}:battle:{message.payload[8:12].hex()}'.encode()).hexdigest()
     event={'eventID':event_id,'battleID':bid,'cursor':cursor,'record':record};s=self.state(c['id']);reducer.apply(s,event,self.registry)
     self.db.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?)',(event_id,c['active_branch'],cursor,origin,bid,dump(record),time.time()))
     self.db.execute('UPDATE branches SET head=? WHERE id=?',(cursor,c['active_branch']));self.db.execute('UPDATE campaigns SET cursor=? WHERE id=?',(cursor,c['id']));self._project(c['id'],s)
    else:
     observation_id=oid;self.db.execute('INSERT INTO observations VALUES (?,?,?,?,?,?)',(oid,c['active_branch'],c['cursor'],origin,dump(record),time.time()))
   self.db.execute('INSERT INTO deliveries VALUES (?,?,?,?,?,?,?)',(delivery,launch['id'],message.generation,message.sequence,wire,event_id,observation_id))
   self.db.execute('INSERT OR REPLACE INTO streams VALUES (?,?,?,?,?)',(message.nonce,message.generation,launch['id'],consumer.last,dump(consumer.battles)))
   return {'duplicate':existing is not None,'eventID':event_id,'observationID':observation_id}
  return self._tx(action)
 def begin_save(self,nonce,save):
  def action():
   self._launch(nonce,1);c=self.campaign();s=self.state()
   if any(not b['ended'] for b in s['battles'].values()):raise WorldError('save requires completed battles')
   if self._one("SELECT id FROM save_intents WHERE campaign=? AND status='pending'",(c['id'],)):raise WorldError('save already pending')
   stream=self._one('SELECT last FROM streams WHERE nonce=? AND run=1',(nonce,));last=stream['last'] if stream else 0
   intent=uid();self.db.execute('INSERT INTO save_intents VALUES (?,?,?,?,?,?,?,?,?,?,NULL)',(intent,c['id'],c['active_branch'],c['cursor'],nonce,1,last,save.fingerprint,save.counter,'pending'))
   return intent
  return self._tx(action)
 def pending_save(self):
  r=self._one("SELECT * FROM save_intents WHERE status='pending'");return dict(r) if r else None
 def finish_save(self,intent,save,receipt,fail=False):
  def action():
   p=self._one('SELECT * FROM save_intents WHERE id=?',(intent,))
   if not p or p['status']!='pending':raise WorldError('no pending save intent')
   c=self.campaign(p['campaign'])
   expected={'nonce':p['nonce'],'run':p['run'],'eventCounter':p['last_sequence'],'ack':p['last_sequence'],'depth':0,'state':0,'drops':0,'counter':(p['old_counter']+1)&0xffffffff}
   if any(receipt.get(k)!=v for k,v in expected.items()) or receipt.get('event')!='savedataUpdated':raise WorldError('save receipt/barrier mismatch')
   if save.counter!=expected['counter'] or save.fingerprint==p['old_fingerprint']:raise WorldError('incomplete/unchanged save')
   if (c['active_branch'],c['cursor'])!=(p['branch'],p['cursor']):raise WorldError('world advanced during save')
   cid=self._checkpoint(c,save,'normal_save')
   if fail:raise WorldError('injected checkpoint transaction failure')
   self.db.execute("UPDATE save_intents SET status='paired',checkpoint=? WHERE id=?",(cid,intent))
   self.db.execute('INSERT INTO outbox VALUES (?,?,?,?)',(uid(),'checkpoint_paired',dump({'checkpointID':cid}),'pending'))
   return self.get_save_checkpoint(save.fingerprint)
  return self._tx(action)
 def abandon_save(self,intent):
  self._tx(lambda:self.db.execute("UPDATE save_intents SET status='incomplete' WHERE id=? AND status='pending'",(intent,)))
