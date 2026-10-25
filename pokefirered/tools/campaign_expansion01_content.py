#!/usr/bin/env python3
"""Export source bindings and modest authored persona rows; no campaign writes."""
import json,copy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from content.policy import OpeningContent
from roster.extract import digest,file_hash

def generate():
 base=OpeningContent.load();rows={};profiles={}
 spec=[(117,'Sally','Route3','Sally','Confident and direct; respects Gym reports as reports, not certainty. Prefers pressure with her existing partners.'),(106,'Greg','Route3','Greg','Patient bug enthusiast; attached to both partners; willing to slow the opponent, without assuming a complete opposing team.'),(107,'James','Route3','James','Proud of his familiar bugs; cautious about public hype, values persistence and ordinary available tactics.'),(108,'Kent','MtMoon_1F','Kent','Curious cave explorer; pragmatic and moderately cautious, regards older route reports as incomplete scouting.')]
 for n,name,area,script,persona in spec:
  actor=f'trainer:fr:trainer:{n:04d}';native=base.cat.own_baseline(actor,n);reg=base.registry['trainers'][native['worldTrainerID']]
  mpath=f'data/maps/{area}/map.json';mp=json.loads((ROOT/mpath).read_text());event=f'{area}_EventScript_{script}'
  obj=next(o for o in mp['object_events'] if o['script']==event)
  spath=f'data/maps/{area}/scripts.inc' if reg['mapReferences'] else 'data/scripts/trainers.inc'
  source=(ROOT/spath).read_text();body=source.split(event+'::',1)[1].split('\n\n',1)[0]
  # VS Seeker scripts branch to separate rematches; this is the first-battle entry.
  if 'trainerbattle_single '+native['symbols'][0] not in body:raise ValueError('missing native singles source')
  if native['doubleBattle'] or any(native['battleItems']) or any(p['heldItem'] for p in native['party']):raise ValueError('unsupported pack format/items')
  row=copy.deepcopy(base.pack['trainers']['trainer:fr:trainer:0116']);origins=[p['baselineKey'] for p in native['party']]
  row.update(displayName=name,worldTrainerID=native['worldTrainerID'],sourceTrainer=n,sourceVariants=[s['sourceID'] for s in reg['sourceRecords']],qualifiedVariant=n,mapEvidence=reg['mapReferences'] or [f'src/vs_seeker.c:{name} {mp["id"]}',f'{spath}:{event}'],homeMap=mp['id'],regions={mp['id']:{'tier':'native','requires':[]}},originals=native['party'],retainedOrigins=origins,signatureOrigins=[],theme=None,stages={'first':{'predicate':'boulder_required','targets':{p['baselineKey']:p['level'] for p in native['party']},'stageCeiling':max(p['level'] for p in native['party']),'gain':0}},designProvenance='CAMPAIGN-EXPANSION-01: authored first-encounter retention; no new resources/growth/move teaching/catches')
  row['resources'].update(owner=actor,initialBattleItems=native['battleItems'],initialHeldItems={p['baselineKey']:p['heldItem'] for p in native['party']})
  rows[actor]=row
  profiles[actor]={'sourceTrainer':n,'stage':'first','battleProfile':'authored-single-no-items','strategy':True,'recap':True,'follow':'first-defeat','persona':persona,'preparationSelection':'sole-choice-only','mapID':mp['id'],'campaignStage':'route3' if area=='Route3' else 'mtmoon','script':event,'scriptSource':spath,'mapSource':mpath,'object':obj,'sourceClass':reg['sourceRecords'][0]['class']}
 files={p:file_hash(ROOT/p) for p in sorted({v[k] for v in profiles.values() for k in ('mapSource','scriptSource')}|{'src/data/trainers.h','src/data/trainer_parties.h','src/vs_seeker.c'})}
 return {'version':1,'packID':'early-kanto-ordinary-1','sourceCommit':base.pack['sourceCommit'],'baseContentSHA256':base.hash,'catalogSHA256':base.cat.hash,'sourceEvidence':files,'trainers':rows,'participation':profiles,'acquisitionsQualified':False,'nativeMemoryBudgetDelta':0}
if __name__=='__main__':
 p=ROOT/'config/campaign_content.json';result=generate()
 if '--write' in sys.argv:p.write_text(json.dumps(result,indent=2)+'\n')
 elif json.loads(p.read_text())!=result:raise ValueError('stale campaign content')
 print(json.dumps({'packID':result['packID'],'SHA256':digest(result),'trainers':list(result['trainers']),'sourceBound':True}))
