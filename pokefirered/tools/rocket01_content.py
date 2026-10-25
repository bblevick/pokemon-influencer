#!/usr/bin/env python3
"""Source-derived first natural Rocket encounter; no game/domain writes."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from content.campaign import CampaignContent
from roster.extract import file_hash,digest

def generate():
 c=CampaignContent.load();n=352;actor=f'trainer:fr:trainer:{n:04d}';native=c.cat.own_baseline(actor,n);reg=c.registry['trainers'][native['worldTrainerID']]
 mapSource='data/maps/MtMoon_B2F/map.json';scriptSource='data/maps/MtMoon_B2F/scripts.inc';mp=json.loads((ROOT/mapSource).read_text());script='MtMoon_B2F_EventScript_Grunt2';obj=next(o for o in mp['object_events'] if o['script']==script)
 t=copy.deepcopy(c.base.pack['trainers']['trainer:fr:trainer:0116']);t.update(displayName='Rocket Grunt 2',worldTrainerID=native['worldTrainerID'],sourceTrainer=n,sourceVariants=[s['sourceID'] for s in reg['sourceRecords']],qualifiedVariant=n,mapEvidence=reg['mapReferences'],homeMap=mp['id'],regions={mp['id']:{'tier':'native','requires':[]}},originals=native['party'],retainedOrigins=[p['baselineKey'] for p in native['party']],signatureOrigins=[],theme=None,stages={'first':{'predicate':'boulder_required','targets':{p['baselineKey']:p['level'] for p in native['party']},'stageCeiling':max(p['level'] for p in native['party']),'gain':0}},designProvenance='ROCKET-01: first natural descending ladder from accepted Kent position; authored first encounter, zero catches/growth/supplies; hostile non-follow exception')
 t['resources'].update(owner=actor,initialBattleItems=native['battleItems'],initialHeldItems={p['baselineKey']:p['heldItem'] for p in native['party']})
 p={'sourceTrainer':n,'stage':'first','battleProfile':'authored-single-no-items','strategy':True,'recap':True,'follow':'excluded-hostile','persona':'A disciplined Rocket operative attached to existing companions. Pragmatic and secretive; learns only from authorized reports and visible battle events. Plans ordinary legal pressure, without inventing a complete opposing team.','preparationSelection':'sole-choice-only','mapID':mp['id'],'campaignStage':'mtmoon','script':script,'scriptSource':scriptSource,'mapSource':mapSource,'object':obj,'sourceClass':reg['sourceRecords'][0]['class']}
 files=[mapSource,scriptSource,'data/maps/MtMoon_1F/map.json','data/maps/MtMoon_B1F/map.json','src/data/trainers.h','src/data/trainer_parties.h','include/constants/opponents.h']
 return {'version':1,'packID':'early-kanto-rocket-1','parentContentSHA256':c.hash,'sourceCommit':c.pack['sourceCommit'],'trainers':{actor:t},'participation':{actor:p},'sourceEvidence':{f:file_hash(ROOT/f) for f in files},'leadershipRecipients':['trainer:fr:trainer:0348'],'acquisitionsQualified':False,'nativeMemoryBudgetDelta':0}
if __name__=='__main__':
 result=generate();path=ROOT/'config/rocket_content.json'
 if '--write' in sys.argv:path.write_text(json.dumps(result,indent=2)+'\n')
 elif json.loads(path.read_text())!=result:raise ValueError('stale Rocket content')
 print(json.dumps({'packID':result['packID'],'SHA256':digest(result)}))
