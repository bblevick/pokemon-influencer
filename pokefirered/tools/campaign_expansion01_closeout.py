#!/usr/bin/env python3
"""Actual bounded closeout receipts; no inference, synthetic game state or ROM writes."""
import json,collections,struct,subprocess
from pathlib import Path
from campaign_expansion01 import ROOT,E,PRIVATE,open_store,save_identity,manifest
from campaign.budget import CampaignBudget
from puppeteer.runtime import cleanup
from roster.extract import file_hash
from campaign_expansion01_build import ram,OLD,DEST
from phase1_events_build import symbols
from vertical_slice01_viewer import METHODS

before=json.loads((E/'C1-before-viewer.json').read_text())
after=json.loads((E/'C1-after-viewer.json').read_text())
assert before['hashes']==after['hashes'] and before['ledger']==after['ledger']
(E/'viewer-proof.json').write_text(json.dumps({'sevenHashesUnchanged':True,'requestLedgerUnchanged':True,'posts':5,'feedPages':2,'followers':2,'visualEvidence':['c1-pokebook-home','c1-feed-page1','c1-feed-page2','c1-brock-post','c1-sally-post','c1-followers','c1-viewer-field2'],'scope':'actual recovered C1 fresh native Continue; offline'},indent=2)+'\n')
trace=[json.loads(line) for line in (E/'causal-trace.jsonl').read_text().splitlines()]
hermes=[r['result'] for r in trace if r['event']=='hermes-finished']
hermes_receipts={request['liveAttempt']:(job,request) for job in hermes for request in job['requests']}
receipts=[]
with CampaignBudget(E/'requests.json') as budget:
 for attempt in budget.read()['attempts']:
  response=attempt.get('response')
  result={'evidence':'retained provider response plus native lifecycle / committed domain result'}
  if attempt['role']=='strategy':
   assert response and response['usage']['cost']==0
   result.update(status='recorded_model_memo',usage=response['usage'],model=response['resolvedModel'])
  elif attempt['role']=='battle':
   scope=attempt['scope'];rows=[r for r in after['lifecycle'] if r['session']==scope['nonce'] and r['nativeRequest']==scope['request']]
   if response:
    executed=next(r for r in rows if r['stage']=='EXECUTED');assert response['result']['usage']['cost']==0
    result.update(status='executed',usage=response['result']['usage'],nativeLifecycleID=executed['lifecycleID'])
   else:
    canceled=next(r for r in rows if r['stage']=='CANCELED_TIMEOUT_FALLBACK')
    result.update(status='provider_deadline_native_fallback',usage=None,costReceipt='unknown; no response received; verified-free route required before POST',nativeLifecycleID=canceled['lifecycleID'])
  elif attempt['role']=='puppeteer':
   job,request=hermes_receipts[attempt['attempt']];assert request['sha256']==attempt['requestHash'] and request['response']['usage']['cost']==0
   result.update(status='committed_actual_hermes',usage=request['response']['usage'],jobID=job['jobID'],postID=job['outcome']['postID'],producer=job['outcome']['producer'])
  else:raise ValueError('unexpected role')
  budget.finish(attempt['attempt'],result);receipts.append({'attempt':attempt['attempt'],'role':attempt['role'],**result})
 budget.close();ledger=budget.read()
