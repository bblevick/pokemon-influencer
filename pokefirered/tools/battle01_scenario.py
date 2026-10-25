#!/usr/bin/env python3
"""Bounded completion path; queued input alone is never an acceptance assertion."""
import sys,json,sqlite3,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 nonce=json.loads((ROOT/'.local/battle01/launch.json').read_text())['nonce']
 for step in range(8):
  subprocess.run([sys.executable,str(ROOT/'tools/battle01_input.py'),'a 20','key 9 0 360','shot complete-'+str(nonce)+'-'+str(step)],check=True,cwd=ROOT)
  db=sqlite3.connect(ROOT/'.local/battle01/world.sqlite3')
  found=any((r:=json.loads(row[0])).get('session')==nonce and r.get('eventType')=='BATTLE_ENDED' for row in db.execute('SELECT record FROM events'))
  db.close()
  if found:print('confirmed canonical BATTLE_ENDED',nonce);return
 raise RuntimeError('no confirmed battle end within bounded path')
if __name__=='__main__':main()
