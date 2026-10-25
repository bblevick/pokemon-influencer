"""Audited BATTLE-01 build identity; audit rows never become canonical facts."""
import json,hashlib
from pathlib import Path
from system1.native import NativePreparationStore,verify_build
from system1.store import PreparationDecisionStore
from roster.extract import file_hash,digest
from world.saves import layout_from_build
ROOT=Path(__file__).resolve().parents[1]
class BattleStore(NativePreparationStore):
 def __init__(self,path,manifest):
  self._battle_ready=False
  prior=ROOT/'evidence/phase3/system1_01a/manifest-native.json';proof,old=verify_build(prior);m=json.loads(Path(manifest).read_text());rom=ROOT/m['rom_path'];dest=rom.parent
  if file_hash(rom)!=m['rom_sha256'] or file_hash(rom.with_suffix('.elf'))!=m['elf_sha256']:raise ValueError('battle ROM checksum')
  if layout_from_build(rom)!=layout_from_build(ROOT/old['rom_path']):raise ValueError('battle save serialization layout')
  for p,h in m['battle_sources'].items():
   if file_hash(dest/p)!=h:raise ValueError('battle overlay differs '+p)
  for p in ('include/global.h','src/save.c','src/event_data.c','include/constants/flags.h','src/pokemon.c','src/battle_util.c','src/battle_ai_switch_items.c','src/data/trainers.h','src/data/trainer_parties.h'):
   if file_hash(dest/p)!=file_hash((ROOT/old['rom_path']).parent/p):raise ValueError('unauthorized mechanical source change '+p)
  if m['battle_abi']!=[708,1036,48,16,52,340,452,708,1024]:raise ValueError('unsupported native tactical ABI')
  if not m['preparation_checks']['priorRAMSymbolsUnchanged'] or m['battle_control']['size']!=48:raise ValueError('battle allocation')
  self.compatibility={**proof,'nativeROM':m['rom_sha256'],'nativeTag':m['build_tag'],'manifestSHA256':file_hash(manifest),'scope':'BATTLE-01 explicit controlled overlay; all non-hook mechanical data and normal save layout preserved'};self.native_manifest=m
  PreparationDecisionStore.__init__(self,path,proof['baselineROM'],proof['baselineTag'])
  self.db.execute('CREATE TABLE IF NOT EXISTS battle_decision_audit(id TEXT PRIMARY KEY,campaign TEXT NOT NULL,branch TEXT NOT NULL,cursor INTEGER NOT NULL,record TEXT NOT NULL)')
  for op in ('UPDATE','DELETE'):self.db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_battle_audit_{op} BEFORE {op} ON battle_decision_audit BEGIN SELECT RAISE(ABORT,'append-only battle audit');END")
  def migrate_audit():
   self.db.execute('CREATE TABLE IF NOT EXISTS battle_audit_branches(branch TEXT PRIMARY KEY,parent_cutoff INTEGER NOT NULL)')
   self.db.execute('CREATE TABLE IF NOT EXISTS battle_audit_checkpoints(checkpoint TEXT PRIMARY KEY,cutoff INTEGER NOT NULL,state_sha TEXT NOT NULL)')
   self.db.execute('CREATE TABLE IF NOT EXISTS battle_audit_view(campaign TEXT PRIMARY KEY,branch TEXT NOT NULL,cutoff INTEGER NOT NULL)')
   for table in ('battle_audit_branches','battle_audit_checkpoints'):
    for op in ('UPDATE','DELETE'):self.db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{op} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'append-only audit pairing');END")
   for b in self.db.execute('SELECT id FROM branches'):self.db.execute('INSERT OR IGNORE INTO battle_audit_branches VALUES(?,0)',(b['id'],))
   for cp in self.db.execute('SELECT id FROM checkpoints'):self.db.execute('INSERT OR IGNORE INTO battle_audit_checkpoints VALUES(?,0,?)',(cp['id'],digest([])))
   c=self.campaign();self.db.execute('INSERT OR IGNORE INTO battle_audit_view VALUES(?,?,0)',(c['id'],c['active_branch']))
  self._tx(migrate_audit);self._battle_ready=True
 def _ensure_audit(self):
  c=self.campaign();v=self._one('SELECT * FROM battle_audit_view')
  if not self._one('SELECT 1 FROM battle_audit_branches WHERE branch=?',(c['active_branch'],)):self.db.execute('INSERT INTO battle_audit_branches VALUES(?,?)',(c['active_branch'],v['cutoff']))
  self.db.execute('UPDATE battle_audit_view SET branch=?',(c['active_branch'],))
 def _writable(self):
  super()._writable()
  if self._battle_ready:self._ensure_audit()
 def _after_memory_transaction(self):
  super()._after_memory_transaction()
  if self._battle_ready:
   self._ensure_audit()
   if self._restoring:
    cp=self._one('SELECT * FROM battle_audit_checkpoints WHERE checkpoint=?',(self._restoring,))
    if not cp:raise ValueError('missing battle audit pairing')
    self.db.execute('UPDATE battle_audit_view SET cutoff=?',(cp['cutoff'],))
    if digest(self.battle_audit())!=cp['state_sha']:raise ValueError('battle audit pairing integrity')
 def battle_audit(self,branch=None,cursor=None,cutoff=None):
  c=self.campaign();v=self._one('SELECT * FROM battle_audit_view');branch=branch or c['active_branch'];cursor=c['cursor'] if cursor is None else cursor;cutoff=v['cutoff'] if cutoff is None else cutoff
  b=self._one('SELECT * FROM branches WHERE id=?',(branch,));bound=self._one('SELECT * FROM battle_audit_branches WHERE branch=?',(branch,))
  prefix=self.battle_audit(b['parent'],min(cursor,b['fork_cursor']),min(cutoff,bound['parent_cutoff'])) if b['parent'] else []
  return prefix+[json.loads(r['record']) for r in self.db.execute('SELECT record FROM battle_decision_audit WHERE branch=? AND cursor<=? AND rowid<=? ORDER BY rowid',(branch,cursor,cutoff))]
 def _checkpoint(self,c,save,kind):
  cp=super()._checkpoint(c,save,kind)
  if self._battle_ready:
   v=self._one('SELECT * FROM battle_audit_view');old=self._one('SELECT * FROM battle_audit_checkpoints WHERE checkpoint=?',(cp,));value=(v['cutoff'],digest(self.battle_audit()))
   if old and (old['cutoff'],old['state_sha'])!=value:raise ValueError('ambiguous audit pairing')
   if not old:self.db.execute('INSERT INTO battle_audit_checkpoints VALUES(?,?,?)',(cp,*value))
  return cp
 def record_battle_audit(self,record):
  def action():
   c=self.campaign();key=digest([c['id'],c['active_branch'],record['session'],record['generation'],record['nativeRequest']]);old=self._one('SELECT record,rowid,cursor FROM battle_decision_audit WHERE id=?',(key,))
   if old:
    view=self._one('SELECT cutoff FROM battle_audit_view WHERE campaign=?',(c['id'],))
    if c['status'] not in ('paired','imported') or old['rowid']>view['cutoff'] or old['cursor']>c['cursor']:raise ValueError('inactive native decision audit')
    previous=json.loads(old['record']);fields=('nativeHash','battle','turn','phase','battler','source','fallbackReason','nativeSelected')
    if any(previous[k]!=record[k] for k in fields):raise ValueError('conflicting native decision audit')
    return key
   self._writable();c=self.campaign();key=digest([c['id'],c['active_branch'],record['session'],record['generation'],record['nativeRequest']])
   row=self.db.execute('INSERT INTO battle_decision_audit VALUES(?,?,?,?,?)',(key,c['id'],c['active_branch'],c['cursor'],json.dumps(record,sort_keys=True)));self.db.execute('UPDATE battle_audit_view SET cutoff=?',(row.lastrowid,));return key
  return self._tx(action)
