"""Event-driven scheduling only; accepted services retain all domain authority."""
import json,time,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from .writer import WriterMailbox
from .context import BROCK,PROMPT
from .provider import ROOT,E,LEDGER
from .budget import CampaignBudget
from puppeteer.runtime import run_job
from strategy.memo import fallback_text,validate_text
from strategy.provider import preflight_text,live_configuration as configuration,OpenRouterProvider,Limits
from system1.provider import run_selection

RICK='trainer:fr:trainer:0102'
class Services:
    def __init__(self,database,live=False,gym_closeout=False):
        self.gym_closeout=gym_closeout
        self.database=database;self.live=live;self.mailbox=WriterMailbox();self.pool=ThreadPoolExecutor(max_workers=1);self.worker=None;self.job=None;self.kind=None;self.strategy_process=None;self.stopped=False
    def log(self,event,**data):
        with (E/'causal-trace.jsonl').open('a') as f:f.write(json.dumps({'event':event,**data},sort_keys=True)+'\n')
    def charge_hermes(self,job,model,request_hash):
        scope=self.mailbox.call(lambda w:w._job(job)[1]) if self.gym_closeout else None
        with CampaignBudget(LEDGER) as budget:
            n=budget.charge('puppeteer',job,model,request_hash)
            if scope:
                value=budget.read();value['attempts'][n-1]['scope']={'campaign':scope['campaignID'],'branch':scope['branchID'],'actor':scope['actorID'],'battleID':scope['battleID']};value['attempts'][n-1]['verifiedFree']=True;budget.write(value)
            return n
    def strategy(self,job):
        boundary='configuration';binding=None
        try:
            binding,_=configuration();boundary='route_metadata'
            route=preflight_text(binding['model']);boundary='request_serialization'
            # Pure validation before creating a worker or charging any POST.
            validator=OpenRouterProvider(binding,'unused-preflight',route,None,None,system_prompt=PROMPT.read_text())
            body,encoded=validator.prepare_request(job['packet']['modelInput'],None,Limits(attempts=1),text=True)
            from roster.hashes import digest
            self.log('strategy-preflight-passed',jobID=job['jobID'],model=binding['model'],providers=route['providerNames'],requestSHA256=digest(body),inputBytes=len(encoded))
        except Exception as error:
            import re
            code=str(error);status=getattr(error,'code',None)
            from strategy.diagnostics import failure_diagnostics
            error.diagnostics=failure_diagnostics(error,job=job['jobID'],binding=binding,stage=boundary,packet=job['packet'])
            self.log('strategy-failure-diagnostic',diagnostics=error.diagnostics)
            self.log('strategy-preflight-failed',jobID=job['jobID'],boundary=boundary,errorClass=type(error).__name__,model=binding['model'] if binding else None,httpStatus=status if type(status)==int else None,code=code if re.fullmatch(r'[a-z][a-z0-9_]{0,95}',code) else 'unspecified')
            raise
        payload={'jobID':job['jobID'],'modelInput':job['packet']['modelInput'],'route':route}
        proc=subprocess.Popen([sys.executable,str(ROOT/'tools/vertical_slice01_worker.py'),'strategy'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,cwd=ROOT)
        self.strategy_process=proc
        try:
            out,err=proc.communicate(json.dumps(payload),timeout=40)
            if proc.returncode:
                error=ValueError('strategy_worker_unavailable')
                try:
                    detail=json.loads(err);diagnostics=detail.get('diagnostics')
                    if isinstance(diagnostics,dict) and diagnostics.get('schemaVersion')==1:
                        # This stderr comes from the project-owned fresh worker, not provider prose.
                        diagnostics.update(jobID=job['jobID'],contextID=job['packet'].get('contextID'),scope=job['packet'].get('scope',{}))
                        error.diagnostics=diagnostics
                        self.log('strategy-failure-diagnostic',diagnostics=diagnostics)
                except (ValueError,TypeError):pass
                raise error
            return json.loads(out)
        except Exception as error:
            from strategy.diagnostics import failure_diagnostics
            error.diagnostics=failure_diagnostics(error,job=job['jobID'],binding=binding,stage='worker_transport',packet=job['packet'])
            self.log('strategy-failure-diagnostic',diagnostics=error.diagnostics)
            raise
        finally:
            if proc.poll() is None:proc.terminate();proc.wait(timeout=3)
            self.strategy_process=None
    def tick(self,w):
        self.mailbox.drain(w)
        if self.worker is not None:
            if not self.worker.done():return
            try:result=self.worker.result()
            except Exception as error:result={'failure':type(error).__name__,'diagnostics':getattr(error,'diagnostics',{})}
            job=self.job
            if self.kind=='strategy':
                try:
                    if 'strategyText' in result:
                        validate_text(result['strategyText']);r=w.finish_memo(job['jobID'],result['strategyText'],'model',result['diagnostics'],job['packet']['contextID'])
                    else:r=w.finish_memo(job['jobID'],fallback_text(job['packet']),'fallback',result,job['packet']['contextID'])
                    self.log('strategy-committed',memo=r)
                except ValueError as error:
                    # No regenerated inference for a revoked/late job.
                    w._tx(lambda:w.db.execute("UPDATE strategy_jobs SET status='revoked' WHERE id=? AND status='active'",(job['jobID'],)))
                    self.log('strategy-stale',jobID=job['jobID'],reason=str(error))
            else:self.log('hermes-finished',result=result)
            self.worker=None;self.job=None;self.kind=None
        if self.stopped or w.pending_save() or w.campaign()['pending_fork'] or w.campaign()['status'] not in ('paired','imported'):return
        obligation=next((o for o in w.puppeteer_state()['obligations'].values() if o['status']!='PUBLISHED'),None)
        if obligation:
            if self.gym_closeout:
                battle=w.get_battle(obligation['battleID'])
                rows=[json.loads(x) for x in (E/'battle-audit.jsonl').read_text().splitlines()] if (E/'battle-audit.jsonl').exists() else []
                # This extra allowance is reserved for Brock's successful fully
                # live result, never another actor or a failed acceptance recap.
                events=[e for e in w.get_canonical_events() if e['battleID']==obligation['battleID']]
                session=next((e['record']['session'] for e in events if e['record']['eventType']=='BATTLE_STARTED'),None)
                native_battle=next((e['record']['battleID'] for e in events),None)
                terminals=[r for r in rows if r['event']=='native-terminal' and r.get('session')==session and r.get('battle')==native_battle]
                if obligation['actorID']!=BROCK or not battle or not battle['ended'] or battle['outcome']!=1 or not terminals or any(r['source'] not in ('mercury','engine_forced') for r in terminals):
                    return
            mode='enabled-test' if self.live and obligation['actorID'] in (RICK,BROCK) else 'offline'
            job=w.begin_job(obligation['obligationID'],mode)
            self.log('recap-obligation',obligation=obligation,jobID=job['jobID'])
            if mode=='offline':self.log('recap-fallback',outcome=w.fallback(job['jobID']));return
            self.kind='puppeteer';self.job=job
            self.worker=self.pool.submit(run_job,self.database,job['jobID'],transport='live',live=True,experiment='closeout',store_factory=self.mailbox.open,charge_request=self.charge_hermes,audit_directory=E/'hermes-jobs')
            return
        lock=w.locked_preparation(BROCK)
        if lock:return
        if self.gym_closeout:return
        # Exposure itself, never feed opening, qualifies this first-encounter job.
        facts=w.evidence_context(BROCK)['authorizedEvidence']
        relevant=[r for r in facts if r['mode']=='delivered' and r['claim'].get('trainerID')=='fr:trainer:0102']
        if not relevant:return
        # A paired information opportunity is recoverable before inference. It
        # does not grant growth, supplies or acquisitions. Browsing is unrelated.
        campaign=w.campaign();memory_cutoff=w._one('SELECT cutoff FROM memory_view')['cutoff']
        paired=w._one('SELECT 1 FROM checkpoints c JOIN memory_checkpoints m ON m.checkpoint=c.id WHERE c.branch=? AND c.cursor=? AND c.kind=? AND m.cutoff=?',(campaign['active_branch'],campaign['cursor'],'normal_save',memory_cutoff))
        if not paired:return
        memos=[r for r in w.memo_records() if r['actor']==BROCK]
        if not memos:
            # A stale consumed job stays recorded; don't spend another POST per tick.
            if w.db.execute("SELECT 1 FROM strategy_jobs WHERE status='revoked' AND json_extract(context,'$.scope.actor')=?",(BROCK,)).fetchone():return
            binding,_=configuration() if self.live else ({'provider':'template','model':'strategy-memo-fallback-v1','adapterVersion':1},None)
            try:job=w.begin_strategy(BROCK,'first',provider_binding=binding)
            except ValueError as error:self.log('strategy-ineligible',reason=str(error));return
            self.log('brock-scouted',authorizedFacts=w.prebattle_facts(BROCK),context=job.get('packet'),jobID=job.get('jobID'))
            if job['status']=='recorded':return
            if self.live:
                w.count_attempt(job['jobID'],job['packet']['contextID']);self.kind='strategy';self.job=job;self.worker=self.pool.submit(self.strategy,job)
            else:
                r=w.finish_memo(job['jobID'],fallback_text(job['packet']),'fallback',{'provider':'template','costUSD':0},job['packet']['contextID']);self.log('strategy-committed',memo=r)
            return
        try:
            job=w.begin_selection(BROCK,'first')
            if job['status']=='committed':return
            if job['status']=='active' and len(job['request']['choices'])!=1:raise ValueError('opening_Brock_requires_sole_authored_candidate')
            decision=run_selection(w,job,source='fallback') if job['status']=='active' else job['decision']
            lock=w.commit_preparation(decision['decisionID']);self.log('brock-preparation-locked',commitment=lock)
        except ValueError as error:self.log('preparation-ineligible',reason=str(error))
    def close(self,w):
        self.stopped=True
        # Kill only tracked fresh processes. The main writer remains live to drain
        # guarded tool recovery until the bounded Hermes job returns.
        if self.strategy_process is not None and self.strategy_process.poll() is None:self.strategy_process.terminate()
        deadline=time.monotonic()+60
        while self.worker is not None and not self.worker.done() and time.monotonic()<deadline:
            self.mailbox.drain(w);time.sleep(.05)
        self.tick(w);self.mailbox.close();self.pool.shutdown(wait=False)
