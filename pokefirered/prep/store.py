"""Append-only PREP timeline extension using existing WORLD paired checkpoints.

Only explicit initialize/capture/reservation operations write. No candidate
selection, companion development, resource spending or commitment API exists.
"""
from __future__ import annotations
import json
from pathlib import Path
from dataclasses import asdict
from puppeteer.store import PuppeteerStore
from world.store import WorldError,dump
from roster.domain import Scope,Context,Companion,Step
from .companions import authored_companions
from roster.extract import digest
from content.policy import OpeningContent,TrustedState,ProgressionEvidence
from .progression import read_boulder

def empty():return {'version':1,'activation':None,'actors':{},'progression':None,'opportunities':{},'reservations':{}}

def apply(s,e):
    p=e['payload'];kind=e['kind']
    if kind=='ACTIVATED':s['activation']=p
    elif kind=='CONTENT_ADOPTED':s['contentExtension']=p
    elif kind=='INITIALIZED':s['actors'][p['actor']]=p
    elif kind=='PROGRESSION':s['progression']={'receiptID':e['id'],**p}
    elif kind=='EARNED':s['opportunities'][p['opportunityID']]={'earnedReceipt':e['id'],'status':'available',**p}
    elif kind=='RESERVED':
        s['opportunities'][p['opportunityID']]['status']='reserved';s['reservations'][p['opportunityID']]=p
    elif kind=='RELEASED':
        s['opportunities'][p['opportunityID']]['status']='available';s['reservations'].pop(p['opportunityID'],None)
    else:raise WorldError('unknown PREP receipt')
    return s

