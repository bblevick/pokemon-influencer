#!/usr/bin/env python3
"""Reviewed wild encounter replay by bounded ordinary A input; no battle AI."""
import json,time
from phase1_ui_input import send,wait_shot,ROOT,E
from phase1_ui_scenario import records,mode
mode('normal')
rows=records('events.jsonl');start=next(r for r in reversed(rows) if r['eventType']=='BATTLE_STARTED');identity=start['session'],start['run'],start['battleID']
for i in range(40):
 ends=[r for r in records('events.jsonl') if (r['session'],r['run'],r['battleID'])==identity and r['eventType']=='BATTLE_ENDED']
 if ends:
  (E/'final-wild-regression.json').write_text(json.dumps({'identity':identity,'start':start,'end':ends[-1],'native_inputs':'default Fight/Tackle A; maximum40 segments; reviewed wild encounter','steps':i},indent=2)+'\n');print(json.dumps({'complete':True,'outcome':ends[-1]['payload']['outcome']}));break
 name='ui-wild-'+str(i);send('key 0 90 180','shot '+name);wait_shot(name)
else:raise RuntimeError('No accepted native battle end; review current menus')
