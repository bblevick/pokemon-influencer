#!/usr/bin/env python3
"""Fresh official Hermes, read-only actor grant. Mocked inference by default."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from puppeteer.runtime import open_store,run_job
p=argparse.ArgumentParser();p.add_argument('--database',type=Path,required=True);p.add_argument('--actor',required=True);p.add_argument('--live',action='store_true');p.add_argument('--experiment',choices=['original','closeout'],default='original');a=p.parse_args()
with open_store(a.database) as w:j=w.begin_recall_job(a.actor)
r=run_job(a.database,j['jobID'],transport='live' if a.live else 'mock',live=a.live,behavior='recall',experiment=a.experiment)
print(json.dumps({'jobID':j['jobID'],'runtimeHome':r['runtimeHome'],'transport':r['transport'],'outcome':r['outcome'],'failures':r['failures']}))
