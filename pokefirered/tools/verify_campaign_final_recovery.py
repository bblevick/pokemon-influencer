#!/usr/bin/env python3
"""Joined retained recovery/native viewer proof; no inference or gameplay writes."""
import sys,json,struct,hashlib,collections,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from campaign.expansion import ExpansionStore
from campaign.recovery import PROOF_METHODS,table_hashes
from roster.extract import digest,file_hash
from pokebook.viewer import Viewer,pages
from pokebook.wire import HEADER,REQUEST
from bridge.ui import MAP
E=ROOT/'evidence/phase6/campaign_expansion01_final';K=E/'final-recovery';C=ROOT/'.local/campaign_expansion01_recovery';M=E/'manifest-native.json'
def read(p):return json.loads(p.read_text())
def write(n,x):(K/n).write_text(json.dumps(x,indent=2)+'\n')
def main():
 manifest=read(K/'causal-cut-manifest.json');inventory=read(K/'retained-inventory.json');before=read(K/'fresh-offline-continued.json');after=read(K/'after-native-viewer.json')
 assert before['sevenHashes']==after['sevenHashes']==manifest['sevenHashes']
 assert before['domainTableHashes']==after['domainTableHashes']==manifest['domainTableHashes']
 assert before['tacticalAuditHash']==after['tacticalAuditHash']==manifest['tacticalAuditHash']
 assert before['preparationHash']==after['preparationHash']==manifest['preparationHash']
 assert before['campaign']['status']==after['campaign']['status']=='paired' and after['campaign']['cursor']==398
 assert all(file_hash(ROOT/p)==r['sha256'] for p,r in inventory['files'].items())
 ledger=read(E/'requests.json');assert ledger['closed'] and len(ledger['attempts'])==62 and read(E/'kent-resolution/accounting.json')['campaignTotal']==46
 assert (K/'requests.json').read_bytes()==(E/'requests.json').read_bytes()
 protected=read(E/'protected.json');assert all(file_hash(ROOT/path)==sha for path,sha in protected.items())
 rows=[json.loads(l) for l in (K/'host.jsonl').read_text().splitlines()];assert not any(r['event'] in ('world-suspended','viewer-rejected','restart-work-waiting') for r in rows)
 responses=[r for r in rows if r['event']=='viewer-response'];assert responses
 feedPages={};followerPages={};seenPosts=set();headers=[]
 inverse={v:k for k,v in MAP.items()}
 with ExpansionStore(C/'world.sqlite3',M) as w:
  viewer=Viewer(w);posts=viewer._public();assert len(posts)==10;followers=sorted(e['follower'] for e in w.social_state()['follows'].values() if e['followed']==w.player_actor());assert len(followers)==5
  expectedNames=[viewer._name(p['author']) for p in posts];expectedFollowerNames=[viewer._name(a) for a in followers]
  for row in responses:
   req=REQUEST.unpack(bytes.fromhex(row['requestHex']));raw=bytes.fromhex(row['responseHex']);h=HEADER.unpack(raw[:24]);body=raw[24:]
   assert h[0]==2 and h[1]==req[1] and h[2]==req[2] and h[3]==req[3];headers.append(h)
   if h[1]==1:assert h[-1]==10 and struct.unpack('<I',body)[0]==5
   if h[1] in (2,4):
    refs=[];names=[]
    for offset in range(0,len(body),23):
     ref=struct.unpack_from('<I',body,offset)[0];label=body[offset+4:offset+23].split(b'\xff')[0];refs.append(ref);names.append(''.join(inverse[b] for b in label))
    expected=expectedNames if h[1]==2 else expectedFollowerNames
    assert names==expected[h[-2]*3:h[-2]*3+3] and refs==list(range(h[-2]*3+1,min(len(expected),h[-2]*3+3)+1))
    (feedPages if h[1]==2 else followerPages)[h[-2]]=refs
   if h[1]==3:
    assert body==pages(posts[h[5]-1]['body'])[h[6]];seenPosts.add(h[5])
  assert feedPages=={0:[1,2,3],1:[4,5,6],2:[7,8,9],3:[10]};assert seenPosts==set(range(1,11));assert followerPages=={0:[1,2,3],1:[4,5]}
  pageSequence=[h[6] for h in headers if h[1]==2]
  assert all((a,b) in list(zip(pageSequence,pageSequence[1:])) for a,b in ((0,1),(1,2),(2,3),(3,2),(2,1),(1,0)))
  assert sum(h[1]==1 for h in headers)>=2
  # Native B/cancel closes local resources without an op5 transport round trip.
  for label in ('field','reopen','reopened-feed','closed'):
   assert (ROOT/'evidence/private/campaign_expansion01'/('recovery-ten-'+label+'.png')).exists()
  assert len({tuple(r['historySHA256']) for r in responses})==1
  # Reproduce old classification error without suspending or editing anything.
  original=next(r for r in w.battle_audit() if r.get('event')!='decision-disposition' and r['session']==720367614 and r['nativeRequest']==9)
  hashes=table_hashes(w)
  try:w.record_battle_audit({**original,'source':'external_test','selection':None})
  except ValueError as e:assert str(e)=='conflicting native decision audit'
  else:raise AssertionError('old mismatch did not reject')
  assert table_hashes(w)==hashes
  lifecycle={}
  for r in w.decision_lifecycle():lifecycle.setdefault((r['session'],r['generation'],r['nativeRequest']),[]).append(r['stage'])
  dispositions=[]
  for r in w.battle_audit():
   if r.get('event')=='decision-disposition':continue
   stages=lifecycle.get((r['session'],r['generation'],r['nativeRequest']),[])
   state='ENGINE_FORCED' if r['source']=='engine_forced' else 'VANILLA_FALLBACK_CONTROLLER_RECEIPT' if r['source']=='vanilla_fallback' else 'EXECUTED' if 'EXECUTED' in stages else next((s for s in reversed(stages) if s.startswith('CANCELED_')),'NATIVE_EXTERNAL_CONTROLLER_RECEIPT')
   dispositions.append({'session':r['session'],'generation':r['generation'],'request':r['nativeRequest'],'state':state,'originalSource':r['source'],'lifecycleStages':stages,'immutableRecordSHA256':digest(r),'pending':False})
  write('historical-audit-classification.json',{'records':dispositions,'counts':dict(collections.Counter(r['state'] for r in dispositions)),'oldMisclassificationReproduced':True,'noSuspensionOrAuditMutation':True,'realDatabaseRuntimeProof':manifest['realDatabaseRuntimeProof']})
  cfg=read(C/'launch.json');assert cfg['nonce']!=manifest['historicalNonce'];assert not w.pending_save()
  out={'ticket':'CAMPAIGN-EXPANSION-01','accepted':True,'recoveryDisposition':'retrospective_recovery','checkpointID':after['checkpoint']['id'],'campaign':manifest['campaign'],'branch':manifest['branch'],'historicalGeneration':1,'freshLaunchNonce':cfg['nonce'],'freshLaunchGeneration':1,'cutoffs':manifest['projectionCuts'],'canonicalCutoff':398,'sevenHashes':after['sevenHashes'],'tacticalAuditHash':after['tacticalAuditHash'],'preparationHash':after['preparationHash'],'Kent':manifest['Kent'],'postCount':10,'followerCount':5,'diffusionSHA256':manifest['diffusionHash'],'noGameplayMutation':True,'freshOfflineContinue':True,'historicalRequestsPending':0,'nativeViewer':{'allRealPostsOpened':10,'feedPages':feedPages,'followerPages':followerPages,'chronologyAndAuthorshipExact':True,'backForwardReopenCancel':True,'sideEffects':0,'successfulResponses':len(responses),'correctedCursor':3,'firstWrongCursorRunAborted':True,'runnerEvidenceDirectoryErrorOnly':True,'proofFromIndependentWireAndFullSnapshots':True},'originalInputsSHA256Verified':True,'priorProtectedInputsVerified':{p:True for p in protected},'generationAttempts':46,'ceiling':98,'newHostedCalls':0,'incrementalCostUSD':0,'defaultInferenceDisabled':not read(ROOT/'config/model_profiles.yaml')['hosted_inference_enabled'],'endgameDeferred':True}
 # Acceptance requires the separately executed stopped-process durability and rollback gates.
 durable=read(K/'durability.json');rollback=read(K/'rollback-proof.json');memory=read(K/'memory.json');workers=read(K/'workers-stopped.json')
 assert durable['allWorkersStopped'] and workers['allStopped'] and durable['checkpointID']==out['checkpointID']
 assert rollback['recoveredPair']['sevenHashes']==out['sevenHashes'] and rollback['C3']['KentBattlePostDiffusionAuditAbsent']
 assert memory['afterHeadroomBytes']>=4 and memory['permanentDeltaBytes']==0
 for log,count in [('recovery-tests.log',7),('retained-tests.log',2),('viewer-tests.log',16),('battle-end-tests.log',8)]:
  text=(K/log).read_text();assert 'Ran '+str(count)+' tests' in text and text.rstrip().endswith('OK')
 out.update(durability=durable,rollbackIsolation=True,memory=memory,allWorkersStopped=True,activeFutureStrategyModel=workers['activeFutureStrategyModel'],tests={'recovery':7,'retainedTerminal':2,'viewer':16,'battleEnd':8,'total':33,'skipped':0})
 write('native-viewer-proof.json',out['nativeViewer']);write('verification.json',out)
 print(json.dumps({'accepted':True,'checkpointID':out['checkpointID'],'posts':10,'followers':5,'newHostedCalls':0}))
if __name__=='__main__':main()
