#!/usr/bin/env python3
"""Host/C checks; emulator acceptance is separately recorded."""
import json,subprocess,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence/phase2/pokebook01'
work=ROOT/'.local/pokebook01-native';shutil.copytree(ROOT/'tests/c_stubs/pokebook',work,dirs_exist_ok=True)
for name in ['window.h','list_menu.h','task.h','pi_ui.h','pi_events.h','pi_pokebook.h','pi_pokebook_wire.h']:shutil.copy2(ROOT/'include'/name,work/name)
commands=[([sys.executable,'-m','unittest','discover','-s','tests','-v'],'host-tests.log')]
for name,src,flags in [('wire','tests/pi_pokebook_test.c',[]),('lifecycle','tests/pi_pokebook_lifecycle_test.c',['-Wno-unused-function','-D__attribute__(x)=','-DPI_UI=1','-I'+str(work)])]:
 out=ROOT/'.local'/('pi_pokebook_'+name+'_test')
 commands += [(['clang','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',*flags,src,'-o',str(out)],'c-'+name+'-compile.log'),([str(out)],'c-'+name+'.log')]
commands += [([sys.executable,'tools/pokebook01_build.py','--verify-existing'],'static-verify.log'),([sys.executable,'tools/validate_ai_contracts.py'],'architecture.log')]
results=[]
for argv,filename in commands:
 with (E/filename).open('w') as f:
  f.write(json.dumps({'argv':argv,'cwd':str(ROOT)})+'\n');f.flush();p=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
 results.append({'argv':argv,'exitCode':p.returncode,'log':str((E/filename).relative_to(ROOT))})
 if p.returncode:break
(E/'tests.json').write_text(json.dumps({'scope':'Host,actual-C with deterministic platform substitutes,ARM link; no emulator steps implied','passed':all(r['exitCode']==0 for r in results),'results':results},indent=2)+'\n')
raise SystemExit(results[-1]['exitCode'])
