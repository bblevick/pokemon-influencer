#!/usr/bin/env python3
"""Current host, actual-C and ARM static checks; no emulator execution implied."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--build-prefix',default='phase1-events');p.add_argument('--evidence-dir',default='evidence/phase1/bridge02');a=p.parse_args();E=ROOT/a.evidence_dir;E.mkdir(parents=True,exist_ok=True);work=ROOT/'.local/phase1-events-native';work.mkdir(parents=True,exist_ok=True)
(work/'constants').mkdir(exist_ok=True)
for p in ['tests/c_stubs/global.h','tests/c_stubs/battle.h','tests/c_stubs/battle_anim.h','tests/c_stubs/battle_setup.h','include/pi_events.h','include/pi_build.h']:shutil.copy2(ROOT/p,work/Path(p).name)
shutil.copy2(ROOT/'include/constants/battle.h',work/'constants/battle.h')
commands=[([sys.executable,'-m','unittest','discover','-s','tests','-v'],'host-unit.log')]
for name,source,extra in [('events','tests/pi_events_test.c',['-DPI_EVENTS_NATIVE_TEST=1']),('observation','tests/pi_observation_test.c',[])]:
 out=ROOT/'.local'/('pi_'+name+'_test')
 commands.append((['clang','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-D__attribute__(x)=','-DPI_EVENTS=1',*extra,'-I'+str(work),source,'src/pi_events.c','-o',str(out)],name+'-native-compile.log'))
 commands.append(([str(out)],name+'-native-tests.log'))
commands.extend([([sys.executable,'tools/phase1_events_build.py','--verify-existing','--output-prefix',a.build_prefix,'--evidence-dir',a.evidence_dir],'static-enabled.log'),([sys.executable,'tools/phase1_events_build.py','--disabled','--verify-existing','--output-prefix',a.build_prefix,'--evidence-dir',a.evidence_dir],'static-disabled.log'),([sys.executable,'tools/validate_ai_contracts.py'],'architecture-regression.log')])
results=[]
for args,log in commands:
 with (E/log).open('w') as f:
  f.write(json.dumps({'command':args})+'\n');f.flush();r=subprocess.run(args,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
 results.append({'command':args,'log':str((E/log).relative_to(ROOT)),'exit_code':r.returncode})
 if r.returncode:break
(E/'host-static-tests.json').write_text(json.dumps({'scope':'host/schema, actual C with native stubs/sanitizers, compiled ARM allocation; not live emulator','passed':all(r['exit_code']==0 for r in results),'results':results},indent=2)+'\n')
raise SystemExit(results[-1]['exit_code'])
