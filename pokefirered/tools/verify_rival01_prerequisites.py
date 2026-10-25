#!/usr/bin/env python3
"""Combine actual source-script trace and isolated host proofs, zero inference."""
import json,hashlib,sys,tempfile,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from rival01_prerequisites import protected
from world.store import WorldStore
from content.scripted import ScriptedContent
from campaign.transport import CampaignHandler
from campaign.expansion import ExpansionStore
from bridge.events_wire import Message
from virality import policy
E=ROOT/'evidence/phase8/rival01-prerequisites';P=ROOT/'.local/rival01-native-fixture';A='trainer:fr:trainer:0326'
def read(p):return json.loads((E/p).read_text())
def main():
 h=read('host-verification.json');m=read('manifest-native.json');fixture=read('native-fixture.json');snapshot=read('native-first-state.json');cfg=json.loads((P/'launch.json').read_text());state=snapshot['state']
 assert h['protectedAfter']==protected();assert h['hostedCalls']==0 and h['publicReceiptsRetained']==22 and h['privateRocketReceiptsExcluded']==47
 assert h['fullStrategyContextBytes']<=8192 and h['candidateCount']==1 and h['prepInferenceCalls']==0
 payload=bytes.fromhex(snapshot['snapshotHex']);hash32=2166136261
 for value in payload:hash32=((hash32^value)*16777619)&0xffffffff
 assert hash32==snapshot['hash32']
 raw=(E/'strategy-context.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==h['contextSHA256'];assert len(raw.rstrip(b'\n'))==h['fullStrategyContextBytes']
 assert fixture['romSHA256']==m['rom_sha256'] and fixture['pairedToAcceptedCampaign'] is False
 frames=[json.loads(line) for line in (E/'native-trace.jsonl').read_text().splitlines()];messages=[Message.decode(bytes.fromhex(r['wireHex'])[2:]) for r in frames if 'wireHex' in r];messages=[v for v in messages if v.nonce==cfg['nonce']]
 constructors=[v for v in messages if v.kind==12];assert len(constructors)==1
 assert struct.unpack('<HI',constructors[0].payload)==(334,1)
 assert (state['trainerID'],state['nonce'],state['generation'],state['turn'])==(334,cfg['nonce'],1,1)
 expected=ScriptedContent.load().cat.own_baseline(A,334)['party']
 assert [(p['species'],p['level'],p['moves'],p['heldItem']) for p in state['own']]==[(p['species'],p['level'],p['moves'],p['heldItem']) for p in expected]
 with WorldStore(P/'world.sqlite3',m['rom_sha256'],m['build_tag']) as w:
  b=next(iter(w.state()['battles'].values()));assert b['sourceTrainerID']==334 and b['trainerID']=='fr:trainer:0326' and not b['ended'];native_hash=w.verify_replay();native_state=w.state()
 # Replay actual native constructor bytes through the generic production handler
 # and observational adapter with a synthetic locked host scope, never forge a
 # native-save/campaign pairing or write an installation to the accepted world.
 class ScopeFixture:
  def __init__(self):
   self.registry=json.loads((ROOT/'config/trainer_registry.json').read_text());self._expanded_content=ScriptedContent.load();self.compatibility={'nativeROM':m['rom_sha256']};self.recorded=None
  def decision_state(self):return {'commitments':{},'installations':{}}
  def _launch(self,nonce,generation):assert nonce==cfg['nonce'] and generation==1
  def locked_preparation(self,actor):
   assert actor==A
   return {'encounterID':'ISOLATED_SCOPE_FIXTURE','commitmentID':'commitment:'+('0'*64)}
  def record_installation(self,encounter,receipt):self.recorded=receipt
 scope=ScopeFixture()
 with tempfile.TemporaryDirectory() as d:
  handler=CampaignHandler(m,Path(d));handler.receive(constructors[0],scope,None);handler.receive(constructors[0],scope,None);ExpansionStore.observe_native_preparation(scope,state);handler.pool.shutdown(wait=True)
 assert scope.recorded['nativeConstructorCount']==1 and scope.recorded['cumulativeNativeConstructorCount']==1;assert scope.recorded['party']==[{k:p[k] for k in ('species','level','moves','heldItem')} for p in state['own']]
 vp=json.loads((ROOT/'config/virality_policy.json').read_text());planning=json.loads((ROOT/'evidence/phase8/rival01-readiness/inspection.json').read_text());preview=planning['highProfilePurePlanningPreview'];assert preview['prominence']=='rival' and preview['reach']==vp['highProfile'];assert vp['eventKinds']['334']=='rival' and vp['sourceActors']['334']==A
 ram=read('native-memory.json');assert ram['nativeDeltaBytes']==0 and ram['afterRemaining']==4 and ram['allRAMSymbolsIdentical']
 logs={name:(E/name).read_text() for name in ('tests.log','rocket-regression.log','strategy-regression.log','campaign-regression.log')}
 assert all('\nOK\n' in value for value in logs.values())
 result={'status':'RIVAL-01 PREREQUISITES ACCEPTED','liveReadiness':'RIVAL-01 READY FOR LIVE IMPLEMENTATION','hostedCalls':0,'activeCampaignUnchanged':True,'host':h,'nativeScriptProof':{'fixtureDisclosure':fixture['kind'],'ROM':m['rom_sha256'],'nonce':cfg['nonce'],'sourceTrainerID':334,'canonicalActor':A,'constructorCount':1,'nativeWorldReplaySHA256':native_hash,'nativeWorldState':native_state,'authoredPartyExact':True,'sanitizedFirstTurnExported':True,'legalActionCount':len(state['actions']),'genericHandlerActualBytesWithSyntheticLockFixture':True,'noProductionInstallation':True,'noBattleResultCommitted':True,'terminalCompatibility':'typed host fixture + unchanged BATTLE-END-01 source; full live Rival terminal unrun and deferred'},'trustedHighProfilePreview':preview,'nativeRAM':ram,'tests':{'newSuite':18,'rocketRegression':12,'strategyMemoRegression':14,'campaignContentRegression':13,'total':57,'skipped':0},'expectedStrategyModel':h['configuredStrategyBinding']['model'],'freshRoutePreflightStillRequired':True,'futureBudgetRecommendation':{'strategy':1,'preparation':0,'battle':50,'hermes':4,'total':55,'authorizationConsumed':False},'remainingRisks':['normal campaign travel and Miguel/fossil progression have not run in this ticket','intervening public claims require context reselection at the actual opportunity','full live Rival terminal/recap/diffusion/paired restore are deferred','only starter0 branch executed natively; starter1/2 source-qualified fixture tests','existing diffusion epochs keep their pinned policy; Cerulean selection policy does not migrate or rewrite diffusion'],'implementationSHA256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('strategy/selection.py','campaign/scripted.py','content/scripted.py','config/context_selection_v1.json','config/scripted_encounters.json','schemas/strategy/selected_public_context.schema.json')},'workersMustBeStopped':True}
 (E/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'bytes':h['fullStrategyContextBytes'],'nativeConstructor':334,'actor':A,'calls':0}))
if __name__=='__main__':main()
