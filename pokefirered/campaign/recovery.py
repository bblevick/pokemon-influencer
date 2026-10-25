"""Exceptional retained-battery pairing: evidence validation, never gameplay repair.

No providers are imported or invoked. Call only on verified writable copies.
The original suspension/audits and the absence of an ordinary save intent remain
recorded in an immutable retrospective-pair manifest. Normal managed saves remain
preferred. Actor capabilities are not issued for suspended forensic inspection.
"""
import collections, hashlib, json, struct, time
from pathlib import Path
from world.store import WorldError, dump
from world.saves import fingerprint
from memory.store import ActorView, VERSION
from roster.extract import digest, file_hash
from battle.lifecycle import TERMINAL

VIEWS=('memory_view','social_view','puppeteer_view','prep_view','strategy_view',
       'preparation_decision_view','virality_view','battle_audit_view')
PROOF_METHODS=('verify_replay','verify_memory_replay','verify_social_replay',
 'verify_puppeteer_replay','verify_strategy_replay','verify_decision_replay','verify_virality_replay')
DOMAIN_TABLES=('events','observations','deliveries','streams','branches','projection',
 'memory_evidence','memory_sources','memory_actors','memory_branches','social_log',
 'social_branches','puppeteer_log','puppeteer_branches','puppeteer_audit','prep_log',
 'prep_branches','strategy_log','strategy_branches','preparation_decision_log',
 'preparation_decision_branches','battle_decision_audit','battle_audit_branches',
 'virality_log','virality_branches','strategy_jobs','puppeteer_jobs','preparation_decision_jobs')

def table_hashes(w):
    return {t:digest([dict(r) for r in w.db.execute('SELECT * FROM "'+t+'" ORDER BY rowid')]) for t in DOMAIN_TABLES}

def forensic_memory_hash(w):
    """Same bounded actor projection from branch-filtered rows, without grants.

    Forensic output stays host-owned evidence. It cannot run model tools or
    unsuspend a campaign; live capability validation remains unchanged.
    """
    c=w.campaign();v=dict(w._one('SELECT * FROM memory_view'));contexts={}
    for actor in sorted(w.registry_actor_ids()):
        rows=w._rows(actor,c['id'],c['active_branch'],c['cursor'],v['cutoff'],0,257)
        groups={}
        for row in rows[:256]:
            r=ActorView._public(row);post=r['source'].get('postID');key=dump([r['mode'],r['claim'],r['source']['sender'],post])
            g=groups.setdefault(key,{'mode':r['mode'],'claim':r['claim'],'sender':r['source']['sender'],'occurrencesInWindow':0,'evidenceIDs':[]})
            if post:g['attribution']={'kind':'reported_post','author':r['source']['sender'],'postID':post,'channel':'pokebook'}
            g['occurrencesInWindow']+=1
            if len(g['evidenceIDs'])<8:g['evidenceIDs'].append(r['memoryID'])
        contexts[actor]={'schemaVersion':VERSION,'actor':w.get_actor(actor),'campaignID':c['id'],'branchID':c['active_branch'],'worldCursor':c['cursor'],'memoryCutoff':v['cutoff'],'directObservations':[g for _,g in sorted(groups.items()) if g['mode']=='direct'],'deliveries':[g for _,g in sorted(groups.items()) if g['mode']=='delivered'],'truncated':len(rows)>256}
    return digest(contexts)

def forensic_hashes(w):
    result={m:getattr(w,m)() for m in PROOF_METHODS if m not in ('verify_memory_replay','verify_virality_replay')}
    result['verify_memory_replay']=forensic_memory_hash(w)
    result['verify_virality_replay']=digest(w.virality_state())
    return result

