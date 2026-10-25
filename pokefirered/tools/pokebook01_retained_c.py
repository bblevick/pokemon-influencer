#!/usr/bin/env python3
"""Rerun retained actual-C bridge tests into new evidence without rewriting old reports."""
import subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence/phase2/pokebook01'
commands=[]
for name,source,flags,extra in [
 ('ui','tests/pi_ui_test.c',['-DPI_UI=1','-DPI_EVENTS=1','-DPI_UI_TEST=1','-DPI_UI_NATIVE_TEST=1','-I.local/phase1-ui-native'],[]),
 ('events','tests/pi_events_test.c',['-DPI_EVENTS=1','-DPI_EVENTS_NATIVE_TEST=1','-I.local/phase1-events-native'],['src/pi_events.c']),
 ('observation','tests/pi_observation_test.c',['-DPI_EVENTS=1','-I.local/phase1-events-native'],['src/pi_events.c'])]:
 out=ROOT/'.local'/('pokebook01-retained-'+name)
 commands += [(['clang','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-D__attribute__(x)=',*flags,source,*extra,'-o',str(out)],name+'-compile.log'),([str(out)],name+'-c.log')]
results=[]
for argv,name in commands:
 with (E/name).open('w') as f:
  f.write(json.dumps({'argv':argv})+'\n');f.flush();p=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
 results.append({'argv':argv,'exitCode':p.returncode,'log':name})
 if p.returncode:break
(E/'retained-c.json').write_text(json.dumps(results,indent=2)+'\n')
raise SystemExit(results[-1]['exitCode'])
