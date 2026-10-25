#!/usr/bin/env python3
"""Zero-inference isolated lifecycle acceptance helpers."""
import sys,json,sqlite3,shutil,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from campaign.store import CampaignStore
from battle.lifecycle import LifecycleMixin
from world.saves import fingerprint,layout_from_build
E=ROOT/'evidence/phase4/battle_end01';PRIVATE=ROOT/'.local/battle_end01';SCREENS=ROOT/'evidence/private/battle_end01';CONFIG=PRIVATE/'launch.json'
class Store(CampaignStore):pass
MODE='external'
def manifest():return json.loads((E/('manifest-'+MODE+'.json')).read_text())
def open_store(path):return Store(path,E/('manifest-'+MODE+'.json'))
def save_identity(path):return fingerprint(Path(path).read_bytes(),layout_from_build(ROOT/manifest()['rom_path']))
def bindings(module):
 for n,v in dict(E=E,PRIVATE=PRIVATE,SCREENS=SCREENS,CONFIG=CONFIG,manifest=manifest,open_store=open_store,save_identity=save_identity).items():setattr(module,n,v)
def main():
 global MODE
 p=argparse.ArgumentParser();p.add_argument('command',choices=['init','launch','host','capture','input','save']);p.add_argument('--mode',choices=['vanilla','external'],default='external');p.add_argument('--label',default='sample');p.add_argument('--seconds',type=int,default=3600);p.add_argument('--terminal-delay-test',action='store_true');p.add_argument('--resume-save',action='store_true');p.add_argument('--restore-save',type=Path);p.add_argument('inputs',nargs='*');a=p.parse_args();MODE=a.mode
 PRIVATE.mkdir(exist_ok=True);SCREENS.mkdir(parents=True,exist_ok=True)
 if a.command=='init':
  dest=PRIVATE/'world.sqlite3'
  if dest.exists():raise ValueError('refuse overwrite retained lifecycle database')
  with sqlite3.connect(ROOT/'.local/vertical_slice01/world.sqlite3') as source,sqlite3.connect(dest) as target:source.backup(target)
  shutil.copy2(ROOT/'.local/vertical_slice01/closeout-gym-ready.sav',PRIVATE/'pre-brock.sav');return
 if a.command=='launch':
  import strategy01_launch as launch
  bindings(launch);launch.prepare(False,a.restore_save or PRIVATE/'pre-brock.sav',manifest_path=E/('manifest-'+MODE+'.json'))
  script=PRIVATE/'run.lua';s=script.read_text().replace('if PI_UI_receive and kind>=4 then','if PI_BATTLE_receive and kind>=8 then PI_BATTLE_receive(kind,nonce,gen,seq,typ,data);return end\n if PI_UI_receive and kind>=4 then')
  script.write_text(s+'\n'+(ROOT/'bridge/campaign_constructor_receipt.lua').read_text()+'\n'+(ROOT/'native/battle_end01/transport.lua').read_text())
  from phase1_events_build import symbols
  syms=symbols(ROOT/manifest()['rom_path'].replace('.gba','.elf'))
  hooks={n:syms[n] for n in ('gBattleOutcome','gBattleMainFunc','gMain','HandleEndTurn_FinishBattle','FreeResetData_ReturnToOvOrDoEvolutions','CB2_EndTrainerBattle','CB2_WhiteOut','CB2_ReturnToFieldContinueScriptPlayMapMusic')}
  (E/('native-hooks-'+MODE+'.json')).write_text(json.dumps(hooks,indent=2)+'\n')
  prefix=';'.join('PI.m.diagnostic_symbols.'+n+'='+str(syms[n]['address']) for n in ('gBattleOutcome','gBattleMainFunc','gMain'))+'\n'
  (PRIVATE/'probe.lua').write_text(prefix+(ROOT/'native/battle_end01/probe.lua').read_text())
  d={k:syms[k]['address'] for k in ('gBattleOutcome','gBattleMons','gStatuses3','gBattlerControllerFuncs','HandleInputChooseAction','HandleInputChooseMove')};d['monSize']=syms['gBattleMons']['size']//4
  (E/('player-menu-symbols-'+MODE+'.json')).write_text(json.dumps(d,indent=2)+'\n')
  (PRIVATE/'player.lua').write_text('PI_END_SYMBOLS={'+','.join(k+'='+str(v) for k,v in d.items())+'}\n'+(ROOT/'native/battle_end01/player_path.lua').read_text())
  return
 if a.command=='host':
  import strategy01_host as host
  from campaign.transport import CampaignHandler
  bindings(host)
  class Hold:
   def tick(self,w):pass
   def close(self,w):pass
  handler=CampaignHandler(manifest(),E)
  if a.terminal_delay_test:
   import time,socket
   deadline=[None]
   def before_ack(msg,w,sock,result):
    from bridge.events import decode_event
    if decode_event(msg)['eventType']!='BATTLE_ENDED':return True
    if deadline[0] is None:
     deadline[0]=time.monotonic()+4
     handler.log('terminal-ack-test',{'stage':'committed_then_disconnect','sequence':msg.sequence,'result':result,'delaySeconds':4})
     sock.shutdown(socket.SHUT_RDWR);return False
    ready=time.monotonic()>=deadline[0]
    handler.log('terminal-ack-test',{'stage':'duplicate_reack' if ready else 'delayed_ack','sequence':msg.sequence,'result':result})
    return ready
   handler.before_event_ack=before_ack
  try:host.run(a.seconds,services=Hold(),battle_handler=handler)
  finally:handler.close()
  return
 if a.command=='input':
  import strategy01_input as driver
  bindings(driver);driver.retained.E=E;print(driver.segment(a.label,a.inputs));return
 if a.command=='save':
  import strategy01_scenario as scenario,strategy01_input as driver
  bindings(scenario);bindings(driver);driver.retained.E=E;scenario.segment=driver.segment
  checkpoint=scenario.normal_save(a.label,0,resume=a.resume_save)
  shutil.copy2(PRIVATE/'pokefirered.sav',PRIVATE/(a.label+'.sav'))
  (E/(a.label+'-checkpoint.json')).write_text(json.dumps(checkpoint,indent=2)+'\n');print(json.dumps(checkpoint));return
 cfg=json.loads(CONFIG.read_text())
 with open_store(cfg['database']) as w:
  from pokebook.viewer import Viewer
  from prep.progression import read_boulder
  out={'label':a.label,'campaign':w.campaign(),'world':w.state(),'memos':w.memo_records(),'decisions':w.decision_state(),'obligations':w.puppeteer_state()['obligations'],'virality':w.virality_state(),'hashes':{m:getattr(w,m)() for m in ('verify_replay','verify_memory_replay','verify_social_replay','verify_puppeteer_replay','verify_strategy_replay','verify_decision_replay','verify_virality_replay')},'audit':w.battle_audit(),'lifecycle':w.decision_lifecycle(),'batteryBoulder':read_boulder(Path(cfg['save']).read_bytes(),w.build)}
 (E/(a.label+'.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'label':a.label,'branch':out['campaign']['active_branch']}))
if __name__=='__main__':main()