accounting={'closed':ledger['closed'],'attempts':len(ledger['attempts']),'roles':dict(collections.Counter(r['role'] for r in receipts)),'confirmedCostUSD':sum(r['usage']['cost'] for r in receipts if r['usage'] is not None),'unconfirmedCostReceipts':sum(r['usage'] is None for r in receipts),'receipts':receipts,'unusedAllowanceClosed':True}
(E/'accounting.json').write_text(json.dumps(accounting,indent=2)+'\n')
cleanup_results=[cleanup(job['runtimeHome'],dry_run=False) for job in hermes if Path(job['runtimeHome']).exists()]
cfg=json.loads((PRIVATE/'launch.json').read_text())
with open_store(cfg['database']) as w:
 hashes={method:getattr(w,method)() for method in METHODS};assert hashes==after['hashes']
 assert all(job['outcome']['episodeID'] in w.puppeteer_state()['episodes'] for job in hermes)
 protected={path:file_hash(ROOT/path)==sha for path,sha in json.loads((E/'protected.json').read_text()).items()};assert all(protected.values())
 # Source-pinned standard trainer flag mapping; read the validated native battery.
 layout=json.loads((ROOT/'config/prep_save_layout.json').read_text())
 def flags(path):
  data=path.read_bytes();identity=save_identity(path);sections={}
  for i in range(identity.slot*14,(identity.slot+1)*14):
   sector=data[i*4096:(i+1)*4096];sid=struct.unpack_from('<H',sector,4084)[0];sections[sid]=sector[:layout['sectionSizes'][sid]]
  block=b''.join(sections[i] for i in (1,2,3,4));return {str(t):bool(block[layout['flagsOffset']+(0x500+t)//8]&(1<<((0x500+t)&7))) for t in (105,106,107,108,117)}
 original_flags=flags(PRIVATE/'C0-ready.sav');current_flags=flags(PRIVATE/'C1-sally-recovered.sav')
 assert not original_flags['117'] and current_flags['117'] and current_flags['105']
 assert not any(current_flags[str(t)] for t in (106,107,108))
 epochs=[e for e in w.virality_state()['epochs'].values() if e['postID']==hermes[-1]['outcome']['postID']]
 epoch=epochs[0];assert epoch['followerCount']==2 and epoch['reach']['budget']==2
 native=[r for r in w.battle_audit() if r.get('battle')==2 and r.get('session')==1851161028 and r.get('event')!='decision-disposition']
 out={'ticket':'CAMPAIGN-EXPANSION-01','accepted':False,'status':'LIVE-BLOCKED; recovered normal C1 retained',
      'blockers':['Sally native meaningful choices: 12 Mercury executions, 3 vanilla fallbacks; first deadline latched remaining encounter','Greg Strategy preflight ProviderError before POST; detailed preflight code not retained for this attempt','Pending-save host restart suspended pairing; existing validated API recovery succeeded, automatic recovery gate unproven'],
      'unrun':['Greg native battle','James live Strategy/battle/recap','Kent live Strategy/battle/recap','native Mt. Moon transition','C2/C3 checkpoints','full trainer behavioral diversity'],
      'protectedHashesUnchanged':protected,'hashes':hashes,'C0TrainerFlags':original_flags,'C1TrainerFlags':current_flags,
      'trainerFlagSource':'src/battle_setup.c FlagSet(TRAINER_FLAGS_START + trainerId); include/constants/flags.h base 0x500; actual validated SaveBlock1',
      'nativeSallySources':dict(collections.Counter(r['source'] for r in native)),
      'SallyVirality':{k:epoch[k] for k in ('postID','followerCount','originStage','reach','publicationOrder')},
      'SallyRecipientsByReason':dict(collections.Counter(r['reason'] for r in epoch['deliveries'])),
      'hermesCleanup':cleanup_results,'durableHermesEpisodesPreserved':True,
      'hostedDefaultDisabled':not json.loads((ROOT/'config/model_profiles.yaml').read_text())['hosted_inference_enabled']}
 before_ram,after_ram=ram(OLD/'pokefirered.elf'),ram(DEST/'pokefirered.elf');assert before_ram==after_ram
 resource=json.loads((E/'native-memory.json').read_text());syms=symbols(DEST/'pokefirered.elf');assert 0x02040000-syms['__pi_mailbox_end']['address']==4
 resource.update(recheckedAllRAMSymbolsIdentical=True,ROMBytes=(DEST/'pokefirered.gba').stat().st_size,ROM_SHA256=file_hash(DEST/'pokefirered.gba'),temporaryStackQualification='no new allocation path; existing 1036-byte battle snapshot heap and 48-byte control unchanged; worst heap/stack peak not measured')
 out['nativeMemory']=resource
 (E/'native-memory-closeout.json').write_text(json.dumps(resource,indent=2)+'\n')
 (E/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'accepted':False,'attempts':accounting['attempts'],'roles':accounting['roles'],'confirmedCostUSD':accounting['confirmedCostUSD'],'unconfirmedCostReceipts':accounting['unconfirmedCostReceipts'],'nativeSallySources':out['nativeSallySources'],'RAMHeadroom':4,'protectedHashesUnchanged':all(protected.values())}))
