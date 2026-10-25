"""Versioned host-only pre-battle descendants; never a native paired save.

An explicit continuation launch preserves a *current* sealed descendant.
Ordinary restore still abandons it. Receipts are referenced, never copied.
"""
import json
import time
from pathlib import Path
from world.store import WorldError, dump, uid
from roster.hashes import digest

METHODS = ('verify_replay', 'verify_memory_replay', 'verify_social_replay',
           'verify_puppeteer_replay', 'verify_strategy_replay',
           'verify_decision_replay', 'verify_virality_replay')

def require(ok, code):
    if not ok:
        raise WorldError(code)

class ContinuationMixin:
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self._one("SELECT name FROM sqlite_master WHERE name='prebattle_version'"):
            if [tuple(r) for r in self.db.execute('SELECT * FROM prebattle_version')]!=[(1,)]:
                self.close()
                raise WorldError('UNSUPPORTED_CONTINUATION_VERSION')

    def _continuation_schema(self):
        if self._one("SELECT name FROM sqlite_master WHERE name='prebattle_version'"):
            require([tuple(r) for r in self.db.execute('SELECT * FROM prebattle_version')] == [(1,)],
                    'UNSUPPORTED_CONTINUATION_VERSION')
            self.db.execute('CREATE TABLE IF NOT EXISTS prebattle_session_closures(origin TEXT PRIMARY KEY, witness TEXT NOT NULL)')
            self._continuation_immutability()
            return
        self.db.execute('CREATE TABLE prebattle_version(version INTEGER NOT NULL)')
        self.db.execute('INSERT INTO prebattle_version VALUES(1)')
        self.db.execute('CREATE TABLE prebattle_continuations(id TEXT PRIMARY KEY, descriptor TEXT NOT NULL, status TEXT NOT NULL)')
        self.db.execute('CREATE TABLE prebattle_sessions(origin TEXT PRIMARY KEY, continuation TEXT NOT NULL, nonce INTEGER UNIQUE NOT NULL, created REAL NOT NULL)')
        self.db.execute('CREATE TABLE prebattle_session_closures(origin TEXT PRIMARY KEY, witness TEXT NOT NULL)')
        self.db.execute("CREATE TRIGGER immutable_prebattle_descriptor BEFORE UPDATE OF descriptor,id ON prebattle_continuations BEGIN SELECT RAISE(ABORT,'immutable continuation'); END")
        self.db.execute("CREATE TRIGGER immutable_prebattle_delete BEFORE DELETE ON prebattle_continuations BEGIN SELECT RAISE(ABORT,'immutable continuation'); END")
        self._continuation_immutability()

    def _continuation_immutability(self):
        for table in ('prebattle_sessions','prebattle_session_closures'):
            for op in ('UPDATE','DELETE'):
                self.db.execute('CREATE TRIGGER IF NOT EXISTS immutable_'+table+'_'+op+
                    ' BEFORE '+op+' ON '+table+" BEGIN SELECT RAISE(ABORT,'append-only continuation session'); END")

    def continuation_catalog(self):
        """Checkpoint API distinguishes paired snapshots from derived journals."""
        pairs = [{'id':r['id'], 'kind':'paired_gameplay', 'checkpointKind':r['kind']}
                 for r in self.db.execute('SELECT * FROM checkpoints')]
        if not self._one("SELECT name FROM sqlite_master WHERE name='prebattle_version'"):
            return pairs
        self._continuation_schema()
        return pairs + [{'id':r['id'], 'kind':'prebattle_continuation', 'status':r['status']}
                        for r in self.db.execute('SELECT * FROM prebattle_continuations')]

    def _continuation_material(self, parent, actor, native_trainer, opportunity, save, proof):
        c = self.campaign()
        require(parent and parent['kind'] == 'normal_save', 'INVALID_CONTINUATION_PARENT')
        require((c['id'], c['active_branch'], c['cursor'], c['pending_fork'], c['status']) ==
                (parent['campaign'], parent['branch'], parent['cursor'], 0, 'paired'),
                'INVALID_CONTINUATION_LINEAGE')
        require(save.as_dict() == json.loads(parent['save_identity']), 'NATIVE_STATE_MISMATCH')
        require(not self.pending_save(), 'CONTINUATION_SAVE_BARRIER')
        # This v1 boundary is deliberately narrow: a managed menu before Continue,
        # with no emitted gameplay. Field equivalence needs a separate witness.
        require(proof.get('kind') == 'managed-menu-no-gameplay-v1' and
                proof.get('save') == save.as_dict() and proof.get('reviewedNoGameplay') is True,
                'NATIVE_EQUIVALENCE_UNPROVED')
        n = proof.get('native', {})
        require(n.get('authenticated') is True and n.get('run') == 1 and
                all(n.get(k) == 0 for k in ('eventCounter','ack','drops','depth')),
                'NATIVE_EVENT_GAP')
        launch = self._one('SELECT * FROM launches WHERE id=? AND nonce=?', (n.get('origin'), n.get('nonce')))
        require(launch and launch['campaign'] == c['id'] and
                launch['loaded_fingerprint'] == save.fingerprint,
                'NATIVE_SESSION_MISMATCH')
        require(n.get('build') == getattr(self, 'native_manifest', {}).get('rom_sha256'),
                'NATIVE_BUILD_MISMATCH')
        stream = self._one('SELECT last FROM streams WHERE nonce=? AND run=1', (n['nonce'],))
        require(not stream or stream['last'] == 0, 'NATIVE_EVENT_GAP')
        require(proof.get('evidence'), 'NATIVE_EQUIVALENCE_UNPROVED')
        from hashlib import sha256
        for artifact in proof['evidence']:
            require(sha256(Path(artifact['path']).read_bytes()).hexdigest() == artifact['sha256'],
                    'NATIVE_EVIDENCE_MISMATCH')
        # No social/canonical/native progress may be spliced across this boundary.
        require(self.verify_replay() == parent['state_sha256'], 'CANONICAL_CUTOFF_MISMATCH')
        for domain in ('memory','social','puppeteer','virality'):
            view = self._one('SELECT * FROM '+domain+'_view')
            paired = self._one('SELECT * FROM '+domain+'_checkpoints WHERE checkpoint=?', (parent['id'],))
            require(view and paired and view['cutoff'] == paired['cutoff'], 'NON_PREBATTLE_DESCENDANT')
        require(not any(not b['ended'] for b in self.state()['battles'].values()), 'ENCOUNTER_ALREADY_STARTED')
        require('trainer:' + self.registry['mapping'].get(str(native_trainer), '') == actor,
                'ACTOR_NATIVE_MISMATCH')
        lock = self.locked_preparation(actor)
        require(lock and lock['locked'], 'COMMITMENT_INCOMPLETE')
        require(lock['opportunityID'] == opportunity, 'OPPORTUNITY_ID_MISMATCH')
        require(not self.decision_state()['installations'].get(lock['encounterID']), 'ENCOUNTER_ALREADY_CONSUMED')
        memo = next((m for m in self.memo_records() if m['strategyID'] == lock['strategyID']), None)
        require(memo and memo['actor'] == actor and memo['scope']['opportunityID'] == opportunity,
                'COMMITMENT_INCOMPLETE')
        require(lock['memoSHA256'] == digest(memo['strategyText']) and lock['strategyText'] == memo['strategyText'],
                'STRATEGY_COMMITMENT_MISMATCH')
        for scope in (memo['scope'], lock['scope']):
            require((scope['campaign'], scope['branch'], scope['cutoff']) ==
                    (c['id'], c['active_branch'], c['cursor']), 'ABANDONED_GENERATION')
        packet = json.loads(self._one('SELECT context FROM strategy_jobs WHERE id=?', (memo['jobID'],))['context'])
        require(packet['contextID'] == memo['contextID'] and
                packet['materialContextSHA256'] == memo['materialContextSHA256'], 'STRATEGY_CONTEXT_MISMATCH')
        # Persistent lineage may originate in an earlier source definition.
        # A typed encounter binding must still distinguish this opportunity
        # from other battles using the same persistent actor.
        bound=packet['modelInput'].get('encounter',{}).get('nativeTrainerID')
        if bound is not None:
            require(bound==native_trainer,'NATIVE_ENCOUNTER_MISMATCH')
            require(all('trainer:'+self.registry['mapping'].get(str(p['origin']).split(':')[0],'')==actor
                        for p in lock['candidate']['party']),'COMPANION_LINEAGE_MISMATCH')
        else:
            require(all(str(p['origin']).split(':')[0]==str(native_trainer) for p in lock['candidate']['party']),
                    'NATIVE_ENCOUNTER_MISMATCH')
        for table in ('strategy_jobs','preparation_decision_jobs','puppeteer_jobs'):
            require(not self._one('SELECT 1 FROM '+table+" WHERE status='active'"), 'PENDING_MODEL_WORK')
        require(all(o['status']=='PUBLISHED' for o in self.puppeteer_state()['obligations'].values()),
                'PENDING_RECAP_WORK')
        tails = {}
        for domain,events in (('strategy',self._strategy_events()),('prep',self._prep_events()),
                              ('preparation_decision',self._decision_events())):
            cutoff=self._one('SELECT cutoff FROM '+domain+'_checkpoints WHERE checkpoint=?',(parent['id'],))['cutoff']
            tail=[e for e in events if e['seq']>cutoff]
            require(all(e['branch']==c['active_branch'] and e['cursor']==c['cursor'] for e in tail),
                    'INVALID_CONTINUATION_LINEAGE')
            tails[domain]=tail
        require([e['kind'] for e in tails['preparation_decision']]==['DECISION','COMMITMENT'] and
                tails['preparation_decision'][1]['payload']==lock and
                tails['preparation_decision'][0]['payload']['decisionID']==lock['decisionID'],
                'SUPERSEDED_OR_CONSUMED_PREPARATION')
        for event in tails['strategy']:
            p=event['payload']
            require(event['kind'] in ('OPPORTUNITY','GRANT','MEMO') and p.get('jobID')==memo['jobID'],
                    'NON_PREBATTLE_DESCENDANT')
            if event['kind']=='MEMO':require(p==memo,'STRATEGY_COMMITMENT_MISMATCH')
        for event in tails['prep']:
            p=event['payload']
            require(event['kind'] in ('CONTENT_ADOPTED','INITIALIZED') and
                    (event['kind']=='CONTENT_ADOPTED' or (p['actor']==actor and p['sourceTrainer']==native_trainer)),
                    'NON_PREBATTLE_DESCENDANT')
        return {'schemaVersion':1, 'parent':parent, 'campaign':c['id'], 'branch':c['active_branch'],
                'cursor':c['cursor'], 'actor':actor, 'nativeTrainer':native_trainer,
                'opportunityID':opportunity, 'encounterID':lock['encounterID'],
                'memo':memo, 'lock':lock, 'contextSHA256':digest(packet),
                'nativeProof':proof,
                'receiptTails':tails,
                'viewBindings':{domain:dict(self._one('SELECT * FROM '+domain+'_view'))
                    for domain in ('memory','social','puppeteer','strategy','prep','preparation_decision','virality')},
                'contentSHA256':self.content.hash, 'build':self.build}

    def create_prebattle_continuation(self, parent_id, actor, native_trainer, opportunity, save, native_proof):
        def action():
            self._continuation_schema()
            parent = self._one('SELECT * FROM checkpoints WHERE id=?', (parent_id,))
            material = self._continuation_material(dict(parent) if parent else None,
                         actor, native_trainer, opportunity, save, native_proof)
            identity = 'prebattle:' + digest(material)
            old = self._one('SELECT * FROM prebattle_continuations WHERE id=?', (identity,))
            if old:
                require(old['status'] == 'valid', 'ABANDONED_CONTINUATION')
                return identity
            # One active authorization per campaign; no implicit supersession.
            require(not self._one("SELECT 1 FROM prebattle_continuations WHERE status='valid'"),
                    'CONTRADICTORY_CONTINUATION')
            self.db.execute('INSERT INTO prebattle_continuations VALUES(?,?,?)', (identity,dump(material),'valid'))
            return identity
        return self._tx(action)

    def authorize_continuation_launch(self, identity, nonce, save, actor, native_trainer, opportunity):
        # Reject unrelated/invalid branches before derived-store transaction
        # hooks attempt to follow their history. Recheck under the writer lock.
        if self._one("SELECT name FROM sqlite_master WHERE name='prebattle_continuations'"):
            row=self._one('SELECT descriptor FROM prebattle_continuations WHERE id=?',(identity,))
            if row:
                d=json.loads(row['descriptor']);c=self.campaign()
                require((c['id'],c['active_branch'],c['cursor'],c['pending_fork']) ==
                        (d['campaign'],d['branch'],d['cursor'],0), 'INVALID_CONTINUATION_LINEAGE')
        def action():
            self._continuation_schema()
            row = self._one('SELECT * FROM prebattle_continuations WHERE id=?', (identity,))
            require(row is not None, 'UNKNOWN_CONTINUATION')
            require(row['status'] == 'valid', 'ABANDONED_CONTINUATION')
            d = json.loads(row['descriptor'])
            require(d['schemaVersion'] == 1 and identity == 'prebattle:'+digest(d), 'CONTINUATION_INTEGRITY')
            require((actor,native_trainer,opportunity) == (d['actor'],d['nativeTrainer'],d['opportunityID']),
                    'OPPORTUNITY_ID_MISMATCH')
            actual = self._continuation_material(d['parent'],actor,native_trainer,opportunity,save,d['nativeProof'])
            require(actual == d, 'CONTINUATION_STATE_CHANGED')
            require(not self._one('SELECT 1 FROM prebattle_sessions s LEFT JOIN prebattle_session_closures c ON c.origin=s.origin WHERE s.continuation=? AND c.origin IS NULL',(identity,)),
                    'PRIOR_NATIVE_SESSION_UNSETTLED')
            require(type(nonce) is int and 0 < nonce <= 0xffffffff and
                    not self._one('SELECT 1 FROM launches WHERE nonce=?',(nonce,)), 'NATIVE_SESSION_REUSE')
            origin = uid()
            self.db.execute("UPDATE launches SET status='inactive' WHERE campaign=?",(d['campaign'],))
            self.db.execute('INSERT INTO launches VALUES(?,?,?,?,?)', (origin,nonce,d['campaign'],save.fingerprint,'active'))
            self.db.execute('INSERT INTO prebattle_sessions VALUES(?,?,?,?)',(origin,identity,nonce,time.time()))
            return origin
        return self._tx(action)

    def continuation_encounter(self, identity, save, actor, native_trainer, opportunity):
        """Retrieve the resolved frozen opportunity, without rebuilding PREP.

        recorded_strategy() plans uncommitted opportunities and intentionally
        cannot rebuild an already spent one. This read uses the sealed records.
        """
        self._continuation_schema()
        row=self._one('SELECT * FROM prebattle_continuations WHERE id=?',(identity,))
        require(row and row['status']=='valid','ABANDONED_CONTINUATION')
        d=json.loads(row['descriptor'])
        require(identity=='prebattle:'+digest(d),'CONTINUATION_INTEGRITY')
        require((actor,native_trainer,opportunity)==(d['actor'],d['nativeTrainer'],d['opportunityID']),
                'OPPORTUNITY_ID_MISMATCH')
        require(self._continuation_material(d['parent'],actor,native_trainer,opportunity,save,d['nativeProof'])==d,
                'CONTINUATION_STATE_CHANGED')
        return {'status':'committed','memo':d['memo'],'preparation':d['lock'],
                'opportunityID':opportunity,'encounterID':d['encounterID']}

    def settle_continuation_session(self, origin, save, native):
        """Trusted managed shutdown receipt, after native is frozen/stopped.

        A crash without this receipt stays blocked; absence of canonical events
        alone does not prove an unobserved native encounter never started.
        """
        def action():
            self._continuation_schema()
            session=self._one('SELECT * FROM prebattle_sessions WHERE origin=?',(origin,))
            require(session is not None,'UNKNOWN_CONTINUATION_SESSION')
            row=self._one('SELECT * FROM prebattle_continuations WHERE id=?',(session['continuation'],))
            require(row and row['status']=='valid','ENCOUNTER_ALREADY_CONSUMED')
            d=json.loads(row['descriptor'])
            require(self._continuation_material(d['parent'],d['actor'],d['nativeTrainer'],d['opportunityID'],save,d['nativeProof'])==d,
                    'CONTINUATION_STATE_CHANGED')
            require((native.get('origin'),native.get('nonce'),native.get('run'),native.get('build')) ==
                    (origin,session['nonce'],1,d['nativeProof']['native']['build']) and native.get('authenticated') and
                    all(native.get(k)==0 for k in ('eventCounter','ack','depth','drops')),
                    'NATIVE_SESSION_UNSETTLED')
            old=self._one('SELECT * FROM prebattle_session_closures WHERE origin=?',(origin,))
            if old:
                require(old['witness']==dump(native),'CONFLICTING_NATIVE_CLOSURE')
            else:self.db.execute('INSERT INTO prebattle_session_closures VALUES(?,?)',(origin,dump(native)))
        return self._tx(action)
