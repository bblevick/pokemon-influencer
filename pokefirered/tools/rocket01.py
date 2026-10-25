#!/usr/bin/env python3
"""ROCKET-01 scoped wrapper using unchanged generic native/host/input services."""
import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['POKEINFLUENCER_EXPERIMENT']='rocket01'
from campaign.rocket import RocketStore
import campaign_expansion01 as generic
generic.ExpansionStore=RocketStore
def add_player_probe():
 import json
 from phase1_events_build import symbols
 from phase1_events_launch import lua
 m=generic.manifest();syms=symbols(generic.ROOT/m['rom_path'].replace('.gba','.elf'));names=['gBattleOutcome','gBattlerControllerFuncs','gBattleMons','gMoveSelectionCursor','gActionSelectionCursor','gStatuses3','HandleInputChooseAction','HandleInputChooseMove'];value={n:syms[n]['address'] for n in names};value['monSize']=88
 script=generic.PRIVATE/'run.lua'
 probe='\nPI_PLAYER_SYMBOLS='+lua(value)+'\n'+(generic.ROOT/'tools/campaign_expansion01_player.lua').read_text()+'\nPI_EXP_PLAYER.enabled=false\n'
 script.write_text(script.read_text()+probe)
 # Probe is test-only ordinary buttons, disabled until explicit a0. Record final script hash.
 from roster.extract import file_hash
 with (generic.E/'test-driver.jsonl').open('a') as f:f.write(json.dumps({'scriptSHA256':file_hash(script),'source':'tools/campaign_expansion01_player.lua','symbols':value,'enabledAtLaunch':False,'memoryWrites':False})+'\n')
if __name__=='__main__':
 if sys.argv[1]=='launch' and '--start' in sys.argv[2:]:raise ValueError('prepare launch first, then start the recorded emulator argv so the disabled test probe is installed before scripting')
 generic.main()
 if sys.argv[1]=='launch':add_player_probe()
