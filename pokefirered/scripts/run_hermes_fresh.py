#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from puppeteer.runtime import run_job,open_store
p=argparse.ArgumentParser();p.add_argument('--database',type=Path,required=True);p.add_argument('--job');p.add_argument('--mode',choices=['offline','mock','shadow','enabled-test'],default='offline');p.add_argument('--live',action='store_true');p.add_argument('--experiment',choices=['original','closeout'],default='original');a=p.parse_args()
with open_store(a.database) as w:
    if a.live and a.mode not in ('shadow','enabled-test'):p.error('live requires explicit shadow or enabled-test mode')
    job=a.job
    if not job:
        o=next((o for o in w.puppeteer_state()['obligations'].values() if o['status']!='PUBLISHED'),None)
        if not o:p.error('no pending recap obligation')
        job=w.begin_job(o['obligationID'],a.mode)['jobID']
    if a.mode=='offline':print(json.dumps(w.fallback(job)));sys.exit(0)
record=run_job(a.database,job,transport='live' if a.live else 'mock',live=a.live,experiment=a.experiment)
print(json.dumps({'jobID':job,'runtimeHome':record['runtimeHome'],'transport':record['transport'],'requests':len(record['requests']),'tools':len(record['tools']),'outcome':record['outcome'],'failures':record['failures']}))
