#!/usr/bin/env python3
"""Existing offline event/save/viewer host plus explicit compatible native build."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
import strategy01_host as retained
from system1_01a_launch import E,PRIVATE,CONFIG,SCREENS,manifest,open_store,save_identity
for name in ('E','PRIVATE','CONFIG','SCREENS','manifest','open_store','save_identity'):setattr(retained,name,globals()[name])
if __name__=='__main__':retained.run(1800)
