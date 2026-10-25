"""Mandatory recaps and durable scoped episodes over WORLD/MEMORY/SOCIAL.

No vendor dependency. Inference receives job-bound methods, never this store.
"""
import copy,json,re,time
from pathlib import Path
from social.store import SocialStore
from memory.store import actor_id,digest
from world.store import ROOT,WorldError,dump,uid
from .recap_contract import RECAP_VERSION, build_submission


def empty():
    return {'version':1,'activation':None,'obligations':{},'episodes':{},'links':{}}


def apply(state,e):
    p=e['payload'];k=e['kind']
    if k=='ACTIVATED':state['activation']=p
    elif k=='RECAP_REQUIRED':state['obligations'][e['id']]={'obligationID':e['id'],**p,'status':'RECAP_REQUIRED'}
    elif k=='GENERATING':state['obligations'][p['obligationID']].update(status='GENERATING',jobID=p['jobID'])
    elif k=='PUBLISHED':state['obligations'][p['obligationID']].update(status='PUBLISHED',outcome=p)
    elif k=='EPISODE':state['episodes'][e['id']]={'episodeID':e['id'],**p}
    elif k=='SOCIAL_LINK':state['links'][e['id']]=p
    else:raise WorldError('unsupported puppeteer log event')
    return state


class PuppeteerStore(SocialStore):
    _supports_puppeteer=True

    def __init__(self,*args,**kwargs):
        self._pp_ready=False
        super().__init__(*args,**kwargs)
        self.pp_config=json.loads((ROOT/'config/hermes_policy.json').read_text())
        self.personas=json.loads((ROOT/'config/trainer_personas.json').read_text())
        self.pp_config_hash=digest([self.pp_config,self.personas])
        try:
            if self._one("SELECT name FROM sqlite_master WHERE name='puppeteer_version'"):
                if [tuple(r) for r in self.db.execute('SELECT * FROM puppeteer_version')]!=[(1,1,self.pp_config_hash)]:raise WorldError('incompatible puppeteer schema/config')
            else:
                self.db.executescript('BEGIN IMMEDIATE;'+(Path(__file__).parent/'migrations/001.sql').read_text())
                try:
                    self.db.execute('INSERT INTO puppeteer_version VALUES (1,1,?)',(self.pp_config_hash,))
                    for table in ('puppeteer_log','puppeteer_branches','puppeteer_checkpoints','puppeteer_audit'):
                        for op in ('UPDATE','DELETE'):
                            self.db.execute(f"CREATE TRIGGER immutable_{table}_{op} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'append-only puppeteer'); END")
                    for b in self.db.execute('SELECT id FROM branches').fetchall():self.db.execute('INSERT INTO puppeteer_branches VALUES (?,0)',(b['id'],))
                    for cp in self.db.execute('SELECT id FROM checkpoints').fetchall():self.db.execute('INSERT INTO puppeteer_checkpoints VALUES (?,0,?)',(cp['id'],digest(empty())))
                    c=self._one('SELECT * FROM campaigns')
                    if c:self.db.execute('INSERT INTO puppeteer_view VALUES (?,?,0,0)',(c['id'],c['active_branch']))
                    self.db.execute('COMMIT')
                except Exception:self.db.execute('ROLLBACK');raise
            self._pp_ready=True
        except Exception:self.close();raise

    def _tx(self,fn):
        if not self._pp_ready:return super()._tx(fn)
        def action():
            self._pp_before=self._one('SELECT * FROM puppeteer_view')
            return fn()
        return super()._tx(action)

    def _on_completed_battles(self):
        # The optional SOCIAL1 processor never races the mandatory processor.
        return

    def _after_memory_transaction(self):
        super()._after_memory_transaction()
        if not self._pp_ready:return
        c=self.campaign();before=self._pp_before
        if not self._one('SELECT * FROM puppeteer_branches WHERE branch=?',(c['active_branch'],)):
            self.db.execute('INSERT INTO puppeteer_branches VALUES (?,?)',(c['active_branch'],before['cutoff'] if before else 0))
        v=self._one('SELECT * FROM puppeteer_view')
        if not v:self.db.execute('INSERT INTO puppeteer_view VALUES (?,?,0,0)',(c['id'],c['active_branch']))
        elif self._restoring:
            cp=self._one('SELECT * FROM puppeteer_checkpoints WHERE checkpoint=?',(self._restoring,))
            if not cp:raise WorldError('missing puppeteer checkpoint')
            self.db.execute('UPDATE puppeteer_view SET branch=?,cutoff=?,epoch=epoch+1 WHERE campaign=?',(c['active_branch'],cp['cutoff'],c['id']))
            if digest(self.puppeteer_state())!=cp['state_sha']:raise WorldError('puppeteer checkpoint replay mismatch')
            self.db.execute("UPDATE puppeteer_jobs SET status='revoked' WHERE status='active'")
            if self._one('SELECT 1 FROM puppeteer_log WHERE branch=? AND seq>?',(c['active_branch'],cp['cutoff'])):self.db.execute('UPDATE campaigns SET pending_fork=1 WHERE id=?',(c['id'],))
            return
        elif v['branch']!=c['active_branch']:
            self.db.execute('UPDATE puppeteer_view SET branch=?,epoch=epoch+1 WHERE campaign=?',(c['active_branch'],c['id']))
            self.db.execute("UPDATE puppeteer_jobs SET status='revoked' WHERE status='active'")
        self._queue_completed();self._sync_links()

    def _checkpoint(self,c,save,kind):
        cid=super()._checkpoint(c,save,kind)
        if not self._pp_ready:return cid
        v=self._one('SELECT * FROM puppeteer_view');cut=v['cutoff'] if v else 0;sha=digest(self.puppeteer_state()) if v else digest(empty())
        old=self._one('SELECT * FROM puppeteer_checkpoints WHERE checkpoint=?',(cid,))
        if old and (old['cutoff'],old['state_sha'])!=(cut,sha):raise WorldError('ambiguous puppeteer save pairing')
        if not old:self.db.execute('INSERT INTO puppeteer_checkpoints VALUES (?,?,?)',(cid,cut,sha))
        return cid

    def _writable(self):
        v=self._one('SELECT * FROM puppeteer_view') if self._pp_ready else None
        super()._writable()
        if v and v['branch']!=self.get_active_branch():
            b=self.get_active_branch()
            self.db.execute('INSERT INTO puppeteer_branches VALUES (?,?)',(b,v['cutoff']))
            self.db.execute('UPDATE puppeteer_view SET branch=?,epoch=epoch+1',(b,))
            self.db.execute("UPDATE puppeteer_jobs SET status='revoked' WHERE status='active'")

    def _pp_events(self,branch=None,cursor=None,cutoff=None):
        c=self.campaign();v=self._one('SELECT * FROM puppeteer_view')
        branch=branch or c['active_branch'];cursor=c['cursor'] if cursor is None else cursor;cutoff=v['cutoff'] if cutoff is None else cutoff
        b=self._one('SELECT * FROM branches WHERE id=?',(branch,));bound=self._one('SELECT * FROM puppeteer_branches WHERE branch=?',(branch,))
        prefix=self._pp_events(b['parent'],min(cursor,b['fork_cursor']),min(cutoff,bound['parent_cutoff'])) if b['parent'] else []
        return prefix+[{**dict(r),'payload':json.loads(r['payload'])} for r in self.db.execute('SELECT * FROM puppeteer_log WHERE campaign=? AND branch=? AND cursor<=? AND seq<=? ORDER BY seq',(c['id'],branch,cursor,cutoff))]

    def puppeteer_state(self):
        s=empty()
        for e in self._pp_events():apply(s,e)
        return s

    def _pp_append(self,kind,key,payload):
        c=self.campaign();identity=digest(['puppeteer1',c['id'],c['active_branch'],kind,key])
        old=self._one('SELECT payload FROM puppeteer_log WHERE id=?',(identity,))
        if old:
            if old['payload']!=dump(payload):raise WorldError('conflicting puppeteer duplicate')
            return identity
        r=self.db.execute('INSERT INTO puppeteer_log(id,campaign,branch,cursor,kind,semantic_key,payload) VALUES (?,?,?,?,?,?,?)',(identity,c['id'],c['active_branch'],c['cursor'],kind,key,dump(payload)))
        self.db.execute('UPDATE puppeteer_view SET branch=?,cutoff=? WHERE campaign=?',(c['active_branch'],r.lastrowid,c['id']))
        return identity

    def activate_puppeteer(self):
        def action():
            s=self.puppeteer_state()
            if s['activation']:return s['activation']
            self._writable()
            if not self.social_state()['activation']:
                p={'worldCursor':self.campaign()['cursor'],'configVersion':1,'configSHA256':self.config_hash,'policyVersion':1,'playerActor':self.player_actor()}
                self._append('ACTIVATED','activation',p)
                for edge in self.config['seedFollows']:self._append('FOLLOW',edge['follower']+'>'+edge['followed'],edge)
            p={'worldCursor':self.campaign()['cursor'],'configSHA256':self.pp_config_hash,'promptVersion':1,'schemaVersion':1,'noHistoricalBackfill':True}
            self._pp_append('ACTIVATED','activation',p);return p
        return self._tx(action)

    def _queue_completed(self):
        s=self.puppeteer_state()
        if not s['activation']:return
        existing={o['battleID'] for o in s['obligations'].values()}
        events={e['eventID']:e for e in self.get_canonical_events()}
        for b in self.state()['battles'].values():
            if not b['trainerID'] or not b['ended'] or b['battleID'] in existing:continue
            end=events[b['endEvent']]
            if end['cursor']<=s['activation']['worldCursor']:continue
            if b['outcome'] not in self.pp_config['mandatoryOutcomeValues']:
                if not self._one("SELECT 1 FROM puppeteer_audit WHERE job=? AND event='unsupported-completed-outcome'",(b['battleID'],)):
                    self.audit(b['battleID'],'unsupported-completed-outcome',{'battleID':b['battleID'],'nativeOutcome':b['outcome'],'reason':'not a supported trainer win/loss/draw; no fabricated result'})
                continue
            actor=actor_id(b['trainerID']);self.get_actor(actor)
            if b['defeated'] and self._follow_eligible(actor):
                edge=actor+'>'+self.player_actor()
                if edge not in self.social_state()['follows']:self._append('FOLLOW',edge,{'follower':actor,'followed':self.player_actor(),'cause':'first_confirmed_eligible_win','battleID':b['battleID'],'endEventID':b['endEvent']})
            self._pp_append('RECAP_REQUIRED',b['battleID']+'>'+actor,{'actorID':actor,'battleID':b['battleID'],'endEventID':b['endEvent'],'endCursor':end['cursor'],'outcome':b['outcome'],'schemaVersion':1})

    def _recap_qualifies(self,actor,battle,state):
        return bool(battle and battle['ended'] and battle['trainerID']==actor.removeprefix('trainer:') and battle['outcome'] in (1,2,3) and any(o['battleID']==battle['battleID'] and o['actorID']==actor for o in self.puppeteer_state()['obligations'].values()))

    def _commit(self,actor,proposal):
        if not getattr(self,'_recap_committing',False):raise WorldError('mandatory recap must use validated obligation processor')
        if proposal['visibility']!='public':raise WorldError('mandatory recap must be public')
        opportunity=self._opportunity(actor,proposal['battleID'])
        records={r['memoryID']:r for r in opportunity['evidence']}
        if not any(i in records and records[i]['claim']['type']=='TRAINER_BATTLE_RESULT' for i in proposal['evidenceIDs']):raise WorldError('mandatory confirmed result omitted')
        return super()._commit(actor,proposal)

    def _cutoffs(self):
        c=self.campaign();m=self._one('SELECT cutoff FROM memory_view');s=self._one('SELECT cutoff,epoch FROM social_view');p=self._one('SELECT cutoff,epoch FROM puppeteer_view')
        return {'campaignID':c['id'],'branchID':c['active_branch'],'worldCursor':c['cursor'],'memoryCutoff':m['cutoff'],'socialCutoff':s['cutoff'],'puppeteerCutoff':p['cutoff'],'socialEpoch':s['epoch'],'puppeteerEpoch':p['epoch']}

    def begin_job(self,obligation_id,mode='offline',deadline=None):
        if mode not in ('offline','mock','shadow','enabled-test'):raise WorldError('unknown processing mode')
        def action():
            self._writable();state=self.puppeteer_state();o=state['obligations'].get(obligation_id)
            if not o or o['status']=='PUBLISHED':raise WorldError('no pending recap obligation')
            if self._one("SELECT 1 FROM puppeteer_jobs WHERE status='active'"):raise WorldError('one active puppeteer job at a time')
            job=uid();expires=time.time()+(deadline or self.pp_config['jobDeadlineSeconds'])
            self._pp_append('GENERATING',obligation_id+'>'+job,{'obligationID':obligation_id,'jobID':job,'mode':mode})
            scope={**self._cutoffs(),'jobID':job,'obligationID':obligation_id,'actorID':o['actorID'],'battleID':o['battleID'],'mode':mode}
            self.db.execute('INSERT INTO puppeteer_jobs VALUES (?,?,?,?,?,?,?,?,NULL,NULL)',(job,scope['campaignID'],scope['branchID'],obligation_id,o['actorID'],dump(scope),expires,'active'))
            return {'jobID':job,'scope':scope,'expires':expires}
        return self._tx(action)

    def begin_recall_job(self,actor,deadline=None):
        """Trusted read-only inspection grant; no second publication obligation."""
        def action():
            self._writable();self.get_actor(actor)
            if self._one("SELECT 1 FROM puppeteer_jobs WHERE status='active'"):raise WorldError('one active puppeteer job at a time')
            episodes=[p for p in self.puppeteer_state()['episodes'].values() if p['actorID']==actor]
            if not episodes:raise WorldError('no actor-owned retained episode to inspect')
            job=uid();scope={**self._cutoffs(),'jobID':job,'obligationID':'','actorID':actor,'battleID':episodes[-1]['battleID'],'mode':'recall'}
            expires=time.time()+(deadline or self.pp_config['jobDeadlineSeconds'])
            self.db.execute('INSERT INTO puppeteer_jobs VALUES (?,?,?,?,?,?,?,?,NULL,NULL)',(job,scope['campaignID'],scope['branchID'],'',actor,dump(scope),expires,'active'))
            return {'jobID':job,'scope':scope,'expires':expires}
        return self._tx(action)

    def finish_recall_job(self,job):
        def action():
            _,scope=self._job(job)
            if scope['mode']!='recall':raise WorldError('not a read-only recall grant')
            outcome={'producer':'hermes_memory_retrieval','jobID':job,'actorID':scope['actorID'],'mutatesGameplay':False,'inputScopeSHA256':digest(scope)}
            self.db.execute("UPDATE puppeteer_jobs SET status='completed',outcome=? WHERE id=?",(dump(outcome),job))
            self.audit(job,'read-only-memory-retrieval',outcome);return outcome
        return self._tx(action)

    def _job(self,job_id,allow_expired=False):
        r=self._one('SELECT * FROM puppeteer_jobs WHERE id=?',(job_id,))
        if not r or r['status']!='active':raise WorldError('revoked or settled puppeteer job')
        scope=json.loads(r['scope']);now=self._cutoffs();c=self.campaign()
        if self.pending_save() or c['status'] not in ('paired','imported') or c['pending_fork']:raise WorldError('job requires settled compatible world/no save barrier')
        if any(scope[k]!=now[k] for k in ('campaignID','branchID','socialEpoch','puppeteerEpoch')) or any(scope[k]>now[k] for k in ('worldCursor','memoryCutoff','socialCutoff','puppeteerCutoff')):raise WorldError('stale job timeline/cutoff')
        if not allow_expired and time.time()>r['expires']:raise WorldError('puppeteer job deadline expired')
        return dict(r),scope

    def _battle_evidence(self,scope):
        actor=scope['actorID'];battle=scope['battleID'];refs={}
        for r in self._rows(actor,scope['campaignID'],scope['branchID'],scope['worldCursor'],scope['memoryCutoff'],limit=4097):
            if len(refs)>=64:break
            if r['mode']=='direct' and r['battle']==battle:
                claim=json.loads(r['claim']);key=dump(claim)
                refs.setdefault(key,{'evidenceID':r['id'],'claim':claim,'sourceKind':'actor_direct_memory'})
        # Only this participant's actually announced own moves. No raw event/RAM
        # dump, unannounced slots, HP, known moves/PP or private opponent party.
        for e in self.get_canonical_events(scope['branchID'],scope['worldCursor']):
            r=e['record'];p=r['payload']
            if e['battleID']==battle and r['eventType']=='BATTLE_ACTION_RESOLVED' and p['actorSide']==1 and p['resolutionKind']=='announced_move':
                claim={'type':'OWN_MOVE_ANNOUNCED','battleID':battle,'trainerID':actor.removeprefix('trainer:'),'speciesID':p['visibleActorSpeciesID'],'moveID':p['announcedMoveID']}
                refs.setdefault(dump(claim),{'evidenceID':e['eventID'],'claim':claim,'sourceKind':'participant_own_announced_action'})
        records=list(refs.values())[:64]
        return {'schemaVersion':1,'actorID':actor,'battleID':battle,'obligationID':scope['obligationID'],'evidence':records,'disclosureAllowlist':self.pp_config['publicDisclosure'],'minimumPublicClaim':'TRAINER_BATTLE_RESULT'}

    def persona(self,actor):
        self.get_actor(actor)
        return copy.deepcopy(self.personas['actors'].get(actor,self.personas['default']))

    def _recall(self,scope):
        state=empty()
        for e in self._pp_events(scope['branchID'],scope['worldCursor'],scope['puppeteerCutoff']):apply(state,e)
        records=[p for p in state['episodes'].values() if p['actorID']==scope['actorID']]
        return {'schemaVersion':1,'scope':'actor_owned_puppeteer_episodes','episodes':records[-self.pp_config['maxRecallEpisodes']:],'truncated':len(records)>self.pp_config['maxRecallEpisodes']}

    def job_tools(self,job_id):
        self._job(job_id)
        return JobTools(self,job_id)

    def fallback_result(self,job_id):
        _,scope=self._job(job_id,allow_expired=True);packet=self._battle_evidence(scope);records=packet['evidence']
        outcome=[r for r in records if r['claim']['type']=='TRAINER_BATTLE_RESULT']
        if len(outcome)!=1:raise WorldError('unrecoverable completed-battle evidence gap; no fabricated recap')
        seen=[r for r in records if r['claim']['type']=='POKEMON_SEEN']
        private=[]
        priority=outcome+seen[:1]+[r for r in records if r['claim']['type']=='MOVE_REVEALED'][:1]+[r for r in records if r['claim']['type']=='OWN_MOVE_ANNOUNCED'][:1]+[r for r in records if r['claim']['type']!='BATTLE_PARTICIPATION']
        for r in priority:
            if r['evidenceID'] not in private:private.append(r['evidenceID'])
        return {'schemaVersion':RECAP_VERSION,'obligationID':scope['obligationID'],'battleID':scope['battleID'],'actorID':scope['actorID'],'publicEvidenceIDs':[r['evidenceID'] for r in outcome+seen[:1]],'privateEvidenceIDs':private[:16],'summaryTemplate':'battle_episode_v1','tone':'matter_of_fact','visibility':'public','priorEpisodeIDs':[p['episodeID'] for p in self._recall(scope)['episodes'][-2:]]}

    def _validate_result(self,scope,result):
        keys={'schemaVersion','obligationID','battleID','actorID','publicEvidenceIDs','privateEvidenceIDs','summaryTemplate','tone','visibility','priorEpisodeIDs'}
        if not isinstance(result,dict) or set(result)!=keys or type(result['schemaVersion'])!=int or result['schemaVersion']!=RECAP_VERSION or any(result[k]!=scope[k] for k in ('obligationID','battleID','actorID')) or result['visibility']!='public' or result['summaryTemplate']!='battle_episode_v1' or result['tone'] not in self.pp_config['allowedTones']:raise WorldError('invalid mandatory recap result schema/scope')
        packet=self._battle_evidence(scope);allowed={r['evidenceID']:r for r in packet['evidence']}
        for key,maximum in [('publicEvidenceIDs',2),('privateEvidenceIDs',16),('priorEpisodeIDs',8)]:
            ids=result[key]
            if not isinstance(ids,list) or not (1 if key!='priorEpisodeIDs' else 0)<=len(ids)<=maximum or any(not isinstance(i,str) or not re.fullmatch('[a-f0-9]{64}',i) for i in ids) or len(set(ids))!=len(ids):raise WorldError('recap reference bounds')
        if any(i not in allowed for i in result['publicEvidenceIDs']+result['privateEvidenceIDs']):raise WorldError('unauthorized battle evidence')
        public=[allowed[i]['claim'] for i in result['publicEvidenceIDs']]
        if not any(c['type']=='TRAINER_BATTLE_RESULT' for c in public) or any(c['type'] not in self.pp_config['publicDisclosure'] for c in public):raise WorldError('mandatory outcome/disclosure policy')
        if any(i not in result['privateEvidenceIDs'] for i in result['publicEvidenceIDs']):raise WorldError('retained summary must reference all disclosed evidence')
        retained=[allowed[i]['claim'] for i in result['privateEvidenceIDs']]
        for kind in ('MOVE_REVEALED','OWN_MOVE_ANNOUNCED'):
            if any(r['claim']['type']==kind for r in allowed.values()) and not any(c['type']==kind for c in retained):raise WorldError('private episode omits available participant action evidence')
        prior={p['episodeID'] for p in self._recall(scope)['episodes']}
        if any(i not in prior for i in result['priorEpisodeIDs']):raise WorldError('foreign/future puppeteer memory reference')
        return allowed

    def _render_episode(self,records):
        claims=[r['claim'] for r in records]
        result=next((c['nativeOutcome'] for c in claims if c['type']=='TRAINER_BATTLE_RESULT'),None)
        return {'outcome':{1:'trainer_loss',2:'trainer_win',3:'draw'}.get(result,'unknown'),
                'seenSpeciesIDs':sorted({c['speciesID'] for c in claims if c['type']=='POKEMON_SEEN'}),
                'observedPlayerMoves':sorted({(c['speciesID'],c['moveID']) for c in claims if c['type']=='MOVE_REVEALED'}),
                'ownAnnouncedMoves':sorted({(c['speciesID'],c['moveID']) for c in claims if c['type']=='OWN_MOVE_ANNOUNCED'})}

    def settle_job(self,job_id,result,*,producer,reason=None,model=None,fail=False):
        def action():
            r,scope=self._job(job_id,allow_expired=producer=='deterministic_fallback')
            o=self.puppeteer_state()['obligations'].get(scope['obligationID'])
            if not o or o['status']!='GENERATING' or o.get('jobID')!=job_id:raise WorldError('obligation already settled or replaced')
            allowed=self._validate_result(scope,result)
            # Shadow must validate the actual proposal, but commits fallback.
            if scope['mode']=='shadow' and producer=='hermes':
                self.audit(job_id,'shadow-valid-proposal',{'result':result});result_commit=self.fallback_result(job_id);producer_commit='deterministic_fallback';reason_commit='shadow_policy'
            else:result_commit=result;producer_commit=producer;reason_commit=reason
            proposal={'battleID':scope['battleID'],'evidenceIDs':result_commit['publicEvidenceIDs'],'visibility':'public','policyVersion':1}
            self._recap_committing=True
            try:post=self._commit(scope['actorID'],proposal) if self._check_minimum(proposal,allowed) else None
            finally:self._recap_committing=False
            episode={'schemaVersion':1,'actorID':scope['actorID'],'battleID':scope['battleID'],'obligationID':scope['obligationID'],'postID':post,'visibility':'actor_private','scope':{k:scope[k] for k in ('campaignID','branchID','worldCursor','memoryCutoff','socialCutoff','puppeteerCutoff')},'sourceEvidenceIDs':result_commit['privateEvidenceIDs'],'publicEvidenceIDs':result_commit['publicEvidenceIDs'],'summaryTemplate':result_commit['summaryTemplate'],'tone':result_commit['tone'],'priorEpisodeIDs':result_commit['priorEpisodeIDs'],'summary':self._render_episode([allowed[i] for i in result_commit['privateEvidenceIDs']]),'producer':producer_commit,'promptVersion':model.get('promptVersion',1) if model else 1,'model':model}
            eid=self._pp_append('EPISODE',scope['obligationID'],episode)
            if fail:raise WorldError('injected recap/publication/memory interruption')
            outcome={'obligationID':scope['obligationID'],'postID':post,'episodeID':eid,'producer':producer_commit,'fallbackReason':reason_commit,'resultSHA256':digest(result_commit),'inputScopeSHA256':digest(scope),'jobID':job_id,'model':model,'promptVersion':model.get('promptVersion',1) if model else 1}
            self._pp_append('PUBLISHED',scope['obligationID'],outcome)
            self.db.execute("UPDATE puppeteer_jobs SET status='completed',result_sha=?,outcome=? WHERE id=?",(digest(result_commit),dump(outcome),job_id))
            self.audit(job_id,'processing-outcome',outcome)
            return outcome
        return self._tx(action)

    def _check_minimum(self,proposal,allowed):
        if not any(allowed[i]['claim']['type']=='TRAINER_BATTLE_RESULT' for i in proposal['evidenceIDs']):raise WorldError('minimum outcome required')
        return True

    def fallback(self,job_id,reason='offline_mode'):
        return self.settle_job(job_id,self.fallback_result(job_id),producer='deterministic_fallback',reason=reason)

    def recover_job(self,job,reason='interrupted_worker'):
        r=self._one('SELECT * FROM puppeteer_jobs WHERE id=?',(job,))
        if not r or r['status']!='active':return {'status':r['status'] if r else 'absent'}
        try:return self.fallback(job,reason)
        except WorldError as error:
            def revoke():
                self.db.execute("UPDATE puppeteer_jobs SET status='revoked' WHERE id=? AND status='active'",(job,))
                self.audit(job,'explicit-recovery-state',{'reason':reason,'grantRevoked':True,'error':str(error),'obligationRemainsDurable':True})
                return {'status':'revoked','reason':str(error)}
            return self._tx(revoke)

    def audit(self,job,event,payload):
        # Operator-only data; caller supplies bounded redacted objects, not env/headers.
        if len(dump(payload).encode())>64000:raise WorldError('audit bound')
        self.db.execute('INSERT INTO puppeteer_audit(job,event,payload) VALUES (?,?,?)',(job,event,dump(payload)))

    def _sync_links(self):
        pp=self.puppeteer_state();posts={p['postID'] for p in pp['episodes'].values()};existing={p['referenceID'] for p in pp['links'].values()};social=self.social_state()
        for collection,idfield in [('feeds','feedID'),('exposures','exposureID')]:
            for r in social[collection].values():
                if r['postID'] in posts and r[idfield] not in existing:
                    self._pp_append('SOCIAL_LINK',r[idfield],{'scope':'director_internal','kind':collection,'referenceID':r[idfield],'postID':r['postID'],'recipient':r['recipient'],'cutoffs':self._cutoffs()})

    def trainer_packet(self,actor):
        self.get_actor(actor);context=self.for_actor(actor).context();state=self.puppeteer_state()
        private=[p for p in state['episodes'].values() if p['actorID']==actor][-8:]
        episodes=[{'episodeID':p['episodeID'],'battleID':p['battleID'],'summary':p['summary'],'sourceEvidenceIDs':p['sourceEvidenceIDs'],'visibility':'actor_private','postID':p['postID']} for p in private]
        # Reported summaries are reconstructed only from this recipient's receipts,
        # never by filtering a global/director free-text summary after generation.
        reports=[]
        for delivery in context['deliveries']:
            reports.append({'claim':delivery['claim'],'attribution':delivery.get('attribution'),'evidenceIDs':delivery['evidenceIDs'],'mode':'reported'})
        species=sorted({g['claim']['speciesID'] for g in context['directObservations']+context['deliveries'] if g['claim']['type']=='POKEMON_SEEN'})
        changes=[]
        for previous,current in zip(episodes,episodes[1:]):
            a=previous['summary'];b=current['summary']
            changes.append({'previousEpisodeID':previous['episodeID'],'episodeID':current['episodeID'],'newlyObservedSpeciesIDs':sorted(set(b['seenSpeciesIDs'])-set(a['seenSpeciesIDs'])),'newlyObservedPlayerMoves':sorted(set(map(tuple,b['observedPlayerMoves']))-set(map(tuple,a['observedPlayerMoves']))),'interpretation':'bounded observation difference; absence is not forgetting or a tendency'})
        return {'schemaVersion':1,'observedChanges':changes,'trainer':self.get_actor(actor),'persona':self.persona(actor),'cutoffs':self._cutoffs(),'directObservations':context['directObservations'],'reportedClaims':reports,'retainedEpisodes':episodes,'observedSpeciesIDs':species,'unknowns':['unseen player party','unannounced player moves','future actions'],'strategicInterpretation':None,'truncated':context['truncated']}

    def director_memory(self):
        return {'scope':'director_internal_never_trainer_context',**self.puppeteer_state()}

    def verify_puppeteer_replay(self):
        for e in self.db.execute("SELECT * FROM puppeteer_log WHERE kind='EPISODE'"):
            p=json.loads(e['payload']);scope={**p['scope'],'actorID':p['actorID'],'battleID':p['battleID'],'obligationID':p['obligationID']};allowed={r['evidenceID']:r for r in self._battle_evidence(scope)['evidence']}
            if any(i not in allowed for i in p['sourceEvidenceIDs']+p['publicEvidenceIDs']):raise WorldError('retained memory source provenance mismatch')
            rendered=self._render_episode([allowed[i] for i in p['sourceEvidenceIDs']])
            if dump(rendered)!=dump(p['summary']):raise WorldError('retained memory summary mismatch')
            post=self._one("SELECT payload FROM social_log WHERE id=? AND kind='POST'",(p['postID'],))
            if not post or json.loads(post['payload'])['evidenceIDs']!=p['publicEvidenceIDs']:raise WorldError('episode publication provenance mismatch')
        return digest(self.puppeteer_state())


class JobTools:
    """The entire future model grant: no actor/timeline/query selectors."""
    def __init__(self,store,job):self.__store=store;self.__job=job
    def get_battle_evidence(self):
        _,scope=self.__store._job(self.__job)
        # One registered retrieval supplies the complete already-filtered job
        # bundle, so a serial tool-using model can submit within three requests.
        return {**self.__store._battle_evidence(scope),'actorContext':self.get_actor_context(),'priorMemory':self.recall_puppeteer_memory()}
    def recall_puppeteer_memory(self):
        _,scope=self.__store._job(self.__job);return self.__store._recall(scope)
    def get_actor_context(self):
        _,scope=self.__store._job(self.__job)
        # Pinned actor packet. It may not widen its cutoff as live world advances.
        packet=self.__store.trainer_packet(scope['actorID'])
        if packet['cutoffs']!= {k:v for k,v in scope.items() if k in packet['cutoffs']}:raise WorldError('context advanced; fresh scoped job required')
        return packet
    def submit_recap_and_memory_result(self,result,model=None):
        _,scope=self.__store._job(self.__job)
        return self.__store.settle_job(self.__job,build_submission(result,scope),producer='hermes',model=model)
