"""Additive save-paired diffusion log. Legacy SOCIAL1 snapshots stay unchanged.

Only the trusted host creates this store and advances domain ticks. No model,
ROM, provider, wall clock or player-viewer dependency enters scheduling.
"""
import json
from pathlib import Path
from memory.store import digest
from social.store import SocialStore, SocialActor
from social import store as legacy_social
from puppeteer.store import PuppeteerStore
from world.store import ROOT, WorldError, dump
from . import policy


def empty():
    return {'version':1,'activation':None,'epochs':{},'feeds':{},'exposures':{},'intel':{},'ticks':{}}


class ViralityMixin:
    _supports_virality=True

    def __init__(self,*args,virality_config=None,**kwargs):
        self._viral_ready=False
        super().__init__(*args,**kwargs)
        try:
            self.viral_config=policy.validate(virality_config or json.loads((ROOT/'config/virality_policy.json').read_text()),self.registry)
            self.viral_hash=digest(self.viral_config)
            if self._one("SELECT name FROM sqlite_master WHERE name='virality_version'"):
                if [tuple(r) for r in self.db.execute('SELECT * FROM virality_version')] != [(1,self.viral_hash)]:raise WorldError('explicit virality balance migration required')
            else:
                self.db.executescript('''BEGIN IMMEDIATE;
CREATE TABLE virality_version(version INTEGER PRIMARY KEY,config_sha TEXT NOT NULL);
CREATE TABLE virality_log(seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT UNIQUE NOT NULL,campaign TEXT NOT NULL REFERENCES campaigns(id),branch TEXT NOT NULL REFERENCES branches(id),cursor INTEGER NOT NULL,kind TEXT NOT NULL,semantic_key TEXT NOT NULL,payload TEXT NOT NULL,UNIQUE(branch,kind,semantic_key));
CREATE TABLE virality_view(campaign TEXT PRIMARY KEY,branch TEXT NOT NULL,cutoff INTEGER NOT NULL,epoch INTEGER NOT NULL);
CREATE TABLE virality_branches(branch TEXT PRIMARY KEY,parent_cutoff INTEGER NOT NULL);
CREATE TABLE virality_checkpoints(checkpoint TEXT PRIMARY KEY,cutoff INTEGER NOT NULL,state_sha TEXT NOT NULL);
''')
                try:
                    self.db.execute('INSERT INTO virality_version VALUES (1,?)',(self.viral_hash,))
                    for table in ('virality_version','virality_log','virality_branches','virality_checkpoints'):
                        for op in ('UPDATE','DELETE'):
                            self.db.execute(f"CREATE TRIGGER immutable_{table}_{op} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'append-only virality'); END")
                    for b in self.db.execute('SELECT id FROM branches').fetchall():self.db.execute('INSERT INTO virality_branches VALUES (?,0)',(b['id'],))
                    for cp in self.db.execute('SELECT id FROM checkpoints').fetchall():self.db.execute('INSERT INTO virality_checkpoints VALUES (?,0,?)',(cp['id'],digest(empty())))
                    c=self._one('SELECT * FROM campaigns')
                    if c:self.db.execute('INSERT INTO virality_view VALUES (?,?,0,0)',(c['id'],c['active_branch']))
                    self.db.execute('COMMIT')
                except Exception:self.db.execute('ROLLBACK');raise
            self._viral_ready=True
        except Exception:self.close();raise

    def _tx(self,fn):
        if not self._viral_ready:return super()._tx(fn)
        def action():
            self._viral_before=self._one('SELECT * FROM virality_view')
            self._viral_posts_before=set(self.social_state()['posts']) if self._one('SELECT * FROM campaigns') else set()
            self._viral_battles_before={b for b,v in self.state()['battles'].items() if v['ended']} if self._one('SELECT * FROM campaigns') else set()
            return fn()
        return super()._tx(action)

    def _after_memory_transaction(self):
        super()._after_memory_transaction()
        if not self._viral_ready:return
        c=self.campaign();v=self._one('SELECT * FROM virality_view');before=self._viral_before
        if not self._one('SELECT * FROM virality_branches WHERE branch=?',(c['active_branch'],)):
            self.db.execute('INSERT INTO virality_branches VALUES (?,?)',(c['active_branch'],before['cutoff'] if before else 0))
        if not v:self.db.execute('INSERT INTO virality_view VALUES (?,?,0,0)',(c['id'],c['active_branch']))
        elif self._restoring:
            cp=self._one('SELECT * FROM virality_checkpoints WHERE checkpoint=?',(self._restoring,))
            if not cp:raise WorldError('missing virality save pairing')
            self.db.execute('UPDATE virality_view SET branch=?,cutoff=?,epoch=epoch+1 WHERE campaign=?',(c['active_branch'],cp['cutoff'],c['id']))
            if digest(self.virality_state()) != cp['state_sha']:raise WorldError('virality checkpoint replay mismatch')
            if self._one('SELECT 1 FROM virality_log WHERE branch=? AND seq>?',(c['active_branch'],cp['cutoff'])):self.db.execute('UPDATE campaigns SET pending_fork=1 WHERE id=?',(c['id'],))
            return
        elif v['branch'] != c['active_branch']:
            self.db.execute('UPDATE virality_view SET branch=?,epoch=epoch+1 WHERE campaign=?',(c['active_branch'],c['id']))
        # Automatically react to newly published posts at a settled domain boundary.
        # Activation adoption is explicit; restores never run the scheduler.
        state=self.virality_state()
        if state['activation'] and not self.pending_save() and c['status'] in ('paired','imported') and not c['pending_fork']:
            posts=self.social_state()['posts']
            new_post=any(p not in self._viral_posts_before and p not in state['epochs'] for p in posts)
            new_battle=any(v['ended'] and b not in self._viral_battles_before for b,v in self.state()['battles'].items())
            if new_post or new_battle:
                self._process('publication' if new_post else 'battle_completion',True)
                self.db.execute('UPDATE memory_view SET cutoff=? WHERE campaign=?',(self._maximum(),c['id']))

    def _checkpoint(self,c,save,kind):
        cid=super()._checkpoint(c,save,kind)
        if not self._viral_ready:return cid
        v=self._one('SELECT * FROM virality_view');cut=v['cutoff'] if v else 0;sha=digest(self.virality_state()) if v else digest(empty())
        old=self._one('SELECT * FROM virality_checkpoints WHERE checkpoint=?',(cid,))
        if old and (old['cutoff'],old['state_sha']) != (cut,sha):raise WorldError('ambiguous virality save pairing')
        if not old:self.db.execute('INSERT INTO virality_checkpoints VALUES (?,?,?)',(cid,cut,sha))
        return cid

    def _writable(self):
        v=self._one('SELECT * FROM virality_view') if self._viral_ready else None
        super()._writable()
        if v and v['branch'] != self.get_active_branch():
            b=self.get_active_branch()
            if not self._one('SELECT * FROM virality_branches WHERE branch=?',(b,)):
                self.db.execute('INSERT INTO virality_branches VALUES (?,?)',(b,v['cutoff']))
            self.db.execute('UPDATE virality_view SET branch=?,epoch=epoch+1',(b,))

    def _viral_events(self,branch=None,cursor=None,cutoff=None):
        c=self.campaign();v=self._one('SELECT * FROM virality_view')
        branch=branch or c['active_branch'];cursor=c['cursor'] if cursor is None else cursor;cutoff=v['cutoff'] if cutoff is None else cutoff
        b=self._one('SELECT * FROM branches WHERE id=?',(branch,));bound=self._one('SELECT * FROM virality_branches WHERE branch=?',(branch,))
        prefix=self._viral_events(b['parent'],min(cursor,b['fork_cursor']),min(cutoff,bound['parent_cutoff'])) if b['parent'] else []
        return prefix+[dict(r) for r in self.db.execute('SELECT * FROM virality_log WHERE campaign=? AND branch=? AND cursor<=? AND seq<=? ORDER BY seq',(c['id'],branch,cursor,cutoff))]

    def virality_state(self):
        if not self._one('SELECT * FROM campaigns'):return empty()
        state=empty()
        for e in self._viral_events():
            p=json.loads(e['payload']);k=e['kind']
            if k=='ACTIVATED':state['activation']=p
            elif k=='EPOCH':state['epochs'][e['semantic_key']]=p
            elif k=='FEED':state['feeds'][e['semantic_key']]={'feedID':e['id'],**p}
            elif k=='EXPOSURE':state['exposures'][e['semantic_key']]={'exposureID':e['id'],**p}
            elif k=='INTEL':state['intel'][e['semantic_key']]=p
            elif k=='TICK':state['ticks'][e['semantic_key']]=p
            else:raise WorldError('unsupported virality event')
        return state

    def _viral_append(self,kind,key,payload):
        c=self.campaign();identity=digest(['virality1',c['id'],c['active_branch'],kind,key])
        old=self._one('SELECT * FROM virality_log WHERE id=?',(identity,))
        if old:
            if old['payload'] != dump(payload):raise WorldError('conflicting virality retry')
            return identity
        self.db.execute('INSERT INTO virality_log(id,campaign,branch,cursor,kind,semantic_key,payload) VALUES (?,?,?,?,?,?,?)',(identity,c['id'],c['active_branch'],c['cursor'],kind,key,dump(payload)))
        seq=self._one('SELECT seq FROM virality_log WHERE id=?',(identity,))['seq']
        self.db.execute('UPDATE virality_view SET cutoff=? WHERE campaign=?',(seq,c['id']))
        return identity

    def virality_scope(self):
        c=self.campaign();v=self._one('SELECT * FROM virality_view');m=self._one('SELECT * FROM memory_view');s=self._one('SELECT * FROM social_view')
        return {'campaign':c['id'],'branch':c['active_branch'],'cursor':c['cursor'],'memoryCutoff':m['cutoff'],'socialCutoff':s['cutoff'],'viralityCutoff':v['cutoff'],'restoreEpoch':v['epoch'],'configSHA256':self.viral_hash}

    def activate_virality(self):
        def action():
            self._writable()
            if not self.virality_state()['activation']:self._viral_append('ACTIVATED','activation',{'configSHA256':self.viral_hash,'worldCursor':self.campaign()['cursor']})
        return self._tx(action)

    def advance_social(self,reason,*,expected_scope=None,expose=True):
        if reason not in ('publication','battle_completion','progression','exposure'):raise WorldError('meaningful social domain tick required')
        if type(expose) is not bool:raise WorldError('exposure flag')
        def action():
            if expected_scope is not None and expected_scope != self.virality_scope():raise WorldError('stale diffusion/scouting job')
            self._writable()
            if not self.virality_state()['activation']:raise WorldError('virality activation required')
            return self._process(reason,expose)
        self._delivering=True
        try:return self._tx(action)
        finally:self._delivering=False

    def _process(self,reason,expose):
        social=self.social_state();state=self.virality_state();posts=list(social['posts'].values());edges=list(social['follows'].values());actors=set(self.registry_actor_ids())
        pending=[(i,p) for i,p in enumerate(posts,1) if p['postID'] not in state['epochs']]
        for order,post in pending[:self.viral_config['maxPostsPerTick']]:
            trusted_post={**post,'sourceTrainerID':self.get_battle(post['battleID'])['sourceTrainerID']}
            epoch=policy.plan(self.viral_config,player=self.player_actor(),post=trusted_post,edges=edges,known_actors=actors,post_order=order)
            epoch.update(postID=post['postID'],scope=self.virality_scope(),configSHA256=self.viral_hash,graph=edges,publicationOrder=order)
            self._viral_append('EPOCH',post['postID'],epoch)
            for feed in epoch['deliveries']:self._viral_append('FEED',dump([feed['recipient'],post['postID']]),feed)
        state=self.virality_state()
        if expose:
            pending_exposure=[(k,f) for k,f in sorted(state['feeds'].items()) if k not in state['exposures']]
            for key,feed in pending_exposure[:self.viral_config['maxExposuresPerTick']]:self._expose_public(key,feed,social)
        # Faction delivery is a different channel, with no public-feed dependency.
        self._rocket_tick()
        material=digest([reason,sorted(self.virality_state()['epochs']),sorted(self.virality_state()['exposures']),sorted(self.virality_state()['intel'])])
        self._viral_append('TICK',material,{'reason':reason,'material':material})
        return self.virality_state()

    def _expose_public(self,key,feed,social):
        post=social['posts'][feed['postID']]
        if post['visibility'] != 'public':raise WorldError('scout private post denied')
        # Reuse an existing SOCIAL1 exposure if it already delivered the same post.
        legacy=social['exposures'].get(feed['recipient']+'>'+feed['postID'])
        ids=[]
        if legacy:ids=legacy['memoryIDs']
        else:
            for evidence in post['evidenceIDs']:
                identity=digest(['virality-post',self.campaign()['id'],self.get_active_branch(),key,evidence])
                ids.append(self._deliver_reference(identity=identity,sender=post['author'],recipient=feed['recipient'],source_memory_id=evidence,source_kind='post_exposure',source_id=post['postID'],channel='pokebook'))
        self._viral_append('EXPOSURE',key,{'recipient':feed['recipient'],'postID':post['postID'],'feedID':feed['feedID'],'memoryIDs':ids,'reason':feed['reason']})

    def _authorize_rocket_reference(self,sender,recipient,source):
        c=self.campaign()
        if policy.profile(self.viral_config,sender)['rocketRole'] != 'member' or policy.profile(self.viral_config,recipient)['rocketRole'] != 'leader' or source['mode'] != 'direct':raise WorldError('Rocket direct observation privilege denied')
        battle=self.get_battle(source['battle'])
        if not battle or battle['trainerID'] != sender[8:]:raise WorldError('unrelated Rocket private memory denied')
        r={'actorID':sender,'campaignID':c['id'],'branchID':c['active_branch'],'mode':'direct','memoryID':source['id'],'claim':json.loads(source['claim'])}
        policy.rocket_intelligence(self.viral_config,member=sender,leader=recipient,records=[r],campaign=c['id'],branch=c['active_branch'])

    def _rocket_tick(self):
        leaders=[a for a,p in self.viral_config['profiles'].items() if p['rocketRole']=='leader']
        state=self.virality_state();committed=0
        for member,p in self.viral_config['profiles'].items():
            if p['rocketRole'] != 'member':continue
            after=0
            while True:
                page=self.for_actor(member).records(after=after,limit=256)
                for r in page['records']:
                    if r['mode'] != 'direct':continue
                    battle=self.get_battle(r['claim'].get('battleID'))
                    if not battle or not battle['ended']:continue
                    for leader in leaders:
                        key=dump([member,leader,r['memoryID']])
                        if key in state['intel']:continue
                        if committed >= self.viral_config['maxIntelPerTick']:return
                        committed += 1
                        identity=digest(['rocket-intel',self.campaign()['id'],self.get_active_branch(),key])
                        self._deliver_reference(identity=identity,sender=member,recipient=leader,source_memory_id=r['memoryID'],source_kind='rocket_intel',source_id=r['memoryID'],channel='ROCKET_INTEL')
                        self._viral_append('INTEL',key,{'recipient':leader,'sourceActor':member,'sourceMemoryID':r['memoryID'],'memoryID':identity,'channel':'ROCKET_INTEL'})
                if not page['hasMore']:break
                after=page['records'][-1]['memoryCursor']

    def for_social_actor(self,actor):
        self.get_actor(actor);c=self.campaign();s=self._one('SELECT * FROM social_view');m=self._one('SELECT * FROM memory_view')
        return ViralitySocialActor(self,actor,c['id'],c['active_branch'],c['cursor'],m['cutoff'],s['cutoff'],s['epoch'])

    def _expose(self,grant,post_id,fail=False):
        grant._validate();key=dump([grant._actor,post_id]);state=self.virality_state()
        if key not in state['feeds']:return super()._expose(grant,post_id,fail)
        if key in state['exposures']:return state['exposures'][key]
        def action():
            grant._validate();self._writable();self._expose_public(key,state['feeds'][key],self.social_state())
            if fail:raise WorldError('injected exposure interruption')
            return self.virality_state()['exposures'][key]
        self._delivering=True
        try:return self._tx(action)
        finally:self._delivering=False

    def public_feed(self,actor):
        self.get_actor(actor);state=self.virality_state()
        return [{'postID':v['postID'],'feedID':v['feedID'],'reason':v['reason'],'seen':k in state['exposures']} for k,v in state['feeds'].items() if v['recipient']==actor]

    def read_public_post(self,actor,post_id):
        self.get_actor(actor);key=dump([actor,post_id]);state=self.virality_state()
        if key not in state['exposures']:raise WorldError('post requires recorded exposure')
        p=self.social_state()['posts'][post_id]
        return {k:p[k] for k in ('postID','author','body','claims','visibility')}

    def _original_origin(self,record):
        row=self._one('SELECT * FROM memory_evidence WHERE id=?',(record['memoryID'],))
        for _ in range(16):
            if not row['parent']:return (row['actor'],row['battle'])
            parent=self._one('SELECT * FROM memory_evidence WHERE id=?',(row['parent'],))
            if not parent or parent['claim'] != row['claim']:raise WorldError('origin provenance mismatch')
            row=parent
        raise WorldError('origin provenance depth')

    def evidence_context(self,actor):
        """Actor-filtered first, then quality/ranking. No global claim retrieval."""
        self.get_actor(actor);state=self.virality_state();posts=self.social_state()['posts'];records=[];after=0
        while True:
            page=self.for_actor(actor).records(after=after,limit=256);records.extend(page['records'])
            if not page['hasMore']:break
            after=page['records'][-1]['memoryCursor']
        latest=max([e['publicationOrder'] for e in state['epochs'].values()]+[0]);rows=[]
        origins={}
        for r in records:
            claim={k:v for k,v in r['claim'].items() if k not in ('battleID','trainerID')};key=dump(claim)
            source=r['source'];origin=self._original_origin(r)
            origins.setdefault(key,set()).add(origin)
        for r in records:
            source=r['source'];post_id=source.get('postID');feed=state['feeds'].get(dump([actor,post_id])) if post_id else None
            sender=source.get('sender') or actor;origin=policy.profile(self.viral_config,sender)['encounterStage']
            battle=self.get_battle(r['claim'].get('battleID'))
            if battle:origin=self.viral_config['encounterStages'].get(str(battle['sourceTrainerID']))
            if feed:origin=feed['originStage']
            related=next((p for p in posts.values() if p['battleID']==r['claim'].get('battleID') and p['author']==sender),None)
            epoch=state['epochs'].get(post_id or (related['postID'] if related else ''))
            order=feed['publicationOrder'] if feed else epoch['publicationOrder'] if epoch else 0
            q=policy.quality(mode=r['mode'],source_actor=sender,channel=source.get('channel') or 'direct_observation',origin_stage=origin,campaign_distance=policy.distance(self.viral_config,origin,actor),path=feed['socialPath'] if feed else [actor] if r['mode']=='direct' else None,reason=feed['reason'] if feed else None,publication_order=order,latest_order=latest,original_source_actor=self._original_origin(r)[0],independent_origins=len(origins[dump({k:v for k,v in r['claim'].items() if k not in ('battleID','trainerID')})]))
            rows.append({**r,'evidenceQuality':q})
        rows.sort(key=lambda r:({'CURRENT':0,'RECENT':1,'OLDER':2}[r['evidenceQuality']['currentRelevance']],-r['evidenceQuality']['publicationOrder'],r['memoryID']))
        return {'schemaVersion':1,'actorID':actor,'scope':self.virality_scope(),'authorizedEvidence':rows[:self.viral_config['maxEvidenceContext']],'truncated':len(rows)>self.viral_config['maxEvidenceContext'],'unknowns':['unseen player party','unannounced moves/items','future input','damage RNG'],'strategicInterpretation':None}

    def verify_virality_replay(self):
        # Each epoch is reproducible from its frozen branch-scoped graph and post.
        for e in self._viral_events():
            p=json.loads(e['payload'])
            if e['kind']=='EPOCH':
                post=self.social_state()['posts'].get(p['postID'])
                if not post:raise WorldError('future or foreign post epoch')
                trusted_post={**post,'sourceTrainerID':self.get_battle(post['battleID'])['sourceTrainerID']}
                frozen=legacy_social.empty();scope=p['scope']
                for row in self._events(scope['branch'],scope['cursor'],scope['socialCutoff']):legacy_social.apply(frozen,row)
                if list(frozen['follows'].values()) != p['graph'] or frozen['posts'].get(p['postID']) != post:raise WorldError('epoch outside frozen social history')
                expected=policy.plan(self.viral_config,player=self.player_actor(),post=trusted_post,edges=p['graph'],known_actors=set(self.registry_actor_ids()),post_order=p['publicationOrder'])
                if any(p[k] != v for k,v in expected.items()):raise WorldError('distribution epoch replay mismatch')
        state=self.virality_state()
        for key,r in state['exposures'].items():
            if key not in state['feeds']:raise WorldError('exposure without delivery')
            post=self.social_state()['posts'][r['postID']]
            rows=[self.for_actor(r['recipient'])._find(i) for i in r['memoryIDs']]
            if [json.loads(x['claim']) for x in rows] != post['claims'] or any(x['source_kind']!='post_exposure' or x['source_id']!=post['postID'] or x['sender']!=post['author'] for x in rows):raise WorldError('public exposure scope/provenance mismatch')
        for r in state['intel'].values():
            source=self.for_actor(r['sourceActor'])._find(r['sourceMemoryID']);self._authorize_rocket_reference(r['sourceActor'],r['recipient'],source)
            receipt=self.for_actor(r['recipient'])._find(r['memoryID'])
            if receipt['claim'] != source['claim'] or receipt['parent'] != source['id'] or receipt['channel'] != 'ROCKET_INTEL':raise WorldError('Rocket receipt mismatch')
        return digest(state)


class ViralityStore(ViralityMixin,SocialStore):
    """Host fixture / accepted SOCIAL campaign writer."""


class ViralityPuppeteerStore(ViralityMixin,PuppeteerStore):
    """Accepted mandatory recap campaign writer; inference remains disabled."""


class ViralitySocialActor(SocialActor):
    """Actor-bound compatibility facade. No free actor/query parameters."""
    def __init__(self,store,*args):
        super().__init__(store,*args);self.__viral=store
    def feed_metadata(self):
        self._validate();rows={r['postID']:r for r in super().feed_metadata()}
        posts=self.__viral.social_state()['posts']
        for f in self.__viral.public_feed(self._actor):
            rows[f['postID']]={'postID':f['postID'],'author':posts[f['postID']]['author'],'seen':f['seen'],'channel':'pokebook'}
        return [rows[k] for k in sorted(rows)][:32]
    def read_post(self,post_id):
        self._validate()
        if dump([self._actor,post_id]) in self.__viral.virality_state()['exposures']:
            return self.__viral.read_public_post(self._actor,post_id)
        return super().read_post(post_id)
