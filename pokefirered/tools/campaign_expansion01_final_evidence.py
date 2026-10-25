#!/usr/bin/env python3
"""Close retained partial campaign receipts. No provider or game writes."""
import os
os.environ['POKEINFLUENCER_EXPERIMENT']='campaign_expansion01'
os.environ['POKEINFLUENCER_CAMPAIGN_FINAL']='1'
import json,collections,struct
from pathlib import Path
from campaign_expansion01 import ROOT,E,PRIVATE,open_store,save_identity
from campaign.budget import CampaignBudget,attempts_hash
from puppeteer.runtime import cleanup
from roster.extract import file_hash
from vertical_slice01_viewer import METHODS

def read(name):return json.loads((E/name).read_text())
def write(name,value):(E/name).write_text(json.dumps(value,indent=2)+'\n')
if __name__=='__main__':
 before=read('C3-james-blocked.json');restored=read('C3-offline-restored.json');after=read('C3-after-viewer.json')
 assert before['hashes']==restored['hashes']==after['hashes']
 assert before['ledger']['attempts']==restored['ledger']['attempts']==after['ledger']['attempts']
 assert restored['ledger']==after['ledger']
 trace=[json.loads(x) for x in (E/'causal-trace.jsonl').read_text().splitlines()]
 jobs=[r['result'] for r in trace if r['event']=='hermes-finished']
 hr={q['liveAttempt']:(j,q) for j in jobs for q in j['requests']}
 receipts=[]
 with CampaignBudget(E/'requests.json') as budget:
  initial=budget.read();prefix=attempts_hash(initial['attempts'][:16])
  for a in initial['attempts'][16:]:
   n=a['attempt'];response=a.get('response');result={'evidence':'retained provider response and source-authoritative native/domain receipts'}
   if a['role']=='battle':
    assert response['httpStatus']==200 and response['result']['usage']['cost']==0
    scope=a['scope'];rows=[r for r in after['lifecycle'] if r['session']==scope['nonce'] and r['nativeRequest']==scope['request']]
    executed=next((r for r in rows if r['stage']=='EXECUTED'),None)
    result.update(usage=response['result']['usage'],trainerID=scope['trainerID'],nativeRequest=scope['request'],session=scope['nonce'])
    if executed:result.update(status='executed',nativeLifecycleID=executed['lifecycleID'])
    else:
     assert scope['nonce']==1738084968 and scope['request'] in (6,12)
     assert response['result']['answers']['preparation']['choice'].endswith(':REPLACE:3')
     emitted=next(r for r in rows if r['stage']=='CONTROLLER_EMITTED')
     canceled=next(r for r in rows if r['stage']=='CANCELED_BATTLE_ENDED')
     next_packet=read(f"turn-{scope['nonce']}-{scope['request']+1}.json")
     assert '"activeSlot": 3' in next_packet['state'] and next_packet['scope']['phase']=='NORMAL_TURN'
     result.update(status='replacement_applied_confirmed_by_next_native_snapshot',nativeLifecycleStage='CANCELED_BATTLE_ENDED',emittedLifecycleID=emitted['lifecycleID'],terminalLifecycleID=canceled['lifecycleID'],confirmationPacket=f"turn-{scope['nonce']}-{scope['request']+1}.json",resolvedActionReceiptAbsent=True)
   elif a['role']=='strategy':
    assert response['httpStatus']==200 and response['usage']['cost']==0
    memo=next(m for m in after['memos'] if m['diagnostics'].get('attempt')==n)
    assert memo['source']=='model' and memo['actor']=='trainer:fr:trainer:0107'
    result.update(status='committed_model_memo',usage=response['usage'],strategyID=memo['strategyID'],model=response['resolvedModel'],provider=response['servingProvider'])
   elif a['role']=='puppeteer':
    job,q=hr[n];assert q['sha256']==a['requestHash'] and q['response']['usage']['cost']==0 and job['outcome']['producer']=='hermes'
    result.update(status='committed_actual_hermes',usage=q['response']['usage'],jobID=job['jobID'],postID=job['outcome']['postID'],episodeID=job['outcome']['episodeID'])
   else:raise AssertionError('unexpected role')
   budget.finish(n,result);receipts.append({'attempt':n,'role':a['role'],**result})
  budget.close();ledger=budget.read();assert attempts_hash(ledger['attempts'][:16])==prefix
 roles=dict(collections.Counter(r['role'] for r in receipts));assert roles=={'battle':31,'puppeteer':4,'strategy':1}
 accounting={'closed':ledger['closed'],'historicalAttemptsImmutable':16,'newAttempts':36,'additionalCeiling':98,'roles':roles,'unusedClosed':62,'unusedByRole':{'battle':53,'puppeteer':8,'strategy':1,'preparation':0},'confirmedCostUSD':sum(r['usage']['cost'] for r in receipts),'unconfirmedNewCostReceipts':0,'receipts':receipts}
 write('accounting.json',accounting)
 prior=read('verification.json') if (E/'verification.json').exists() else {}
 results=list(prior.get('hermesCleanup',[]))
 results.extend(cleanup(j['runtimeHome'],dry_run=False) for j in jobs if Path(j['runtimeHome']).exists())
 cfg=json.loads((PRIVATE/'launch.json').read_text())
 with open_store(cfg['database']) as w:
  hashes={method:getattr(w,method)() for method in METHODS};assert hashes==after['hashes']
  assert all(j['outcome']['episodeID'] in w.puppeteer_state()['episodes'] for j in jobs)
 protected={p:file_hash(ROOT/p)==sha for p,sha in read('protected.json').items()};assert all(protected.values())
 for actor,packet in after['actors'].items():
  for claim in packet['reportedClaims']:
   post=after['social']['posts'][claim['attribution']['postID']]
   assert claim['claim'] in post['claims'] and claim['mode']=='reported'
 layout=json.loads((ROOT/'config/prep_save_layout.json').read_text())
 path=PRIVATE/'C3-james-blocked.sav';identity=save_identity(path);data=path.read_bytes();sections={}
 for i in range(identity.slot*14,(identity.slot+1)*14):
  sector=data[i*4096:(i+1)*4096];sid=struct.unpack_from('<H',sector,4084)[0];sections[sid]=sector[:layout['sectionSizes'][sid]]
 block=b''.join(sections[i] for i in (1,2,3,4))
 flags={str(t):bool(block[layout['flagsOffset']+(0x500+t)//8]&(1<<((0x500+t)&7))) for t in (89,102,105,106,107,108,117,414)}
 assert all(v for k,v in flags.items() if k!='108') and not flags['108']
 memos={m['actor']:m for m in after['memos']};kent=memos['trainer:fr:trainer:0108'];assert kent['source']=='fallback'
 greg=memos['trainer:fr:trainer:0106'];assert greg['strategyID']==next(m for m in read('starting-C1.json')['memos'] if m['actor']==greg['actor'])['strategyID']
 counts={str(t):sum(b['sourceTrainerID']==t for b in after['world']['battles'].values()) for t in (102,106,107,108,117,414)}
 assert counts=={'102':1,'106':1,'107':1,'108':0,'117':1,'414':1}
 resources=[json.loads(l) for l in (E/'emulator.jsonl.resources').read_text().splitlines()]
 heap={'samples':len(resources),'maximumSampledAllocated':max(r['allocated'] for r in resources),'minimumSampledFree':min(r['free'] for r in resources),'minimumSampledLargest':min(r['largest'] for r in resources),'qualification':'sampled screens only; stack and worst-case high-water unmeasured'}
 write('partial-golden-trace.json',{'scope':'C1 -> Greg -> C2 -> incidental Ben -> James -> C3 -> offline Continue; Kent UNRUN','causalEvents':trace,'battleReceipts':receipts,'checkpoint':after['checkpoint'],'save':after['save'],'trainerFlags':flags})
 verification={'ticket':'CAMPAIGN-EXPANSION-01','accepted':False,'status':'BLOCKED at required Kent live Strategy gate','blocker':kent['diagnostics'],'KentStrategyID':kent['strategyID'],'postBlockMetadata':read('post-block-route-check.json'),'generationCallsForKent':0,'completedSubgates':['Greg native live battle, actual Hermes recap/follow/diffusion, C2 fresh Continue','James Dots memo, native live battle, actual Hermes recap/follow/diffusion, C3 offline fresh Continue'],'unrun':['Kent model memo and live battle/recap','Mt. Moon transition','final Kent paired-save/offline Continue','full final feed pagination and behavioral diversity acceptance'],'restoreSevenHashesMatch':True,'viewerSevenHashesUnchanged':True,'viewerLedgerUnchanged':True,'viewerLimitation':'Home followers=4 and Rick/Brock posts viewed; later feed request returned PokeBook unavailable. Greg-labeled initial screenshot is actually Brock; later corrected screenshot unavailable. No full browsing acceptance claimed.','publicClaimsAllSourceMatched':True,'posts':len(after['social']['posts']),'playerFollowers':sum(f['followed'].startswith('player:') for f in after['social']['follows'].values()),'trainerFlags':flags,'nativeBattleCounts':counts,'GregMemoUnchanged':True,'hashes':hashes,'protectedHashesUnchanged':protected,'hermesCleanup':results,'durableActualHermesEpisodesPreserved':True,'accounting':{k:v for k,v in accounting.items() if k!='receipts'},'nativeMemory':read('native-memory-current.json'),'nativeHeap':heap,'hostedDefaultDisabled':not json.loads((ROOT/'config/model_profiles.yaml').read_text())['hosted_inference_enabled']}
 old=E/'verification.json'
 if old.exists() and not (E/'initial-verification.json').exists():(E/'initial-verification.json').write_bytes(old.read_bytes())
 write('verification.json',verification)
 print(json.dumps({k:verification[k] for k in ('accepted','status','posts','playerFollowers','restoreSevenHashesMatch','viewerLedgerUnchanged','accounting')}))
