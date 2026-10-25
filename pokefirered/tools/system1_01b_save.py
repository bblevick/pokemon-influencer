#!/usr/bin/env python3
"""Retained reviewed normal Save menu path, paired with battle audit prefix."""
import sys,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import strategy01_scenario as scenario
import system1_01b_launch as battle
for name in ('PRIVATE','CONFIG','SCREENS','ROOT','E','open_store','save_identity'):setattr(scenario,name,getattr(battle,name))
def segment(label,commands):
 subprocess.run([sys.executable,str(ROOT/'tools/system1_01b_input.py'),*commands,'shot '+label],cwd=ROOT,check=True)
 return battle.SCREENS/(label+'.png')
scenario.segment=segment
if __name__=='__main__':print(json.dumps(scenario.normal_save('system1-battle-paired',0,'--resume' in sys.argv),indent=2))
