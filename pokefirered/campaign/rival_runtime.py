"""Rival-only acceptance binding over the accepted ordered scheduler."""
import json
from pathlib import Path
from .expansion_runtime import ExpansionServices
from .provider import E,LEDGER
from .budget import CampaignBudget
from strategy.selection import public_candidates
from world.store import dump
ACTOR='trainer:fr:trainer:0326'
class RivalServices(ExpansionServices):
 participation_scope={ACTOR}
 def strategy(self,job):
  packet=job['packet']
  if packet['scope']['actor']!=ACTOR or packet['modelInput']['encounter']['nativeTrainerID']!=334:raise ValueError('rival_strategy_scope')
  if len(dump(packet).encode('utf-8'))>8192:raise ValueError('rival_context_budget')
  return super().strategy(job)
 def charge_hermes(self,job,model,request_hash):
  scope=self.mailbox.call(lambda w:w._job(job)[1])
  if scope['actorID']!=ACTOR:raise ValueError('rival_hermes_scope')
  with CampaignBudget(LEDGER) as budget:
   n=budget.charge('puppeteer',job,model,request_hash);value=budget.read()
   value['attempts'][n-1].update(scope={'campaign':scope['campaignID'],'branch':scope['branchID'],'actor':scope['actorID'],'battleID':scope['battleID']},verifiedFree=True);budget.write(value);return n
 def tick(self,w):
  # A production packet is audited before the inherited scheduler begins its job.
  if self.live and not self.stopped and self.worker is None and not w.pending_save() and w.campaign()['status'] in ('paired','imported') and ACTOR in getattr(w.content,'delta',{}).get('participation',{}) and not any(m['actor']==ACTOR for m in w.memo_records()):
   from strategy.provider import live_configuration
   binding,_=live_configuration();packet=w.context_packet(ACTOR,provider_binding=binding);audit=w.last_selection_audit;rows=public_candidates(w,ACTOR)
   private={r['memoryID'] for r in w.virality_state()['intel'].values()}
   if private & (set(audit['selectedEvidenceIDs'])|{r['evidenceID'] for r in rows}):raise ValueError('rival_private_intel_leak')
   if len(dump(packet).encode())>8192:raise ValueError('rival_context_budget')
   (E/'live-strategy-context.json').write_text(dump(packet)+'\n')
   (E/'live-selection-audit.json').write_text(json.dumps({**audit,'allEligiblePublicReceipts':rows,'privateRocketReceiptsExcluded':len(private),'privateRocketIncluded':0},indent=2)+'\n')
  return super().tick(w)
