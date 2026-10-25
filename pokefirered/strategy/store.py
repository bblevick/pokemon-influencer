"""Separate derived intent log, save pairing and revocable immutable job grants."""
from __future__ import annotations
import json
from pathlib import Path
from prep.store import PrepStore
from world.store import WorldError,dump
from roster.extract import digest
from .context import build_context,configuration_identity
from .domain import validate,normalize

def empty():return {'version':1,'opportunities':{},'postures':{}}

class StrategyStore(PrepStore):
    _supports_strategy=True
    def __init__(self,*args,**kw):
        self._strategy_ready=False
        super().__init__(*args,**kw)
        try:
            if self._one("SELECT name FROM sqlite_master WHERE name='strategy_version'"):
                if [tuple(r) for r in self.db.execute('SELECT * FROM strategy_version')]!=[(1,configuration_identity())]:raise WorldError('strategy configuration changed; explicit adoption required')
            else:
                self.db.executescript('BEGIN IMMEDIATE;'+(Path(__file__).parent/'migration.sql').read_text())
                try:
                    self.db.execute('INSERT INTO strategy_version VALUES (1,?)',(configuration_identity(),))
                    for table in ('strategy_log','strategy_branches','strategy_checkpoints'):
                        for op in ('UPDATE','DELETE'):self.db.execute(f"CREATE TRIGGER immutable_{table}_{op} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'append-only Strategy'); END")
                    for b in self.db.execute('SELECT id FROM branches'):self.db.execute('INSERT INTO strategy_branches VALUES (?,0)',(b['id'],))
                    for cp in self.db.execute('SELECT id FROM checkpoints'):self.db.execute('INSERT INTO strategy_checkpoints VALUES (?,0,?)',(cp['id'],digest(empty())))
                    c=self.campaign();self.db.execute('INSERT INTO strategy_view VALUES (?,?,0,0)',(c['id'],c['active_branch']))
                    self.db.execute('COMMIT')
                except Exception:self.db.execute('ROLLBACK');raise
            if self._one("SELECT name FROM sqlite_master WHERE name='strategy_memo_version'") and not getattr(self,'_supports_memo',False):raise WorldError('memo database requires MemoStore')
            self._strategy_ready=True
        except Exception:self.close();raise

    def _ensure_strategy(self):
        c=self.campaign();v=self._one('SELECT * FROM strategy_view')
        if not self._one('SELECT * FROM strategy_branches WHERE branch=?',(c['active_branch'],)):
            self.db.execute('INSERT INTO strategy_branches VALUES (?,?)',(c['active_branch'],v['cutoff']))
        if v['branch']!=c['active_branch']:self.db.execute('UPDATE strategy_view SET branch=?,epoch=epoch+1',(c['active_branch'],))

    def _writable(self):
        super()._writable()
        if self._strategy_ready:self._ensure_strategy()

    def _after_memory_transaction(self):
        super()._after_memory_transaction()
        if not self._strategy_ready:return
        self._ensure_strategy()
        if self._restoring:
            cp=self._one('SELECT * FROM strategy_checkpoints WHERE checkpoint=?',(self._restoring,))
            if not cp:raise WorldError('missing strategy pairing')
            self.db.execute('UPDATE strategy_view SET cutoff=?,epoch=epoch+1',(cp['cutoff'],))
            if self.verify_strategy_replay()!=cp['state_sha']:raise WorldError('strategy pairing mismatch')
            self.db.execute("UPDATE strategy_jobs SET status='revoked',outcome='restore' WHERE status='active'")
            if self._one('SELECT 1 FROM strategy_log WHERE branch=? AND seq>?',(self.get_active_branch(),cp['cutoff'])):self.db.execute('UPDATE campaigns SET pending_fork=1')

    def _strategy_events(self,branch=None,cursor=None,cutoff=None):
        c=self.campaign();v=self._one('SELECT * FROM strategy_view');branch=branch or c['active_branch'];cursor=c['cursor'] if cursor is None else cursor;cutoff=v['cutoff'] if cutoff is None else cutoff
        b=self._one('SELECT * FROM branches WHERE id=?',(branch,));bound=self._one('SELECT * FROM strategy_branches WHERE branch=?',(branch,))
        prefix=self._strategy_events(b['parent'],min(cursor,b['fork_cursor']),min(cutoff,bound['parent_cutoff'])) if b['parent'] else []
        return prefix+[{**dict(r),'payload':json.loads(r['payload'])} for r in self.db.execute('SELECT * FROM strategy_log WHERE branch=? AND cursor<=? AND seq<=? ORDER BY seq',(branch,cursor,cutoff))]

    def strategy_state(self):
        s=empty()
        for e in self._strategy_events():
            p=e['payload']
            if e['kind'] in ('OPPORTUNITY','GRANT'):s['opportunities'][p['jobID']]=p
            elif e['kind'] in ('POSTURE','MEMO'):s['postures'][p['jobID']]=p
            else:raise WorldError('unknown strategy receipt')
        return s

    def verify_strategy_replay(self):return digest(self.strategy_state())

    def _append_strategy(self,kind,key,payload):
        self._ensure_strategy();c=self.campaign();identity=digest(['strategy1',c['id'],c['active_branch'],kind,key]);old=self._one('SELECT payload FROM strategy_log WHERE id=?',(identity,))
        if old:
            if old['payload']!=dump(payload):raise WorldError('conflicting strategy receipt')
            return identity
        r=self.db.execute('INSERT INTO strategy_log(id,campaign,branch,cursor,kind,payload) VALUES (?,?,?,?,?,?)',(identity,c['id'],c['active_branch'],c['cursor'],kind,dump(payload)))
        self.db.execute('UPDATE strategy_view SET cutoff=?',(r.lastrowid,));return identity

    def _checkpoint(self,c,save,kind):
        cid=super()._checkpoint(c,save,kind)
        if self._strategy_ready:
            self._ensure_strategy();v=self._one('SELECT * FROM strategy_view');sha=self.verify_strategy_replay();old=self._one('SELECT * FROM strategy_checkpoints WHERE checkpoint=?',(cid,))
            if old and (old['cutoff'],old['state_sha'])!=(v['cutoff'],sha):raise WorldError('ambiguous strategy pairing; native new save required')
            if not old:self.db.execute('INSERT INTO strategy_checkpoints VALUES (?,?,?)',(cid,v['cutoff'],sha))
        return cid

    def context_packet(self,*args,**kw):return build_context(self,*args,**kw)

    def recorded_strategy(self,actor,stage='forest-post-boulder-1',purpose='preparation',provider_binding=None):
        packet=self.context_packet(actor,stage,purpose,provider_binding)
        for decision in reversed(list(self.strategy_state()['postures'].values())):
            if decision['actor']==actor and decision['materialContextSHA256']==packet['materialContextSHA256']:
                # Historical bound snapshot is unchanged; explicit fresh grant is separate.
                return {'decision':decision,'currentContextID':packet['contextID'],'currentEnvelopeID':packet['scope']['envelopeID'],'status':'current'}
        return None

    def begin_strategy(self,actor,stage='forest-post-boulder-1',purpose='preparation',provider_binding=None):
        def action():
            if self.pending_save():raise WorldError('strategy save barrier')
            recorded=self.recorded_strategy(actor,stage,purpose,provider_binding)
            if recorded:return {'status':'recorded','decision':recorded['decision']}
            self._writable();packet=self.context_packet(actor,stage,purpose,provider_binding)
            job='strategy-job:'+digest([packet['scope']['campaign'],packet['scope']['branch'],actor,purpose,packet['materialContextSHA256']])
            old=self._one('SELECT * FROM strategy_jobs WHERE id=?',(job,))
            if old:
                if old['status']=='active' and json.loads(old['context'])['contextID']==packet['contextID']:return {'status':'active','jobID':job,'packet':json.loads(old['context'])}
                if old['status']=='completed':raise WorldError('completed strategy not in active prefix')
                self.db.execute("UPDATE strategy_jobs SET context=?,status='active',outcome=NULL WHERE id=?",(dump(packet),job))
                self._append_strategy('GRANT',packet['contextID'],{'jobID':job,'context':packet})
                return {'status':'active','jobID':job,'packet':packet}
            if self._one("SELECT 1 FROM strategy_jobs WHERE status='active'"):raise WorldError('one strategy job at a time')
            self.db.execute('INSERT INTO strategy_jobs(id,context,status) VALUES (?,?,?)',(job,dump(packet),'active'))
            self._append_strategy('OPPORTUNITY',job,{'jobID':job,'context':packet})
            return {'status':'active','jobID':job,'packet':packet}
        return self._tx(action)

    def job_current(self,job):
        row=self._one('SELECT * FROM strategy_jobs WHERE id=?',(job,))
        if not row or row['status']!='active' or self.pending_save():return False
        packet=json.loads(row['context']);s=packet['scope']
        try:return self.context_packet(s['actor'],packet['modelInput']['preparation']['stage'],s['strategyPurpose'],s['providerConfiguration'])['contextID']==packet['contextID']
        except ValueError:return False

    def count_attempt(self,job,context_id=None):
        def action():
            if not self.job_current(job):raise WorldError('stale_strategy_job')
            row=self._one('SELECT attempts,context FROM strategy_jobs WHERE id=?',(job,))
            if context_id!=json.loads(row['context'])['contextID']:raise WorldError('wrong_strategy_grant')
            if row['attempts']>=3:raise WorldError('strategy_job_budget')
            self.db.execute('UPDATE strategy_jobs SET attempts=attempts+1 WHERE id=?',(job,))
        self._tx(action)

    def finish_strategy(self,job,posture,source,diagnostics,context_id=None):
        if source not in ('model','fallback','mock'):raise ValueError('strategy_source')
        def action():
            if not self.job_current(job):raise WorldError('stale_strategy_job')
            packet=json.loads(self._one('SELECT context FROM strategy_jobs WHERE id=?',(job,))['context'])
            if context_id!=packet['contextID']:raise WorldError('wrong_strategy_grant')
            normalized=normalize(validate(posture,packet));s=packet['scope']
            result={'strategyID':'strategy:'+digest([job,normalized]),'jobID':job,'actor':s['actor'],'scope':s,'contextID':packet['contextID'],'materialContextSHA256':packet['materialContextSHA256'],'normalizedOutput':normalized,'source':source,'diagnostics':diagnostics,'schemaVersion':2,'promptVersion':1}
            self._append_strategy('POSTURE',job,result);self.db.execute("UPDATE strategy_jobs SET status='completed',outcome=? WHERE id=?",(result['strategyID'],job));return result
        return self._tx(action)

    def revoke_strategy(self,job,reason):
        return self._tx(lambda:self.db.execute("UPDATE strategy_jobs SET status='revoked',outcome=? WHERE id=? AND status='active'",(reason,job)))
