"""Deterministic social log over canonical facts and actor-owned memory.

Only trusted application code issues SocialActor capabilities. Publication,
distribution, exposure and memory delivery are separate committed operations.
"""
import json
import re
from pathlib import Path
from memory.store import MemoryStore, actor_id, digest
from world.store import ROOT, WorldError, dump, uid
from . import policy

VERSION = 1


def empty():
    return {'version': 1, 'activation': None, 'follows': {}, 'proposals': {}, 'outcomes': {},
            'posts': {}, 'pending': {}, 'feeds': {}, 'exposures': {}, 'tick': 0}


def apply(state, event):
    p = event['payload']; kind = event['kind']; key = event['semantic_key']
    if kind == 'ACTIVATED': state['activation'] = p
    elif kind == 'FOLLOW': state['follows'][key] = {'edgeID': event['id'], **p}
    elif kind == 'OUTCOME': state['outcomes'][key] = p
    elif kind == 'PROPOSAL': state['proposals'][key] = p
    elif kind == 'POST': state['posts'][event['id']] = {'postID': event['id'], **p}
    elif kind == 'JOB': state['pending'][key] = p
    elif kind == 'JOB_DONE': state['pending'].pop(key, None)
    elif kind == 'FEED': state['feeds'][key] = {'feedID': event['id'], **p}
    elif kind == 'EXPOSURE': state['exposures'][key] = {'exposureID': event['id'], **p}
    elif kind == 'TICK': state['tick'] = p['tick']
    else: raise WorldError('unsupported social event')
    return state


