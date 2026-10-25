#!/usr/bin/env python3
"""Reuse reviewed input and normal-save route, isolated native acceptance context."""
import sys,time,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
import strategy01_input as inp
import strategy01_scenario as ret
from system1_01a_launch import E,PRIVATE,CONFIG,SCREENS,open_store,save_identity
inp.retained.E=E;inp.E=E;inp.SCREENS=SCREENS
for name in ('E','PRIVATE','CONFIG','SCREENS','open_store','save_identity'):setattr(ret,name,globals()[name])
ret.segment=inp.segment
if __name__=='__main__':
 if sys.argv[1]=='save':print(json.dumps(ret.normal_save(sys.argv[2],int(sys.argv[3])),indent=2))
 elif sys.argv[1]=='continue':print(ret.continue_from_reviewed_title(sys.argv[2]))
