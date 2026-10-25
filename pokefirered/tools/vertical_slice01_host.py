#!/usr/bin/env python3
"""One continuously managed writer; offline by default, scoped live opt-in."""
import sys,json,argparse,time,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from campaign.store import CampaignStore
from campaign.runtime import Services
from campaign.provider import E,PRIVATE,CampaignBattleProvider,LEDGER
from campaign.budget import CampaignBudget
from campaign.transport import CampaignHandler
from system1.provider import configuration,preflight
from world.saves import fingerprint,layout_from_build
import strategy01_host as host
MANIFEST=E/'manifest-native.json';MANIFEST_OVERRIDE=None
def manifest_path():
 if MANIFEST_OVERRIDE is not None:return MANIFEST_OVERRIDE
 config=PRIVATE/'launch.json'
 return Path(json.loads(config.read_text())['manifest']) if config.exists() else MANIFEST
def manifest():return json.loads(manifest_path().read_text())
def open_store(path):return CampaignStore(path,manifest_path())
def save_identity(path):return fingerprint(Path(path).read_bytes(),layout_from_build(ROOT/manifest()['rom_path']))
def main():
 global MANIFEST_OVERRIDE
 p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,default=1800);p.add_argument('--live',action='store_true');p.add_argument('--shadow',action='store_true');p.add_argument('--continue-authorized-run',action='store_true');p.add_argument('--gym-closeout',action='store_true');p.add_argument('--manifest',type=Path);a=p.parse_args();MANIFEST_OVERRIDE=a.manifest
 E.mkdir(parents=True,exist_ok=True);PRIVATE.mkdir(parents=True,exist_ok=True)
 for name,value in {'E':E,'PRIVATE':PRIVATE,'CONFIG':PRIVATE/'launch.json','manifest':manifest,'open_store':open_store,'save_identity':save_identity}.items():setattr(host,name,value)
 cfg=json.loads(host.CONFIG.read_text());stop=threading.Event();route={}
 with CampaignBudget(LEDGER) as budget:
  extended=bool(budget.read().get('gymCloseoutAuthorization'))
 if a.live and extended and not a.gym_closeout:raise ValueError('extended allowance requires explicit Gym-only closeout')
 if a.gym_closeout:
  if not extended or a.shadow:raise ValueError('Gym closeout authorization/profile required')
  with open_store(cfg['database']) as w:
   lock=w.locked_preparation('trainer:fr:trainer:0414')
   if not lock or not any(m['source']=='model' and m['strategyID']==lock['strategyID'] for m in w.memo_records()):raise ValueError('exact accepted live memo and lock required')
 if a.continue_authorized_run:
  if not a.live:raise ValueError('continuation requires explicit live mode')
  with CampaignBudget(LEDGER) as budget:budget.continue_authorized_run()
 def refresh():
  while not stop.is_set():
   try:
    binding,_=configuration();value=preflight(binding['model']);route.clear();route.update(value)
    (E/'system1-preflight.json').write_text(json.dumps({'binding':binding,**value},indent=2)+'\n')
   except Exception:pass
   stop.wait(50)
 if a.live:
  binding,_=configuration();route.update(preflight(binding['model']))
  thread=threading.Thread(target=refresh,daemon=True);thread.start()
  provider=CampaignBattleProvider(lambda:dict(route),gym_closeout=a.gym_closeout)
 else:provider=None
 handler=CampaignHandler(manifest(),E,provider=provider,shadow=a.shadow,decision_source='mercury' if a.live else 'external_test',decision_seconds=2.75 if a.live else 2.5)
 services=Services(cfg['database'],live=a.live,gym_closeout=a.gym_closeout)
 try:host.run(a.seconds,services=services,battle_handler=handler)
 finally:
  stop.set()
  if a.live:
   with CampaignBudget(LEDGER) as budget:budget.close()
if __name__=='__main__':main()
