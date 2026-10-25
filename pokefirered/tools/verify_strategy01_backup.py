#!/usr/bin/env python3
"""Check real backup experiment artifacts; no network or simulated acceptance."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence/phase3/strategy01/backup';checks=[]
def read(name):return json.loads((E/(name+'.json')).read_text())
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
meta=read('models-preflight');budget=read('closed-budget');result=read('live-result');packet=read('live-context');cleanup=read('cleanup');privacy=read('privacy');leak=read('no-authority-leak')
check('first backup exact model qualified only for availability/free tools',meta['POKEINFLUENCER_STRATEGY_MODEL_BACKUP']['model']=='thinkingmachines/inkling-small:free')
check('forced tool capability explicitly missing',meta['POKEINFLUENCER_STRATEGY_MODEL_BACKUP']['reason']=='required_tool_parameters_unavailable')
check('Qwen exact named contingency metadata qualified',meta['POKEINFLUENCER_STRATEGY_MODEL_BACKUP_BACKUP']['status']=='qualified_metadata')
check('router gate fails before model request',meta['POKEINFLUENCER_MODEL_BACKUP']['status']=='blocked_metadata')
check('explicit contingency selection not a model chain',read('authorization')['selectedTestRole']=='backup_backup' and not read('authorization')['automaticCrossModelFallback'])
check('permanent renewed five request cap',budget['maximumAttempts']==5 and budget['closed'] and len(budget['attempts'])==3)
check('one job only',len({a['jobID'] for a in budget['attempts']})==1)
check('all actual requests only Qwen',all(a['requestedModel']=='qwen/qwen3.8-27b:free' for a in budget['attempts']))
check('HTTP400 429 429 actual evidence',[a['response']['httpStatus'] for a in budget['attempts']]==[400,429,429])
check('same unmodified request/input hashes',len({a['requestSHA256'] for a in budget['attempts']})==len({a['modelInputSHA256'] for a in budget['attempts']})==1)
check('zero price supported provider routing',all(a['routing']['only']==['ModelRun'] and a['routing']['max_price']=={'prompt':0,'completion':0} and a['routing']['require_parameters'] for a in budget['attempts']))
check('truthfully fallback never accepted',result['source']=='fallback' and read('completion')['status']=='STRATEGY-01 LIVE ACCEPTANCE STILL BLOCKED')
check('old ledgers permanently preserved',all(json.loads((ROOT/p).read_text())['closed'] for p in ['evidence/phase3/strategy01/closed-budget.json','evidence/phase3/strategy01/closeout/closed-budget.json']))
check('full scoped model input same as primary',read('context-equivalence')['modelInputEqual'] and packet['modelInput']==json.loads((E.parent/'closeout/live-context.json').read_text())['modelInput'])
check('no stable candidate identifiers', 'candidateID' not in json.dumps(packet['modelInput']))
check('sixteen candidates remain',packet['candidateCount']==leak['candidateCount']==16)
check('all canonical subjective and PREP state unchanged',leak['before']==leak['after'])
check('zero downstream choices resources and other inference',all(leak[k]==0 for k in ('candidateSelections','installations','resourceSpends','battleActions','SystemOneCalls','HermesCalls')))
check('native opponent party plus count byte identical',read('native-no-mutation')['unchanged'] and read('native-no-mutation')['comparedBytes']==601)
check('native ROM unchanged',read('native-no-mutation')['wholeROMSHA256']=='bec6245f354e0846a9e606ba0665d9dabc2e4f9825ba278342755143de56e829')
check('Rick own evidence only',{x['claim']['type'] for x in privacy['trainer:fr:trainer:0102']['evidence']}=={'POKEMON_SEEN','MOVE_REVEALED','TRAINER_BATTLE_RESULT'})
check('Janice no private moves or episodes',not privacy['trainer:fr:trainer:0116']['privateEpisodes'] and all(x['mode']=='reported' and x['claim']['type']!='MOVE_REVEALED' for x in privacy['trainer:fr:trainer:0116']['evidence']))
check('Doug stays empty',not privacy['trainer:fr:trainer:0103']['evidence'] and not privacy['trainer:fr:trainer:0103']['privateEpisodes'])
check('no unrestricted director notes',all(not x['authorizedDirectorNotes'] for x in privacy.values()))
check('fresh replay no inference',read('fresh-runtime-fallback-replay')['modelRequests']==0)
check('paired before excludes attempted future',read('restored-before')['newResultAbsent'] and read('restored-before')['lateRejected'])
check('protected historical and foundation bytes preserved',not read('preservation')['changed'] and not read('foundation-preservation')['changed'])
for name in ('protected-before',):
 check('historical artifact hash snapshot still exact',all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in read(name).items()))
for log,n in [('focused-before-live.log',50),('configuration-alias-before-live.log',28),('focused-after-final.log',30),('configuration-final.log',11)]:
 s=(E/log).read_text();check(log+' actual pass','Ran '+str(n)+' tests' in s and s.rstrip().endswith('OK'))
check('services jobs and listeners stopped',not cleanup['remaining'] and cleanup['activeStrategyJobs']==0 and not cleanup['pendingSave'] and not cleanup['listening18782'] and not cleanup['listening18783'])
check('hosted default and ledger disabled',not cleanup['hostedInferenceEnabled'] and cleanup['budgetClosed'])
value={'assertions':len(checks),'passed':checks,'scope':'real metadata/failed requests plus host/native non-mutation; no live acceptance or after-live paired reload'}
(E/'artifact-checks.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps({'assertions':len(checks),'status':'passed'}))
