#!/usr/bin/env python3
"""Zero-inference isolated host qualification. Never opens the campaign for writing."""
import copy,json,hashlib,sqlite3,sys,time,fcntl
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from campaign.scripted import ScriptedStore
from strategy.selection import public_candidates
from strategy.memo import fallback_text,memo_context
from strategy.social_context import build_social_evidence
from strategy.provider import live_configuration,OpenRouterProvider,Limits
from prep.domain import resolve_preparation_bundle
from content.scripted import ScriptedContent
from world.store import dump
from world.saves import fingerprint,layout_from_build
from roster.hashes import digest
E=ROOT/'evidence/phase8/rival01-prerequisites';PRIVATE=ROOT/'.local/rival01-prerequisites';ACTOR='trainer:fr:trainer:0326';M=E/'manifest-native.json'
METHODS=['verify_replay','verify_memory_replay','verify_social_replay','verify_puppeteer_replay','verify_strategy_replay','verify_decision_replay','verify_virality_replay']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def protected():
 paths=[ROOT/'.local/rocket01'/n for n in ['world.sqlite3','post-rocket-pair.sqlite3','post-rocket-pair.sav','pokefirered.sav']]+[ROOT/'evidence/phase7/rocket01/requests.json',ROOT/'config/model_profiles.yaml',ROOT/'config/virality_policy.json',ROOT/'config/campaign_content.json',ROOT/'config/rocket_content.json']
 return {str(p.relative_to(ROOT)):sha(p) for p in paths}
def clone(name):
 p=PRIVATE/(name+'.sqlite3');p.unlink(missing_ok=True)
 src=sqlite3.connect('file:'+str(ROOT/'.local/rocket01/post-rocket-pair.sqlite3')+'?mode=ro',uri=True);dst=sqlite3.connect(p);src.backup(dst);dst.close();src.close();return p
