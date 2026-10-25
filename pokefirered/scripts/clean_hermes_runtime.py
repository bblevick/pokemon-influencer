#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from puppeteer.runtime import cleanup,recover_runtime
p=argparse.ArgumentParser();p.add_argument('target',type=Path);p.add_argument('--delete',action='store_true');p.add_argument('--stop',action='store_true');p.add_argument('--recover',action='store_true');p.add_argument('--quarantine',action='store_true');a=p.parse_args()
if a.stop or a.recover or a.quarantine:
    print(json.dumps(recover_runtime(a.target,stop=a.stop,quarantine=a.quarantine)))
    if a.quarantine:sys.exit(0)
print(json.dumps(cleanup(a.target,dry_run=not a.delete)))
