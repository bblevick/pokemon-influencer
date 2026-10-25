#!/usr/bin/env python3
"""Explicit host-only Doug fixture report; never native evidence."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"tools"))
from tests.test_prep01 import PrepTests,DOUG
from prep01_report import report
case=PrepTests('test_doug_brock_janice');case.setUp()
try:
 case.eligible(103)
 out=report(case.path,DOUG,'forest-post-boulder-1');out['evidenceKind']='host normal-save/typed-event fixture, NOT native Doug playthrough'
 (ROOT/'evidence/phase3/prep01/doug-fixture-report.json').write_text(json.dumps(out,indent=2)+'\n')
 print('Doug candidates',len(out['result']['candidateSet']['candidates']))
finally:case.tearDown()
