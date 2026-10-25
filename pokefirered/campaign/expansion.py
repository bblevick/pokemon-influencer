"""Generic participation/content adoption over the accepted campaign writer."""
import copy,json
from dataclasses import asdict
from .store import CampaignStore
from content.policy import OpeningContent
from content.campaign import CampaignContent
from prep.companions import authored_companions
from roster.extract import digest
from strategy.memo import memo_context,memo_configuration
from strategy.social_context import build_social_evidence
from .context import PROMPT

class ExpansionStore(CampaignStore):
 _supports_campaign_content=True
 content_type=CampaignContent
 def __init__(self,*a,**kw):
  self._extension_ready=False;super().__init__(*a,**kw)
  self._base_content=self.content;self._expanded_content=self.content_type.load();self._extension_ready=True;self._select_content()
 def _select_content(self):
  receipt=self.preparation_state().get('contentExtension')
  if receipt:
   if receipt['contentSHA256']!=self._expanded_content.hash:raise ValueError('campaign content changed; explicit future version adoption required')
   self.content=self._expanded_content
  else:self.content=self._base_content
 def _after_memory_transaction(self):
  super()._after_memory_transaction()
  if self._extension_ready:self._select_content()
 def adopt_content(self):
  def action():
   current=self.preparation_state().get('contentExtension')
   if current:return current
   self._writable()
   if self.pending_save() or not self.preparation_state()['progression'] or not all(self.preparation_state()['progression']['flags'].values()):raise ValueError('paired Boulder progression required')
   extension=self._expanded_content;receipt={'contentSHA256':extension.hash,'baseContentSHA256':self._base_content.hash,'version':extension.extension['version'],'packID':extension.extension['packID']}
   self._append_prep('CONTENT_ADOPTED',receipt['packID'],receipt)
   for actor,t in extension.extension['trainers'].items():
    self._append_prep('INITIALIZED',actor,{'actor':actor,'companions':[asdict(c) for c in authored_companions(extension.cat,actor,t['sourceTrainer'])],'resources':{'owner':actor,'stock':[],'categories':t['resources']['categories'],'restock':False,'contentSHA256':extension.hash,'sourceTrainer':t['sourceTrainer']},'sourceTrainer':t['sourceTrainer'],'retainedOrigins':t['retainedOrigins'],'active':True})
   return receipt
  return self._tx(action)
 def context_packet(self,actor,stage='first',purpose='preparation',provider_binding=None):
  if not isinstance(self.content,CampaignContent) or actor not in self.content.extension['participation']:return super().context_packet(actor,stage,purpose,provider_binding)
  profile=self.content.extension['participation'][actor];p=memo_context(self,actor,stage,purpose,provider_binding);social=build_social_evidence(self,actor)
  p['modelInput']['authorizedSocialEvidence']={k:copy.deepcopy(social[k]) for k in ('schemaVersion','actorID','authorizedFacts','unknowns','truncated')}
  p['modelInput']['opponentCurrentLead']='UNKNOWN';p['modelInput']['campaignBehavior']={'reference':self.content.extension['packID']+':'+actor,'identity':profile['persona'],'preparation':'authored first encounter; no new levels, companions or supplies'}
  v=digest([memo_configuration(),PROMPT.read_text(),self.content.hash,'campaign-scouting-v1']);p['scope'].update(configurationSHA256=v,promptVersion=3,socialContextVersion=3)
  p['materialContextSHA256']=digest([p['modelInput'],p['scope']['opportunityID'],purpose,v,p['scope']['providerConfiguration']]);p.pop('contextID');p['contextID']='strategy-context:'+digest(p)
  if len(json.dumps(p['modelInput']).encode())>24576:raise ValueError('campaign strategy input bound')
  return p

 def observe_native_preparation(self,state):
  if state['trainerID'] not in [n for p in self._expanded_content.extension['participation'].values() for n in p.get('qualifiedSourceIDs',[p['sourceTrainer']])]:return super().observe_native_preparation(state)
  actor='trainer:'+self.registry['mapping'][str(state['trainerID'])];lock=self.locked_preparation(actor)
  if not lock:return
  if lock['encounterID'] in self.decision_state()['installations']:return
  count=getattr(self,'native_constructions',{}).get((state['nonce'],state['generation'],state['trainerID']))
  if count is None:raise ValueError('missing generic native constructor receipt')
  receipt={'nonce':state['nonce'],'generation':state['generation'],'commitmentDigest':lock['commitmentID'].split(':')[1],'nativeROM':self.compatibility['nativeROM'],'party':[{k:p[k] for k in ('species','level','moves','heldItem')} for p in state['own']],'nativeConstructorCount':1,'cumulativeNativeConstructorCount':count,'source':'native authored CreateNPCTrainerParty; consecutive counter delta exactly one checked by transport','battle':state['battle']}
  self.record_installation(lock['encounterID'],receipt)

 def _follow_eligible(self,actor):
  if getattr(self,'_extension_ready',False) and isinstance(self.content,CampaignContent):
   profile=self.content.extension['participation'].get(actor)
   if profile:return profile['follow']=='first-defeat'
  return super()._follow_eligible(actor)
