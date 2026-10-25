#!/usr/bin/env python3
"""Public metadata GETs only. No inference, campaign writer, ROM or key output."""
import sys,json,time,hashlib,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['POKEINFLUENCER_EXPERIMENT']='rival01'
from strategy.provider import live_configuration,preflight_text,public_get
from system1.provider import configuration,preflight
from puppeteer.runtime import model_configuration,verify_free_model
from campaign.provider import E
def main():
 E.mkdir(parents=True,exist_ok=True)
 report={'scope':'RIVAL-01 fresh route checks before production state mutation','checkedAtUnix':time.time(),'hostedGenerationCalls':0,'httpMethods':['GET'],'roles':{},'authorization':{'source':'c5a5c563-de12-4360-8918-e08aadc95b75','overallCeiling':40,'requestedRoleCaps':{'strategy':3,'preparation':0,'battle':32,'puppeteer':5},'readinessRoleCaps':{'strategy':1,'preparation':0,'battle':50,'puppeteer':4},'effectiveRoleCaps':{'strategy':1,'preparation':0,'battle':32,'puppeteer':4},'effectiveMaximumUsableAttempts':37}}
 checks={
  'strategy':lambda:preflight_text(live_configuration()[0]['model']),
  'battle':lambda:preflight(configuration()[0]['model']),
 }
 def hermes():
  model,_=model_configuration();catalog=verify_free_model(model);ends=public_get('https://openrouter.ai/api/v1/models/'+model+'/endpoints')
  eligible=[e for e in ends['data']['endpoints'] if e.get('model_id')==model and e.get('status')==0 and e.get('uptime_last_5m',0)>0 and {'tools','max_tokens'}<=set(e.get('supported_parameters',[])) and all(float(e.get('pricing',{}).get(k,-1))==0 for k in ('prompt','completion'))]
  if not eligible:raise ValueError('no_healthy_free_hermes_tool_route')
  return {'model':model,'catalog':catalog,'endpoints':eligible,'checkedAtUnix':time.time(),'usageContract':'actual accepted Hermes harness with scoped tools; not bare chat'}
 checks['puppeteer']=hermes
 for role,check in checks.items():
  try:report['roles'][role]={'qualified':True,'route':check()}
  except Exception as error:report['roles'][role]={'qualified':False,'errorClass':type(error).__name__,'code':str(error)[:200]}
 required=all(report['roles'][role]['qualified'] for role in ('strategy','battle'))
 report['productionGameplayMayStart']=required;report['status']='ROUTES QUALIFIED' if required else 'RIVAL-01 BLOCKED — '+('STRATEGY ROUTE' if not report['roles']['strategy']['qualified'] else 'SYSTEM ONE ROUTE')
 (E/'preflight.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'status':report['status'],'roles':{k:{'qualified':v['qualified'],'model':v.get('route',{}).get('model'),'code':v.get('code')} for k,v in report['roles'].items()},'generationCalls':0,'effectiveRoleCaps':report['authorization']['effectiveRoleCaps']}),flush=True)
 return 0 if required else 2
if __name__=='__main__':raise SystemExit(main())
