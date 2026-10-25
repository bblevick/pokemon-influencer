#!/usr/bin/env python3
"""Retained BATTLE-01 bounded input/receipt driver, isolated destinations."""
import sys,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import strategy01_transport_input as retained
retained.E=ROOT/'evidence/phase4/system1_01b'
s=(ROOT/'tools/battle01_input.py').read_text().replace("retained.E=ROOT/'evidence/phase4/battle01'","retained.E=ROOT/'evidence/phase4/system1_01b'")
exec(compile(s,str(ROOT/'tools/battle01_input.py'),'exec'),{'__name__':'__main__','__file__':str(ROOT/'tools/battle01_input.py')})
