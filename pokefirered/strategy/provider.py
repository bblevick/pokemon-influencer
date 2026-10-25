"""Guarded transport only: sole typed tool, free verified route, bounded ledger."""
from __future__ import annotations
import json,os,time,urllib.request,urllib.error,fcntl,signal
from pathlib import Path
from dataclasses import dataclass
from typing import Protocol
ROOT=Path(__file__).resolve().parents[1]
from roster.hashes import digest,canonical

@dataclass(frozen=True)
class Limits:
    input_bytes:int=24576
    input_tokens:int=24576 # UTF-8 bytes is a conservative token upper bound
    output_tokens:int=1800
    response_bytes:int=65536
    request_seconds:int=35
    job_seconds:int=120
    attempts:int=3
    def __post_init__(self):
        for name,maximum in (('input_bytes',24576),('input_tokens',24576),('output_tokens',1800),('response_bytes',65536),('request_seconds',35),('job_seconds',120),('attempts',3)):
            if type(getattr(self,name))!=int or not 1<=getattr(self,name)<=maximum:raise ValueError('strategy_hard_limit:'+name)

class LanguageModelProvider(Protocol):
    def complete(self,packet,limits):...

class ProviderError(ValueError):pass

class FixtureProvider:
    def __init__(self,value=None,error=None):self.value=value;self.error=error;self.calls=0
    def complete(self,packet,limits):return self.structured(packet,None,limits)
    def structured(self,packet,output_schema,limits):
        self.calls+=1
        if self.error:raise ProviderError(self.error)
        return json.loads(json.dumps(self.value)),{'provider':'fixture','model':'fixture-v1','costUSD':0,'latencySeconds':0}

def live_configuration(model_role="primary"):
    # Explicit live entry only; allowlisted assignments, never expose full environment/key.
    config=json.loads((ROOT/'config/model_profiles.yaml').read_text());role=config['profiles']['experimental']['roles']['strategy'];values={}
    model_envs={'primary':role['model_env'],'backup':'POKEINFLUENCER_STRATEGY_MODEL_BACKUP','backup_backup':'POKEINFLUENCER_STRATEGY_MODEL_BACKUP_BACKUP','emergency':'POKEINFLUENCER_MODEL_BACKUP'}
    if model_role not in model_envs:raise ProviderError('unknown_strategy_model_role')
    selected_env=model_envs[model_role]
    credential_names=tuple(dict.fromkeys((config['credentials_env'],'OPENROUTER_API_KEY')))
    for name in (selected_env,*credential_names):
        if os.environ.get(name):values[name]=os.environ[name]
    env=ROOT/'.env'
    if env.exists():
        for line in env.read_text().splitlines():
            name,sep,value=line.partition('=');name=name.strip()
            if sep and name in (selected_env,*credential_names) and name not in values:values[name]=value.strip().strip('"').strip("'")
    model=values.get(selected_env,role['default_model'] if model_role=='primary' else None);key=next((values[n] for n in credential_names if values.get(n)),None)
    if not model:raise ProviderError('missing_strategy_model_role:'+model_role)
    if model=='openrouter/free':raise ProviderError('unqualified_dynamic_model_router')
    if role['provider']!='openrouter_chat' or not config['policy']['free_only'] or config['policy']['max_cost_usd']!=0 or config['policy']['allow_paid_fallback'] or config['policy']['allow_model_substitution']:raise ProviderError('unsupported_strategy_policy')
    if not model.endswith(':free'):raise ProviderError('free_model_required')
    if not key:raise ProviderError('missing_OPENROUTER_KEY')
    return {'provider':role['provider'],'model':model,'adapterVersion':6},key

def public_get(url):
    with urllib.request.urlopen(url,timeout=15) as response:
        data=response.read(2*1024*1024+1)
    if len(data)>2*1024*1024:raise ProviderError('metadata_byte_limit')
    return json.loads(data)

