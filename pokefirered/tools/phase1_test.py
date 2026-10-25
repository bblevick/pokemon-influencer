#!/usr/bin/env python3
"""Host/static checks; live emulator verification is a separate evidence command."""
from pathlib import Path
import json
import argparse
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--build-prefix',default='phase1');p.add_argument('--evidence-dir',default='evidence/phase1');a=p.parse_args();E=ROOT/a.evidence_dir;E.mkdir(parents=True,exist_ok=True)
work=ROOT/'.local/phase1-native';work.mkdir(parents=True,exist_ok=True)
for p in [ROOT/'tests/c_stubs/global.h',ROOT/'tests/c_stubs/main.h',ROOT/'include/pi_protocol.h',ROOT/'include/pi_build.h']:shutil.copy2(p,work/p.name)
commands=[
 ([sys.executable,'-m','unittest','discover','-s','tests','-v'],'host-tests.log'),
 (['clang','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-D__attribute__(x)=','-DPI_BRIDGE=1','-DPI_BRIDGE_TEST=1','-I',str(work),'tests/pi_mailbox_test.c','src/pi_bridge.c','-o',str(ROOT/'.local/pi_mailbox_test')],'native-compile.log'),
 ([str(ROOT/'.local/pi_mailbox_test')],'rom-state-machine-host.log'),
 ([sys.executable,'tools/phase1_build.py','--verify-existing','--output-prefix',a.build_prefix,'--evidence-dir',a.evidence_dir],'static-enabled.log'),
 ([sys.executable,'tools/phase1_build.py','--disabled','--verify-existing','--output-prefix',a.build_prefix,'--evidence-dir',a.evidence_dir],'static-disabled.log')]
results=[]
for args,filename in commands:
 with (E/filename).open('w') as f:
  f.write(json.dumps({'command':args})+'\n');f.flush();r=subprocess.run(args,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
 results.append({'command':args,'log':str((E/filename).relative_to(ROOT)),'exit_code':r.returncode})
 if r.returncode:break
(E/'host-static-tests.json').write_text(json.dumps({'scope':'host protocol, actual C logic on native platform, and compiled ARM allocation/layout; not emulator execution','results':results,'passed':all(r['exit_code']==0 for r in results)},indent=2)+'\n')
raise SystemExit(results[-1]['exit_code'])