class SocialStore(MemoryStore):
    _supports_social = True

    def __init__(self, *args, config=None, **kwargs):
        self._social_ready = False
        super().__init__(*args, **kwargs)
        if self._one("SELECT name FROM sqlite_master WHERE name='puppeteer_version'") and not getattr(self, '_supports_puppeteer', False):
            self.close();raise WorldError('puppeteer-enabled database requires PuppeteerStore writer')
        self.config = config or json.loads((ROOT / 'config/social_slice.json').read_text())
        names = json.loads((ROOT / 'config/social_species_names.json').read_text())
        self.names = names['names']
        self.config_hash = digest([self.config, names, self.registry['catalogSHA256']])
        try:
            if self.config['version'] != 1 or self.config['policyVersion'] != 1 or self.config['templateVersion'] != 1 or not 1 <= self.config['maxClaims'] <= 2 or not 1 <= self.config['maxRecipients'] <= 8 or not 1 <= self.config['maxJobsPerTick'] <= 4:
                raise WorldError('unsupported social configuration')
            for actor, classification in self.config['eligibility'].items():
                self.get_actor(actor)
                if classification not in ('ordinary_slice_eligible', 'excluded'):
                    raise WorldError('unknown eligibility classification')
            for edge in self.config['seedFollows']:
                self.get_actor(edge['follower']); self.get_actor(edge['followed'])
                if edge['cause'] != 'authored_vertical_slice' or edge['follower'] == edge['followed']:
                    raise WorldError('invalid authored edge')
            if len(self.config['seedFollows']) > 8:
                raise WorldError('authored graph bounds')
            exists = self._one("SELECT name FROM sqlite_master WHERE name='social_version'")
            if exists:
                if [tuple(r) for r in self.db.execute('SELECT * FROM social_version')] != [(1, 1, self.config_hash)]:
                    raise WorldError('incompatible social schema/reducer/configuration')
            else:
                self.db.executescript('BEGIN IMMEDIATE;' + (Path(__file__).parent / 'migrations/001.sql').read_text())
                try:
                    self.db.execute('INSERT INTO social_version VALUES (1,1,?)', (self.config_hash,))
                    for table in ('social_log', 'social_branches', 'social_checkpoints'):
                        for op in ('UPDATE', 'DELETE'):
                            self.db.execute(f"CREATE TRIGGER immutable_{table}_{op} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'append-only social'); END")
                    for b in self.db.execute('SELECT id FROM branches').fetchall():
                        self.db.execute('INSERT INTO social_branches VALUES (?,0)', (b['id'],))
                    for cp in self.db.execute('SELECT id FROM checkpoints').fetchall():
                        self.db.execute('INSERT INTO social_checkpoints VALUES (?,0,?)', (cp['id'], digest(empty())))
                    c = self._one('SELECT * FROM campaigns')
                    if c:
                        self.db.execute('INSERT INTO social_view VALUES (?,?,0,0)', (c['id'], c['active_branch']))
                    self.db.execute('COMMIT')
                except Exception:
                    self.db.execute('ROLLBACK'); raise
            self._social_ready = True
        except Exception:
            self.close(); raise

    def _tx(self, fn):
        if self._one("SELECT name FROM sqlite_master WHERE name='puppeteer_version'") and not getattr(self, '_supports_puppeteer', False):
            raise WorldError('puppeteer-enabled database requires PuppeteerStore writer')
        if not self._social_ready:
            return super()._tx(fn)
        def action():
            self._social_before = self._one('SELECT * FROM social_view')
            return fn()
        return super()._tx(action)

    def _after_memory_transaction(self):
        if not self._social_ready:
            return
        c = self.campaign(); before = self._social_before
        if not self._one('SELECT * FROM social_branches WHERE branch=?', (c['active_branch'],)):
            self.db.execute('INSERT INTO social_branches VALUES (?,?)', (c['active_branch'], before['cutoff'] if before else 0))
        view = self._one('SELECT * FROM social_view WHERE campaign=?', (c['id'],))
        if not view:
            self.db.execute('INSERT INTO social_view VALUES (?,?,0,0)', (c['id'], c['active_branch']))
        elif self._restoring:
            cp = self._one('SELECT * FROM social_checkpoints WHERE checkpoint=?', (self._restoring,))
            if cp is None:
                raise WorldError('missing social checkpoint')
            self.db.execute('UPDATE social_view SET branch=?,cutoff=?,epoch=epoch+1 WHERE campaign=?', (c['active_branch'], cp['cutoff'], c['id']))
            if digest(self.social_state()) != cp['state_sha']:
                raise WorldError('social checkpoint replay mismatch')
            if self._one('SELECT 1 FROM social_log WHERE branch=? AND seq>? LIMIT 1', (c['active_branch'], cp['cutoff'])):
                self.db.execute('UPDATE campaigns SET pending_fork=1 WHERE id=?', (c['id'],))
            return # Never execute abandoned jobs/policies while restoring.
        elif view['branch'] != c['active_branch']:
            self.db.execute('UPDATE social_view SET branch=?,epoch=epoch+1 WHERE campaign=?', (c['active_branch'], c['id']))
        self._on_completed_battles()

    def _checkpoint(self, c, save, kind):
        cid = super()._checkpoint(c, save, kind)
        if not self._social_ready:
            return cid
        view = self._one('SELECT * FROM social_view WHERE campaign=?', (c['id'],))
        cutoff = view['cutoff'] if view else 0
        state_hash = digest(self.social_state()) if view else digest(empty())
        old = self._one('SELECT * FROM social_checkpoints WHERE checkpoint=?', (cid,))
        if old and (old['cutoff'], old['state_sha']) != (cutoff, state_hash):
            raise WorldError('ambiguous social save pairing')
        if not old:
            self.db.execute('INSERT INTO social_checkpoints VALUES (?,?,?)', (cid, cutoff, state_hash))
        return cid

    def player_actor(self):
        return 'player:' + self.campaign()['id']

    def _events(self, branch=None, cursor=None, cutoff=None):
        c = self.campaign(); view = self._one('SELECT * FROM social_view WHERE campaign=?', (c['id'],))
        branch = branch or c['active_branch']; cursor = c['cursor'] if cursor is None else cursor
        cutoff = view['cutoff'] if cutoff is None else cutoff
        b = self._one('SELECT * FROM branches WHERE id=?', (branch,))
        boundary = self._one('SELECT * FROM social_branches WHERE branch=?', (branch,))
        prefix = self._events(b['parent'], min(cursor,b['fork_cursor']), min(cutoff,boundary['parent_cutoff'])) if b['parent'] else []
        rows = self.db.execute('SELECT * FROM social_log WHERE campaign=? AND branch=? AND cursor<=? AND seq<=? ORDER BY seq', (c['id'],branch,cursor,cutoff))
        return prefix + [{**dict(r), 'payload': json.loads(r['payload'])} for r in rows]

    def social_state(self):
        state = empty()
        for e in self._events(): apply(state,e)
        return state

    def _append(self, kind, key, payload):
        c = self.campaign(); view = self._one('SELECT * FROM social_view WHERE campaign=?',(c['id'],))
        identity = digest(['social1',c['id'],c['active_branch'],kind,key])
        old = self._one('SELECT * FROM social_log WHERE id=?',(identity,))
        if old:
            if old['payload'] != dump(payload): raise WorldError('conflicting social duplicate')
            return identity
        result = self.db.execute('INSERT INTO social_log(id,campaign,branch,cursor,kind,semantic_key,payload) VALUES (?,?,?,?,?,?,?)', (identity,c['id'],c['active_branch'],c['cursor'],kind,key,dump(payload)))
        self.db.execute('UPDATE social_view SET branch=?,cutoff=? WHERE campaign=?',(c['active_branch'],result.lastrowid,c['id']))
        return identity

    def _writable(self):
        c = self.campaign()
        if c['status'] not in ('paired','imported') or self.pending_save():
            raise WorldError('social write requires paired world and no save barrier')
        if c['pending_fork']:
            # Authorized host-only divergence: same canonical prefix, distinct
            # subjective/social future. Never reuse restored RAM event origins.
            v = self._one('SELECT * FROM social_view WHERE campaign=?',(c['id'],))
            m = self._one('SELECT * FROM memory_view WHERE campaign=?',(c['id'],))
            child = uid()
            self.db.execute('INSERT INTO branches VALUES (?,?,?,?,?)',(child,c['id'],c['active_branch'],c['cursor'],c['cursor']))
            self.db.execute('INSERT INTO memory_branches VALUES (?,?)',(child,m['cutoff']))
            self.db.execute('INSERT INTO social_branches VALUES (?,?)',(child,v['cutoff']))
            self.db.execute('UPDATE campaigns SET active_branch=?,pending_fork=0 WHERE id=?',(child,c['id']))
            self.db.execute('UPDATE memory_view SET branch=? WHERE campaign=?',(child,c['id']))
            self.db.execute('UPDATE social_view SET branch=?,epoch=epoch+1 WHERE campaign=?',(child,c['id']))

    def activate(self):
        def action():
            current = self.social_state()
            if current['activation']: return current['activation']
            self._writable(); c = self.campaign()
            p = {'worldCursor':c['cursor'],'configVersion':1,'configSHA256':self.config_hash,'policyVersion':1,'playerActor':self.player_actor()}
            self._append('ACTIVATED','activation',p)
            for edge in self.config['seedFollows']:
                self._append('FOLLOW',edge['follower']+'>'+edge['followed'],edge)
            return p
        return self._tx(action)

    def _recap_qualifies(self, actor, battle, state):
        return battle and battle['ended'] and battle['defeated'] and battle['trainerID']==actor.removeprefix('trainer:') and self._follow_eligible(actor)

    def _follow_eligible(self,actor):
        return self.config['eligibility'].get(actor)=='ordinary_slice_eligible'

    def _opportunity(self, actor, battle):
        state = self.social_state(); b = self.get_battle(battle)
        if not state['activation'] or not self._recap_qualifies(actor,b,state):
            raise WorldError('no eligible completed battle opportunity')
        events = self.get_canonical_events()
        end = next(e for e in events if e['eventID']==b['endEvent'])
        if end['cursor'] <= state['activation']['worldCursor']:
            raise WorldError('battle precedes explicit activation')
        view = self.for_actor(actor)
        # Select only sources from this battle; do not expose a full private
        # context to publication policy. Read storage in bounded source order.
        evidence = []; after=0
        for _ in range(16):
            page = view.records(after=after,limit=256)
            evidence += [r for r in page['records'] if r['mode']=='direct' and r['claim']['battleID']==battle and r['claim']['type'] in ('TRAINER_BATTLE_RESULT','POKEMON_SEEN')]
            if not page['hasMore']:break
            after=page['records'][-1]['memoryCursor']
        else: raise WorldError('opportunity retrieval bound')
        unique = {}; 
        for r in evidence: unique.setdefault(dump(r['claim']),r)
        return {'actorID':actor,'battleID':battle,'evidence':list(unique.values()),'worldCursor':self.get_current_world_cursor()}

    def _commit(self, actor, proposal):
        if not isinstance(proposal,dict) or set(proposal)!={'battleID','evidenceIDs','visibility','policyVersion'} or type(proposal['policyVersion'])!=int or proposal['policyVersion']!=1 or proposal['visibility'] not in ('public','private') or not isinstance(proposal['battleID'],str) or not re.fullmatch('[a-f0-9]{64}',proposal['battleID']):
            raise WorldError('unsupported proposal; body/extra claims prohibited')
        ids = proposal['evidenceIDs']
        if not isinstance(ids,list) or not 1<=len(ids)<=self.config['maxClaims'] or any(not isinstance(i,str) or not re.fullmatch('[a-f0-9]{64}',i) for i in ids) or len(set(ids))!=len(ids):
            raise WorldError('proposal claim bounds')
        opportunity = self._opportunity(actor,proposal['battleID'])
        allowed = {r['memoryID']:r for r in opportunity['evidence']}
        if any(i not in allowed for i in ids):raise WorldError('foreign/private/unsupported evidence reference')
        records=[allowed[i] for i in ids]; claims=[r['claim'] for r in records]
        if len({r['type'] for r in claims})!=len(claims):raise WorldError('duplicate claim type')
        body = policy.render(claims,self.names)
        current = self.social_state(); existing=next((p for p in current['posts'].values() if p['battleID']==proposal['battleID']),None)
        if existing:
            if existing['author']!=actor or existing['claims']!=claims or existing['visibility']!=proposal['visibility']:raise WorldError('recap already committed')
            return existing['postID']
        p={'author':actor,'battleID':proposal['battleID'],'claims':claims,'evidenceIDs':ids,'body':body,'visibility':proposal['visibility'],'templateVersion':1,'policyVersion':1,'configSHA256':self.config_hash,'contextWorldCursor':self.get_current_world_cursor(),'contextMemoryCutoff':self._one('SELECT cutoff FROM memory_view')['cutoff']}
        post = self._append('POST',proposal['battleID'],p)
        self._append('JOB',post,{'postID':post})
        return post

    def _on_completed_battles(self):
        current=self.social_state()
        if not current['activation']:return
        pending=[]
        for b in self.state()['battles'].values():
            actor=actor_id(b['trainerID']) if b['trainerID'] else None
            if b['ended'] and b['defeated'] and self._follow_eligible(actor) and b['battleID'] not in current['outcomes']:
                end=next(e for e in self.get_canonical_events() if e['eventID']==b['endEvent'])
                if end['cursor']>current['activation']['worldCursor']:pending.append((end['cursor'],actor,b))
        if len(pending)>4:raise WorldError('social trigger bound; no unbounded historical backfill')
        for _,actor,b in sorted(pending):
            edge=actor+'>'+self.player_actor()
            if edge not in self.social_state()['follows']:
                self._append('FOLLOW',edge,{'follower':actor,'followed':self.player_actor(),'cause':'first_confirmed_eligible_win','battleID':b['battleID'],'endEventID':b['endEvent']})
            opportunity=self._opportunity(actor,b['battleID']);proposal=policy.propose(opportunity)
            self._append('PROPOSAL',b['battleID'],{'actor':actor,'proposal':proposal,'policyVersion':1})
            post=self._commit(actor,proposal) if proposal and self.config['autoPublish'] else None
            self._append('OUTCOME',b['battleID'],{'proposal':proposal,'status':'published' if post else 'awaiting_author' if proposal else 'no_author_evidence','postID':post,'policyVersion':1})

    def tick(self, tick):
        def action():
            state=self.social_state()
            if type(tick)!=int or tick<1 or tick not in (state['tick'],state['tick']+1):raise WorldError('social tick order')
            if tick==state['tick']:return state
            self._writable();state=self.social_state()
            self._append('TICK',str(tick),{'tick':tick,'policyVersion':1})
            for job in sorted(state['pending'])[:self.config['maxJobsPerTick']]:
                post=state['posts'][job]
                if post['visibility']=='public':
                    edges=sorted((e for e in state['follows'].values() if e['followed']==post['author']),key=lambda e:e['follower'])
                    for edge in edges[:self.config['maxRecipients']]:
                        key=edge['follower']+'>'+job
                        if key not in state['feeds']:
                            self._append('FEED',key,{'recipient':edge['follower'],'postID':job,'tick':tick,'reason':'one_hop_follower','qualifyingEdgeID':edge['edgeID'],'policyVersion':1})
                self._append('JOB_DONE',job,{'tick':tick,'postID':job,'visibility':post['visibility']})
            return self.social_state()
        return self._tx(action)

    def for_social_actor(self, actor):
        """Trusted issuer, never register this factory with future Hermes."""
        self.get_actor(actor)
        c=self.campaign();v=self._one('SELECT * FROM social_view WHERE campaign=?',(c['id'],));m=self._one('SELECT cutoff FROM memory_view WHERE campaign=?',(c['id'],))
        return SocialActor(self,actor,c['id'],c['active_branch'],c['cursor'],m['cutoff'],v['cutoff'],v['epoch'])

    def _expose(self, grant, post_id, fail=False):
        if not isinstance(post_id,str) or not re.fullmatch('[a-f0-9]{64}',post_id):raise WorldError('invalid post reference')
        def action():
            grant._validate();state=self.social_state();key=grant._actor+'>'+post_id
            if key not in state['feeds']:raise WorldError('post not delivered to actor feed')
            if key in state['exposures']:return state['exposures'][key]
            self._writable();post=self.social_state()['posts'][post_id]
            receipts=[]
            for source_id in post['evidenceIDs']:
                identity=digest(['post-memory',self.campaign()['id'],self.get_active_branch(),post_id,grant._actor,source_id])
                receipts.append(self._deliver_reference(identity=identity,sender=post['author'],recipient=grant._actor,source_memory_id=source_id,source_kind='post_exposure',source_id=post_id,channel='pokebook'))
            if fail:raise WorldError('injected exposure interruption')
            self._append('EXPOSURE',key,{'recipient':grant._actor,'postID':post_id,'memoryIDs':receipts,'channel':'pokebook','socialTick':state['tick']})
            return self.social_state()['exposures'][key]
        self._delivering=True
        try:return self._tx(action)
        finally:self._delivering=False

    def verify_social_replay(self):
        # Pure replay of committed decisions; never rerun policy to change past
        # recipients or text. Direct memory replay separately audits source data.
        for e in self.db.execute('SELECT * FROM social_log WHERE kind=\'FEED\''):
            p=json.loads(e['payload']);before=empty()
            for prior in self._events(e['branch'],e['cursor'],e['seq']-1):apply(before,prior)
            post=before['posts'].get(p['postID'])
            edge=next((r for r in before['follows'].values() if r['edgeID']==p['qualifyingEdgeID']),None)
            if not post or post['visibility']!='public' or not edge or (edge['follower'],edge['followed'])!=(p['recipient'],post['author']) or p['tick']!=before['tick'] or p['reason']!='one_hop_follower':raise WorldError('feed graph provenance mismatch')
        for e in self.db.execute('SELECT * FROM social_log WHERE kind=\'POST\''):
            p=json.loads(e['payload'])
            if p['body']!=policy.render(p['claims'],self.names) or not 1<=len(p['claims'])<=self.config['maxClaims'] or len(p['claims'])!=len(p['evidenceIDs']) or p['contextWorldCursor']!=e['cursor'] or p['configSHA256']!=self.config_hash:raise WorldError('post rendering/claim mismatch')
            scopes=self._scope(e['branch'],p['contextWorldCursor'],p['contextMemoryCutoff'])
            for source,claim in zip(p['evidenceIDs'],p['claims']):
                r=self._one('SELECT * FROM memory_evidence WHERE id=?',(source,))
                if not r or r['campaign']!=e['campaign'] or r['actor']!=p['author'] or r['mode']!='direct' or r['battle']!=p['battleID'] or json.loads(r['claim'])!=claim or not any(r['branch']==b and r['cursor']<=c and r['seq']<=n for b,c,n in scopes):raise WorldError('post author provenance mismatch')
        for e in self.db.execute('SELECT * FROM social_log WHERE kind=\'EXPOSURE\''):
            p=json.loads(e['payload'])
            before=empty()
            for prior in self._events(e['branch'],e['cursor'],e['seq']-1):apply(before,prior)
            key=p['recipient']+'>'+p['postID']
            post=before['posts'].get(p['postID'])
            if not post or key not in before['feeds'] or key in before['exposures'] or post['visibility']!='public' or p['channel']!='pokebook':raise WorldError('exposure feed provenance mismatch')
            rows=[self._one('SELECT * FROM memory_evidence WHERE id=?',(i,)) for i in p['memoryIDs']]
            if len(rows)!=len(post['claims']) or any(not r or r['campaign']!=e['campaign'] or r['branch']!=e['branch'] or r['cursor']!=e['cursor'] or r['actor']!=p['recipient'] or r['source_kind']!='post_exposure' or r['source_id']!=p['postID'] or r['sender']!=post['author'] or r['channel']!='pokebook' or r['parent']!=source or json.loads(r['claim'])!=claim for r,claim,source in zip(rows,post['claims'],post['evidenceIDs'])):raise WorldError('exposure/memory receipt mismatch')
        return digest(self.social_state())