def qualify_route(model,catalog,endpoints):
    rows=[x for x in catalog['data'] if x['id']==model]
    if len(rows)!=1:raise ProviderError('configured_model_unavailable')
    row=rows[0]
    if not {'tools','tool_choice','max_tokens'}<=set(row['supported_parameters']):raise ProviderError('required_tool_parameters_unavailable')
    if any(float(row['pricing'].get(k,-1))!=0 for k in ('prompt','completion')):raise ProviderError('catalog_price_unknown_or_paid')
    eligible=[]
    for endpoint in endpoints['data']['endpoints']:
        if endpoint.get('model_id')!=model:continue
        if any(float(endpoint.get('pricing',{}).get(k,-1))!=0 for k in ('prompt','completion')):continue
        if not {'tools','tool_choice','max_tokens'}<=set(endpoint.get('supported_parameters',[])):continue
        if not endpoint.get('supports_tool_choice',{}).get('function'):continue
        # Nonzero/unknown endpoint status is not a demonstrated available route.
        if endpoint.get('status')!=0 or endpoint.get('uptime_last_5m',0)<=0:continue
        eligible.append(endpoint)
    if not eligible:raise ProviderError('no_healthy_verified_zero_price_function_tool_route')
    aliases=[x['id'] for x in catalog['data'] if row.get('canonical_slug') and x.get('canonical_slug')==row['canonical_slug']]
    return {'providerName':eligible[0]['provider_name'],'providerNames':list(dict.fromkeys(e['provider_name'] for e in eligible)),'endpoints':eligible,'model':model,'canonicalAliases':aliases,'catalog':row,'endpoint':eligible[0],'checkedAtUnix':time.time()}

def preflight(model):
    cat=public_get('https://openrouter.ai/api/v1/models');ends=public_get('https://openrouter.ai/api/v1/models/'+model+'/endpoints')
    return qualify_route(model,cat,ends)

class LiveBudget:
    def __init__(self,path,maximum_attempts=10):
        if type(maximum_attempts)!=int or not 1<=maximum_attempts<=10:raise ValueError('strategy_experiment_attempt_limit')
        self.maximum_attempts=maximum_attempts;self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
    def __enter__(self):
        self.lock=self.path.with_suffix('.lock').open('a')
        try:fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:self.lock.close();raise
        return self
    def __exit__(self,*args):self.lock.close()
    def read(self):return json.loads(self.path.read_text()) if self.path.exists() else {'version':1,'maximumAttempts':self.maximum_attempts,'closed':False,'attempts':[]}
    def write(self,value):
        with self.path.open('w') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        self.path.chmod(0o600)
    def charge(self,job,model):
        value=self.read()
        if type(value.get('maximumAttempts'))!=int or not 1<=value['maximumAttempts']<=10:raise ProviderError('invalid_strategy_budget_limit')
        if value['closed'] or len(value['attempts'])>=min(self.maximum_attempts,value['maximumAttempts']) or sum(a['jobID']==job for a in value['attempts'])>=3:raise ProviderError('live_strategy_budget_exhausted_or_closed')
        value['attempts'].append({'jobID':job,'requestedModel':model,'startedAtUnix':time.time()});self.write(value)
        return len(value['attempts'])
    def close(self):
        value=self.read();value['closed']=True;self.write(value)

