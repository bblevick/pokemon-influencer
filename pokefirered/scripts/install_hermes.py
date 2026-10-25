#!/usr/bin/env python3
"""Reproduce the reviewed project-local official Hermes install; never touch homes."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(argv,**kwargs):subprocess.run(list(map(str,argv)),cwd=ROOT,check=True,**kwargs)
p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');a=p.parse_args()
lock=json.loads((ROOT/'config/hermes_runtime.lock.json').read_text());source=ROOT/'.local/hermes-source';venv=ROOT/'.local/hermes-venv';bootstrap=ROOT/'.local/hermes-bootstrap'
if not source.exists():
    if a.verify_only:raise SystemExit('pinned source unavailable')
    run(['git','clone','--depth','1','--branch',lock['releaseTag'],lock['repository'],source])
revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
if revision!=lock['revision']:raise SystemExit('existing source differs; no destructive checkout/reset performed')
if subprocess.check_output(['git','-C',str(source),'diff','--name-only'],text=True).strip():raise SystemExit('Hermes source modified')
if (source/'.env').exists():raise SystemExit('source dotenv must be absent')
for filename,key in [('uv.lock','uvLockSHA256'),('pyproject.toml','pyprojectSHA256')]:
    if hashlib.sha256((source/filename).read_bytes()).hexdigest()!=lock[key]:raise SystemExit('source manifest checksum mismatch')
if not a.verify_only:
    if not bootstrap.exists():run([sys.executable,'-m','venv',bootstrap])
    run([bootstrap/'bin/python','-m','pip','install','uv=='+lock['uvVersion']])
    # uv may install the pinned CPython from its normal package-managed source.
    if not venv.exists():run([bootstrap/'bin/uv','venv','--python',lock['runtimePython'].removeprefix('Python '),venv])
    env=dict(os.environ,UV_PROJECT_ENVIRONMENT=str(venv))
    run([bootstrap/'bin/uv','sync','--project',source,'--locked','--no-default-groups','--no-install-project'],env=env)
    run([venv/'bin/python','-m','compileall','-q',source,venv/'lib'])
version=subprocess.check_output([str(venv/'bin/python'),'--version'],text=True).strip()
if version!=lock['runtimePython']:raise SystemExit('runtime Python pin mismatch')
print(json.dumps({'revision':revision,'runtimePython':version,'uvLockSHA256':lock['uvLockSHA256'],'verifyOnly':a.verify_only,'installationSeparateFromDisposableHomes':True}))
