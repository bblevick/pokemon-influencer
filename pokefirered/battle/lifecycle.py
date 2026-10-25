"""Decision lifecycle evidence, distinct from canonical battle facts and effects."""
import json
from roster.extract import digest
TERMINAL={'EXECUTED','CANCELED_BATTLE_ENDED','CANCELED_TIMEOUT_FALLBACK','CANCELED_RESET','CANCELED_RUN_ABORT','CANCELED_UNSUPPORTED'}
STAGES=TERMINAL|{'REQUESTED','RESULT_PUBLISHED','CONTROLLER_EMITTED'}
class LifecycleMixin:
 def record_decision_lifecycle(self,record):
  if record.get('stage') not in STAGES:raise ValueError('unknown decision lifecycle stage')
  def action():
   scope=record['scope'];c=self.campaign()
   if scope['campaign']!=c['id'] or scope['branch']!=c['active_branch']:raise ValueError('stale lifecycle branch')
   identity=[c['id'],c['active_branch'],record['session'],record['generation'],record['nativeRequest']]
   keys=[digest(['lifecycle',*identity,stage]) for stage in sorted(TERMINAL)]
   view=self._one('SELECT cutoff FROM battle_audit_view WHERE campaign=?',(c['id'],))
   visible=(c['cursor'],view['cutoff'])
   terminal=self._one('SELECT record FROM battle_decision_audit WHERE cursor<=? AND rowid<=? AND id IN ('+','.join('?' for _ in keys)+')',(*visible,*keys))
   terminal=json.loads(terminal['record']) if terminal else None
   if terminal:
    if c['status'] not in ('paired','imported'):raise ValueError('inactive lifecycle duplicate')
    if terminal['stage']!=record['stage']:raise ValueError('decision already terminal')
    fields=('session','generation','nativeRequest','nativeHash','battle','turn','phase','battler','nativeSelected')
    if any(terminal.get(k)!=record.get(k) for k in fields):raise ValueError('conflicting lifecycle duplicate')
    return terminal['lifecycleID']
   key=digest(['lifecycle',*identity,record['stage']]);old=self._one('SELECT record FROM battle_decision_audit WHERE id=? AND cursor<=? AND rowid<=?',(key,*visible))
   if old:
    if c['status'] not in ('paired','imported'):raise ValueError('inactive lifecycle duplicate')
    previous=json.loads(old['record']);fields=('session','generation','nativeRequest','nativeHash','battle','turn','phase','battler','nativeSelected')
    if any(previous.get(k)!=record.get(k) for k in fields):raise ValueError('conflicting lifecycle duplicate')
    return key
   self._writable();c=self.campaign()
   if c['active_branch']!=scope['branch']:raise ValueError('stale lifecycle branch')
   payload={**record,'event':'decision-disposition','lifecycleID':key}
   row=self.db.execute('INSERT INTO battle_decision_audit VALUES(?,?,?,?,?)',(key,c['id'],c['active_branch'],c['cursor'],json.dumps(payload,sort_keys=True)))
   self.db.execute('UPDATE battle_audit_view SET cutoff=?',(row.lastrowid,));return key
  return self._tx(action)
 def decision_lifecycle(self):return [r for r in self.battle_audit() if r.get('event')=='decision-disposition']
