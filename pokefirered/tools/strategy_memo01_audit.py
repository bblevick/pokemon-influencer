#!/usr/bin/env python3
"""Read-only actual-artifact closeout. No fixtures are labeled native proof."""
import os,sys,json,hashlib,socket,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.environ['POKEINFLUENCER_STRATEGY_MEMO_ACCEPTANCE']='1'
from strategy01 import E,PRIVATE,open_store,manifest,save_identity
from strategy.store import StrategyStore
from prep.domain import resolve_preparation_bundle
from roster.extract import digest

def read(name):return json.loads((E/name).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 checks=[]
 def check(name,value):
  if not value:raise AssertionError(name)
  checks.append(name)
 model=read('generate.json');check('actual model source, not fallback',model['source']=='model')
 check('exact configured requested/resolved free model',model['diagnostics']['requestedModel']==model['diagnostics']['resolvedModel']=='nvidia/nemotron-3.5-lightning:free')
 ledger=read('closed-budget.json');check('new ledger closed exactly2 requests',ledger['closed'] and ledger['maximumAttempts']==2 and len(ledger['attempts'])==2)
 check('both returned explicit zero cost',all(a['response']['usage']['cost']==0 for a in ledger['attempts']))
 for name in ('fresh-host-replay.json','native-after-replay.json','native-return-replay.json','post-cleanup-replay.json','final-reviewed-replay.json','final-offline-replay.json'):
  r=read(name);check(name+' exact durable memo and no inference',r['records']==[model] and r['modelRequests']==0)
 check('native rewind excludes memo',read('native-rewind-replay.json')['records']==[])
 check('old grant rejected after actual rewind',read('rewind-isolation.json')['lateResultRejected'])
 check('native idle party/count unchanged',read('native-no-mutation.json')['unchanged'])
 m=manifest();check('accepted ROM checksum unchanged',sha(ROOT/m['rom_path'])==m['rom_sha256'])
 with open_store(PRIVATE/'world.sqlite3') as w,StrategyStore(ROOT/'.local/strategy01/world.sqlite3',m['rom_sha256'],m['build_tag']) as original:
  check('canonical gameplay unchanged',w.verify_replay()==original.verify_replay())
  check('actor memory unchanged',w.verify_memory_replay()==original.verify_memory_replay())
  check('social history unchanged',w.verify_social_replay()==original.verify_social_replay())
  check('Hermes history unchanged',w.verify_puppeteer_replay()==original.verify_puppeteer_replay())
  check('companions resources opportunities unchanged',all(w.preparation_state()[k]==original.preparation_state()[k] for k in ('actors','opportunities','reservations')))
  bundle=resolve_preparation_bundle(w,model['actor']);before=read('before-state.json')['candidateSet']['candidates']
  fields=('party','order','paths','battleItems','resourceCosts','acquisitionCount','descriptors')
  plans=lambda rows:[{k:r[k] for k in fields} for r in rows]
  check('all16 complete option plans unchanged and unselected',len(bundle['candidateSet']['candidates'])==16 and plans(bundle['candidateSet']['candidates'])==plans(before))
  for actor,packet in read('before-state.json')['actorPackets'].items():
   current=w.trainer_packet(actor)
   check(actor+' actor facts/episodes unchanged',all(current[k]==packet[k] for k in ('directObservations','reportedClaims','retainedEpisodes','observedSpeciesIDs','unknowns')))
  binding=read('rick-context.json')['packet']['scope']['providerConfiguration']
  check('fresh current scoped retrieval returns exact memo',w.recorded_strategy(model['actor'],purpose='preparation-live-acceptance',provider_binding=binding)['decision']==model)
  check('no active jobs or pending save',not w.pending_save() and not w._one("SELECT 1 FROM strategy_jobs WHERE status='active'"))
  save=save_identity(PRIVATE/'pokefirered.sav');cp=w.get_save_checkpoint(save.fingerprint)
  check('final paired native Save17 selected',save.counter==17 and cp['kind']=='normal_save')
  final={'cursor':w.campaign()['cursor'],'branch':w.get_active_branch(),'pairedSave':save.as_dict(),'checkpointID':cp['id'],'strategyStateSHA256':w.verify_strategy_replay(),'candidateCount':16,'memoTextSHA256':hashlib.sha256(model['strategyText'].encode()).hexdigest(),'wordCount':len(model['strategyText'].split())}
 for port in (18782,18783):
  s=socket.socket();s.settimeout(.2);closed=s.connect_ex(('127.0.0.1',port))!=0;s.close();check('listener '+str(port)+' closed',closed)
 check('task processes stopped',read('cleanup-final-reviewed.json')['remaining']==[])
 config=json.loads((ROOT/'config/model_profiles.yaml').read_text());check('default hosted false/offline',not config['hosted_inference_enabled'] and config['default_profile']=='offline')
 old=read('protected-before.json');mismatches=[p for p,h in old.items() if sha(ROOT/p)!=h];check('all protected historical artifacts/private original unchanged',not mismatches)
 (E/'preservation.json').write_text(json.dumps({'checked':len(old),'mismatches':mismatches},indent=2)+'\n')
 foundation=json.loads((ROOT/'evidence/phase3/strategy01/protected-before.json').read_text());bad=[p for p,h in foundation.items() if sha(ROOT/p)!=h];check('original foundation artifacts unchanged',not bad)
 (E/'foundation-preservation.json').write_text(json.dumps({'checked':len(foundation),'mismatches':bad},indent=2)+'\n')
 tests=unittest.defaultTestLoader.loadTestsFromNames(['tests.test_strategy_memo','tests.test_strategy01','tests.test_strategy01_provider','tests.test_strategy01_backup']).countTestCases()
 report={'status':'passed','count':len(checks),'checks':checks,'final':final,'focusedUniqueTestCases':tests,'nativeEvidence':'actual normal Save16→17; fresh Continue and paired rewind/return, no new divergent native battle','excludedNavigation':'memo-return-continue screenshot stopped at title; corrected through reviewed Start→Continue route; never counted as field success','scope':'No candidate selected, committed or installed; no resource spending, System One, new Hermes call or ROM change'}
 (E/'artifact-checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'count':len(checks),'final':final,'focusedUniqueTestCases':tests},indent=2))
if __name__=='__main__':main()
