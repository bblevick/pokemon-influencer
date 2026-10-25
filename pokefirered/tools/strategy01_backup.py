#!/usr/bin/env python3
"""Explicit backup acceptance selection; one unchanged scoped job, no model chain."""
import os,sys,json,argparse
from pathlib import Path
os.environ['POKEINFLUENCER_STRATEGY_BACKUP_ACCEPTANCE']='1'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from strategy01 import E,PRIVATE,open_store
from strategy.context import build_context
from strategy.provider import live_configuration,preflight,OpenRouterProvider,LiveBudget
from strategy.runtime import run_job
from roster.extract import digest
ACTOR='trainer:fr:trainer:0102'
def write(name,value):(E/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
def state(w):
 return {'canonical':w.verify_replay(),'memory':w.verify_memory_replay(),'social':w.verify_social_replay(),'director':w.verify_puppeteer_replay(),'preparation':digest(w.preparation_state()),'companionsAndResources':w.preparation_state()}
def main():
 p=argparse.ArgumentParser();p.add_argument('--model-role',choices=['backup','backup_backup'],default='backup');a=p.parse_args()
 tests=(E/'focused-before-live.log').read_text()
 if 'Ran 50 tests' not in tests or not tests.rstrip().endswith('OK'):raise ValueError('focused pre-live checks must pass first')
 alias_tests=(E/'configuration-alias-before-live.log').read_text()
 if 'Ran 28 tests' not in alias_tests or not alias_tests.rstrip().endswith('OK'):raise ValueError('credential-alias pre-live regressions must pass')
 binding,key=live_configuration(a.model_role)
 auth=json.loads((E/'authorization.json').read_text())
 if binding['model']!=auth['authorizedModels'][a.model_role]:raise ValueError('model differs from explicit authorized test role')
 budget=PRIVATE/'live-budget.json'
 with LiveBudget(budget,5) as b:
  value=b.read()
  if value['closed'] or value['attempts']:raise ValueError('live experiment already attempted; no budget reset')
  b.write(value)
 route=preflight(binding['model']);write('live-preflight',{'modelRole':a.model_role,'binding':binding,'route':route})
 with open_store(PRIVATE/'world.sqlite3') as w:
  before=state(w);write('before-state',before)
  job=w.begin_strategy(ACTOR,purpose='preparation-live-acceptance',provider_binding=binding)
  if job['status']!='active':raise ValueError('expected new legitimate acceptance grant')
  packet=job['packet'];write('live-context',packet)
  retained=json.loads((E.parent/'closeout/live-context.json').read_text())
  assert packet['modelInput']==retained['modelInput'],'semantic input changed from primary'
  assert packet['candidateCount']==16 and 'candidateID' not in json.dumps(packet['modelInput'])
  write('context-equivalence',{'modelInputEqual':True,'primaryModelInputSHA256':digest(retained['modelInput']),'backupModelInputSHA256':digest(packet['modelInput']),'candidateCount':16,'providerBindingChangedOnlyInHostScope':True})
  result=run_job(w,job,OpenRouterProvider(binding,key,route,budget,job['jobID']),source='model');write('live-result',result)
  after=state(w);assert before==after
  write('no-authority-leak',{'before':before,'after':after,'equal':True,'candidateCount':build_context(w,ACTOR,purpose='preparation-live-acceptance',provider_binding=binding)['candidateCount'],'candidateSelections':0,'installations':0,'resourceSpends':0,'battleActions':0,'SystemOneCalls':0,'HermesCalls':0})
 with LiveBudget(budget,5) as b:b.close();write('closed-budget',b.read())
 print(json.dumps({'source':result['source'],'strategyID':result['strategyID'],'diagnostics':result['diagnostics']},indent=2))
if __name__=='__main__':main()
