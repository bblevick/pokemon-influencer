#!/usr/bin/env python3
"""Managed expansion entry point over retained launch/host/ordinary-input helpers."""
import os,sys,json,argparse
from pathlib import Path
os.environ.setdefault('POKEINFLUENCER_EXPERIMENT','campaign_expansion01')
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from campaign.expansion import ExpansionStore
from campaign.provider import E,PRIVATE,LEDGER
MANIFEST=E/'manifest-native.json'
def manifest():return json.loads(MANIFEST.read_text())
def open_store(path):return ExpansionStore(path,MANIFEST)
def save_identity(path):
 from world.saves import fingerprint,layout_from_build
 return fingerprint(Path(path).read_bytes(),layout_from_build(ROOT/manifest()['rom_path']))
def bind(module):
 for name,value in {'E':E,'PRIVATE':PRIVATE,'CONFIG':PRIVATE/'launch.json','SCREENS':ROOT/'evidence/private'/PRIVATE.name,'manifest':manifest,'open_store':open_store,'save_identity':save_identity}.items():setattr(module,name,value)
def main():
 command=sys.argv[1];rest=sys.argv[2:]
 if command=='launch':
  import strategy01_launch as launch
  p=argparse.ArgumentParser();p.add_argument('--restore',type=Path);p.add_argument('--start',action='store_true');a=p.parse_args(rest);bind(launch)
  launch.prepare(False,a.restore,launch_hook=lambda w,cp:w.adopt_content(),manifest_path=MANIFEST)
  script=PRIVATE/'run.lua';s=script.read_text().replace('if PI_UI_receive and kind>=4 then','if PI_BATTLE_receive and kind>=8 then PI_BATTLE_receive(kind,nonce,gen,seq,typ,data);return end\n if PI_UI_receive and kind>=4 then')
  from phase1_events_build import symbols
  syms=symbols(ROOT/manifest()['rom_path'].replace('.gba','.elf'))
  # Add only the read-only source-bound trainer symbol to generated Lua manifest.
  s=s.replace('PI_CONFIG=',"PI_MANIFEST.diagnostic_symbols.gTrainerBattleOpponent_A=%d\nPI_CONFIG="%syms['gTrainerBattleOpponent_A']['address'],1)
  script.write_text(s+'\n'+(ROOT/'bridge/campaign_generic_constructor_receipt.lua').read_text()+'\n'+(ROOT/'native/battle_end01/transport.lua').read_text())
  if a.start:
   import subprocess
   subprocess.run([str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA'),'-C','hwaccelVideo=0','-C','savegamePath='+str(PRIVATE),str(ROOT/manifest()['rom_path'])],cwd=ROOT,check=True)
 elif command=='host':
  import vertical_slice01_host as host
  from campaign.expansion_runtime import ExpansionServices
  if os.environ.get('POKEINFLUENCER_EXPERIMENT')=='rocket01':
   from content.rocket import RocketContent
   class ExpansionServices(ExpansionServices):
    participation_scope=set(RocketContent.load().delta['participation'])
  bind(host);host.MANIFEST_OVERRIDE=MANIFEST;host.CampaignStore=ExpansionStore;host.Services=ExpansionServices
  sys.argv=[sys.argv[0],*rest];host.main()
 elif command in ('input','route','save'):
  import vertical_slice01_input as inp
  bind(inp);bind(inp.driver);inp.driver.retained.E=E
  import strategy01 as original;bind(original)
  if command=='input':
   p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('commands',nargs='+');a=p.parse_args(rest);print(inp.segment(a.label,a.commands))
  elif command=='route':
   import prep01_route as route
   route.segment=inp.segment;route.E=E;route.open_store=open_store
   p=argparse.ArgumentParser();p.add_argument('map');p.add_argument('x',type=int);p.add_argument('y',type=int);p.add_argument('--label',required=True);a=p.parse_args(rest)
   out=route.walk(a.map,(a.x,a.y),a.label,config_path=PRIVATE/'launch.json');(E/(a.label+'-route.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
  else:
   import strategy01_scenario as scenario;bind(scenario);scenario.segment=inp.segment
   p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('--menu-cursor',type=int,default=0);p.add_argument('--resume-intent',action='store_true');a=p.parse_args(rest);print(json.dumps(scenario.normal_save(a.label,a.menu_cursor,a.resume_intent),indent=2))
 else:raise ValueError('unknown expansion command')
if __name__=='__main__':main()
