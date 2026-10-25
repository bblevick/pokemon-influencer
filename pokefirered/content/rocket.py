"""Additive source-bound Rocket first encounter; accepted ordinary pack immutable."""
import copy,json
from .campaign import CampaignContent
from .policy import ROOT
from roster.extract import digest,file_hash

class RocketContent(CampaignContent):
 VERSION=2
 @classmethod
 def load(cls,root=ROOT):
  previous=CampaignContent.load(root);delta=json.loads((root/'config/rocket_content.json').read_text())
  if delta['version']!=1 or delta['parentContentSHA256']!=previous.hash or delta['sourceCommit']!=previous.pack['sourceCommit'] or delta['nativeMemoryBudgetDelta']!=0 or delta['acquisitionsQualified']:raise ValueError('Rocket content parent/version mismatch')
  if set(delta['trainers'])!=set(delta['participation']) or set(delta['trainers'])&set(previous.pack['trainers']):raise ValueError('Rocket content identity overlap')
  social=json.loads((root/'config/virality_policy.json').read_text())
  for actor,t in delta['trainers'].items():
   profile=social['profiles'][actor]
   if profile['rocketRole']!='member' or profile['sourceClass']!='TRAINER_CLASS_TEAM_ROCKET' or profile['prominence']!='ordinary' or profile['scouting'] is not None or t['sourceTrainer'] not in profile['sourceTrainerIDs']:raise ValueError('Rocket trusted source membership required')
   if delta['participation'][actor]['follow']!='excluded-hostile':raise ValueError('Rocket hostile follow policy required')
  leaders=[a for a,p in social['profiles'].items() if p['rocketRole']=='leader']
  if delta['leadershipRecipients']!=leaders or 'trainer:fr:trainer:0348' not in leaders:raise ValueError('Rocket leadership source binding')
  x=copy.deepcopy(previous.extension);x.update(version=2,packID=delta['packID'])
  for k in ('trainers','participation','sourceEvidence'):x[k].update(delta[k])
  instance=cls(previous.base,x);instance.previous=previous;instance.delta=delta
  return instance
 def follow_policy(self,actor):
  social=json.loads((ROOT/'config/virality_policy.json').read_text())
  return 'excluded-hostile' if social['profiles'].get(actor,{}).get('rocketRole')=='member' else super().follow_policy(actor)
