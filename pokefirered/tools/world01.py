#!/usr/bin/env python3
"""Offline world commands. No inference or implicit imported-save attachment."""
import argparse,json,sys,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from world.store import WorldStore
from world.saves import fingerprint,layout_from_build
from phase1_ui_build import verify_ui
E=ROOT/'evidence/phase2/world01'
def manifest():
 m=json.loads((ROOT/'evidence/phase1/bridge03/manifest-enabled.json').read_text());verify_ui(m);return m
def open_store(path):
 m=manifest();return WorldStore(path,m['rom_sha256'],m['build_tag'])
def save_identity(path):
 m=manifest();return fingerprint(Path(path).read_bytes(),layout_from_build(ROOT/m['rom_path']))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--database',type=Path,default=ROOT/'.local/world01/world.sqlite3');p.add_argument('command',choices=['import','fingerprint','state','replay','branches','save-begin','save-abandon']);p.add_argument('--save',type=Path);p.add_argument('--intent');a=p.parse_args();a.database.parent.mkdir(parents=True,exist_ok=True)
 if a.command=='fingerprint':result=save_identity(a.save).as_dict()
 else:
  if a.command in ('state','replay','branches'):
   with sqlite3.connect('file:'+str(a.database)+'?mode=ro',uri=True) as db:
    meta={k:json.loads(v) for k,v in db.execute('SELECT key,value FROM metadata')}
   store=WorldStore(a.database,meta['build'],meta['tag'])
  else:store=open_store(a.database)
  with store as w:
   if a.command=='import':result=w.import_save(save_identity(a.save))
   elif a.command=='state':result={'campaign':w.campaign(),'state':w.state()}
   elif a.command=='replay':result={'state':w.replay(),'sha256':w.verify_replay()}
   elif a.command=='branches':result=[dict(r) for r in w.db.execute('SELECT * FROM branches')]
   elif a.command=='save-abandon':w.abandon_save(a.intent);result={'incomplete':a.intent}
   else:
    cfg=json.loads((ROOT/'.local/world01-launch.json').read_text());result={'intent':w.begin_save(cfg['nonce'],save_identity(a.save or cfg['save']))}
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