def history(w):return [tuple(r) for r in w.db.execute('SELECT id,context,outcome FROM strategy_jobs ORDER BY id')]
def main():
 PRIVATE.mkdir(parents=True,exist_ok=True);guard=(PRIVATE/'qualification.lock').open('a');fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
 E.mkdir(parents=True,exist_ok=True);PRIVATE.mkdir(parents=True,exist_ok=True);before=protected();binding,_=live_configuration();path=clone('host-qualification')
 with ScriptedStore(path,M) as w:
  initial={m:getattr(w,m)() for m in METHODS};historical=history(w);mem=copy.deepcopy(w.for_actor(ACTOR).records(limit=256));old_content=w.content.hash
  receipt=w.adopt_content();assert w.adopt_content()==receipt;assert history(w)==historical
  post_adoption={m:getattr(w,m)() for m in METHODS}
  assert w.for_actor(ACTOR).records(limit=256)['records']==mem['records']
  rows=public_candidates(w,ACTOR);assert len(rows)==22;assert w.for_actor(ACTOR).records(limit=256)['records']==mem['records']
  legacy=memo_context(w,ACTOR,'first',provider_binding=binding);social=build_social_evidence(w,ACTOR);legacy['modelInput']['authorizedSocialEvidence']={k:copy.deepcopy(social[k]) for k in ('schemaVersion','actorID','authorizedFacts','unknowns','truncated')};legacy_bytes=len(dump(legacy).encode('utf-8'))
  packets=[w.context_packet(ACTOR,provider_binding=binding) for _ in range(2)];assert dump(packets[0])==dump(packets[1]);packet=packets[0];audit=w.last_selection_audit
  assert len(dump(packet).encode('utf-8'))<=8192
  private={r['memoryID'] for r in w.virality_state()['intel'].values()};assert len(private)==47
  assert not private&{r['evidenceID'] for r in rows};assert not private&set(audit['selectedEvidenceIDs'])
  grunt=[r for r in rows if r['sourceTrainerID']==352];assert len(grunt)==2
  bundle=resolve_preparation_bundle(w,ACTOR,'first');cs=bundle['candidateSet']['candidates'];assert len(cs)==1
  baseline=w.content.cat.own_baseline(ACTOR,334)['party'];assert [(r['species'],r['level'],r['moves'],r['heldItem']) for r in cs[0]['party']]==[(r['species'],r['level'],r['moves'],r['heldItem']) for r in baseline]
  # Serialization-only route fixture; never implies current provider health.
  route={'checkedAtUnix':time.time(),'model':binding['model'],'providerName':'SERIALIZATION_FIXTURE_ONLY','endpoint':{'supported_parameters':[]}}
  adapter=OpenRouterProvider(binding,'UNUSED_NO_NETWORK',route,None,'unused');body,encoded=adapter.prepare_request(packet['modelInput'],None,Limits(),text=True)
  assert 'tools' not in body and 'tool_choice' not in body
  selected=packet['modelInput']['authorizedSocialEvidence']['claims'];before_bytes=json.loads((ROOT/'evidence/phase8/rival01-readiness/inspection.json').read_text())['prebattleBounds']['actualFrozenProjectionBytes']
  (E/'strategy-context.json').write_text(dump(packet)+'\n');(E/'selection-audit.json').write_text(json.dumps(audit,indent=2)+'\n');(E/'authorized-public-receipts.json').write_text(json.dumps(rows,indent=2)+'\n')
  result={'hostedCalls':0,'scope':'isolated host-copy qualification; no live strategy/preparation','protectedBefore':before,'historicalStrategyJobsUnchanged':True,'projectionHashesBeforeAdoption':initial,'projectionHashesAfterIsolatedBranchAdoption':post_adoption,'receipt':receipt,'publicReceiptsRetained':22,'privateRocketReceiptsExcluded':47,'gruntPublicClaimsEligible':2,'memoryDeleted':False,'oldFrozenPublicViewBytes':before_bytes,'legacyUnselectedFullContextFixtureBytes':legacy_bytes,'fullStrategyContextBytes':len(dump(packet).encode()),'modelInputBytes':len(dump(packet['modelInput']).encode()),'serializedChatRequestBytes':len(encoded),'contextID':packet['contextID'],'contextSHA256':sha(E/'strategy-context.json'),'canonicalContextSHA256':digest(packet),'modelInputSHA256':digest(packet['modelInput']),'repeatedPreflightIdentical':True,'selectedNormalizedClaimCount':len(selected),'selectedEvidenceReferenceCount':len(audit['selectedEvidenceIDs']),'selectedSourceActorCount':len({r['sourceActor'] for c in selected for r in c['references']}),'configuredStrategyBinding':binding,'currentProviderRouteChecked':False,'candidateCount':1,'authoredParty':baseline,'candidate':cs[0],'prepInferenceCalls':0,'nativeStarterBranches':{str(n):{'sourceTrainer':ScriptedContent.load(starter=n).pack['trainers'][ACTOR]['sourceTrainer'],'actor':ACTOR} for n in range(3)}}
  job=w.begin_strategy(ACTOR,'first',provider_binding=binding);assert job['packet']==packet
  memo=w.finish_memo(job['jobID'],fallback_text(packet),'fallback',{'qualification':'isolated deterministic test','costUSD':0},packet['contextID'])
  assert w.begin_strategy(ACTOR,'first',provider_binding=binding)['status']=='recorded'
  request=w.begin_selection(ACTOR,'first')['request']
  from system1.provider import run_selection
  decision=run_selection(w,{'status':'active','request':request});lock=w.commit_preparation(decision['decisionID']);assert lock['strategyID']==memo['strategyID'];assert len(dump(lock['authorizedPrebattleFacts']).encode())<=8192
  assert w.begin_selection(ACTOR,'first')['status']=='committed';assert len(history(w))==len(historical)+1
  assert all(r in history(w) for r in historical)
  frozen=dump(lock);policy=copy.deepcopy(w.content.selection_policy);w.content.selection_policy['maximumEvidenceBytes']=256;assert dump(w.locked_preparation(ACTOR))==frozen;assert w.prebattle_facts(ACTOR)==lock['authorizedPrebattleFacts'];w.content.selection_policy=policy
  result['fixtureFallbackAndSoleCommitmentFrozen']=True;result['fixtureLockSHA256']=digest(lock)
  m=json.loads(M.read_text());identity=fingerprint((ROOT/'.local/rocket01/post-rocket-pair.sav').read_bytes(),layout_from_build(ROOT/m['rom_path']));w.restore(identity)
  assert w.content.hash==old_content;assert w.locked_preparation(ACTOR) is None;assert w.for_actor(ACTOR).records(limit=256)['records']==mem['records'];assert {m:getattr(w,m)() for m in METHODS}==initial
  result['restoreSave20RollsBackQualificationOnly']=True;result['acceptedCheckpoint']=w.get_save_checkpoint(identity.fingerprint)
 assert before==protected();result['protectedAfter']=protected();result['protectedUnchanged']=True
 (E/'host-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['fullStrategyContextBytes','selectedNormalizedClaimCount','selectedEvidenceReferenceCount','publicReceiptsRetained','protectedUnchanged','hostedCalls']}))
if __name__=='__main__':main()
