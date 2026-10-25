#!/usr/bin/env python3
"""Verify retained renewed-window artifacts, never inference or emulator claims."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence/phase3/strategy01/closeout'
def read(name):return json.loads((E/(name+'.json')).read_text())
checks=[]
def check(name,condition):
 if not condition:raise AssertionError(name)
 checks.append(name)
b=read('closed-budget');attempts=b['attempts'];old=json.loads((ROOT/'evidence/phase3/strategy01/closed-budget.json').read_text());p=read('live-context');r=read('live-result');state=read('no-authority-leak');cleanup=read('cleanup');private=read('privacy')
check('historical ten remain closed',old['closed'] and len(old['attempts'])==10)
check('renewed three attempts closed',b['closed'] and len(attempts)==3)
check('one logical job',len({a['jobID'] for a in attempts})==1)
check('exact current Nemotron',all(a['requestedModel']=='nvidia/nemotron-3.5-lightning:free' for a in attempts))
check('identical requests on upstream retries',len({a['requestSHA256'] for a in attempts})==1)
check('input audit matches scoped packet',all(a['modelInputSHA256']==hashlib.sha256(json.dumps(p['modelInput'],sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest() for a in attempts))
check('actual upstream 502 in all envelopes',all(a['response']['httpStatus']==200 and a['response']['error']['code']==502 and 'Nvidia' in a['response']['error']['message'] for a in attempts))
check('no model output or usage returned',all(a['response']['usage']=={} and a['response']['resolvedModel']=='missing_or_invalid' for a in attempts))
check('backoff intervals at least five and ten seconds',attempts[1]['startedAtUnix']-attempts[0]['startedAtUnix']>=5 and attempts[2]['startedAtUnix']-attempts[1]['startedAtUnix']>=10)
check('verified provider allowlist only',all(a['routing']['only']==['Nvidia'] and a['routing']['allow_fallbacks'] and a['routing']['max_price']=={'prompt':0,'completion':0} and a['routing']['require_parameters'] for a in attempts))
check('result truthfully fallback',r['source']=='fallback' and r['diagnostics']['failures']==['provider_error_502']*3)
check('fallback not used for acceptance',read('completion')['status']=='STRATEGY-01 LIVE ACCEPTANCE STILL BLOCKED')
check('candidate IDs absent', 'candidateID' not in json.dumps(p['modelInput']))
check('sixteen candidates remain',p['candidateCount']==state['candidateCount']==16)
check('all upstream gameplay hashes unchanged',state['before']==state['after'])
check('zero downstream choices',state['candidateSelections']==state['installations']==state['resourceSpends']==state['battleActions']==0)
check('Rick authorized only',{x['claim']['type'] for x in private['trainer:fr:trainer:0102']['evidence']}=={'MOVE_REVEALED','POKEMON_SEEN','TRAINER_BATTLE_RESULT'})
check('Doug no evidence/private episode',not private['trainer:fr:trainer:0103']['evidence'] and not private['trainer:fr:trainer:0103']['privateEpisodes'])
check('Janice reports no Rick private move',all(x['mode']=='reported' and x['claim']['type']!='MOVE_REVEALED' for x in private['trainer:fr:trainer:0116']['evidence']) and not private['trainer:fr:trainer:0116']['privateEpisodes'])
check('director not exposed',all(not v['authorizedDirectorNotes'] for v in private.values()))
check('offline fresh replay no calls',read('fresh-runtime-fallback-replay')['modelRequests']==0)
check('paired before excludes new derived future',read('restored-before')['renewedResultAbsent'])
check('late result rejected',read('restored-before')['lateRejected'])
check('all prior protected artifacts preserved',not read('preservation')['changed'] and all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha for path,sha in read('protected-before').items()))
check('offline tests really passed','Ran 40 tests' in (E/'focused-before-live.log').read_text() and (E/'focused-before-live.log').read_text().rstrip().endswith('OK'))
check('task processes/listeners stopped',not cleanup['remaining'] and not cleanup['listening18782'] and not cleanup['listening18783'])
check('no pending work and default offline',cleanup['activeStrategyJobs']==0 and not cleanup['pendingSave'] and not cleanup['hostedInferenceEnabled'] and cleanup['renewedBudgetClosed'] and not cleanup['backupModelUsed'])
result={'assertions':len(checks),'passed':checks,'scope':'actual renewed artifacts; upstream blocked, no live posture/after-live native acceptance claimed'}
(E/'artifact-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'assertions':len(checks),'status':'passed'}))
