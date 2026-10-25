"""Subjective text only. No extraction of claims, permissions or executable choices."""
from __future__ import annotations
import json,unicodedata,time
from pathlib import Path
from roster.extract import digest
from world.store import WorldError,dump
from .store import StrategyStore
from .context import build_context,configuration_identity,ROOT
from .provider import Limits,ProviderError

MAX_BYTES=4096
PROMPT=ROOT/'prompts/strategy_memo_v1.txt'
def validate_text(text):
    if not isinstance(text,str) or not text.strip():raise ValueError('empty_strategy_memo')
    try:encoded=text.encode('utf-8',errors='strict')
    except UnicodeError:raise ValueError('strategy_memo_encoding') from None
    if len(encoded)>MAX_BYTES:raise ValueError('strategy_memo_byte_limit')
    # Paragraph LF is permitted. C0/C1, bidi/format controls and surrogates are not.
    if any(c!='\n' and unicodedata.category(c) in ('Cc','Cf','Cs') for c in text):raise ValueError('strategy_memo_control')
    return text

def memo_configuration():return digest([configuration_identity(),PROMPT.read_text(),'memo-v1',MAX_BYTES])

def memo_context(store,*args,**kw):
    p=build_context(store,*args,**kw);s=p['scope']
    s.update(configurationSHA256=memo_configuration(),promptVersion=2,strategySchemaVersion=3)
    p['schemaVersion']=2
    p['materialContextSHA256']=digest([p['modelInput'],s['opportunityID'],s['strategyPurpose'],memo_configuration(),s['providerConfiguration']])
    p.pop('contextID');p['contextID']='strategy-context:'+digest(p)
    return p

class MemoStore(StrategyStore):
    _supports_memo=True
    def __init__(self,*args,**kw):
        super().__init__(*args,**kw)
        try:
            if self._one("SELECT name FROM sqlite_master WHERE name='preparation_decision_version'") and not getattr(self,'_supports_preparation_decisions',False):raise WorldError('preparation decisions require PreparationDecisionStore')
            def migrate():
                if self._one("SELECT name FROM sqlite_master WHERE name='strategy_memo_version'"):
                    if [tuple(r) for r in self.db.execute('SELECT * FROM strategy_memo_version')]!=[(1,memo_configuration())]:raise WorldError('memo configuration changed; explicit adoption required')
                else:
                    self.db.execute('CREATE TABLE strategy_memo_version(version INTEGER NOT NULL,configuration_sha TEXT NOT NULL)')
                    self.db.execute('INSERT INTO strategy_memo_version VALUES(1,?)',(memo_configuration(),))
            self._tx(migrate)
        except Exception:self.close();raise
    def context_packet(self,*args,**kw):return memo_context(self,*args,**kw)
    def memo_records(self):return [r for r in self.strategy_state()['postures'].values() if r.get('schemaVersion')==3]
    def count_attempt(self,job,context_id=None):
        def action():
            if not self.job_current(job):raise WorldError('stale_strategy_job')
            row=self._one('SELECT attempts,context FROM strategy_jobs WHERE id=?',(job,))
            if context_id!=json.loads(row['context'])['contextID']:raise WorldError('wrong_strategy_grant')
            if row['attempts']>=1:raise WorldError('strategy_memo_single_attempt')
            self.db.execute('UPDATE strategy_jobs SET attempts=attempts+1 WHERE id=?',(job,))
        return self._tx(action)
    def finish_strategy(self,*args,**kw):raise WorldError('memo jobs require exact text submission')
    def finish_memo(self,job,text,source,diagnostics,context_id):
        validate_text(text)
        if source not in ('model','fallback','mock'):raise ValueError('strategy_source')
        def action():
            if not self.job_current(job):raise WorldError('stale_strategy_job')
            packet=json.loads(self._one('SELECT context FROM strategy_jobs WHERE id=?',(job,))['context'])
            if context_id!=packet['contextID']:raise WorldError('wrong_strategy_grant')
            s=packet['scope']
            r={'strategyID':'strategy-memo:'+digest([job,text]),'jobID':job,'actor':s['actor'],'scope':s,'contextID':context_id,'materialContextSHA256':packet['materialContextSHA256'],'strategyText':text,'source':source,'diagnostics':diagnostics,'schemaVersion':3,'promptVersion':s['promptVersion'],'createdAtUTC':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
            self._append_strategy('MEMO',job,r)
            self.db.execute("UPDATE strategy_jobs SET status='completed',outcome=? WHERE id=?",(r['strategyID'],job))
            return r
        return self._tx(action)

def fallback_text(packet):
    name=packet['modelInput']['trainer']['name']
    return name+' intends to preserve existing partners and use only preparation options allowed by the current opportunity. Resources are finite; no new supplies or companions are assumed. Past observations are evidence about previous encounters, not certainty about the next opponent. The current opposing party and lead remain unknown. Preparation and battle choices must come from the trusted legal options.'

def run_memo_job(store,job,provider,source='mock',limits=Limits(attempts=1)):
    if job['status']=='recorded':return job['decision']
    p=job['packet'];identity=job['jobID'];start=time.monotonic();error=None
    try:
        if limits.job_seconds<limits.request_seconds:raise ProviderError('job_deadline')
        store.count_attempt(identity,p['contextID'])
        text,diagnostics=provider.complete(p['modelInput'],limits)
        validate_text(text)
        if time.monotonic()-start>limits.job_seconds:raise ProviderError('late_job_deadline')
        return store.finish_memo(identity,text,source,diagnostics,p['contextID'])
    except (ValueError,KeyError,TypeError,OSError) as exc:
        error=str(exc) if isinstance(exc,ProviderError) else 'invalid_or_unavailable_memo'
    # Stale jobs are rejected by finish_memo, including the fallback path.
    return store.finish_memo(identity,fallback_text(p),'fallback',{'provider':'template','model':'strategy-memo-fallback-v1','costUSD':0,'failure':error},p['contextID'])
