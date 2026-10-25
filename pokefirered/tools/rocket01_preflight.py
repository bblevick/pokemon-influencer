#!/usr/bin/env python3
"""Public route GETs and pure request qualification; zero generation attempts."""
import os,sys,json,time
from pathlib import Path
os.environ['POKEINFLUENCER_EXPERIMENT']='rocket01'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from campaign.provider import E,PRIVATE,LEDGER
from campaign.rocket import RocketStore
from campaign.budget import CampaignBudget
from strategy.provider import live_configuration,preflight_text,public_get,OpenRouterProvider,Limits
from system1.provider import configuration,preflight
from puppeteer import runtime

def hermes_route():
 model,_=runtime.model_configuration();catalog=runtime.verify_free_model(model)
 endpoints=public_get('https://openrouter.ai/api/v1/models/'+model+'/endpoints')['data']['endpoints']
 healthy=[e for e in endpoints if e.get('model_id')==model and e.get('status')==0 and e.get('uptime_last_5m',0)>0 and {'tools','max_tokens'}<=set(e.get('supported_parameters',[])) and all(float(e.get('pricing',{}).get(k,-1))==0 for k in ('prompt','completion'))]
 if not healthy:raise ValueError('no healthy zero price Hermes tool route')
 return {'model':model,'catalog':catalog,'endpoints':healthy,'checkedAtUnix':time.time(),'contract':'actual Hermes automatic tool calls; no forced tool_choice or required response_format'}

def main():
 report={'checkedAtUnix':time.time(),'generationCalls':0,'roles':{}}
 for role,check in [('strategy',lambda:preflight_text(live_configuration()[0]['model'])),('battle',lambda:preflight(configuration()[0]['model'])),('puppeteer',hermes_route)]:
  try:r=check();report['roles'][role]={'qualified':True,'route':r}
  except Exception as error:report['roles'][role]={'qualified':False,'errorClass':type(error).__name__,'code':str(error)[:120]}
 (E/'preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:{'qualified':v['qualified'],'model':v.get('route',{}).get('model'),'code':v.get('code')} for k,v in report['roles'].items()}))
 if not all(v['qualified'] for v in report['roles'].values()):raise ValueError('required live route not qualified; no gameplay/generation started')
 with CampaignBudget(LEDGER) as budget:
  if not LEDGER.exists():budget.authorize_rocket()
if __name__=='__main__':main()
