"""Versioned additive campaign content; historical opening pack stays immutable."""
import copy,json
from jsonschema import Draft202012Validator
from .policy import OpeningContent,ROOT
from roster.extract import digest,file_hash

class CampaignContent(OpeningContent):
 VERSION=1
 def follow_policy(self,actor):return 'first-defeat'
 def __init__(self,base,extension):
  # Validate the unchanged base through its original strict contract first.
  self.base=base;self.extension=copy.deepcopy(extension)
  self.pack=copy.deepcopy(base.pack);self.pack['trainers'].update(extension['trainers'])
  self.pack['version']=base.pack['version']+extension['version']
  self.data=base.data;self.basis=base.basis;self.registry=base.registry;self.cat=base.cat;self.adaptation=base.adaptation
  self.hash=digest(self.pack);self.validate()
 @classmethod
 def load(cls,root=ROOT):return cls(OpeningContent.load(root),json.loads((root/'config/campaign_content.json').read_text()))
 def validate(self):
  x=self.extension
  if x['version']!=self.VERSION or x['baseContentSHA256']!=self.base.hash or x['catalogSHA256']!=self.cat.hash or x['sourceCommit']!=self.data['sourceCommit'] or x['acquisitionsQualified'] or x['nativeMemoryBudgetDelta']!=0:raise ValueError('unqualified campaign content version')
  if set(x['trainers'])!=set(x['participation']) or set(x['trainers'])&set(self.base.pack['trainers']):raise ValueError('campaign identity overlap')
  if any(file_hash(ROOT/p)!=h for p,h in x['sourceEvidence'].items()):raise ValueError('stale campaign source')
  schema=json.loads((ROOT/'schemas/content/pack.schema.json').read_text())['properties']['trainers']['properties']['trainer:fr:trainer:0116']
  social=json.loads((ROOT/'config/virality_policy.json').read_text())
  for actor,t in x['trainers'].items():
   Draft202012Validator(schema).validate(t);native=self.cat.own_baseline(actor,t['sourceTrainer']);profile=x['participation'][actor]
   reg=self.registry['trainers'][native['worldTrainerID']];origins=[p['baselineKey'] for p in native['party']]
   if profile['sourceTrainer']!=t['sourceTrainer'] or profile['stage']!='first' or profile['battleProfile']!='authored-single-no-items' or profile['strategy'] is not True or profile['recap'] is not True or profile['follow']!=self.follow_policy(actor) or profile['preparationSelection']!='sole-choice-only':raise ValueError('unqualified campaign participation')
   stages=[s for s in social['progression'] if s['mapID']==t['homeMap']]
   if len(stages)!=1 or stages[0]['stageID']!=profile['campaignStage'] or social['encounterStages'].get(str(t['sourceTrainer']))!=profile['campaignStage'] or social['sourceActors'].get(str(t['sourceTrainer']))!=actor:raise ValueError('campaign progression binding')
   if t['originals']!=native['party'] or t['worldTrainerID']!=native['worldTrainerID'] or t['qualifiedVariant']!=native['id'] or t['sourceVariants']!=[s['sourceID'] for s in reg['sourceRecords']]:raise ValueError('campaign baseline identity')
   if native['doubleBattle'] or any(native['battleItems']) or any(p['heldItem'] for p in native['party']):raise ValueError('unqualified campaign mode/items')
   if t['retainedOrigins']!=origins or t['signatureOrigins'] or t['theme'] is not None:raise ValueError('ordinary campaign identity')
   mp=json.loads((ROOT/profile['mapSource']).read_text());objects=[o for o in mp['object_events'] if o['script']==profile['script']]
   if len(objects)!=1 or objects[0]!=profile['object'] or mp['id']!=t['homeMap'] or profile['mapID']!=t['homeMap']:raise ValueError('campaign map binding')
   source=(ROOT/profile['scriptSource']).read_text();body=source.split(profile['script']+'::',1)[1].split('\n\n',1)[0]
   if 'trainerbattle_single '+native['symbols'][0] not in body:raise ValueError('campaign encounter binding')
   if t['regions']!={t['homeMap']:{'tier':'native','requires':[]}} or t['stages']!={'first':{'predicate':'boulder_required','targets':{p['baselineKey']:p['level'] for p in native['party']},'stageCeiling':max(p['level'] for p in native['party']),'gain':0}}:raise ValueError('campaign first-stage bounds')
   expected=copy.deepcopy(self.base.pack['trainers']['trainer:fr:trainer:0116']['resources']);expected.update(owner=actor,initialBattleItems=native['battleItems'],initialHeldItems={p['baselineKey']:p['heldItem'] for p in native['party']})
   if t['resources']!=expected:raise ValueError('campaign resources')
