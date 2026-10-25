#!/usr/bin/env python3
"""Reproducible source-record catalog from the pinned Git tree (no ROM data)."""
import json,re,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PIN='037335f4c725d7c9aecdac87066f2002b4bd7e14'
def source(path):return subprocess.check_output(['git','show',PIN+':'+path],cwd=ROOT,text=True)
def generate():
 constants={k:int(v) for k,v in re.findall(r'#define (TRAINER_\w+)\s+(\d+)',source('include/constants/opponents.h'))}
 blocks=dict(re.findall(r'\[(TRAINER_\w+)\] = \{(.*?)(?=\n    \},)',source('src/data/trainers.h'),re.S))
 families=[]
 table=source('src/vs_seeker.c').split('sRematches[] = {',1)[1].split('\n};',1)[0]
 for ids,mapname in re.findall(r'\{ \{(.*?)\},\s*MAP\((MAP_\w+)\) \}',table,re.S):
  slots=[constants[x.strip()] if x.strip() in constants else None for x in ids.split(',')]
  if slots and slots[0]:families.append({'kind':'vs_seeker','sourceIDs':sorted(set(x for x in slots if x)), 'slots':slots,'map':mapname})
 # Explicit story-person bindings, not a name-based or suffix-based heuristic.
 families += [{'kind':'story_rival','sourceIDs':sorted(v for k,v in constants.items() if k.startswith(('TRAINER_RIVAL_','TRAINER_CHAMPION_')))}, {'kind':'story_giovanni','sourceIDs':[348,349,350]}]
 for name in ('LORELEI','BRUNO','AGATHA','LANCE'):
  families.append({'kind':'elite_four_variant','sourceIDs':[constants['TRAINER_ELITE_FOUR_'+name],constants['TRAINER_ELITE_FOUR_'+name+'_2']]})
 maps={k:[] for k in constants}
 paths=subprocess.check_output(['git','ls-tree','-r','--name-only',PIN,'data/maps'],cwd=ROOT,text=True).splitlines()
 for path in paths:
  if path.endswith('scripts.inc'):
   for k in set(re.findall(r'\bTRAINER_\w+\b',source(path))):
    if k in maps:maps[k].append(path)
 mapping={};people={}
 for k,n in sorted(constants.items(),key=lambda x:x[1]):
  if not n or k not in blocks:continue
  family=next((f for f in families if n in f['sourceIDs']),None)
  base=family['sourceIDs'][0] if family else n
  wid=f'fr:trainer:{base:04d}'
  block=blocks[k];name=re.search(r'\.trainerName = _\("(.*?)"\)',block);cls=re.search(r'\.trainerClass = (\w+)',block)
  mapping[str(n)]=wid
  p=people.setdefault(wid,{'worldTrainerID':wid,'primarySourceID':base,'sourceRecords':[], 'rematchFamily':family,'mapReferences':[]})
  p['sourceRecords'].append({'sourceID':n,'constant':k,'name':name.group(1) if name else '', 'class':cls.group(1) if cls else None,'scripts':maps[k]})
  p['mapReferences']=sorted(set(p['mapReferences']+maps[k]))
 output={'registryVersion':1,'sourceCommit':PIN,'mapping':mapping,'trainers':people,'families':families,'identityPolicy':'Explicit source rematch/story families only; equal display names do not merge people. Multi-trainer records remain a composite identity. Unused records are catalogued, not asserted encountered.'}
 output['catalogSHA256']=hashlib.sha256(json.dumps(output,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 return output
if __name__=='__main__':
 out=generate();path=ROOT/'config/trainer_registry.json';path.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'sourceRecords':len(out['mapping']),'worldIdentities':len(out['trainers']),'families':len(out['families']),'rick':out['trainers'][out['mapping']['102']],'catalogSHA256':out['catalogSHA256']},indent=2))
