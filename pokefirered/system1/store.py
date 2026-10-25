"""Derived selection/commitment log; atomic projection; native pairing is separate."""
import json,copy
from dataclasses import asdict
from world.store import WorldError,dump
from roster.extract import digest
from strategy.memo import MemoStore
from prep.domain import _replay
from roster.domain import Companion,Step
from .domain import build_request,validate_decision,revalidate,debit_stock,candidate_for
from world.continuation import ContinuationMixin

def empty():return {'version':1,'decisions':{},'commitments':{},'installations':{}}
class PreparationDecisionStore(ContinuationMixin, MemoStore):
    _supports_preparation_decisions=True
    def __init__(self,*a,**kw):
        self._decision_ready=False
        super().__init__(*a,**kw)
        def migrate():
            if self._one("SELECT name FROM sqlite_master WHERE name='preparation_decision_version'"):
                if [tuple(r) for r in self.db.execute('SELECT * FROM preparation_decision_version')]!=[(1,)]:raise WorldError('decision version mismatch')
            else:
                self.db.execute('CREATE TABLE preparation_decision_version(version INTEGER NOT NULL)');self.db.execute('INSERT INTO preparation_decision_version VALUES(1)')
                self.db.execute('CREATE TABLE preparation_decision_log(seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT UNIQUE NOT NULL,branch TEXT NOT NULL,cursor INTEGER NOT NULL,kind TEXT NOT NULL,payload TEXT NOT NULL)')
                self.db.execute('CREATE TABLE preparation_decision_branches(branch TEXT PRIMARY KEY,parent_cutoff INTEGER NOT NULL)')
                self.db.execute('CREATE TABLE preparation_decision_view(campaign TEXT PRIMARY KEY,branch TEXT NOT NULL,cutoff INTEGER NOT NULL,epoch INTEGER NOT NULL)')
                self.db.execute('CREATE TABLE preparation_decision_checkpoints(checkpoint TEXT PRIMARY KEY,cutoff INTEGER NOT NULL,state_sha TEXT NOT NULL)')
                self.db.execute('CREATE TABLE preparation_decision_jobs(id TEXT PRIMARY KEY,packet TEXT NOT NULL,status TEXT NOT NULL,attempts INTEGER NOT NULL)')
                for table in ('preparation_decision_log','preparation_decision_branches','preparation_decision_checkpoints'):
                    for op in ('UPDATE','DELETE'):self.db.execute(f"CREATE TRIGGER immutable_{table}_{op} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'append-only preparation decision');END")
                for b in self.db.execute('SELECT id FROM branches'):self.db.execute('INSERT INTO preparation_decision_branches VALUES(?,0)',(b['id'],))
                for cp in self.db.execute('SELECT id FROM checkpoints'):self.db.execute('INSERT INTO preparation_decision_checkpoints VALUES(?,0,?)',(cp['id'],digest(empty())))
                c=self.campaign();self.db.execute('INSERT INTO preparation_decision_view VALUES(?,?,0,0)',(c['id'],c['active_branch']))
        try:self._tx(migrate);self._decision_ready=True
        except Exception:self.close();raise
    def _ensure_decision(self):
        c=self.campaign();v=self._one('SELECT * FROM preparation_decision_view')
        if not self._one('SELECT 1 FROM preparation_decision_branches WHERE branch=?',(c['active_branch'],)):
            self.db.execute('INSERT INTO preparation_decision_branches VALUES(?,?)',(c['active_branch'],v['cutoff']))
        if v['branch']!=c['active_branch']:self.db.execute('UPDATE preparation_decision_view SET branch=?,epoch=epoch+1',(c['active_branch'],))
    def _writable(self):
        super()._writable()
        if self._decision_ready:self._ensure_decision()
    def _after_memory_transaction(self):
        # Select decision prefix BEFORE inherited PREP restore validation, because
        # committed companions/opportunities are part of that trusted projection.
        if self._decision_ready:self._ensure_decision()
        if self._decision_ready and self._restoring:
            cp=self._one('SELECT * FROM preparation_decision_checkpoints WHERE checkpoint=?',(self._restoring,))
            if not cp:raise WorldError('missing preparation decision pairing')
            self.db.execute('UPDATE preparation_decision_view SET cutoff=?,epoch=epoch+1',(cp['cutoff'],))
            if self.verify_decision_replay()!=cp['state_sha']:raise WorldError('preparation decision pairing mismatch')
            self.db.execute("UPDATE preparation_decision_jobs SET status='revoked' WHERE status='active'")
            if self._one('SELECT 1 FROM preparation_decision_log WHERE branch=? AND seq>?',(self.get_active_branch(),cp['cutoff'])):self.db.execute('UPDATE campaigns SET pending_fork=1')
        super()._after_memory_transaction()
    def _decision_events(self,branch=None,cursor=None,cutoff=None):
        c=self.campaign();v=self._one('SELECT * FROM preparation_decision_view');branch=branch or c['active_branch'];cursor=c['cursor'] if cursor is None else cursor;cutoff=v['cutoff'] if cutoff is None else cutoff
        b=self._one('SELECT * FROM branches WHERE id=?',(branch,));bound=self._one('SELECT * FROM preparation_decision_branches WHERE branch=?',(branch,))
        prefix=self._decision_events(b['parent'],min(cursor,b['fork_cursor']),min(cutoff,bound['parent_cutoff'])) if b['parent'] else []
        return prefix+[{**dict(r),'payload':json.loads(r['payload'])} for r in self.db.execute('SELECT * FROM preparation_decision_log WHERE branch=? AND cursor<=? AND seq<=? ORDER BY seq',(branch,cursor,cutoff))]
    def decision_state(self):
        s=empty()
        for e in self._decision_events():
            p=e['payload']
            if e['kind']=='DECISION':s['decisions'][p['request']['requestID']]=p
            elif e['kind']=='COMMITMENT':s['commitments'][p['opportunityID']]=p
            elif e['kind']=='INSTALLATION':s['installations'][p['encounterID']]=p
            elif e['kind']=='NATIVE_PROVENANCE':s.setdefault('nativeProvenance',{})[e['id']]=p
            else:raise WorldError('unknown preparation decision receipt')
        return s
    def verify_decision_replay(self):return digest(self.decision_state())
    def _append_decision(self,kind,key,payload):
        self._ensure_decision();c=self.campaign();identity=digest(['preparation-decision1',c['id'],c['active_branch'],kind,key]);old=self._one('SELECT payload FROM preparation_decision_log WHERE id=?',(identity,))
        if old:
            if old['payload']!=dump(payload):raise WorldError('conflicting decision receipt')
            return identity
        row=self.db.execute('INSERT INTO preparation_decision_log(id,branch,cursor,kind,payload) VALUES(?,?,?,?,?)',(identity,c['active_branch'],c['cursor'],kind,dump(payload)));self.db.execute('UPDATE preparation_decision_view SET cutoff=?',(row.lastrowid,));return identity
    def preparation_state(self):
        s=super().preparation_state()
        if not self._decision_ready:return s
        for oid,c in self.decision_state()['commitments'].items():
            s['actors'][c['actor']]['companions']=copy.deepcopy(c['companions'])
            s['actors'][c['actor']]['resources']['stock']=copy.deepcopy(c['remainingStock'])
            # Authored first encounters are declarative, not earned training tokens.
            if oid not in s['opportunities']:
                if c.get('stage')!='first':raise WorldError('missing earned preparation opportunity')
                s['opportunities'][oid]={'opportunityID':oid,'actor':c['actor'],'stage':'first','kind':'first-encounter','earnedAllowance':0}
            s['opportunities'][oid]['status']='committed';s['opportunities'][oid]['commitmentID']=c['commitmentID'];s['reservations'].pop(oid,None)
        return s
    def get_preparation_opportunity(self,actor,stage='forest-post-boulder-1'):
        if self._decision_ready and stage=='first':
            lock=self.locked_preparation(actor)
            if lock and lock.get('stage')=='first':return self.preparation_state()['opportunities'][lock['opportunityID']]
        return super().get_preparation_opportunity(actor,stage)
    def locked_preparation(self,actor):
        return next((c for c in reversed(list(self.decision_state()['commitments'].values())) if c['actor']==actor),None)
    def _checkpoint(self,c,save,kind):
        cid=super()._checkpoint(c,save,kind)
        if self._decision_ready:
            self._ensure_decision();v=self._one('SELECT * FROM preparation_decision_view');sha=self.verify_decision_replay();old=self._one('SELECT * FROM preparation_decision_checkpoints WHERE checkpoint=?',(cid,))
            if old and (old['cutoff'],old['state_sha'])!=(v['cutoff'],sha):raise WorldError('ambiguous preparation decision pairing')
            if not old:self.db.execute('INSERT INTO preparation_decision_checkpoints VALUES(?,?,?)',(cid,v['cutoff'],sha))
        return cid
    def begin_selection(self,actor,stage='forest-post-boulder-1'):
        def action():
            if self.pending_save():raise WorldError('preparation save barrier')
            locked=self.locked_preparation(actor)
            if locked:return {'status':'committed','commitment':locked}
            self._writable();p=build_request(self,actor,stage);previous=self.decision_state()['decisions'].get(p['requestID'])
            if previous:return {'status':'recorded','decision':previous}
            old=self._one('SELECT * FROM preparation_decision_jobs WHERE id=?',(p['requestID'],))
            if old:
                if old['status']=='revoked':raise WorldError('revoked preparation grant; new branch required')
                return {'status':'active','request':json.loads(old['packet'])}
            if self._one("SELECT 1 FROM preparation_decision_jobs WHERE status='active'"):raise WorldError('one preparation decision at a time')
            self.db.execute('INSERT INTO preparation_decision_jobs VALUES(?,?,?,0)',(p['requestID'],dump(p),'active'));return {'status':'active','request':p}
        return self._tx(action)
    def revoke_selection(self,request_id):
        # A preflight formatting change may revoke an unused grant, never erase it.
        def action():
            row=self._one('SELECT status,attempts FROM preparation_decision_jobs WHERE id=?',(request_id,))
            if not row or row['status']!='active' or row['attempts']:raise WorldError('only unused grants may be revoked')
            self.db.execute("UPDATE preparation_decision_jobs SET status='revoked' WHERE id=?",(request_id,))
        self._tx(action)
    def selection_current(self,p):
        row=self._one('SELECT status,packet FROM preparation_decision_jobs WHERE id=?',(p['requestID'],))
        if not row or row['status']!='active' or row['packet']!=dump(p) or self.pending_save() or self.locked_preparation(p['actor']):return False
        try:return build_request(self,p['actor'],p['stage'])['requestID']==p['requestID']
        except ValueError:return False
    def count_selection_attempt(self,p):
        def action():
            if not self.selection_current(p):raise WorldError('stale preparation grant')
            row=self._one('SELECT attempts FROM preparation_decision_jobs WHERE id=?',(p['requestID'],))
            if row['attempts']>=2:raise WorldError('preparation logical decision budget')
            self.db.execute('UPDATE preparation_decision_jobs SET attempts=attempts+1 WHERE id=?',(p['requestID'],))
        self._tx(action)
    def finish_selection(self,p,result,source):
        if source not in ('model','fallback','mock','sole'):raise WorldError('decision source')
        validate_decision(result,p['choices'])
        def action():
            previous=self.decision_state()['decisions'].get(p['requestID'])
            if previous:
                if previous['result']!=result or previous['source']!=source:raise WorldError('conflicting duplicate selection')
                return previous
            if not self.selection_current(p):raise WorldError('stale preparation decision')
            r={'decisionID':'selection:'+digest([p['requestID'],result,source]),'request':p,'result':result,'source':source,'phase':'SYSTEM1_DECISION_RECORDED'}
            self._append_decision('DECISION',p['requestID'],r);self.db.execute("UPDATE preparation_decision_jobs SET status='completed' WHERE id=?",(p['requestID'],));return r
        return self._tx(action)
    def commit_preparation(self,decision_id):
        def action():
            if self.pending_save():raise WorldError('preparation save barrier')
            ds=self.decision_state();d=next((d for d in ds['decisions'].values() if d['decisionID']==decision_id),None)
            if not d:raise WorldError('decision outside active timeline')
            p=d['request'];oid=p['scope']['opportunityID'];old=ds['commitments'].get(oid)
            if old:
                if old['decisionID']!=decision_id:raise WorldError('conflicting commitment')
                return old
            self._writable();candidate,proof=revalidate(self,p,d['result']);s=self.preparation_state();owner=s['actors'][p['actor']];remaining=debit_stock(owner['resources']['stock'],candidate['resourceCosts'])
            companions=[]
            for oldc in owner['companions']:
                c=Companion(**{**oldc,'moves':tuple(oldc['moves']),'history':tuple(Step(**x) for x in oldc['history'])})
                steps=[Step(**x) for x in candidate['paths'][c.lineage]];companions.append(asdict(_replay(c,steps)))
            r={'schemaVersion':1,'commitmentID':'commitment:'+digest([decision_id,candidate]),'encounterID':'prepared-encounter:'+digest([p['scope']['campaign'],p['scope']['branch'],oid]),'decisionID':decision_id,'opportunityID':oid,'actor':p['actor'],'stage':p['stage'],'scope':p['scope'],'strategyID':p['memo']['strategyID'],'memoSHA256':p['memoSHA256'],'strategyText':p['memo']['strategyText'],'candidate':candidate,'companions':json.loads(json.dumps(companions)),'remainingStock':remaining,'resourceCosts':candidate['resourceCosts'],'revalidation':proof,'phase':'COMMITTED','locked':True}
            if hasattr(self,'prebattle_facts'):
                r['authorizedPrebattleFacts']=self.prebattle_facts(p['actor'])
            self._append_decision('COMMITMENT',oid,r);return r
        return self._tx(action)

    def record_installation(self,encounter_id,receipt):
        def action():
            c=next((c for c in self.decision_state()['commitments'].values() if c['encounterID']==encounter_id),None)
            if not c:raise WorldError('installation outside active commitment')
            expected=[next(p for p in c['candidate']['party'] if p['lineage']==lineage) for lineage in c['candidate']['order']]
            self._launch(receipt.get('nonce'),receipt.get('generation'))
            if receipt.get('commitmentDigest')!=c['commitmentID'].split(':')[1] or receipt.get('nativeROM')!=getattr(self,'compatibility',{}).get('nativeROM'):raise WorldError('native installation identity mismatch')
            if receipt.get('party')!=[{k:p[k] for k in ('species','level','moves','heldItem')} for p in expected] or receipt.get('nativeConstructorCount')!=1:raise WorldError('native installation mismatch')
            r={'encounterID':encounter_id,'commitmentID':c['commitmentID'],'receipt':receipt,'phase':'INSTALLED_FOR_ENCOUNTER'}
            old=self.decision_state()['installations'].get(encounter_id)
            if old:return old
            self._append_decision('INSTALLATION',encounter_id,r);return r
        return self._tx(action)
