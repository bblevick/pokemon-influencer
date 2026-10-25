"""Native fixed-choice transport; no chat/tools/reasoning/resampling."""
import json,os,time,signal,urllib.request,urllib.error,math
from pathlib import Path
from typing import Protocol
from roster.hashes import canonical,digest
from strategy.provider import public_get,ProviderError,LiveBudget
from .validation import validate_decision
ROOT=Path(__file__).resolve().parents[1]
class DecisionProvider(Protocol):
    def decide(self,state,question,choices):...
class FixtureDecisionProvider:
    def __init__(self,choice,error=None):self.choice=choice;self.error=error;self.calls=0
    def decide(self,state,question,choices):
        self.calls+=1
        if self.error:raise ProviderError(self.error)
        return {'choiceID':self.choice,'probabilities':None,'confidence':None,'diagnostics':{'provider':'fixture','costUSD':0}}

def configuration():
    config=json.loads((ROOT/'config/model_profiles.yaml').read_text());r=config['profiles']['experimental']['roles']['system1'];names=(r['model_env'],config['credentials_env'],'OPENROUTER_API_KEY');values={n:os.environ[n] for n in names if os.environ.get(n)}
    path=ROOT/'.env'
    if path.exists():
        for line in path.read_text().splitlines():
            name,sep,value=line.partition('=');name=name.strip()
            if sep and name in names and name not in values:values[name]=value.strip().strip('"').strip("'")
    model=values.get(r['model_env'],r['default_model']);key=next((values[n] for n in names[1:] if values.get(n)),None)
    policy=config['policy']
    if r['provider']!='openrouter_systemone' or not policy['free_only'] or policy['max_cost_usd']!=0 or policy['allow_paid_fallback'] or policy['allow_model_substitution'] or not model.endswith(':free'):raise ProviderError('unqualified_system1_policy')
    if not key:raise ProviderError('missing_system1_credential')
    return {'provider':'openrouter_systemone','model':model,'adapterVersion':1},key

def preflight(model):
    cat=public_get('https://openrouter.ai/api/v1/models');ends=public_get('https://openrouter.ai/api/v1/models/'+model+'/endpoints');rows=[r for r in cat['data'] if r['id']==model]
    row=rows[0] if len(rows)==1 else ends.get('data',{})
    if row.get('id')!=model or row.get('architecture',{}).get('output_modalities')!=['decisions']:raise ProviderError('native_decision_capability_unqualified')
    if rows and any(float(row.get('pricing',{}).get(k,-1))!=0 for k in ('prompt','completion')):raise ProviderError('unknown_or_paid_system1_catalog')
    eligible=[e for e in ends['data']['endpoints'] if e.get('model_id')==model and e.get('status')==0 and e.get('uptime_last_5m',0)>0 and all(float(e.get('pricing',{}).get(k,-1))==0 for k in ('prompt','completion'))]
    if not eligible:raise ProviderError('no_healthy_free_native_decision_route')
    aliases=[r['id'] for r in cat['data'] if row.get('canonical_slug') and r.get('canonical_slug')==row['canonical_slug']]
    for e in eligible:
        version=e.get('name','').partition(' | ')[2]
        if version.startswith(model.split(':')[0].rsplit('/',1)[0]+'/') and version.endswith(':free'):aliases.extend((version,version.removesuffix(':free')))
    return {'model':model,'catalog':row,'catalogDiscovery':'model-list' if rows else 'exact-model-endpoints','endpoints':eligible,'canonicalAliases':sorted(set(aliases)),'checkedAtUnix':time.time(),'api':'https://openrouter.ai/api/v1/systemone'}

class Budget(LiveBudget):
    def __init__(self,path):super().__init__(path,10)
    def charge(self,job,model):
        value=self.read()
        if sum(a['jobID']==job for a in value['attempts'])>=2:raise ProviderError('system1_logical_decision_budget')
        return super().charge(job,model)

