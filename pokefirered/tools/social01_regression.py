#!/usr/bin/env python3
"""Retained Phase0/1 regressions, independent Phase2 reports and logs."""
import json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence/phase2/social01/regressions';E.mkdir(parents=True,exist_ok=True)
def run(argv,name):
 with (E/name).open('w') as f:
  f.write(json.dumps({'argv':argv})+'\n');f.flush();result=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
 results.append({'argv':argv,'exitCode':result.returncode,'log':str((E/name).relative_to(ROOT))})
 if result.returncode:raise RuntimeError(name)
results=[]
try:
 run([sys.executable,'-m','unittest','discover','-s','tests','-v'],'host.log')
 # All source builds are unchanged; rerun actual C sanitizers and audited ARM
 # existing-build verifiers. Preserve previous manifests/evidence.
 for phase,prefix,source in [('ping','phase1-ui-ping','evidence/phase1/bridge03/ping-regression'),('events','phase1-ui-events','evidence/phase1/bridge03/events-regression')]:
  out=E/phase;out.mkdir(exist_ok=True)
  for n in ['manifest-enabled.json','manifest-disabled.json']:shutil.copy2(ROOT/source/n,out/n)
  tool='tools/phase1_test.py' if phase=='ping' else 'tools/phase1_events_test.py'
  run([sys.executable,tool,'--build-prefix',prefix,'--evidence-dir',str(out.relative_to(ROOT))],phase+'.log')
 # Parameterize the retained UI runner's evidence constant only. Its actual
 # native compiler/test commands and build verification remain unchanged.
 script=(ROOT/'tools/phase1_ui_test.py').read_text().replace("E=ROOT/'evidence/phase1/bridge03'", "E=ROOT/'evidence/phase2/social01/regressions/ui'")
 script=script.replace("[sys.executable,'tools/phase1_ui_build.py','--verify-existing']", "[sys.executable,'tools/world01_verify_ui.py']").replace("[sys.executable,'tools/phase1_ui_build.py','--disabled','--verify-existing']", "[sys.executable,'tools/world01_verify_ui.py','--disabled']")
 (E/'ui').mkdir(exist_ok=True);runner=ROOT/'tools/.social01-ui-regression.py';runner.write_text(script)
 try:run([sys.executable,str(runner)],'ui.log')
 finally:runner.unlink()
 for tool,name in [('pokemon_influencer_handoff/tools/validate_handoff.py','handoff'),('tools/validate_ai_contracts.py','architecture'),('tools/verify_phase0_emulator.py','retained-phase0'),('tools/verify_phase1_emulator.py','retained-ping'),('tools/verify_phase1_events_emulator.py','retained-events'),('tools/verify_phase1_ui_emulator.py','retained-ui'),('tools/verify_world01.py','retained-world'),('tools/verify_memory01.py','retained-memory'),('tools/social_species_catalog.py','source-species')]:run([sys.executable,tool],name+'.log')
finally:
 (E/'results.json').write_text(json.dumps({'scope':'host, C sanitizers, existing ARM build, handoff, architecture and retained live evidence; no new earlier-phase playthrough','results':results,'passed':bool(results) and all(r['exitCode']==0 for r in results)},indent=2)+'\n')
