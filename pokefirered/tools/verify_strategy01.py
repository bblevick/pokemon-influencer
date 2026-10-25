#!/usr/bin/env python3
"""Verify actual stored artifacts; explicitly does not accept the missing live gate."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from strategy01 import E
from strategy.domain import validate
from jsonschema import Draft202012Validator

def run():
 checks=[]
 def check(name,value):
  if not value:raise AssertionError(name)
  checks.append(name)
 read=lambda name:json.loads((E/name).read_text())
 for name in ('context','posture','behavior'):
  Draft202012Validator.check_schema(json.loads((ROOT/f'schemas/strategy/{name}.schema.json').read_text()));checks.append(name+'_schema_definition')
 budget=read('closed-budget.json');check('budget_closed_exactly10',budget['closed'] and len(budget['attempts'])==10)
 jobs={a['jobID'] for a in budget['attempts']};check('at_most3_per_job',all(sum(x['jobID']==j for x in budget['attempts'])<=3 for j in jobs))
 errors=[a.get('response',{}).get('error',{}) for a in budget['attempts']];check('last3_real_upstream502',all(e.get('code')==502 for e in errors[-3:]))
 before=read('before-native-continue.json');after=read('after-native-continue.json');clean=read('post-cleanup-replay.json');native=read('native-after-strategy.json')
 check('before_no_future_strategy',before['records']==[])
 check('after_exact_recorded_outputs',after['records']==native['records']==clean['records'])
 check('no_valid_live_posture',all(r['source']=='fallback' for r in after['records']))
 check('replays_zero_requests',all(r['modelRequests']==0 for r in (before,after,clean)))
 check('native_save16',native['save']['counter']==16 and native['checkpoint']['kind']=='normal_save')
 receipts=[json.loads(x) for x in (E/'save-receipts.jsonl').read_text().splitlines()]
 check('actual_native_callback15_16',[r['counter'] for r in receipts]==[15,16])
 check('native_save_barriers',all(r['drops']==r['depth']==0 and r['ack']==r['eventCounter']==0 for r in receipts))
 rick=read('rick-context.json');check('Rick16_not_selected',rick['candidateCount']==16 and 'candidateID' not in json.dumps(rick['modelInput']))
 check('Rick_authorized_Tackle',any(e['mode']=='direct' and e['claim'].get('moveID')==33 for e in rick['modelInput']['evidence']))
 check('no_frequency_counters','occurrencesInWindow' not in json.dumps(rick['modelInput']))
 check('own_partners_unchanged',[p['level'] for p in native['companionState']]==[6,6] and [p['species'] for p in native['companionState']]==[13,10])
 check('zero_resources',native['resourceState']['stock']==[])
 janice=read('janice-exposed-offline.json');claims=[e['claim'] for e in janice['context']['modelInput']['evidence']]
 check('Janice_only_published_claims',{c['type'] for c in claims}=={'POKEMON_SEEN','TRAINER_BATTLE_RESULT'} and all('moveID' not in c for c in claims));validate(janice['mockPosture'],janice['context']);checks.append('Janice_mock_reference_valid')
 transition=read('janice-exposure-transition-fixture.json');check('unexposed_then_exposed_fixture',transition['fixtureOnly'] and not transition['before']['modelInput']['evidence'] and bool(transition['after']['modelInput']['evidence']) and transition['sameOwnCompanions'])
 brock=read('brock-offline.json');check('Brock_support0_signature',brock['context']['modelInput']['identityPolicy']['theme']['maximumSupport']==0 and bool(brock['context']['modelInput']['identityPolicy']['signatureLineages']))
 check('default_hosted_disabled',not json.loads((ROOT/'config/model_profiles.yaml').read_text())['hosted_inference_enabled'])
 check('ROM_unchanged',hashlib.sha256((ROOT/'.local/pokebook01-enabled/pokefirered.gba').read_bytes()).hexdigest()=='bec6245f354e0846a9e606ba0665d9dabc2e4f9825ba278342755143de56e829')
 check('task_workers_stopped',read('cleanup.json')['remaining']==[])
 preserved=read('preservation.json');check('all244_protected_unchanged',preserved['checked']==244 and preserved['changed']==[])
 return {'assertions':len(checks),'checks':checks,'actualLiveGate':'NOT_ACCEPTED','reason':'configured NVIDIA free provider returned upstream502; ten-call budget exhausted','fallbackNativePersistence':'passed'}
if __name__=='__main__':
 result=run();(E/'artifact-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
