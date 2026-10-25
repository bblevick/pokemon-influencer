#!/usr/bin/env python3
"""Rival-scoped managed entry point over retained launch/host/ordinary-input helpers."""
import os,sys,json,argparse
from pathlib import Path
os.environ['POKEINFLUENCER_EXPERIMENT']='rival01'
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from campaign.scripted import ScriptedStore
from campaign.provider import E,PRIVATE,LEDGER
MANIFEST=E/'manifest-native.json'
def manifest():return json.loads(MANIFEST.read_text())
def open_store(path):return ScriptedStore(path,MANIFEST)
def save_identity(path):
 from world.saves import fingerprint,layout_from_build
 return fingerprint(Path(path).read_bytes(),layout_from_build(ROOT/manifest()['rom_path']))
def rival_ready(w,cp):
 import struct
 from world.saves import layout_from_build
 sizes=layout_from_build(ROOT/manifest()['rom_path']);data=(PRIVATE/'pokefirered.sav').read_bytes();identity=save_identity(PRIVATE/'pokefirered.sav');sections={}
 for n in range(identity.slot*14,(identity.slot+1)*14):
  sector=data[n*4096:(n+1)*4096];sid=struct.unpack_from('<H',sector,4084)[0];sections[sid]=sector[:sizes[sid]]
 sb1=b''.join(sections[i] for i in range(1,5));x,y=struct.unpack_from('<hh',sb1);group,num=sb1[4:6]
 starter=struct.unpack_from('<H',sb1,0x1000+2*(0x4031-0x4000))[0];scene=struct.unpack_from('<H',sb1,0x1000+2*(0x4052-0x4000))[0]
 if cp['kind']!='normal_save' or (group,num)!=(3,3) or y<=6 or starter!=0 or scene!=0:raise ValueError('Rival adoption requires normal paired Cerulean pre-trigger Save, Bulbasaur branch and scene0')
 receipt=w.adopt_content()
 (E/'content-adoption.json').write_text(json.dumps({'checkpoint':cp,'receipt':receipt,'nativePosition':[x,y],'map':[group,num],'starter':starter,'scene':scene,'sourceTrainer':334,'actor':'trainer:fr:trainer:0326'},indent=2)+'\n')
 return receipt
def bind(module):
 for name,value in {'E':E,'PRIVATE':PRIVATE,'CONFIG':PRIVATE/'launch.json','SCREENS':ROOT/'evidence/private'/PRIVATE.name,'manifest':manifest,'open_store':open_store,'save_identity':save_identity}.items():setattr(module,name,value)
def main():
 command=sys.argv[1];rest=sys.argv[2:]
 if command=='launch':
  import strategy01_launch as launch
  p=argparse.ArgumentParser();p.add_argument('--restore',type=Path);p.add_argument('--start',action='store_true');p.add_argument('--rival-ready',action='store_true');a=p.parse_args(rest);bind(launch)
  launch.prepare(False,a.restore,launch_hook=rival_ready if a.rival_ready else None,manifest_path=MANIFEST)
  script=PRIVATE/'run.lua';s=script.read_text().replace('if PI_UI_receive and kind>=4 then','if PI_BATTLE_receive and kind>=8 then PI_BATTLE_receive(kind,nonce,gen,seq,typ,data);return end\n if PI_UI_receive and kind>=4 then')
  from phase1_events_build import symbols
  syms=symbols(ROOT/manifest()['rom_path'].replace('.gba','.elf'))
  # Add only the read-only source-bound trainer symbol to generated Lua manifest.
  s=s.replace('PI_CONFIG=',"PI_MANIFEST.diagnostic_symbols.gTrainerBattleOpponent_A=%d\nPI_CONFIG="%syms['gTrainerBattleOpponent_A']['address'],1)
  script.write_text(s+'\n'+(ROOT/'bridge/campaign_generic_constructor_receipt.lua').read_text()+'\n'+(ROOT/'native/battle_end01/transport.lua').read_text())
  from phase1_events_launch import lua
  from rival01_player_symbols import player_symbols
  player_symbols,source_proof=player_symbols(ROOT,manifest())
  script.write_text(script.read_text()+'\nPI_PLAYER_SYMBOLS='+lua(player_symbols)+'\n'+(ROOT/'tools/rival01_player.lua').read_text()+'\n'+(ROOT/'tools/rival01_wild.lua').read_text())
  if a.start:
   import subprocess
   subprocess.run([str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA'),'-C','hwaccelVideo=0','-C','savegamePath='+str(PRIVATE),str(ROOT/manifest()['rom_path'])],cwd=ROOT,check=True)
 elif command=='host':
  import vertical_slice01_host as host
  from campaign.rival_runtime import RivalServices
  bind(host);host.MANIFEST_OVERRIDE=MANIFEST;host.CampaignStore=ScriptedStore;host.Services=RivalServices
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
