#!/usr/bin/env python3
"""Read-only PREP report: complete packages, no selection or installation."""
import argparse,json,sqlite3
from pathlib import Path
from prep01 import open_store,ROOT
from prep.domain import resolve_preparation_bundle

def report(database,actor,stage):
    # A viewer must not implicitly migrate a foundation archive.
    with sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True) as reader:
        if not reader.execute("SELECT name FROM sqlite_master WHERE name='prep_version'").fetchone():raise ValueError('explicit PREP migration/activation required before reporting')
    with open_store(database) as store:
        before=[store.verify_replay(),store.verify_memory_replay(),store.verify_social_replay(),store.verify_puppeteer_replay(),store.preparation_state()]
        result=resolve_preparation_bundle(store,actor,stage)
        after=[store.verify_replay(),store.verify_memory_replay(),store.verify_social_replay(),store.verify_puppeteer_replay(),store.preparation_state()]
        if before!=after:raise ValueError('report changed history')
        return {'actor':actor,'stage':stage,'campaign':store.campaign(),'companionState':store.get_trainer_companion_state(actor),
                'resourceState':store.get_trainer_resource_state(actor),'opportunity':store.get_preparation_opportunity(actor,stage),
                'result':result,'sideEffects':False,'modelsCalled':False,'teamSelected':False,'teamInstalled':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--database',required=True);p.add_argument('--actor',required=True);p.add_argument('--stage',default='forest-post-boulder-1');p.add_argument('--out',type=__import__('pathlib').Path,required=True);a=p.parse_args();r=report(a.database,a.actor,a.stage);a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['result']['status'],'output':str(a.out)}))
