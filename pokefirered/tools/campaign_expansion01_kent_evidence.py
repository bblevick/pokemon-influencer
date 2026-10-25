#!/usr/bin/env python3
"""Retained Kent closeout receipts; no inference, projection mutation or resume."""
import os
os.environ['POKEINFLUENCER_EXPERIMENT']='campaign_expansion01';os.environ['POKEINFLUENCER_CAMPAIGN_FINAL']='1'
import sys,json,sqlite3,collections,struct,hashlib,subprocess
from pathlib import Path
from campaign_expansion01 import E,PRIVATE,ROOT,save_identity
from campaign.budget import CampaignBudget,attempts_hash
from puppeteer.runtime import cleanup
from roster.extract import file_hash
K=E/'kent-resolution'
def read(n):return json.loads((E/n).read_text())
def write(n,v):(K/n).write_text(json.dumps(v,indent=2)+'\n')
if __name__=='__main__':
 s=read('k-Kent-social-settled.json');before=read('kent-resolution/lock-before.json');cfg=json.loads((PRIVATE/'launch.json').read_text());postID='4c446e1b80369b07b895e0744a60ee31d7d2a3ddb49a4ebf4cd4232e433f95f3'
 trace=[json.loads(l) for l in (E/'causal-trace.jsonl').read_text().splitlines()];job=next(r['result'] for r in trace if r['event']=='hermes-finished' and r['result']['jobID']=='ea1abc9d-60dd-452f-9cdb-ef0fc6275234');assert job['outcome']['producer']=='hermes' and job['outcome']['fallbackReason'] is None
 requests={q['liveAttempt']:q for q in job['requests']};receipts=[]
 with CampaignBudget(E/'requests.json') as b:
  ledger=b.read();prefix=attempts_hash(ledger['attempts'][:52]);assert len(ledger['attempts'])==62
  for a in ledger['attempts'][52:]:
   if a['role']=='battle':
    response=a['response'];scope=a['scope'];assert scope['trainerID']==108 and response['httpStatus']==200 and response['result']['usage']['cost']==0
    done=next(r for r in s['lifecycle'] if r['session']==scope['nonce'] and r['nativeRequest']==scope['request'] and r['stage']=='EXECUTED')
    outcome={'status':'executed','usage':response['result']['usage'],'nativeLifecycleID':done['lifecycleID'],'trainerID':108,'session':scope['nonce'],'nativeRequest':scope['request']}
   elif a['role']=='puppeteer':
    q=requests[a['attempt']];assert q['sha256']==a['requestHash'] and q['response']['usage']['cost']==0
    outcome={'status':'committed_actual_hermes','usage':q['response']['usage'],'jobID':job['jobID'],'postID':postID,'episodeID':job['outcome']['episodeID']}
   else:raise AssertionError('Kent Strategy/preparation forbidden')
   b.finish(a['attempt'],outcome);receipts.append({'attempt':a['attempt'],'role':a['role'],**outcome})
  b.close();ledger=b.read();assert attempts_hash(ledger['attempts'][:52])==prefix
 old=read('accounting.json');totalCost=old['confirmedCostUSD']+sum(r['usage']['cost'] for r in receipts)
 accounting={'closed':True,'historicalBefore98Scope':16,'priorCampaignCalls':36,'KentCalls':10,'KentRoles':{'battle':8,'puppeteer':2,'strategy':0,'preparation':0},'campaignTotal':46,'campaignCeiling':98,'allLedgerRows':62,'unusedAggregateClosed':52,'remainingRolesClosed':{'battle':45,'puppeteer':6,'strategy':1,'preparation':0},'unusedStrategyNotAuthorized':1,'reportedCostUSD':totalCost,'allNewCampaignReceiptsHaveCost':True,'prior52RowsImmutable':True,'KentReceipts':receipts}
 write('accounting.json',accounting)
 db=sqlite3.connect('file:'+cfg['database']+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
 def retained_hash():
  tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
  rows={t:[list(r) for r in db.execute('SELECT * FROM "'+t+'" ORDER BY rowid')] for t in tables}
  return hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
 retainedBefore=retained_hash();c=dict(db.execute('SELECT * FROM campaigns').fetchone());assert c['status']=='incomplete' and c['cursor']==398
 assert db.execute("SELECT COUNT(*) FROM strategy_jobs WHERE status='active'").fetchone()[0]==0
 assert db.execute("SELECT COUNT(*) FROM puppeteer_jobs WHERE status='active'").fetchone()[0]==0
 deliveries=[dict(r) for r in db.execute("SELECT actor,mode,claim,source_kind,source_id,sender,channel FROM memory_evidence WHERE source_id=?",(postID,))];assert len(deliveries)==132
 for r in deliveries:assert r['mode']=='delivered' and r['source_kind']=='post_exposure' and json.loads(r['claim']) in s['social']['posts'][postID]['claims']
 cleaned=cleanup(job['runtimeHome'],dry_run=False) if Path(job['runtimeHome']).exists() else {'alreadyRemoved':job['runtimeHome']}
 assert retainedBefore==retained_hash();write('cleanup.json',{'runtime':cleaned,'allDatabaseRowsSHA256Unchanged':retainedBefore,'durableEpisodeID':job['outcome']['episodeID'],'durableEpisodeInRetainedProjection':job['outcome']['episodeID'] in s['puppeteer']['episodes'],'statusNotChanged':c['status']})
 oldmemo=next(m for m in s['memos'] if m['actor']=='trainer:fr:trainer:0108');assert oldmemo==before['memo'];assert s['decisions']['commitments'][before['preparationLock']['opportunityID']]==before['commitment']
 audit=[r for r in s['audit'] if r.get('session')==720367614 and r.get('event')!='decision-disposition'];assert dict(collections.Counter(r['source'] for r in audit))=={'mercury':8,'engine_forced':1}
 retained=next(r for r in audit if r['nativeRequest']==9);incoming={**retained,'source':'external_test','selection':None};fields=('nativeHash','battle','turn','phase','battler','fallbackReason','nativeSelected');assert all(retained[f]==incoming[f] for f in fields)
 write('restart-conflict.json',{'classification':'host-mode relabeling of identical retained native receipt','nonce':720367614,'nativeRequest':9,'originalSource':'mercury','offlineIncomingSource':'external_test','allEngineFieldsIdentical':True,'engineFields':{f:retained[f] for f in fields},'originalAudit':retained,'nativeReadOnlyEvidence':'emulator.jsonl event retained-terminal-proof: state7/source1, same hash/selection','currentCampaignStatus':c['status'],'automaticResumeAvailable':False,'currentStateWasNotUnsuspendedOrRolledBack':True,'futureDuplicateHandlingFixed':True,'nativeFutureRestartProofUnrun':True})
 layout=json.loads((ROOT/'config/prep_save_layout.json').read_text());path=PRIVATE/'Kent-victory-UNPAIRED.sav';data=path.read_bytes();identity=save_identity(path);sections={}
 for i in range(identity.slot*14,(identity.slot+1)*14):
  sec=data[i*4096:(i+1)*4096];sid=struct.unpack_from('<H',sec,4084)[0];sections[sid]=sec[:layout['sectionSizes'][sid]]
 block=b''.join(sections[i] for i in (1,2,3,4));flags={str(t):bool(block[layout['flagsOffset']+(0x500+t)//8]&(1<<((0x500+t)&7))) for t in (89,102,105,106,107,108,117,118,414)};assert all(flags.values())
 epoch=next(e for e in s['virality']['epochs'].values() if e['postID']==postID);assert epoch['followerCount']==5 and epoch['originStage']=='mtmoon' and epoch['reach']['budget']==12
 write('Kent-social-proof.json',{'battle':next(b for b in s['world']['battles'].values() if b['sourceTrainerID']==108),'HermesOutcome':job['outcome'],'post':s['social']['posts'][postID],'followersBefore':4,'followersAfter':5,'virality':epoch,'publicReportedRowsSourceMatched':132,'publicClaimsOnly':True,'noPrivateMoveDeliveredViaThisPost':True,'KentMemoUnchanged':True,'KentCommitmentUnchanged':True,'nativeSources':dict(collections.Counter(r['source'] for r in audit)),'liveExecuted':8,'trainerFlagsInUnpairedNativeSave':flags,'nativeSavePaired':False})
 protected={p:file_hash(ROOT/p)==h for p,h in read('protected.json').items()};assert all(protected.values())
 out={'ticket':'CAMPAIGN-EXPANSION-01','accepted':False,'status':'STILL BLOCKED: host suspended on retained terminal provenance replay; final feed/pair/reload unrun','completedSubgates':['real C3 restore, no Kent reroll','real8/current9 plus explicit9/12-post native pagination fixtures','Mt. Moon native transition','Kent actual native victory,8 live Mercury executions,1 engine-forced bypass','real Hermes recap,once-only follow,5-follower district diffusion'],'unrun':['full real10-post native feed/follower browsing','validated final pairing','fresh offline final Continue','native proof of retained-receipt restart fix'],'noKentStrategyOrPreparationCalls':True,'noNewInferenceNeededToRepairRemainingGate':True,'accounting':accounting,'nearestPairedSave':str(PRIVATE/'C3-james-blocked.sav'),'unpairedVictory':read('kent-resolution/unpaired-victory-preservation.json'),'retainedDatabaseStatus':c['status'],'protectedHashesUnchanged':protected,'memory':read('kent-resolution/memory.json'),'allWorkersStopped':True,'defaultInferenceDisabled':not json.loads((ROOT/'config/model_profiles.yaml').read_text())['hosted_inference_enabled'],'endgameDeferred':True}
 write('verification.json',out);db.close();print(json.dumps({'accepted':False,'status':out['status'],'campaignCalls':46,'KentExecuted':8,'posts':10,'followers':5,'costUSD':totalCost}))
