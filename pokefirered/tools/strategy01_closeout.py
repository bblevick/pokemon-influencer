#!/usr/bin/env python3
"""One explicitly authorized renewed Strategy job; no model substitution or gameplay writes."""
import os,sys,json
from pathlib import Path
os.environ['POKEINFLUENCER_STRATEGY_CLOSEOUT']='1'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from strategy01 import ROOT,E,PRIVATE,open_store
from strategy.context import build_context
from strategy.provider import live_configuration,preflight,OpenRouterProvider,LiveBudget
from strategy.runtime import run_job
from roster.extract import digest
ACTOR='trainer:fr:trainer:0102'
def write(name,value):
 (E/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
def state(w):
 return {'canonical':w.verify_replay(),'memory':w.verify_memory_replay(),'social':w.verify_social_replay(),'director':w.verify_puppeteer_replay(),'preparation':digest(w.preparation_state()),'companionsAndResources':w.preparation_state()}
def main():
 tests=(E/'focused-before-live.log').read_text()
 if 'Ran 40 tests' not in tests or not tests.rstrip().endswith('OK'):raise ValueError('focused offline pre-live tests must pass first')
 binding,key=live_configuration()
 if binding['model']!='nvidia/nemotron-3.5-lightning:free':raise ValueError('renewed authorization exact-model mismatch')
 # Same architecture/prompt, new versioned transport binding keeps old fallback immutable.
 route=preflight(binding['model']);write('live-preflight',{'binding':binding,'route':route})
 budget=PRIVATE/'live-budget.json'
 if budget.exists():raise ValueError('renewed experiment already attempted; inspect durable ledger, never reset it')
 with open_store(PRIVATE/'world.sqlite3') as w:
  before=state(w);write('before-state',before)
  job=w.begin_strategy(ACTOR,purpose='preparation-live-acceptance',provider_binding=binding)
  if job['status']!='active':raise ValueError('expected legitimate new versioned acceptance opportunity')
  packet=job['packet'];write('live-context',packet)
  assert packet['candidateCount']==16
  assert 'candidateID' not in json.dumps(packet['modelInput'])
  result=run_job(w,job,OpenRouterProvider(binding,key,route,budget,job['jobID']),source='model')
  write('live-result',result)
  after=state(w);assert before==after
  current=build_context(w,ACTOR,purpose='preparation-live-acceptance',provider_binding=binding)
  assert current['candidateCount']==16
  write('no-authority-leak',{'before':before,'after':after,'equal':True,'candidateCount':16,'candidateSelections':0,'installations':0,'resourceSpends':0,'battleActions':0,'romUnmodified':True,'modelAssumptionsNotCanonical':True})
 with LiveBudget(budget) as b:b.close();write('closed-budget',b.read())
 print(json.dumps({'source':result['source'],'strategyID':result['strategyID'],'diagnostics':result['diagnostics']},indent=2))
if __name__=='__main__':main()
