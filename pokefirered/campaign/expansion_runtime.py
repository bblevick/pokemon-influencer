"""One ordered, data-driven first-encounter scheduler; no per-trainer branches."""
import json,re
from .runtime import Services
from .provider import E
from .budget import CampaignBudget
from .provider import LEDGER
from strategy.provider import live_configuration as configuration
from strategy.memo import validate_text,fallback_text
from puppeteer.runtime import run_job
from system1.provider import run_selection

class ExpansionServices(Services):
 participation_scope=None
 def tick(self,w):
  self.mailbox.drain(w)
  if self.worker is not None:
   if not self.worker.done():return
   try:result=self.worker.result()
   except Exception as error:
    code=str(error)
    result={'failure':type(error).__name__,'diagnostics':getattr(error,'diagnostics',{}),'code':code if re.fullmatch(r'[a-z][a-z0-9_]{0,95}',code) else 'unspecified'}
   if self.kind=='strategy':
    job=self.job
    try:
     if 'strategyText' in result:
      validate_text(result['strategyText']);memo=w.finish_memo(job['jobID'],result['strategyText'],'model',result['diagnostics'],job['packet']['contextID'])
     else:memo=w.finish_memo(job['jobID'],fallback_text(job['packet']),'fallback',result,job['packet']['contextID'])
     self.log('strategy-committed',memo=memo)
    except ValueError as error:self.log('strategy-stale',jobID=job['jobID'],reason=str(error))
   else:self.log('hermes-finished',result=result)
   self.worker=None;self.kind=None;self.job=None
  if self.stopped or w.pending_save() or w.campaign()['pending_fork'] or w.campaign()['status'] not in ('paired','imported'):return
  content=getattr(w.content,'extension',None)
  if content is None:return
  profiles={a:p for a,p in content['participation'].items() if self.participation_scope is None or a in self.participation_scope}
  obligation=next((o for o in w.puppeteer_state()['obligations'].values() if o['status']!='PUBLISHED'),None)
  if obligation:
   mode='enabled-test' if self.live and obligation['actorID'] in profiles else 'offline';job=w.begin_job(obligation['obligationID'],mode)
   self.log('recap-obligation',obligation=obligation,jobID=job['jobID'])
   if mode=='offline':self.log('recap-fallback',outcome=w.fallback(job['jobID']));return
   self.kind='puppeteer';self.job=job;self.worker=self.pool.submit(run_job,self.database,job['jobID'],transport='live',live=True,experiment='closeout',store_factory=self.mailbox.open,charge_request=self.charge_hermes,audit_directory=E/'hermes-jobs');return
  # Resolve only the next unfinished content encounter after previous recap/diffusion.
  # Travel/menus do not regenerate frozen memos. No social evidence is required.
  for actor,profile in profiles.items():
   battles=[b for b in w.state()['battles'].values() if b['trainerID']==w.content.pack['trainers'][actor]['worldTrainerID']]
   if any(b['ended'] for b in battles):continue
   if any(not b['ended'] for b in battles):return
   if w.locked_preparation(actor):return
   memos=[m for m in w.memo_records() if m['actor']==actor]
   if not memos:
    if w.db.execute("SELECT 1 FROM strategy_jobs WHERE status='revoked' AND json_extract(context,'$.scope.actor')=?",(actor,)).fetchone():return
    binding,_=configuration() if self.live else ({'provider':'template','model':'strategy-memo-fallback-v1','adapterVersion':1},None)
    job=w.begin_strategy(actor,profile['stage'],provider_binding=binding)
    self.log('trainer-context',actor=actor,context=job.get('packet'),jobID=job.get('jobID'))
    if job['status']=='recorded':return
    if self.live:
     w.count_attempt(job['jobID'],job['packet']['contextID']);self.kind='strategy';self.job=job;self.worker=self.pool.submit(self.strategy,job)
    else:self.log('strategy-committed',memo=w.finish_memo(job['jobID'],fallback_text(job['packet']),'fallback',{'provider':'template','costUSD':0},job['packet']['contextID']))
    return
   job=w.begin_selection(actor,profile['stage'])
   if job['status']=='committed':return
   if job['status']=='active' and len(job['request']['choices'])!=1:raise ValueError('unqualified multi-candidate campaign selection')
   decision=run_selection(w,job,source='fallback') if job['status']=='active' else job['decision']
   self.log('preparation-locked',actor=actor,commitment=w.commit_preparation(decision['decisionID']),soleChoiceBypass=True)
   return
