#!/usr/bin/env python3
"""Read-only final UI build audit; no earlier evidence overwritten."""
import json,sys,shutil
from phase1_ui_build import ROOT,verify_ui
# Source hashes and physical ELF layout remain the accepted B3 evidence.
p=ROOT/'evidence/phase1/bridge03'/('manifest-disabled.json' if '--disabled' in sys.argv else 'manifest-enabled.json')
m=json.loads(p.read_text())
if '--disabled' not in sys.argv:verify_ui(m)
else:
 import hashlib
 if hashlib.sha256((ROOT/m['rom_path']).read_bytes()).hexdigest()!=json.loads((ROOT/'evidence/phase0/baseline.json').read_text())['sha256']:raise ValueError('disabled baseline differs')
print(json.dumps({'passed':True,'romSHA256':m['rom_sha256'],'staticPassed':m['static_passed'],'existingBuild':True}))
