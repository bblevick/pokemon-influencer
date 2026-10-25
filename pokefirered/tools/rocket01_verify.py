#!/usr/bin/env python3
"""Offline audit of retained actual ROCKET-01 evidence; never generates history."""
import argparse, json, sqlite3, re
from collections import Counter
from pathlib import Path
from rocket01 import generic
from vertical_slice01_viewer import METHODS
from world.store import WorldError, dump
E=generic.E; P=generic.PRIVATE
MEMBER='trainer:fr:trainer:0352'; LEADER='trainer:fr:trainer:0348'
def read(name): return json.loads((E/name).read_text())
def records(w,actor):
    out=[];after=0
    while True:
        page=w.for_actor(actor).records(after=after,limit=256);out+=page['records']
        if not page['hasMore']:return out
        after=out[-1]['memoryCursor']
def hashes(w):return {m:getattr(w,m)() for m in METHODS}
def save(path):return generic.save_identity(path)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--clone-name',default='rollback-audit');parser.add_argument('--output-subdir');options=parser.parse_args()
    if not re.fullmatch('[a-z0-9-]{1,32}',options.clone_name):raise ValueError('bounded private clone name')
    if options.output_subdir and not re.fullmatch('[a-z0-9-]{1,32}',options.output_subdir):raise ValueError('bounded evidence subdirectory')
    output=E/options.output_subdir if options.output_subdir else E
    output.mkdir(exist_ok=True)
    cfg=json.loads((P/'launch.json').read_text()); retained=read('post-rocket-pair.json')
    post=next(p for p in retained['social']['posts'].values() if p['author']==MEMBER)
    battle=post['battleID'];public={dump(c) for c in post['claims']}
    cp=retained['checkpoint'];results={}
    with generic.open_store(cfg['database']) as w:
        direct=[r for r in records(w,MEMBER) if r['mode']=='direct' and r['claim'].get('battleID')==battle]
        intel=[r for r in records(w,LEADER) if r['source'].get('channel')=='ROCKET_INTEL' and r['claim'].get('battleID')==battle]
        byid={r['memoryID']:r for r in direct}
        assert len(direct)==47 and {r['source']['parentMemoryID'] for r in intel}==set(byid) and len(intel)==len(direct)
        for r in intel:
            assert r['claim']==byid[r['source']['parentMemoryID']]['claim'] and r['mode']=='delivered' and r['source']['sender']==MEMBER
            assert w.for_actor(LEADER).provenance(r['memoryID'])[1]['actorID']==MEMBER
        intel_times=[w._one('SELECT created_at FROM memory_evidence WHERE id=?',(r['memoryID'],))['created_at'] for r in intel]
        first_hermes=read('requests.json')['attempts'][12]['startedAtUnix']
        assert max(intel_times)<first_hermes and all(r['worldCursor']==443 for r in intel)
        results['automaticPrivateTiming']={'lastReceiptCreatedAtUnix':max(intel_times),'firstHermesPOSTAtUnix':first_hermes,'allDeliveryWorldCursors':443,'committedBeforeAnyHermesPOST':True}
        semantics={dump(r['claim']) for r in direct};assert public<=semantics
        epoch=retained['virality']['epochs'][post['postID']]
        exposures=[r for r in retained['virality']['exposures'].values() if r['postID']==post['postID']]
        ordinary=next(r['recipient'] for r in exposures if r['reason']=='ordinary_discovery')
        recipient_records={}
        for actor in w.viral_config['profiles']:
            rs=[r for r in records(w,actor) if r['claim'].get('battleID')==battle]
            if actor not in (MEMBER,LEADER):assert all(r['source'].get('channel')!='ROCKET_INTEL' for r in rs)
            reported=[r for r in rs if r['source'].get('channel')=='pokebook']
            assert {dump(r['claim']) for r in reported}<=public
            if reported:recipient_records[actor]=[r['memoryID'] for r in reported]
        known={dump(r['claim']) for r in records(w,ordinary) if r['source'].get('channel')=='pokebook' and r['claim'].get('battleID')==battle}
        assert known==public and epoch['prominence']=='ordinary' and epoch['followerCount']==5
        results.update(directReceiptCount=len(direct),distinctDirectClaims=len(semantics),publicClaimCount=len(public),privateReceiptCount=len(intel),ordinaryRecipient=ordinary,publicRecipients=recipient_records,publicReach={k:epoch[k] for k in ('prominence','followerCount','originStage','reachBand','reach')},deliveryReasons=dict(Counter(r['reason'] for r in exposures)),sameClaimExactProvenance=True,nonRocketPrivateDenial=True,publicClaimsSubset=True)
        matrix=[]
        for key in sorted(semantics):
            claim=json.loads(key);matrix.append({'claim':claim,'gruntDirect':True,'publicPost':key in public,'ordinaryRecipient':key in known,'rocketLeadership':True,'directReceiptIDs':[r['memoryID'] for r in direct if dump(r['claim'])==key],'privateReceiptIDs':[r['memoryID'] for r in intel if dump(r['claim'])==key]})
        matrix.append({'claim':'unseen party / unrevealed moves / hidden stats / RNG / unsupported items','gruntDirect':False,'publicPost':False,'ordinaryRecipient':False,'rocketLeadership':False,'basis':'source-backed supported claim schemas and actor-scoped projection; no omniscient read'})
        results['matrix']=matrix
        scope=w.virality_scope()
    target=P/(options.clone_name+'.sqlite3')
    if target.exists():raise ValueError('refuse overwrite rollback evidence')
    src=sqlite3.connect('file:'+cfg['database']+'?mode=ro',uri=True);dst=sqlite3.connect(target);src.backup(dst);dst.close();src.close()
    rollback=[]
    with generic.open_store(target) as w:
        # A scheduler tick may legitimately advance tick bookkeeping. Exactly-once
        # concerns delivery identities, not the hash of all scheduler state.
        before_intel=w.virality_state()['intel'];w.advance_social('battle_completion')
        assert w.virality_state()['intel']==before_intel
        results['automaticRetryNoDuplicate']=True
        for name in ('pre-rocket.sav','before-rocket-pair.sav'):
            w.restore(save(P/name))
            assert not any(r['claim'].get('battleID')==battle for actor in (MEMBER,LEADER) for r in records(w,actor))
            assert post['postID'] not in w.social_state()['posts'] and not w.virality_state()['intel']
            denied=False
            try:w.advance_social('battle_completion',expected_scope=scope)
            except WorldError:denied=True
            assert denied;rollback.append({'save':name,'futureObservationsPostIntelAbsent':True,'lateDeliveryScopeDenied':True})
        w.restore(save(P/'post-rocket-pair.sav'));assert hashes(w)==retained['hashes']
    results['rollback']=rollback;results['postRestoreSevenHashesExact']=True
    lifecycle=[r for r in retained['lifecycle'] if r['session']==1929702381]
    grouped={n:[r for r in lifecycle if r['nativeRequest']==n] for n in sorted({r['nativeRequest'] for r in lifecycle})}
    assert len(grouped)==11 and all(rows[-1]['stage']=='EXECUTED' and rows[-1]['source']=='mercury' and not rows[-1]['fallbackReason'] for rows in grouped.values())
    results['liveDecisionDispositions']={str(n):{'stages':[r['stage'] for r in rows],'selected':rows[-1]['nativeSelected'],'phase':rows[-1]['phase'],'note':'canonical action resolution; native effects may be prevented by faint/sleep'} for n,rows in grouped.items()}
    failure=read('hermes-failure.json');invalid=[]
    for request in failure['requests']:
        for choice in request['response'].get('choices',[]):
            for tool in choice['message'].get('tool_calls',[]) or []:
                fn=tool['function']
                if fn['name']=='submit_recap_and_memory_result':
                    args=json.loads(fn['arguments']);assert 'schemaVersion' not in args['result'];invalid.append({'attempt':request['liveAttempt'],'missingRequiredField':'result.schemaVersion','runtimeRejected':True})
    assert len(invalid)==3
    obligation=next(o for o in retained['puppeteer']['obligations'].values() if o['battleID']==battle)
    assert obligation['outcome']['producer']=='deterministic_fallback'
    ledger=read('requests.json');assert ledger['closed']
    additional=len(ledger['attempts'])-16
    assert (additional==0 or ledger.get('rocketQualificationAuthorization')) and 0<=additional<=4
    if additional and not options.output_subdir:raise ValueError('disposition audits must preserve original evidence in a separate subdirectory')
    results['inference']={'attempts':len(ledger['attempts']),'originalAttempts':16,'newQualificationAttempts':additional,'roles':dict(Counter(a['role'] for a in ledger['attempts'])),'closed':True,'hermesInvalidSubmissions':invalid,'publicProducer':'deterministic_fallback','historicalRocketLiveHermesAccepted':False}
    if (E/'post-rocket-reloaded.json').exists():
        fresh=read('post-rocket-reloaded.json')
        assert fresh['hashes']==retained['hashes'] and fresh['memos']==retained['memos'] and fresh['decisions']==retained['decisions'] and fresh['virality']['intel']==retained['virality']['intel']
        assert [a['requestHash'] for a in fresh['ledger']['attempts']]==[a['requestHash'] for a in retained['ledger']['attempts']]
        results['freshOfflineContinue']={'evidence':'post-rocket-reloaded.json','nativeFieldScreenshot':'evidence/private/rocket01/rocket-reload-field.png','sameCheckpointID':fresh['checkpoint']['id']==cp['id'],'sevenHashesExact':True,'sameMemoAndLocks':True,'samePrivateReceiptIDs':True,'noNewInferenceAttempts':True}
    results['nativeViewer']=read('rocket-viewer-proof.json')
    if (E/'rocket-reloaded-viewer-proof.json').exists():results['reloadedNativeViewer']=read('rocket-reloaded-viewer-proof.json')
    results['status']='BLOCKED_LIVE_HERMES';results['checkpoint']=cp
    results['RAM']=read('native-memory.json')
    (output/'observation-matrix.json').write_text(json.dumps(matrix,indent=2)+'\n')
    memo=next(m for m in retained['memos'] if m['actor']==MEMBER)
    trace={'startingPair':read('starting-pair.json'),'strategy':memo,'preparationEvidence':'post-rocket-pair.json#decisions','battleID':battle,'terminalEventID':obligation['endEventID'],'directReceiptIDs':list(byid),'recapObligationID':obligation['obligationID'],'recapOutcome':obligation['outcome'],'publicPostID':post['postID'],'publicExposureIDs':[r['exposureID'] for r in exposures],'privateDeliveries':intel,'leaderPreview':'post-rocket-pair.json#leadershipStrategyKnowledgePreview','pairedSave':cp,'freshOfflineContinue':results.get('freshOfflineContinue'),'status':results['status']}
    (output/'golden-causal-trace.json').write_text(json.dumps(trace,indent=2)+'\n')
    (output/'verification.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({'status':results['status'],'direct':len(direct),'private':len(intel),'public':len(public),'rollback':True,'decisions':len(grouped)}))
if __name__=='__main__':main()