class OpenRouterProvider:
    def __init__(self,binding,key,route,budget,job,budget_class=LiveBudget,system_prompt=None):self.binding=binding;self._key=key;self.route=route;self.budget=budget;self.job=job;self.budget_class=budget_class;self.system_prompt=system_prompt
    def complete(self,packet,limits):return self._request(packet,None,limits,text=True)
    def smoke(self,limits):return self._request({'instruction':'Write one short sentence about a fictional trainer preparing carefully.'},None,limits,text=True,system_prompt='Return one short plain-text sentence. This is a transport smoke test, not a game decision.')
    def structured(self,packet,output_schema,limits):
        # Historical compatibility only; current Strategy jobs call complete.
        return self._request(packet,output_schema,limits)
    def prepare_request(self,packet,output_schema,limits,text=False,system_prompt=None):
        if time.time()-self.route['checkedAtUnix']>60:raise ProviderError('route_preflight_expired')
        if self.route['model']!=self.binding['model']:raise ProviderError('route_model_mismatch')
        tool={'type':'function','function':{'name':'submit_strategic_posture','description':'Submit bounded strategic intent only, never a candidate or action choice.','parameters':output_schema}}
        body={'model':self.binding['model'],'messages':[{'role':'system','content':(ROOT/'prompts/strategy01.txt').read_text()},{'role':'user','content':json.dumps(packet,sort_keys=True)}],
          'tools':[tool],'tool_choice':{'type':'function','function':{'name':'submit_strategic_posture'}},'max_tokens':limits.output_tokens,
          'provider':{'only':self.route.get('providerNames',[self.route['providerName']]),'allow_fallbacks':True,'require_parameters':True,'max_price':{'prompt':0,'completion':0}}}
        if text:
            body.pop('tools');body.pop('tool_choice')
            body['messages'][0]['content']=system_prompt or self.system_prompt or (ROOT/'prompts/strategy_memo_v1.txt').read_text()
        if all('reasoning' in e['supported_parameters'] for e in self.route.get('endpoints',[self.route['endpoint']])):body['reasoning']={'enabled':False}
        encoded=canonical(body)
        if len(encoded)>limits.input_bytes or len(encoded)>limits.input_tokens:raise ProviderError('request_input_limit')
        return body,encoded

    def _request(self,packet,output_schema,limits,text=False,system_prompt=None):
        from .diagnostics import failure_diagnostics
        start=time.monotonic();self._failure_stage='request_serialization';self._request_hash=None
        try:return self._request_impl(packet,output_schema,limits,text,system_prompt)
        except Exception as error:
            error.diagnostics=failure_diagnostics(error,job=self.job,binding=self.binding,stage=self._failure_stage,packet=packet,elapsed=round(time.monotonic()-start,6))
            error.diagnostics['requestSHA256']=self._request_hash
            raise

    def _request_impl(self,packet,output_schema,limits,text=False,system_prompt=None):
        body,encoded=self.prepare_request(packet,output_schema,limits,text,system_prompt)
        self._request_hash=digest(body);self._failure_stage='provider_request'
        request=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',data=encoded,headers={'Authorization':'Bearer '+self._key,'Content-Type':'application/json'},method='POST')
        start=time.monotonic()
        def timeout(signum,frame):raise ProviderError('request_deadline')
        # Only fresh single main-thread CLI jobs use this adapter. No callbacks/transactions.
        previous=signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,limits.request_seconds)
        try:
            with self.budget_class(self.budget) as ledger:
                attempt=ledger.charge(self.job,self.binding['model'])
                audit=ledger.read();audit['attempts'][attempt-1].update({'requestSHA256':digest(body),'modelInputSHA256':digest(packet),'routing':body['provider']});ledger.write(audit)
                try:
                    with urllib.request.urlopen(request,timeout=limits.request_seconds) as response:
                        http_status=getattr(response,'status',200);data=response.read(limits.response_bytes+1)
                except urllib.error.HTTPError as error:
                    detail={'code':error.code,'message':'HTTP provider failure'}
                    try:
                        error_data=error.read(limits.response_bytes+1)
                        if len(error_data)<=limits.response_bytes:
                            envelope=json.loads(error_data)
                            if isinstance(envelope,dict) and isinstance(envelope.get('error'),dict):
                                payload=envelope['error'];detail['message']=str(payload.get('message','HTTP provider failure')).replace(self._key,'<redacted>')[:240]
                                metadata=payload.get('metadata',{})
                                if isinstance(metadata,dict) and isinstance(metadata.get('provider_name'),str):detail['providerName']=metadata['provider_name'].replace(self._key,'<redacted>')[:160]
                    except (ValueError,OSError,AttributeError,TypeError,KeyError):pass
                    audit=ledger.read();audit['attempts'][attempt-1]['response']={'httpStatus':error.code,'latencySeconds':round(time.monotonic()-start,3),'error':detail};ledger.write(audit)
                    raise ProviderError('http_'+str(error.code)) from None
                except TimeoutError:raise ProviderError('request_timeout') from None
                except OSError:raise ProviderError('provider_transport_failure') from None
            self._failure_stage='response_validation'
            if len(data)>limits.response_bytes:raise ProviderError('provider_response_byte_limit')
            result=json.loads(data)
            if not isinstance(result,dict):raise ProviderError('malformed_response_root')
            if not isinstance(result.get('usage',{}),dict):raise ProviderError('malformed_usage')
            canonical_slug=self.route.get('catalog',{}).get('canonical_slug')
            permitted={self.binding['model'],*self.route.get('canonicalAliases',[])}
            if canonical_slug:permitted.update((canonical_slug,canonical_slug+':free'))
            resolved=result.get('model')
            safe_usage={k:v for k,v in result.get('usage',{}).items() if k in ('prompt_tokens','completion_tokens','total_tokens','cost') and isinstance(v,(int,float))}
            with self.budget_class(self.budget) as ledger:
                finish_reason=result.get('choices',[{}])[0].get('finish_reason') if isinstance(result.get('choices'),list) and result.get('choices') else None
                audit=ledger.read();audit['attempts'][attempt-1]['response']={'resolvedModel':resolved if isinstance(resolved,str) and len(resolved)<160 else 'missing_or_invalid','usage':safe_usage,'keys':sorted(result)[:20],'httpStatus':http_status,'latencySeconds':round(time.monotonic()-start,3),'finishReason':finish_reason if finish_reason in ('stop','length','tool_calls','content_filter','error') else 'unknown'}
                if isinstance(result.get('error'),dict):
                    error=result['error'];audit['attempts'][attempt-1]['response']['error']={'code':error.get('code'),'message':str(error.get('message',''))[:240].replace(self._key,'<redacted>')}
                ledger.write(audit)
            if isinstance(result.get('error'),dict):raise ProviderError('provider_error_'+str(result['error'].get('code','unknown')))
            if resolved not in permitted:raise ProviderError('resolved_model_mismatch')
            choices=result.get('choices',[])
            if len(choices)!=1:raise ProviderError('one_choice_required')
            message=choices[0]['message'];calls=message.get('tool_calls',[])
            if text and (message.get('refusal') or choices[0].get('finish_reason')!='stop' or calls):raise ProviderError('incomplete_or_refused_text')
            if not text and (len(calls)!=1 or calls[0].get('type')!='function' or calls[0]['function']['name']!='submit_strategic_posture'):raise ProviderError('one_typed_submission_required')
            usage=result.get('usage',{})
            if text and (type(usage.get('completion_tokens'))!=int or usage['completion_tokens']<0):raise ProviderError('invalid_output_token_receipt')
            if usage.get('completion_tokens',limits.output_tokens+1)>limits.output_tokens:raise ProviderError('output_token_limit')
            if usage.get('cost',-1)!=0:raise ProviderError('unconfirmed_zero_usage_cost')
            args=message.get('content') if text else json.loads(calls[0]['function']['arguments'])
            if text:
                from .memo import validate_text
                validate_text(args)
            serving=result.get('provider')
            with self.budget_class(self.budget) as ledger:
                audit=ledger.read();audit['attempts'][attempt-1]['response'].update({'servingProvider':serving if isinstance(serving,str) and len(serving)<160 else None,**({'strategyText':args} if text else {'toolSubmission':{'name':'submit_strategic_posture','arguments':args}}),'responseID':result.get('id')});ledger.write(audit)
            diagnostics={'provider':'openrouter_chat','requestedModel':self.binding['model'],'resolvedModel':result['model'],'adapterVersion':self.binding['adapterVersion'],'attempt':attempt,'latencySeconds':round(time.monotonic()-start,3),'usage':{k:usage[k] for k in ('prompt_tokens','completion_tokens','total_tokens','cost') if k in usage},'costUSD':0,'servingProvider':serving if isinstance(serving,str) and len(serving)<160 else None,'requestSHA256':digest(body),'modelInputSHA256':digest(packet)}
            return args,diagnostics # No provider prose or reasoning/transcripts persisted.
        finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)