class SocialActor:
    """Actor-bound application capability. Only specific methods become tools."""
    def __init__(self,store,actor,campaign,branch,cursor,memory_cutoff,social_cutoff,epoch):
        self.__store=store;self._actor=actor;self.__campaign=campaign;self.__branch=branch
        self.__cursor=cursor;self.__memory=memory_cutoff;self.__social=social_cutoff;self.__epoch=epoch

    def _validate(self):
        s=self.__store;c=s.campaign();v=s._one('SELECT * FROM social_view WHERE campaign=?',(c['id'],));m=s._one('SELECT cutoff FROM memory_view WHERE campaign=?',(c['id'],))
        if c['status'] not in ('paired','imported') or (c['id'],c['active_branch'],c['cursor'],m['cutoff'],v['cutoff'],v['epoch'])!=(self.__campaign,self.__branch,self.__cursor,self.__memory,self.__social,self.__epoch):raise WorldError('stale or revoked social actor grant')

    def opportunities(self):
        self._validate();s=self.__store
        activation=s.social_state()['activation']
        if not activation:return []
        ends={e['eventID']:e['cursor'] for e in s.get_canonical_events()}
        return [s._opportunity(self._actor,b['battleID']) for b in s.state()['battles'].values() if b['trainerID']==self._actor.removeprefix('trainer:') and b['ended'] and b['defeated'] and s._follow_eligible(self._actor) and ends[b['endEvent']]>activation['worldCursor']][:4]

    def submit(self,proposal):
        def action():
            self._validate();self.__store._writable()
            # Validation/commit and the author-selected proposal are one atomic
            # action. The trigger's earlier deterministic candidate is retained.
            post=self.__store._commit(self._actor,proposal)
            key='author:'+proposal['battleID']
            self.__store._append('PROPOSAL',key,{'actor':self._actor,'proposal':proposal,'policyVersion':1,'selection':'author_submission'})
            self.__store._append('OUTCOME',key,{'proposal':proposal,'status':'published','postID':post,'policyVersion':1})
            return post
        return self.__store._tx(action)

    def feed_metadata(self):
        self._validate();state=self.__store.social_state()
        # Metadata omits body, claims and internal evidence IDs, including unread.
        return [{'postID':f['postID'],'author':state['posts'][f['postID']]['author'],'seen':key in state['exposures'],'channel':'pokebook'} for key,f in sorted(state['feeds'].items()) if f['recipient']==self._actor][:32]

    def expose(self,post_id):
        return self.__store._expose(self,post_id)

    def read_post(self,post_id):
        self._validate();s=self.__store;state=s.social_state();post=state['posts'].get(post_id)
        if not post or (post['author']!=self._actor and self._actor+'>'+post_id not in state['exposures']):raise WorldError('post body requires recorded exposure')
        return {k:post[k] for k in ('postID','author','claims','body','visibility','templateVersion')}

    def relationships(self):
        self._validate();s=self.__store
        return [e for e in s.social_state()['follows'].values() if self._actor in (e['follower'],e['followed'])][:32]
