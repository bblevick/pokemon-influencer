#!/usr/bin/env python3
"""Reproducible BRIDGE-03 native scenarios after File>Load and Continue."""
import argparse,json,time,hashlib
from pathlib import Path
from phase1_ui_input import send,wait_shot,ROOT,E

def mode(name):
 (ROOT/'.local/ui-host-mode.json').write_text(json.dumps({'mode':name})+'\n')
def records(file):
 p=E/file
 return [json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []
def wait_response(start,kind,result,choice,seconds=15):
 deadline=time.monotonic()+seconds
 while time.monotonic()<deadline:
  rows=records('ui-responses.jsonl')[start:]
  for row in rows:
   if (row['commandType'],row['result'],row['choiceID'])==(kind,result,choice):return row
  time.sleep(.1)
 raise TimeoutError(f'No correlated response type={kind} result={result} choice={choice}')
def scenario(name,host_mode='normal',kind=1,result=0,choice=0):
 base=name
 if (ROOT/'evidence/private/bridge03'/f'{name}-shown.png').exists():name=base+'-'+str(len(records('scenarios.jsonl'))+1)
 mode(host_mode);start=len(records('ui-responses.jsonl'))
 commands=[f'ui {kind}','key 9 0 180',f'shot {name}-shown']
 if result==0:
  if kind==2 and choice==22:commands+=['key 7 6 15']
  commands+=['key 0 8 30',f'shot {name}-resumed']
 elif host_mode=='ui-timeout':commands=[f'ui {kind}','key 9 0 40',f'shot {name}-shown','key 9 0 100',f'shot {name}-resumed']
 else:commands+=[f'shot {name}-resumed']
 send(*commands);wait_shot(name+'-resumed');row=wait_response(start,kind,result,choice)
 # Let the receipt settle before the next diagnostic request.
 send('key 9 0 100',f'shot {name}-settled');wait_shot(name+'-settled')
 item={'scenario':base,'name':name,'host_mode':host_mode,'expected':{'kind':kind,'result':result,'choice':choice},'response':row,'screenshots':[]}
 for suffix in ['shown','resumed']:
  p=ROOT/'evidence/private/bridge03'/f'{name}-{suffix}.png';item['screenshots'].append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 with (E/'scenarios.jsonl').open('a') as f:f.write(json.dumps(item,sort_keys=True)+'\n')
 print(json.dumps(item),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('scenario',choices=['acceptance','faults','notice','choice']);a=p.parse_args()
 if a.scenario in ('notice','acceptance'):scenario('notice',kind=1)
 if a.scenario in ('choice','acceptance'):scenario('choice',kind=2,choice=22)
 if a.scenario=='faults':
  for name,status,kind in [('bad-schema',3,1),('bad-character',4,1),('bad-terminator',4,1),('bad-length',2,1),('bad-count',2,2),('bad-id',2,2),('oversized',2,1),('short',2,1),('ui-timeout',6,1)]:scenario(name,name,kind,status,0)
  for name in ['duplicate','stale','duplicate-response']:scenario(name,name)
 mode('normal')