def text_route_health(endpoint):
    # Current accepting status is mandatory. Missing short-window telemetry is
    # distinct from a measured zero; choose the first published uptime window.
    if endpoint.get('status')!=0:return False,None
    for field in ('uptime_last_5m','uptime_last_30m','uptime_last_1d'):
        value=endpoint.get(field)
        if isinstance(value,(int,float)) and not isinstance(value,bool):return 0<value<=100,field
    return False,None

def qualify_text_route(model,catalog,endpoints):
    rows=[r for r in catalog['data'] if r['id']==model]
    if len(rows)!=1:raise ProviderError('configured_model_unavailable')
    row=rows[0]
    if 'max_tokens' not in row.get('supported_parameters',[]):raise ProviderError('text_token_bound_unavailable')
    if 'text' not in row.get('architecture',{}).get('output_modalities',['text']):raise ProviderError('text_output_unavailable')
    if any(float(row.get('pricing',{}).get(k,-1))!=0 for k in ('prompt','completion')):raise ProviderError('catalog_price_unknown_or_paid')
    eligible=[r for r in endpoints['data']['endpoints'] if r.get('model_id')==model and text_route_health(r)[0] and 'max_tokens' in r.get('supported_parameters',[]) and all(float(r.get('pricing',{}).get(k,-1))==0 for k in ('prompt','completion'))]
    if not eligible:raise ProviderError('no_healthy_verified_zero_price_text_route')
    aliases=[r['id'] for r in catalog['data'] if row.get('canonical_slug') and r.get('canonical_slug')==row['canonical_slug']]
    return {'providerName':eligible[0]['provider_name'],'providerNames':list(dict.fromkeys(r['provider_name'] for r in eligible)),'endpoints':eligible,'model':model,'canonicalAliases':aliases,'catalog':row,'endpoint':eligible[0],'checkedAtUnix':time.time(),'mode':'ordinary-text','healthEvidence':{r['provider_name']:text_route_health(r)[1] for r in eligible}}

def preflight_text(model):
    return qualify_text_route(model,public_get('https://openrouter.ai/api/v1/models'),public_get('https://openrouter.ai/api/v1/models/'+model+'/endpoints'))
