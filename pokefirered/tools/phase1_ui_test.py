#!/usr/bin/env python3
"""Host/actual-C/compiled-ARM tests. Live evidence verification is separate."""
import json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence/phase1/bridge03';work=ROOT/'.local/phase1-ui-native';work.mkdir(exist_ok=True)
s=(ROOT/'tests/c_stubs/global.h').read_text().replace('#include <stdint.h>','#include <stdint.h>\n#include <stddef.h>\ntypedef uint8_t bool8;\ntypedef int32_t s32;')
(work/'global.h').write_text(s)
for f in ['pi_ui.h','pi_events.h','pi_build.h']:shutil.copy2(ROOT/'include'/f,work/f)
commands=[([sys.executable,'-m','unittest','discover','-s','tests','-v'],'host-unit.log'),(['clang','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-D__attribute__(x)=','-DPI_UI=1','-DPI_UI_TEST=1','-DPI_EVENTS=1','-DPI_UI_NATIVE_TEST=1','-I'+str(work),'tests/pi_ui_test.c','-o',str(ROOT/'.local/pi_ui_test')],'ui-native-compile.log'),([str(ROOT/'.local/pi_ui_test')],'ui-native-tests.log'),([sys.executable,'tools/phase1_ui_build.py','--verify-existing'],'static-enabled.log'),([sys.executable,'tools/phase1_ui_build.py','--disabled','--verify-existing'],'static-disabled.log')]
results=[]
for args,name in commands:
 with (E/name).open('w') as f:
  f.write(json.dumps({'command':args})+'\n');f.flush();p=subprocess.run(args,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
 results.append({'command':args,'exit_code':p.returncode,'log':str((E/name).relative_to(ROOT))})
 if p.returncode:break
(E/'host-static-tests.json').write_text(json.dumps({'scope':'unit/actual C sanitizer/compiled ARM; no live emulator execution','passed':all(r['exit_code']==0 for r in results),'results':results},indent=2)+'\n')
raise SystemExit(results[-1]['exit_code'])