def native_state(path,layout):
    data=Path(path).read_bytes();s=fingerprint(data,layout['sectionSizes']);sections={}
    for i in range(s.slot*14,(s.slot+1)*14):
        sec=data[i*4096:(i+1)*4096];sid=struct.unpack_from('<H',sec,4084)[0];sections[sid]=sec[:layout['sectionSizes'][sid]]
    block=b''.join(sections[i] for i in (1,2,3,4));off=layout['flagsOffset']
    # Exact pinned include/global.h SaveBlock1 pos0/location4/partyCount0x34.
    return s,{'position':list(struct.unpack_from('<hh',block,0)),
      'mapGroup':block[4],'mapNum':block[5],'partyCount':block[0x34],
      'partyBytesSHA256':hashlib.sha256(block[0x38:0x290]).hexdigest(),
      'inventoryBytesSHA256':hashlib.sha256(block[0x290:0x5f8]).hexdigest(),
      'trainerFlags':{str(t):bool(block[off+(0x500+t)//8]&(1<<((0x500+t)&7))) for t in range(1,743)},
      'boulderFlags':{str(n):bool(block[off+n//8]&(1<<(n&7))) for n in (0x4b0,0x820)}}

def require(ok,reason):
    if not ok:raise WorldError('recovery inadmissible: '+reason)

def prove(w,*,battery,prior_battery,receipt,launch,settled,lock,inventory,manifest_path,layout):
    c=w.campaign();identity,native=native_state(battery,layout);prior,oldnative=native_state(prior_battery,layout)
    manifest=json.loads(Path(manifest_path).read_text())
    require(c==settled['campaign'] or all(c[k]==settled['campaign'][k] for k in ('id','active_branch','cursor','pending_fork')),'campaign cut differs')
    require(c['status']=='incomplete' and not c['pending_fork'],'expected preserved suspended settled branch')
    require(w.pending_save() is None,'ambiguous pending save intent')
    require(w.compatibility['nativeROM']==manifest['rom_sha256'],'native build compatibility')
    require(file_hash(Path(manifest_path).parents[3]/manifest['rom_path'])==manifest['rom_sha256'],'ROM hash')
    require(identity.counter==(prior.counter+1)&0xffffffff and identity.fingerprint!=prior.fingerprint,'counter/fingerprint lineage')
    cp=w.get_save_checkpoint(prior.fingerprint);require(cp is not None,'previous valid pair')
    require((cp['campaign'],cp['branch'])==(c['id'],c['active_branch']),'previous paired branch')
    l=w._one('SELECT * FROM launches WHERE nonce=?',(receipt['nonce'],));require(l is not None,'launch authority absent')
    require((l['id'],l['campaign'],l['loaded_fingerprint'])==(launch['origin'],c['id'],prior.fingerprint),'save launch does not descend from C3')
    require(receipt['nonce']==launch['nonce'] and receipt['run']==1,'native run identity')
    stream=w._one('SELECT * FROM streams WHERE nonce=? AND run=1',(receipt['nonce'],));require(stream is not None,'stream missing')
    require(stream['launch']==l['id'],'stream origin')
    expected={'event':'savedataUpdated','eventCounter':stream['last'],'ack':stream['last'],'depth':0,'state':0,'drops':0,'counter':identity.counter}
    require(all(receipt.get(k)==v for k,v in expected.items()),'native durable save barrier')
    deliveries=[dict(r) for r in w.db.execute('SELECT * FROM deliveries WHERE launch=? AND run=1 ORDER BY sequence',(l['id'],))]
    require([r['sequence'] for r in deliveries]==list(range(1,stream['last']+1)),'noncontiguous ingested stream')
    streamstate=json.loads(stream['state']);require(all(b['ended'] and not b['incomplete'] for b in streamstate.values()),'unfinished native stream battle')
    world=w.state();require(world==w.replay(),'canonical replay mismatch');require(all(b['ended'] for b in world['battles'].values()),'unfinished active battle')
    activeEvents={e['eventID']:e for e in w.get_canonical_events()}
    from bridge.events_wire import Message
    from bridge.events import Consumer
    consumer=Consumer(receipt['nonce'],1,w.tag)
    for d in deliveries:
        msg=Message.decode(bytes.fromhex(d['wire'])[2:]);r,_=consumer.accept(msg)
        require((msg.nonce,msg.generation,msg.sequence)==(receipt['nonce'],1,d['sequence']),'wire identity')
        if d['event']:
            require(d['event'] in activeEvents,'inactive or absent stream event')
            require(activeEvents[d['event']]['record']==r,'wire/canonical record differs')
        else:require(w._one('SELECT id FROM observations WHERE id=?',(d['observation'],)) is not None,'missing observation')
    kent=next(b for b in world['battles'].values() if b['sourceTrainerID']==108)
    require(kent['defeated'] and kent['outcome']==1 and kent['endEvent'] in activeEvents,'Kent terminal event missing')
    require(activeEvents[kent['endEvent']]['cursor']==c['cursor'],'world advanced after Kent terminal cut')
    require(all(native['trainerFlags'][str(b['sourceTrainerID'])] for b in world['battles'].values() if b['sourceTrainerID'] and b['defeated']),'native trainer flags disagree')
    delta={t for t,value in native['trainerFlags'].items() if value!=oldnative['trainerFlags'][t]}
    expectedDelta={str(b['sourceTrainerID']) for b in world['battles'].values() if b['sourceTrainerID'] and b['defeated'] and b['endEvent'] in activeEvents and activeEvents[b['endEvent']]['cursor']>cp['cursor']}
    require(delta==expectedDelta=={'108','118'},'unexplained native trainer flag changes')
    require((native['mapGroup'],native['mapNum'])==(1,1) and native['position']==[7,30],'native saved Mt. Moon position')
    require(native['boulderFlags']==oldnative['boulderFlags'] and all(native['boulderFlags'].values()),'story milestone mismatch')
    hashes=forensic_hashes(w);require(hashes==settled['hashes'],'all seven settled hashes differ')
    require(w.memo_records()==settled['memos'] and w.decision_state()==settled['decisions'],'strategy/preparation differs from settled cut')
    memo=next(m for m in w.memo_records() if m['actor']=='trainer:fr:trainer:0108');require(memo==lock['memo'] and memo['source']=='fallback','Kent fallback changed')
    require(w.decision_state()['commitments'][lock['preparationLock']['opportunityID']]==lock['commitment'],'Kent lock changed')
    audit=w.battle_audit();require(audit==settled['audit'],'audit changed');groups={}
    for r in w.decision_lifecycle():groups.setdefault((r['session'],r['generation'],r['nativeRequest']),[]).append(r)
    require(all(any(r['stage'] in TERMINAL for r in rows) for rows in groups.values()),'nonterminal historical lifecycle')
    executed=[r for r in w.decision_lifecycle() if r['session']==receipt['nonce'] and r['stage']=='EXECUTED']
    require(len(executed)==8 and {r['nativeRequest'] for r in executed}=={1,2,3,4,5,6,7,9},'Kent Mercury execution set')
    nativeAudit=[r for r in audit if r['session']==receipt['nonce'] and r.get('event')!='decision-disposition']
    require(dict(collections.Counter(r['source'] for r in nativeAudit))=={'mercury':8,'engine_forced':1},'Kent native terminal audit')
    social=w.social_state();require(social==settled['social'] and w.puppeteer_state()==settled['puppeteer'] and w.virality_state()==settled['virality'],'social cuts differ')
    posts=list(social['posts'].values());post=next(p for p in posts if p['battleID']==kent['battleID'])
    require(len(posts)==10 and post['author']=='trainer:fr:trainer:0108','retained actual feed')
    followers=[e for e in social['follows'].values() if e['followed']==w.player_actor()];require(len(followers)==5 and sum(e['follower']==post['author'] for e in followers)==1,'follow graph')
    require(all(o['status']=='PUBLISHED' for o in w.puppeteer_state()['obligations'].values()),'unpublished mandatory recap')
    jobRows={t:[dict(r) for r in w.db.execute('SELECT * FROM '+t+' ORDER BY rowid')] for t in ('strategy_jobs','puppeteer_jobs','preparation_decision_jobs')}
    require(all(r['status']=='completed' for rows in jobRows.values() for r in rows),'unterminated durable generation job')
    viral=w.virality_state();epoch=next(e for e in viral['epochs'].values() if e['postID']==post['postID']);require(epoch['followerCount']==5 and epoch['reach']['budget']==12,'Kent district diffusion')
    # Every active exposed public claim must already have exact durable actor receipts.
    exposures=[r for r in viral['exposures'].values() if r['postID']==post['postID']];require(len(exposures)==66,'Kent exposure count')
    for r in exposures:
        rows=[w._one('SELECT * FROM memory_evidence WHERE id=?',(i,)) for i in r['memoryIDs']]
        require(all(x and x['actor']==r['recipient'] and x['source_kind']=='post_exposure' and x['source_id']==post['postID'] and x['sender']==post['author'] for x in rows),'exposure provenance')
        require([json.loads(x['claim']) for x in rows]==post['claims'],'public claim mismatch')
    cuts={t:dict(w._one('SELECT * FROM '+t)) for t in VIEWS}
    require(all(v['campaign']==c['id'] and v['branch']==c['active_branch'] for v in cuts.values()),'projection branch mismatch')
    suspensions=[dict(r) for r in w.db.execute("SELECT * FROM outbox WHERE kind='world_suspended'")]
    require(bool(suspensions) and json.loads(suspensions[-1]['payload'])=={'reason':'conflicting native decision audit'} and w._one('SELECT id FROM outbox ORDER BY rowid DESC')['id']==suspensions[-1]['id'],'different latest suspension cause')
    # Execute the repaired pure lookup on the actual retained audit, and load
    # terminal lifecycle groups through the real runtime with an offline bomb.
    from battle.transport import Handler
    import tempfile
    class NoProvider:
        def decide(self,*a):raise AssertionError('historical inference attempted')
    beforeRuntime=table_hashes(w)
    with tempfile.TemporaryDirectory() as tmp:
        h=Handler(manifest,Path(tmp),provider=NoProvider())
        try:
            for r in nativeAudit:
                incoming={**r,'source':'external_test','selection':None}
                original=h.retained_terminal(w,incoming,1 if r['source']=='mercury' else 3)
                require(original==r,'historical native provenance changed')
            h.recover(w)
            require(not h.pending and not h.awaiting and h.job is None,'historical requests became pending')
            require(table_hashes(w)==beforeRuntime,'historical replay wrote audit/domain state')
        finally:h.close()
    domain=table_hashes(w)
    return {'version':1,'mode':'retrospective recovery; no original managed intent existed','tool':'campaign.recovery/v1',
      'build':manifest['rom_sha256'],'baselineBuild':w.build,'manifestSHA256':file_hash(manifest_path),
      'campaign':c['id'],'branch':c['active_branch'],'generation':1,'historicalNonce':receipt['nonce'],'launchOrigin':l['id'],
      'nativeSave':identity.as_dict(),'nativeBatterySHA256':file_hash(battery),'nativeSourceState':native,
      'priorCheckpoint':dict(cp),'canonicalCutoff':c['cursor'],'projectionCuts':cuts,'sevenHashes':hashes,
      'preparationHash':digest(w.preparation_state()),'tacticalAuditHash':digest(audit),
      'jobOutboxCut':{'jobs':jobRows,'outbox':[dict(r) for r in w.db.execute('SELECT * FROM outbox ORDER BY rowid')]},
      'Kent':{'battleID':kent['battleID'],'terminalEventID':kent['endEvent'],'strategyID':memo['strategyID'],'strategyHash':digest(memo),'strategySource':'fallback','commitmentID':lock['commitment']['commitmentID'],'postID':post['postID'],'executedRequests':[1,2,3,4,5,6,7,9],'engineForcedRequests':[8]},
      'followerCount':5,'postCount':10,'feedCountCorrection':'eight stated in request; ten actual retained posts including Ben/Robin; preserve all',
      'followerGraphHash':digest(followers),'diffusionHash':digest(viral),'receipt':receipt,
      'originalSuspension':suspensions,'domainTableHashes':domain,'immutableInventorySHA256':digest(inventory),
      'admissible':True,'noInferenceRequired':True,'realDatabaseRuntimeProof':{'retainedNativeReceipts':9,'MercuryHistoricalExecuted':8,'engineForced':1,'pendingRequests':0,'auditWrites':0,'providerCalls':0}}

def recover(w,manifest,save):
    """Atomically bind existing projections via the canonical extension chain.

    This API never edits campaign/game truth or synthesizes a save intent.
    A later ordinary restore of the resulting known pair resumes capabilities.
    """
    require(manifest.get('admissible') is True,'manifest not admissible')
    require(manifest['nativeSave']==save.as_dict(),'native identity changed')
    require(manifest['version']==1 and manifest['build']==w.compatibility['nativeROM'] and manifest['baselineBuild']==w.build,'build/recovery version changed')
    exists=w._one("SELECT name FROM sqlite_master WHERE name='retrospective_pairs'")
    if exists:
        old=w._one('SELECT * FROM retrospective_pairs WHERE manifest_sha=?',(digest(manifest),))
        if old:
            require(old['manifest']==dump(manifest),'recovery manifest conflict')
            cp=w.get_save_checkpoint(save.fingerprint)
            require(cp is not None and cp['id']==old['checkpoint'],'recovery checkpoint missing')
            return cp # immutable metadata lookup only; never restore or alter a current branch
    require(table_hashes(w)==manifest['domainTableHashes'],'domain mutated since proof')
    c=w.campaign();require((c['id'],c['active_branch'],c['cursor'])==(manifest['campaign'],manifest['branch'],manifest['canonicalCutoff']),'cut changed')
    require({t:dict(w._one('SELECT * FROM '+t)) for t in VIEWS}==manifest['projectionCuts'],'projection cutoff changed')
    require(forensic_hashes(w)==manifest['sevenHashes'],'projection mismatch')
    before=table_hashes(w);sha=digest(manifest)
    def action():
        w.db.execute('CREATE TABLE IF NOT EXISTS retrospective_pairs(checkpoint TEXT PRIMARY KEY,manifest_sha TEXT UNIQUE NOT NULL,manifest TEXT NOT NULL,created_at REAL NOT NULL)')
        for op in ('UPDATE','DELETE'):w.db.execute('CREATE TRIGGER IF NOT EXISTS immutable_retrospective_pairs_'+op+' BEFORE '+op+" ON retrospective_pairs BEGIN SELECT RAISE(ABORT,'immutable retrospective recovery'); END")
        old=w._one('SELECT * FROM retrospective_pairs WHERE manifest_sha=?',(sha,))
        if old:return w.get_save_checkpoint(save.fingerprint)
        require(w.get_save_checkpoint(save.fingerprint) is None,'save already paired outside this recovery')
        cp=w._checkpoint(c,save,'retrospective_recovery')
        require(table_hashes(w)==before,'checkpoint attempted domain mutation')
        w.db.execute('INSERT INTO retrospective_pairs VALUES(?,?,?,?)',(cp,sha,dump(manifest),time.time()))
        return w.get_save_checkpoint(save.fingerprint)
    cp=w._tx(action);require(table_hashes(w)==before,'recovery altered domain truth')
    return cp
