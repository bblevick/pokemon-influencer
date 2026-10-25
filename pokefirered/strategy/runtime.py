"""Fresh scoped bounded job; inference outside SQLite transactions/callbacks."""
from __future__ import annotations
import time
from jsonschema.exceptions import ValidationError
from .provider import Limits,ProviderError
from .domain import SCHEMA,validate,fallback

def run_job(store,job,provider,source='mock',limits=Limits()):
    if job['status']=='recorded':return job['decision']
    start=time.monotonic();errors=[];backoffs=[];packet=job['packet'];identity=job['jobID']
    for attempt in range(limits.attempts):
        if time.monotonic()-start+limits.request_seconds>limits.job_seconds:errors.append('job_deadline');break
        if not store.job_current(identity):raise ValueError('stale_strategy_job')
        try:
            store.count_attempt(identity,packet['contextID'])
            posture,diagnostics=provider.structured(packet['modelInput'],SCHEMA,limits)
            validate(posture,packet)
            if time.monotonic()-start>limits.job_seconds:raise ProviderError('late_job_deadline')
            diagnostics={**diagnostics,'failures':errors,'attemptsThisRun':attempt+1,'backoffSeconds':backoffs}
            return store.finish_strategy(identity,posture,source,diagnostics,packet['contextID'])
        except (ValueError,KeyError,TypeError,ValidationError,OSError) as error:
            # Validation text may include provider output; persist only controlled code/class.
            errors.append(str(error) if isinstance(error,ProviderError) else 'provider_busy_or_io_error' if isinstance(error,OSError) else 'invalid_structured_posture')
            code=str(error)
            # Unchanged client errors and throttling cannot be repaired by rapid retry.
            if isinstance(error,ProviderError) and code in ('http_400','http_429','provider_error_400','provider_error_429'):break
            if isinstance(error,ProviderError) and (code.startswith('http_5') or code.startswith('provider_error_5')) and attempt+1<limits.attempts:
                delay=5*(attempt+1)
                if time.monotonic()-start+delay+limits.request_seconds>limits.job_seconds:errors.append('job_deadline');break
                backoffs.append(delay);time.sleep(delay)
            if isinstance(error,ProviderError) and any(code in str(error) for code in ('budget','preflight','model_mismatch')):break
    return store.finish_strategy(identity,fallback(packet),'fallback',{'provider':'template','model':'strategy-fallback-v1','failures':errors,'backoffSeconds':backoffs,'costUSD':0},packet['contextID'])
