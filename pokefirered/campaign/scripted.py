"""Explicit future-opportunity adoption; history uses unchanged parent content."""
import copy,json
from .rocket import RocketStore
from content.scripted import ScriptedContent
from strategy.memo import memo_context,memo_configuration
from strategy.selection import public_candidates,select
from roster.hashes import digest
from world.store import dump,WorldError

class ScriptedStore(RocketStore):
 content_type=ScriptedContent
 def _select_content(self):
  receipt=self.preparation_state().get('contentExtension')
  if not receipt:self.content=self._base_content;return
  content=self._expanded_content
  while content is not None:
   if receipt['contentSHA256']==content.hash:self.content=content;return
   content=getattr(content,'previous',None)
  raise WorldError('unknown versioned scripted content receipt')
 def context_packet(self,actor,stage='first',purpose='preparation',provider_binding=None):
  if not isinstance(self.content,ScriptedContent) or actor not in self.content.delta['participation']:return super().context_packet(actor,stage,purpose,provider_binding)
  profile=self.content.delta['participation'][actor];rows=public_candidates(self,actor);audit=None
  policy=copy.deepcopy(self.content.selection_policy)
  base_model=None
  def transform(model,opportunity):
   nonlocal base_model
   model=copy.deepcopy(model);model['evidence']=[]
   model['evidenceLimitation']='selected public claims, attributed reports; counts denote independent origins, never action frequency'
   model['persona']={'reference':profile['encounterID']+':persona-v1','description':profile['persona']}
   model['encounter']={'encounterID':profile['encounterID'],'nativeTrainerID':profile['sourceTrainer'],'actorID':actor,'mapID':profile['mapID'],'campaignStage':profile['campaignStage'],'eventKind':'rival','preparation':'source-authored unchanged party; one legal candidate'}
   model['opponentCurrentLead']='UNKNOWN';base_model=model
   return select(rows,model,actor=actor,stage=profile['campaignStage'],opportunity=opportunity,policy=policy)[0]
  template=memo_context(self,actor,stage,purpose,provider_binding,context_transform=transform)
  # Resolve own state/envelope once; budget whole groups in the frozen snapshot.
  for budget in range(policy['maximumEvidenceBytes'],0,-256):
   packet=copy.deepcopy(template)
   packet['modelInput'],audit=select(rows,base_model,actor=actor,stage=profile['campaignStage'],opportunity=template['scope']['opportunityID'],policy=policy,evidence_budget=budget)
   packet['scope'].update(contextSelectionPolicyID=policy['policyID'],contextSelectionPolicyVersion=policy['version'],contextSelectionPolicySHA256=digest(policy),contextSelectionEvidenceBudget=budget,selectedEvidenceIDs=audit['selectedEvidenceIDs'],contextSchemaVersion=4)
   packet['materialContextSHA256']=digest([packet['modelInput'],packet['scope']['opportunityID'],purpose,packet['scope']['providerConfiguration'],digest(policy),audit['selectedEvidenceIDs']]);packet.pop('contextID');packet['contextID']='strategy-context:'+digest(packet)
   if len(dump(packet).encode('utf-8'))<=policy['targetModelBytes']:
    audit['canonicalPolicySHA256']=digest(policy);audit['usedEvidenceBudget']=budget;audit['bytesFullContextAfter']=len(dump(packet).encode('utf-8'));self.last_selection_audit=audit
    return packet
  raise WorldError('required context and provenance cannot fit 8192-byte contract')
 def prebattle_facts(self,actor):
  if not isinstance(self.content,ScriptedContent) or actor not in self.content.delta['participation']:return super().prebattle_facts(actor)
  memo=next((m for m in reversed(self.memo_records()) if m['actor']==actor),None)
  if memo:
   packet=json.loads(self._one('SELECT context FROM strategy_jobs WHERE id=?',(memo['jobID'],))['context'])
  else:packet=self.context_packet(actor)
  result=copy.deepcopy(packet['modelInput']['authorizedSocialEvidence']);result['contextSelection']=packet['modelInput']['contextSelection']
  if len(dump(result).encode('utf-8'))>8192:raise WorldError('frozen selected facts exceed bound')
  return result
