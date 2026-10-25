#!/usr/bin/env python3
"""Offline replay: SQLite or canonical fixture. No ROM/emulator/network required."""
import argparse,json,hashlib,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from world.store import WorldStore,dump,SCHEMA
from world import reducer
from bridge.events import JSON_VALIDATOR

def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--database',type=Path);g.add_argument('--fixture',type=Path);p.add_argument('--export',type=Path);a=p.parse_args()
 registry=json.loads((ROOT/'config/trainer_registry.json').read_text())
 if a.database:
  with sqlite3.connect('file:'+str(a.database)+'?mode=ro',uri=True) as db:meta={k:json.loads(v) for k,v in db.execute('SELECT key,value FROM metadata')}
  with WorldStore(a.database,meta['build'],meta['tag']) as w:
   state=w.replay();digest=w.verify_replay();fixture={'schemaVersion':SCHEMA,'reducerVersion':reducer.VERSION,'registrySHA256':registry['catalogSHA256'],'romSHA256':meta['build'],'events':w.get_canonical_events(),'expectedState':state,'stateSHA256':digest}
  if a.export:a.export.write_text(json.dumps(fixture,indent=2)+'\n')
 else:
  fixture=json.loads(a.fixture.read_text())
  if (fixture['schemaVersion'],fixture['reducerVersion'],fixture['registrySHA256'])!=(SCHEMA,reducer.VERSION,registry['catalogSHA256']):raise ValueError('incompatible replay fixture')
  state=reducer.empty()
  for event in fixture['events']:
   JSON_VALIDATOR.validate(event['record']);reducer.apply(state,event,registry)
  digest=hashlib.sha256(dump(state).encode()).hexdigest()
  if digest!=fixture['stateSHA256'] or state!=fixture['expectedState']:raise ValueError('fixture replay mismatch')
 print(json.dumps({'passed':True,'cursor':state['cursor'],'stateSHA256':digest,'mode':'offline canonical replay','state':state},indent=2))
if __name__=='__main__':main()