class NativeDecisionProvider:
    def __init__(self,binding,key,route,budget,job,request_seconds=35,budget_class=Budget):self.binding=binding;self._key=key;self.route=route;self.budget=budget;self.job=job;self.request_seconds=request_seconds;self.budget_class=budget_class
    def decide(self,state,question,choices):
        if time.time()-self.route['checkedAtUnix']>120 or self.route['model']!=self.binding['model']:raise ProviderError('system1_preflight_expired_or_mismatched')
        if not isinstance(state,str) or not isinstance(question,str) or not 1<=len(choices)<=32 or not all(isinstance(k,str) and isinstance(v,str) for k,v in choices.items()):raise ProviderError('bounded_choice_request')
        body={'model':self.binding['model'],'state':state,'questions':{'preparation':{'type':'choice','instructions':question,'criteria':choices}}}
        data=canonical(body)
        if len(data)>32768:raise ProviderError('system1_conservative_input_token_byte_bound')
        request=urllib.request.Request(self.route['api'],data=data,headers={'Authorization':'Bearer '+self._key,'Content-Type':'application/json'},method='POST')
        start=time.monotonic()
        def timeout(signum,frame):raise ProviderError('system1_request_deadline')
        previous=signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,self.request_seconds)
        try:
            with self.budget_class(self.budget) as b:
                attempt=b.charge(self.job,self.binding['model']);audit=b.read();audit['attempts'][attempt-1]['requestSHA256']=digest(body);b.write(audit)
                try:
                    with urllib.request.urlopen(request,timeout=self.request_seconds) as r:raw=r.read(65537);status=r.status
                except urllib.error.HTTPError as error:
                    raw=error.read(65537);detail={'httpStatus':error.code,'message':'HTTP provider failure'}
                    try:detail['message']=str(json.loads(raw).get('error',{}).get('message',''))[:240].replace(self._key,'<redacted>')
                    except (ValueError,AttributeError):pass
                    audit=b.read();audit['attempts'][attempt-1]['response']=detail;b.write(audit);raise ProviderError('system1_http_'+str(error.code)) from None
                except (OSError,TimeoutError):raise ProviderError('system1_transport_failure') from None
            if len(raw)>65536:raise ProviderError('system1_response_bound')
            result=json.loads(raw)
            if not isinstance(result,dict):raise ProviderError('system1_response_shape')
            safe={k:result.get(k) for k in ('id','model','provider','answers','usage','error') if k in result}
            safe=json.loads(json.dumps(safe).replace(self._key,'<redacted>'))
            # Full typed decision statistics retained; no arbitrary transcripts.
            with self.budget_class(self.budget) as b:
                audit=b.read();audit['attempts'][attempt-1]['response']={'httpStatus':status,'result':safe,'latencySeconds':round(time.monotonic()-start,3)};b.write(audit)
            return decode_result(result,self.binding,self.route,choices,time.monotonic()-start,digest(body))
        finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)

def run_selection(store,job,provider=None,source='model'):
    if job['status']!='active':return job
    p=job['request'];failure=None
    if len(p['choices'])==1:r={'choiceID':next(iter(p['choices'])),'probabilities':None,'confidence':None,'diagnostics':{'provider':'sole-legal-choice','modelRequests':0}};source='sole'
    elif provider is None:r={'choiceID':p['fallbackCandidateID'],'probabilities':None,'confidence':None,'diagnostics':{'provider':'continuity-fallback','modelRequests':0}};source='fallback'
    else:
        try:
            store.count_selection_attempt(p);r=provider.decide(p['state'],p['question'],p['choices']);validate_decision(r,p['choices'])
        except (ValueError,KeyError,TypeError,OSError) as error:
            r={'choiceID':p['fallbackCandidateID'],'probabilities':None,'confidence':None,'diagnostics':{'provider':'continuity-fallback','failure':str(error) if isinstance(error,ProviderError) else 'invalid_or_unavailable_choice'}};source='fallback'
    return store.finish_selection(p,r,source)


def decode_result(result,binding,route,choices,latency,request_sha):
    if result.get('error'):raise ProviderError('system1_provider_error')
    permitted={binding['model'],*route.get('canonicalAliases',[])};slug=route['catalog'].get('canonical_slug')
    if slug:permitted.update((slug,slug+':free'))
    if result.get('model') not in permitted:raise ProviderError('system1_serving_model_mismatch')
    usage=result.get('usage')
    if not isinstance(usage,dict) or type(usage.get('cost')) not in (int,float) or usage['cost']!=0:raise ProviderError('system1_unconfirmed_zero_cost')
    for name,limit in (('input_tokens',32768),('output_tokens',4096)):
        if name in usage and (type(usage[name])!=int or not 0<=usage[name]<=limit):raise ProviderError('system1_usage_bound')
    if set(result.get('answers',{}))!={'preparation'}:raise ProviderError('system1_one_answer_required')
    answer=result['answers']['preparation']
    if not isinstance(answer,dict) or answer.get('type')!='choice':raise ProviderError('system1_choice_required')
    decision={'choiceID':answer.get('choice'),'probabilities':answer.get('probabilities'),'confidence':answer.get('confidence'),'diagnostics':{'provider':'openrouter_systemone','requestedModel':binding['model'],'resolvedModel':result['model'],'servingProvider':result.get('provider'),'adapterVersion':1,'responseID':result.get('id'),'usage':usage,'costUSD':0,'latencySeconds':round(latency,3),'requestSHA256':request_sha}}
    validate_decision(decision,choices);return decision
