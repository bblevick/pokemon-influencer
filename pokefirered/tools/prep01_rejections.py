#!/usr/bin/env python3
"""Explicit invalid host counterexamples against the actual paired Rick envelope."""
import json,copy
from prep01 import E,open_store
from prep.domain import resolve_preparation_envelope,generate_preparation_candidates,validate_preparation_candidate
from roster.extract import digest
with open_store('.local/prep01/world.sqlite3') as w:
 e=resolve_preparation_envelope(w,'trainer:fr:trainer:0102');packages=generate_preparation_candidates(e)['candidates'];results=[]
 def reject(label,c):
  c['validation']={};c['descriptors']={};c['candidateID']='candidate:'+digest({k:v for k,v in c.items() if k not in ('candidateID','validation','descriptors')})
  proof=validate_preparation_candidate(e,c,w)
  if proof['valid']:raise ValueError('counterexample accepted: '+label)
  results.append({'example':label,'candidateID':c['candidateID'],'envelopeID':c['envelopeID'],'rejection':proof,'counterexampleOnly':True})
 c=copy.deepcopy(packages[0]);c['resourceCosts']=[[4,1]];reject('one capture item despite zero finite stock and opening acquisition allowance',c)
 c=copy.deepcopy(packages[0]);lineage=c['party'][0]['lineage'];c['paths'][lineage]=[{'kind':'level','species':13,'level':7,'value':0,'slot':0},{'kind':'evolution','species':15,'level':7,'value':0,'slot':0}];c['party'][0].update(species=15,level=7);reject('Weedle directly to Beedrill without Kakuna path',c)
 for move in [78,79,16]:
  c=copy.deepcopy(next(x for x in packages if any(p['species']==12 for p in x['party'])));partner=next(p for p in c['party'] if p['species']==12);partner['moves'][0]=move;c['paths'][partner['lineage']].append({'kind':'level_move','species':12,'level':10,'value':move,'slot':0});reject('Butterfree move '+str(move)+' prematurely at level 10',c)
 (E/'rejected-options.json').write_text(json.dumps({'evidenceKind':'invalid host counterexamples derived from actual paired Rick envelope; not native team changes','results':results,'sourceCommit':w.content.pack['sourceCommit'],'catalogSHA256':w.content.cat.hash,'sideEffects':False},indent=2)+'\n')
 print(json.dumps({'rejected':len(results),'reasons':[x['rejection']['reason'] for x in results]}))