class PrepStore(PuppeteerStore):
    _supports_preparation=True
    def __init__(self,*args,content=None,**kw):
        self._prep_ready=False;self.content=content or OpeningContent.load();self._native_capture=None
        super().__init__(*args,**kw)
        try:
            exists=self._one("SELECT name FROM sqlite_master WHERE name='prep_version'")
            if exists:
                if self._one("SELECT 1 FROM prep_log WHERE kind='CONTENT_ADOPTED' LIMIT 1") and not getattr(self,'_supports_campaign_content',False):raise WorldError('campaign content requires version-aware ExpansionStore')
                if [tuple(r) for r in self.db.execute('SELECT * FROM prep_version')]!=[(1,self.content.hash)]:raise WorldError('incompatible PREP content/schema; explicit future adoption required')
            else:
                self.db.executescript('BEGIN IMMEDIATE;'+(Path(__file__).parent/'migration.sql').read_text())
                try:
                    self.db.execute('INSERT INTO prep_version VALUES (1,?)',(self.content.hash,))
                    for table in ('prep_log','prep_branches','prep_checkpoints'):
                        for op in ('UPDATE','DELETE'):self.db.execute(f"CREATE TRIGGER immutable_{table}_{op} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'append-only PREP'); END")
                    for b in self.db.execute('SELECT id FROM branches'):self.db.execute('INSERT INTO prep_branches VALUES (?,0)',(b['id'],))
                    for cp in self.db.execute('SELECT id FROM checkpoints'):self.db.execute('INSERT INTO prep_checkpoints VALUES (?,0,?)',(cp['id'],digest(empty())))
                    c=self._one('SELECT * FROM campaigns')
                    if c:self.db.execute('INSERT INTO prep_view VALUES (?,?,0,0)',(c['id'],c['active_branch']))
                    self.db.execute('COMMIT')
                except Exception:self.db.execute('ROLLBACK');raise
            self._prep_ready=True
        except Exception:self.close();raise

    def _tx(self,fn):
        if not self._prep_ready:return super()._tx(fn)
        def action():
            self._prep_before=self._one('SELECT * FROM prep_view')
            return fn()
        return super()._tx(action)

    def _ensure_branch(self):
        c=self.campaign();v=self._one('SELECT * FROM prep_view')
        if not self._one('SELECT * FROM prep_branches WHERE branch=?',(c['active_branch'],)):
            cut=v['cutoff'] if v else 0
            self.db.execute('INSERT INTO prep_branches VALUES (?,?)',(c['active_branch'],cut))
        if not v:self.db.execute('INSERT INTO prep_view VALUES (?,?,0,0)',(c['id'],c['active_branch']))
        elif v['branch']!=c['active_branch']:self.db.execute('UPDATE prep_view SET branch=?,epoch=epoch+1',(c['active_branch'],))

    def _after_memory_transaction(self):
        super()._after_memory_transaction()
        if not self._prep_ready:return
        self._ensure_branch()
        if self._restoring:
            cp=self._one('SELECT * FROM prep_checkpoints WHERE checkpoint=?',(self._restoring,))
            if not cp:raise WorldError('missing PREP pairing')
            self.db.execute('UPDATE prep_view SET cutoff=?,epoch=epoch+1',(cp['cutoff'],))
            if digest(self.preparation_state())!=cp['state_sha']:raise WorldError('PREP replay pairing mismatch')
            if self._one('SELECT 1 FROM prep_log WHERE branch=? AND seq>?',(self.get_active_branch(),cp['cutoff'])):
                self.db.execute('UPDATE campaigns SET pending_fork=1')
            return
        # New completed canonical battle can satisfy the second prerequisite.
        self._earn_available()

    def _writable(self):
        super()._writable()
        if self._prep_ready:self._ensure_branch()

    def _events(self,branch=None,cursor=None,cutoff=None):
        # Keep SocialStore's own private _events API intact.
        return super()._events(branch,cursor,cutoff)

    def _prep_events(self,branch=None,cursor=None,cutoff=None):
        c=self.campaign();v=self._one('SELECT * FROM prep_view')
        branch=branch or c['active_branch'];cursor=c['cursor'] if cursor is None else cursor;cutoff=v['cutoff'] if cutoff is None else cutoff
        b=self._one('SELECT * FROM branches WHERE id=?',(branch,));bound=self._one('SELECT * FROM prep_branches WHERE branch=?',(branch,))
        prefix=self._prep_events(b['parent'],min(cursor,b['fork_cursor']),min(cutoff,bound['parent_cutoff'])) if b['parent'] else []
        return prefix+[{**dict(r),'payload':json.loads(r['payload'])} for r in self.db.execute('SELECT * FROM prep_log WHERE branch=? AND cursor<=? AND seq<=? ORDER BY seq',(branch,cursor,cutoff))]

    def preparation_state(self):
        s=empty()
        for e in self._prep_events():apply(s,e)
        return s

    def _append_prep(self,kind,key,payload):
        self._ensure_branch();c=self.campaign();identity=digest(['prep1',c['id'],c['active_branch'],kind,key])
        old=self._one('SELECT payload FROM prep_log WHERE id=?',(identity,))
        if old:
            if old['payload']!=dump(payload):raise WorldError('conflicting PREP duplicate')
            return identity
        r=self.db.execute('INSERT INTO prep_log(id,campaign,branch,cursor,kind,semantic_key,payload) VALUES (?,?,?,?,?,?,?)',(identity,c['id'],c['active_branch'],c['cursor'],kind,key,dump(payload)))
        self.db.execute('UPDATE prep_view SET cutoff=?',(r.lastrowid,))
        return identity

    def activate_preparation(self):
        def action():
            current=self.preparation_state()
            if current['activation']:return current['activation']
            self._writable();c=self.campaign()
            activation={'contentSHA256':self.content.hash,'catalogSHA256':self.content.cat.hash,'campaign':c['id'],'version':1}
            self._append_prep('ACTIVATED','activation',activation)
            for actor,t in self.content.pack['trainers'].items():
                companions=[asdict(x) for x in authored_companions(self.content.cat,actor,t['sourceTrainer'])]
                resources={'owner':actor,'stock':[],'categories':t['resources']['categories'],'restock':False,'contentSHA256':self.content.hash,'sourceTrainer':t['sourceTrainer']}
                self._append_prep('INITIALIZED',actor,{'actor':actor,'companions':companions,'resources':resources,'sourceTrainer':t['sourceTrainer'],'retainedOrigins':t['retainedOrigins'],'active':True})
            return activation
        return self._tx(action)

    def _earn_available(self):
        s=self.preparation_state()
        if self.campaign()['status'] not in ('paired','imported'):return
        if not s['activation'] or not s['progression'] or not all(s['progression']['flags'].values()):return
        for actor,t in self.content.pack['trainers'].items():
            if 'forest-post-boulder-1' not in t['stages']:continue
            won=[b for b in self.state()['battles'].values() if b['trainerID']==t['worldTrainerID'] and b['ended'] and b['defeated'] and b['outcome']==1]
            if not won:continue
            oid=self.content.opportunity_id(Scope(self.campaign()['id'],self.get_active_branch(),actor,0,0),'forest-post-boulder-1')
            if oid not in s['opportunities']:
                self._append_prep('EARNED',oid,{'opportunityID':oid,'actor':actor,'stage':'forest-post-boulder-1','worldTrainerID':t['worldTrainerID'],'winEvents':[b['endEvent'] for b in won],'milestoneReceipt':s['progression']['receiptID'],'contentSHA256':self.content.hash})

    def _checkpoint(self,c,save,kind):
        if self._prep_ready and self._native_capture:
            native=self._native_capture
            if native['save']['fingerprint']!=save.fingerprint:raise WorldError('native evidence/checkpoint mismatch')
            self._append_prep('PROGRESSION',save.fingerprint,native)
            self._earn_available()
        cid=super()._checkpoint(c,save,kind)
        if self._prep_ready:
            self._ensure_branch();v=self._one('SELECT * FROM prep_view');sha=digest(self.preparation_state())
            old=self._one('SELECT * FROM prep_checkpoints WHERE checkpoint=?',(cid,))
            if old and (old['cutoff'],old['state_sha'])!=(v['cutoff'],sha):raise WorldError('ambiguous PREP pairing')
            if not old:self.db.execute('INSERT INTO prep_checkpoints VALUES (?,?,?)',(cid,v['cutoff'],sha))
        return cid

    def finish_save_with_progression(self,intent,battery,receipt):
        data=Path(battery).read_bytes();native=read_boulder(data,self.build)
        self._native_capture=native
        from world.saves import fingerprint
        try:
            layout=json.loads((Path(__file__).resolve().parents[1]/'config/prep_save_layout.json').read_text())
            return self.finish_save(intent,fingerprint(data,layout['sectionSizes']),receipt)
        finally:self._native_capture=None

    def trusted_state(self,actor):
        c=self.campaign();v=self._one('SELECT * FROM prep_view');s=self.preparation_state()
        if c['status'] not in ('paired','imported') or self.pending_save():raise WorldError('PREP requires active paired state and no save barrier')
        if not s['activation'] or actor not in s['actors']:raise WorldError('missing durable companion/resource initialization')
        row=s['actors'][actor];companions=[]
        for p in row['companions']:
            companions.append(Companion(**{**p,'moves':tuple(p['moves']),'history':tuple(Step(**x) for x in p['history'])}))
        scope=Scope(c['id'],c['active_branch'],actor,v['epoch'],c['cursor'])
        ctx=Context(scope,tuple(companions),frozenset(),(),(),tuple(tuple(x) for x in row['resources']['stock']),frozenset(),0,0,None,False)
        native=s['progression'];e=None
        if native:
            cp=self.get_save_checkpoint(native['save']['fingerprint'])
            # Only an active branch-prefix checkpoint may witness progression.
            active_ids={x['id'] for x in self._prep_events()}
            if cp and native['receiptID'] in active_ids:
                e=ProgressionEvidence(scope,self.build,native['sourceCommit'],tuple(native['flags'].items()),(native['receiptID'],),cp['id'],digest(s['activation']))
        wins=frozenset(t['actorID'] for t in self.content.data['trainers'] if any(b['trainerID']==t['worldTrainerID'] and b['ended'] and b['defeated'] and b['outcome']==1 for b in self.state()['battles'].values()))
        return TrustedState(ctx,e,wins,frozenset(k for k,o in s['opportunities'].items() if o['status'] in ('committed','consumed')),True)

    def get_preparation_opportunity(self,actor,stage='forest-post-boulder-1'):
        s=self.preparation_state();oid=self.content.opportunity_id(Scope(self.campaign()['id'],self.get_active_branch(),actor,0,0),stage)
        if stage=='first':
            r=self.content.resolve(self.trusted_state(actor),stage)
            return {'opportunityID':oid,'actor':actor,'stage':stage,'status':'available','kind':'first-encounter','earnedAllowance':0} if r['status']=='permitted' else None
        return s['opportunities'].get(oid)

    def get_trainer_companion_state(self,actor):return self.preparation_state()['actors'].get(actor,{}).get('companions')
    def get_trainer_resource_state(self,actor):return self.preparation_state()['actors'].get(actor,{}).get('resources')

    def reserve_resources(self,oid,costs,request_id):
        """No candidate chosen. Abstract exclusive reservation for later workflows."""
        if not isinstance(request_id,str) or not 1<=len(request_id)<=128:raise WorldError('bounded reservation request ID required')
        for item,n in costs:
            if type(item)!=int or item<=0:raise WorldError('invalid reservation item')
            self.content.cat.lookup('items',item)
        def action():
            s=self.preparation_state();previous=s['reservations'].get(oid)
            if previous and previous['requestID']==request_id:
                if previous['costs']!=[list(x) for x in costs]:raise WorldError('conflicting reservation retry')
                return previous
            if any(e['kind']=='RELEASED' and e['payload']['requestID']==request_id for e in self._prep_events()):raise WorldError('released reservation request cannot be reused')
            self._writable();s=self.preparation_state();o=s['opportunities'].get(oid)
            if not o or o['status']!='available':raise WorldError('opportunity not available')
            stock=dict(s['actors'][o['actor']]['resources']['stock']);used={}
            for r in s['reservations'].values():
                if r['actor']==o['actor']:
                    for item,n in r['costs']:used[item]=used.get(item,0)+n
            if len(dict(costs))!=len(costs) or any(type(n)!=int or n<=0 or stock.get(item,0)-used.get(item,0)<n for item,n in costs):raise WorldError('finite reservation deficit')
            p={'opportunityID':oid,'actor':o['actor'],'requestID':request_id,'costs':[list(x) for x in costs]}
            self._append_prep('RESERVED',request_id,p);return p
        return self._tx(action)

    def release_reservation(self,oid,request_id):
        """Explicit cancellation without resource expenditure or team selection."""
        def action():
            s=self.preparation_state();r=s['reservations'].get(oid)
            if not r: return False
            if r['requestID']!=request_id:raise WorldError('wrong reservation owner')
            self._writable();self._append_prep('RELEASED',request_id,{'opportunityID':oid,'requestID':request_id})
            return True
        return self._tx(action)
