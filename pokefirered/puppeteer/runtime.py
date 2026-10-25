"""Fresh official Hermes worker + guarded host transport (no game vendor dependency).

The parent owns SQLite, credentials and grants. The child owns only a fresh
AIAgent conversation and the four bound RPC tool definitions.
"""
from contextlib import closing
import fcntl,hashlib,json,os,re,shutil,signal,socket,sqlite3,subprocess,time,uuid
from http.server import HTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from world.store import ROOT,WorldError,dump
from puppeteer.store import PuppeteerStore
from puppeteer.recap_contract import model_result_schema, build_submission, PROMPT_VERSION, RECAP_VERSION, HOST_FIELDS

PIN='f97608f178d1ffeca59860195ab7da295f7c8e5f'
INSTALL=ROOT/'.local/hermes-source'
PYTHON=ROOT/'.local/hermes-venv/bin/python'
HOMES=ROOT/'.runtime/hermes/jobs'
AUDIT=ROOT/'evidence/phase2/hermes01/jobs'
NAMES=('get_battle_evidence','recall_puppeteer_memory','get_actor_context','submit_recap_and_memory_result')
POLICY=json.loads((ROOT/'config/hermes_policy.json').read_text())
MARKER='.pokemon-hermes-owner.json'


def open_store(path):
    with closing(sqlite3.connect('file:'+str(Path(path).resolve())+'?mode=ro',uri=True)) as db:
        meta={k:json.loads(v) for k,v in db.execute('SELECT * FROM metadata')}
    return PuppeteerStore(path,meta['build'],meta['tag'])


def safe_root(root=HOMES):
    root=Path(root)
    if not root.is_absolute() or root!=HOMES:raise WorldError('only fixed project disposable root allowed')
    for p in [root,*root.parents]:
        if p.is_symlink():raise WorldError('symlinked runtime ancestry')
    return root


def checked_home(target,allow_active=False,inspect_contents=True):
    root=safe_root();p=Path(target)
    if not p.is_absolute() or '..' in p.parts or p.parent!=root or not re.fullmatch(r'[a-f0-9-]{36}',p.name):raise WorldError('unsafe cleanup target')
    if p.is_symlink() or not p.is_dir():raise WorldError('unsafe/missing runtime home')
    marker=p/MARKER
    if marker.is_symlink() or not marker.is_file():raise WorldError('missing safe ownership marker')
    owner=json.loads(marker.read_text())
    if owner.get('schemaVersion')!=1 or owner.get('jobID')!=p.name or owner.get('home')!=str(p) or not re.fullmatch(r'[a-f0-9]{64}',owner.get('ownerToken','')):raise WorldError('foreign runtime ownership')
    # Refuse even interior symlinks; never follow external cleanup targets.
    for current,dirs,files in os.walk(p,followlinks=False) if inspect_contents else []:
        if any((Path(current)/n).is_symlink() for n in dirs+files):raise WorldError('symlink in runtime; quarantine required')
    pid=owner.get('pid',0)
    if pid:
        try:os.kill(pid,0)
        except ProcessLookupError:pass
        else:
            if not allow_active:raise WorldError('active runtime; stop its tracked worker first')
    if owner.get('active') and not allow_active:raise WorldError('active runtime ownership')
    return p,owner


def cleanup(target,dry_run=True):
    p,owner=checked_home(target)
    # Read-only check before wipe: never erase an unresolved model grant.
    dbpath=Path(owner['database'])
    if dbpath.is_symlink() or dbpath.is_relative_to(HOMES):raise WorldError('unsafe durable database path in marker')
    if dbpath.exists():
        with closing(sqlite3.connect('file:'+str(dbpath)+'?mode=ro',uri=True)) as db:
            job=db.execute('SELECT status FROM puppeteer_jobs WHERE id=?',(owner['domainJobID'],)).fetchone()
            if job and job[0]=='active':raise WorldError('active grant requires explicit recovery before cleanup')
    else:
        auditpath=AUDIT/(p.name+'.json')
        if not auditpath.is_file() or auditpath.is_symlink():raise WorldError('database unavailable without retained settled audit')
        audit=json.loads(auditpath.read_text())
        if audit.get('runtimeHome')!=str(p) or audit.get('jobID')!=owner['domainJobID'] or not audit.get('outcome'):raise WorldError('unresolved grant; missing database recovery required')
    result={'candidates':[str(p)],'dryRun':dry_run}
    if not dry_run:shutil.rmtree(p)
    return result


def create_home(job,database):
    root=safe_root();root.mkdir(parents=True,exist_ok=True)
    home=root/str(uuid.uuid4());home.mkdir(mode=0o700)
    owner={'schemaVersion':1,'jobID':home.name,'domainJobID':job,'home':str(home),'database':str(Path(database).resolve()),'ownerToken':uuid.uuid4().hex+uuid.uuid4().hex,'pid':0,'active':True}
    (home/MARKER).write_text(dump(owner));(home/'work').mkdir()
    cfg={'tools':{'tool_search':{'enabled':'off'}},'agent':{'api_max_retries':1,'auto_recovery_cycles':0,'empty_response_guard':{'enabled':False},'stall_guards':False,'task_completion_guidance':False,'parallel_tool_call_guidance':False,'environment_probe':False,'bot_mode_protocol':False},'compression':{'enabled':False,'idle_compact_after_seconds':0},'skills':{'auto_load':[]},'plugins':{'enabled':[]},'memory':{'memory_enabled':False,'user_profile_enabled':False},'model':{'context_length':128000,'streaming':False,'default_headers':{'HTTP-Referer':'https://hermes-agent.nousresearch.com','X-Title':'Hermes Agent'}}}
    (home/'config.yaml').write_text(json.dumps(cfg));return home,owner


def model_configuration():
    profiles=json.loads((ROOT/'config/model_profiles.yaml').read_text());role=profiles['profiles']['experimental']['roles']['puppeteer']
    # Parse only two allowlisted assignments; never print whole dotenv/env.
    values={}
    envpath=ROOT/'.env'
    if envpath.exists():
        for line in envpath.read_text().splitlines():
            m=re.fullmatch(r'\s*(?:export\s+)?(OPENROUTER_KEY|OPENROUTER_API_KEY|POKEINFLUENCER_PUPPETEER_MODEL)\s*=\s*(.*?)\s*',line)
            if m:values[m[1]]=m[2].strip('\"\'')
    model=os.environ.get(role['model_env']) or values.get(role['model_env']) or role['default_model']
    key=os.environ.get(profiles['credentials_env']) or values.get(profiles['credentials_env']) or os.environ.get('OPENROUTER_API_KEY') or values.get('OPENROUTER_API_KEY')
    if not model.endswith(':free') or not key:raise WorldError('configured free model/credential unavailable')
    return model,key


def verify_free_model(model,timeout=15):
    with urlopen(Request('https://openrouter.ai/api/v1/models',headers={'User-Agent':'PokemonInfluencer-HERMES01'}),timeout=timeout) as r:catalog=json.load(r)
    row=next((r for r in catalog['data'] if r['id']==model),None)
    if not row:raise WorldError('configured model absent from current OpenRouter catalog')
    price=row.get('pricing',{})
    if not price or any(float(v)!=0 for k,v in price.items() if v is not None):raise WorldError('unknown/nonzero model pricing')
    if not {'tools','max_tokens'}<=set(row.get('supported_parameters',[])):raise WorldError('configured model lacks required tool/token capability')
    return {'id':row['id'],'pricing':price,'supported_parameters':row['supported_parameters'],'context_length':row['context_length'],'verifiedAt':time.time()}


def charge_live(experiment='original'):
    if experiment not in ('original','closeout'):raise WorldError('unknown bounded experiment')
    path=ROOT/('.local/hermes01/closeout-live-budget.json' if experiment=='closeout' else '.local/hermes01/live-budget.json');path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a+') as f:
        fcntl.flock(f,fcntl.LOCK_EX);f.seek(0);text=f.read();state=json.loads(text) if text else {'attempts':0,'limit':10}
        if state.get('closed'):raise WorldError('HERMES-01 live experiment closed')
        if state['attempts']>=10:raise WorldError('HERMES-01 total live request budget exhausted')
        state['attempts']+=1;f.seek(0);f.truncate();f.write(dump(state));f.flush();os.fsync(f.fileno())
        return state['attempts']


def mock_response(body,index,behavior='valid'):
    def call(name,args,n):return {'id':'pi_call_'+str(n),'type':'function','function':{'name':name,'arguments':dump(args)}}
    msg={'role':'assistant','content':None};finish='tool_calls'
    if index==1:
        requested=[t['function']['name'] for t in body.get('tools',[])]
        names=[NAMES[1]] if requested==[NAMES[1]] else [NAMES[0]] if behavior in ('bundle','content','parse-error') else NAMES[:3]
        msg['tool_calls']=[call(n,{},i) for i,n in enumerate(names)]
    elif index==2 and behavior=='recall':msg['content']='Authorized prior episodes retrieved.';finish='stop'
    elif index==2:
        records={m.get('name'):json.loads(m['content']) for m in body['messages'] if m['role']=='tool' and m.get('name')}
        # Hermes's normalized tool messages may omit name; use tool_call_id.
        if not records:
            outputs=[json.loads(m['content']) for m in body['messages'] if m['role']=='tool'];records=dict(zip(NAMES,outputs))
        packet=records[NAMES[0]];e=packet['evidence'];public=[r['evidenceID'] for r in e if r['claim']['type']=='TRAINER_BATTLE_RESULT']+[r['evidenceID'] for r in e if r['claim']['type']=='POKEMON_SEEN'][:1]
        result={'schemaVersion':RECAP_VERSION,'obligationID':packet['obligationID'],'battleID':packet['battleID'],'actorID':packet['actorID'],'publicEvidenceIDs':public,'privateEvidenceIDs':[r['evidenceID'] for r in e if r['claim']['type']!='BATTLE_PARTICIPATION'][:16],'summaryTemplate':'battle_episode_v1','tone':'competitive','visibility':'public','priorEpisodeIDs':[r['episodeID'] for r in records.get(NAMES[1],packet.get('priorMemory',{}))['episodes'][-2:]]}
        if behavior=='refusal':msg['content']='NO_POST';finish='stop'
        else:
            if behavior=='content':result={k:v for k,v in result.items() if k not in HOST_FIELDS}
            msg['tool_calls']=[call(NAMES[3],{'result':result if behavior in ('valid','bundle','content') else {'NO_POST':True}},3)]
            if behavior=='parse-error':msg['tool_calls'][0]['function']['arguments']='{'
    else:msg['content']='Processing complete.';finish='stop'
    return {'id':'pi-mock-'+str(index),'object':'chat.completion','created':int(time.time()),'model':body['model'],'choices':[{'index':0,'message':msg,'finish_reason':finish}],'usage':{'prompt_tokens':100,'completion_tokens':100,'total_tokens':200}}


def _run_job(database,job,transport='mock',behavior='valid',live=False,experiment='original',store_factory=None,charge_request=None,audit_directory=None):
    opener=store_factory or open_store
    audit_root=Path(audit_directory) if audit_directory is not None else AUDIT
    if experiment not in ('original','closeout'):raise WorldError('unknown bounded experiment')
    max_requests=4 if experiment=='closeout' else 3
    if transport not in ('mock','live'):raise WorldError('unknown transport')
    if transport=='live' and not live:raise WorldError('live requires explicit bounded experiment flag')
    if (INSTALL/'.env').exists():raise WorldError('Hermes source dotenv must be absent')
    revision=subprocess.check_output(['git','-C',str(INSTALL),'rev-parse','HEAD'],text=True).strip()
    if revision!=PIN or not PYTHON.exists():raise WorldError('pinned Hermes installation unavailable')
    lockpath=ROOT/'.local/hermes01/runtime.lock';lockpath.parent.mkdir(parents=True,exist_ok=True)
    with lockpath.open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise WorldError('another model worker is active')
        with opener(database) as initial:job_row,grant=initial._job(job)
        end=time.monotonic()+max(0,job_row['expires']-time.time())
        model,key=('pokemon-test/mock',None) if transport=='mock' else model_configuration()
        capability=verify_free_model(model,timeout=min(15,max(.1,end-time.monotonic()))) if transport=='live' else {'id':model,'mock':True}
        home,owner=create_home(job,database);audit_root.mkdir(parents=True,exist_ok=True)
        record={'schemaVersion':1,'jobID':job,'runtimeHome':str(home),'hermesRevision':PIN,'transport':transport,'experiment':experiment,'maxRequests':max_requests,'model':model,'capability':capability,'requests':[],'tools':[],'failures':[]}
        token=owner['ownerToken'];proc=None
        class Handler(BaseHTTPRequestHandler):
            def setup(self):
                super().setup();self.connection.settimeout(2)
            def log_message(self,*args):pass
            def reply(self,obj,status=200):
                raw=dump(obj).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
            def do_POST(self):
                try:
                    if self.headers.get('Authorization')!='Bearer '+token:raise WorldError('invalid local transport grant')
                    length=int(self.headers.get('Content-Length','0'))
                    if not 0<length<=POLICY['maxInputBytes'] or time.monotonic()>end:raise WorldError('request bound/deadline')
                    raw=self.rfile.read(length);body=json.loads(raw)
                    if self.path=='/v1/chat/completions':
                        if len(record['requests'])>=max_requests:raise WorldError('per-job model request budget')
                        if body.get('model')!=model or body.get('stream') or type(body.get('max_tokens'))!=int or not 1<=body['max_tokens']<=1200 or 'max_completion_tokens' in body:raise WorldError('model/token/stream guard')
                        names={t['function']['name'] for t in body.get('tools',[])}
                        if not names<=set(NAMES):raise WorldError('unapproved model tool definition')
                        text=raw.decode()
                        if any(s in text for s in ('/Users/','/home/','OPENROUTER_KEY','PI_PRIVATE_CANARY','pokefirered.gba')):raise WorldError('private context excluded from model transport')
                        attempt={'startedAt':time.time(),'request':body,'sha256':hashlib.sha256(raw).hexdigest()};record['requests'].append(attempt)
                        if transport=='mock':response=mock_response(body,len(record['requests']),behavior)
                        else:
                            attempt['liveAttempt']=charge_request(job,model,attempt['sha256']) if charge_request else charge_live(experiment)
                            attempt['harnessAttribution']={'HTTP-Referer':'https://hermes-agent.nousresearch.com','X-Title':'Hermes Agent','source':'pinned agent/auxiliary_client.py _OR_HEADERS_BASE; actual AIAgent runtime'}
                            forwarded={**body,'provider':{'allow_fallbacks':False,'max_price':{'prompt':0,'completion':0}},'models':None}
                            forwarded.pop('models')
                            req=Request('https://openrouter.ai/api/v1/chat/completions',data=dump(forwarded).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','User-Agent':'PokemonInfluencer-HERMES01','HTTP-Referer':'https://hermes-agent.nousresearch.com','X-Title':'Hermes Agent'})
                            with urlopen(req,timeout=min(15,max(.1,end-time.monotonic()))) as r:response=json.load(r)
                        if len(dump(response).encode())>64000:raise WorldError('response audit bound')
                        attempt['response']=response;attempt['finishedAt']=time.time();attempt['latencySeconds']=attempt['finishedAt']-attempt['startedAt'];self.reply(response)
                    elif self.path.startswith('/tool/'):
                        name=self.path.removeprefix('/tool/')
                        if name not in NAMES or len(record['tools'])>=6:raise WorldError('game tool allowlist/budget')
                        entry={'name':name,'arguments':body};record['tools'].append(entry)
                        if not isinstance(body,dict) or (set(body)!={'result'} if name==NAMES[3] else bool(body)):raise WorldError('tool selectors/arguments prohibited')
                        with opener(database) as w:
                            tools=w.job_tools(job)
                            if name==NAMES[3]:entry['trustedSubmission']=build_submission(body['result'],w._job(job)[1])
                            output=tools.submit_recap_and_memory_result(body['result'],model={'id':model,'revision':PIN,'transport':transport,'promptVersion':PROMPT_VERSION,'inputRequestSHA256':record['requests'][-1]['sha256'],'promptSHA256':hashlib.sha256((ROOT/'prompts/hermes_recap_v3.txt').read_bytes()).hexdigest()}) if name==NAMES[3] else getattr(tools,name)()
                        entry['output']=output;self.reply(output)
                    else:raise WorldError('unsupported local route')
                except Exception as error:
                    reason=type(error).__name__+': '+str(error)
                    if isinstance(error,HTTPError):
                        detail=error.read(4000).decode(errors='replace')
                        if key:detail=detail.replace(key,'[credential redacted]')
                        reason+='; '+detail[:1200]
                        record.setdefault('providerErrors',[]).append({'status':error.code,'body':detail[:1200]})
                    # Provider exceptions may contain request URLs, never headers/key.
                    record['failures'].append(reason[:400]);self.reply({'error':{'message':reason[:400],'type':'pi_guard'}},400)
        server=HTTPServer(('127.0.0.1',0),Handler);server.timeout=.1
        env={'PATH':str(PYTHON.parent)+':/usr/bin:/bin','LANG':'en_US.UTF-8','HERMES_HOME':str(home),'HERMES_SAFE_MODE':'1','PYTHONPATH':str(ROOT)+os.pathsep+str(INSTALL),'PYTHONDONTWRITEBYTECODE':'1','HERMES_ENVIRONMENT_HINT':'Isolated game-test agent. Only supplied game tools are available.'}
        child_cfg={'home':str(home),'endpoint':'http://127.0.0.1:'+str(server.server_port),'token':token,'model':model,'recapContentSchema':model_result_schema(),'prompt':str(ROOT/'prompts/hermes_recap_v3.txt'),'purpose':grant['mode'],'maxRequests':max_requests,'stopAfterSubmission':experiment=='closeout','qualificationOnly':bool(getattr(initial,'qualification_only',False))}
        (home/'job.json').write_text(dump(child_cfg))
        import threading
        main_thread=threading.current_thread() is threading.main_thread()
        previous_term=signal.getsignal(signal.SIGTERM) if main_thread else None
        def terminate(signum,frame):raise KeyboardInterrupt('task-owned launcher cancelled')
        if main_thread:signal.signal(signal.SIGTERM,terminate)
        try:
            with (audit_root/(home.name+'.worker.log')).open('w') as out:
                proc=subprocess.Popen([str(PYTHON),'-u',str(ROOT/'scripts/hermes_worker.py'),'--job-config',str(home/'job.json')],cwd=home/'work',env=env,stdout=out,stderr=subprocess.STDOUT)
                owner['pid']=proc.pid;(home/MARKER).write_text(dump(owner))
                while proc.poll() is None and time.monotonic()<end:server.handle_request()
                if proc.poll() is None:
                    record['failures'].append('hard_job_deadline');proc.terminate()
                    try:proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=3)
                record['workerExit']=proc.returncode
        finally:
            if main_thread:signal.signal(signal.SIGTERM,previous_term)
            server.server_close()
            if proc and proc.poll() is None:proc.terminate();proc.wait(timeout=3)
            owner.update(pid=0,active=False);(home/MARKER).write_text(dump(owner))
            with opener(database) as w:
                row=w._one('SELECT * FROM puppeteer_jobs WHERE id=?',(job,))
                if row['status']=='active':
                    try:
                        if grant['mode']=='recall' and proc.returncode==0 and NAMES[1] in {t['name'] for t in record['tools'] if 'output' in t}:w.finish_recall_job(job)
                        else:w.fallback(job,'runtime_failed_or_no_valid_submission')
                    except WorldError as error:
                        # Save/restore invalidation is recovery state, never fabricate facts.
                        w.recover_job(job,'grant_revoked');record['failures'].append('grant_revoked: '+str(error))
                row=w._one('SELECT * FROM puppeteer_jobs WHERE id=?',(job,));record['outcome']=json.loads(row['outcome']) if row['outcome'] else None
                w.audit(job,'runtime-audit-summary',{'transport':transport,'model':model,'requestCount':len(record['requests']),'toolCount':len(record['tools']),'failures':record['failures'],'runtimeHomeID':home.name})
            (audit_root/(home.name+'.json')).write_text(json.dumps(record,indent=2))
        return record


def recover_runtime(target,stop=False,quarantine=False):
    p,owner=checked_home(target,allow_active=True,inspect_contents=not quarantine)
    pid=owner.get('pid',0)
    alive=False
    if pid:
        try:os.kill(pid,0);alive=True
        except ProcessLookupError:pass
    if alive:
        if not stop:raise WorldError('tracked runtime is active; explicit --stop required')
        command=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True).strip()
        if str(ROOT/'scripts/hermes_worker.py') not in command or str(p/'job.json') not in command:raise WorldError('PID ownership mismatch; no process signalled')
    if Path(owner['database']).exists():
        with open_store(owner['database']) as w:recovery=w.recover_job(owner['domainJobID'],'explicit_runtime_cleanup')
    elif quarantine:
        recovery={'status':'database_unavailable','grantNotReusable':True,'reason':'abandoned owned execution; no campaign data deleted'}
        AUDIT.mkdir(parents=True,exist_ok=True)
        (AUDIT/(p.name+'.cleanup-recovery.json')).write_text(dump({'jobID':owner['domainJobID'],'runtimeHome':str(p),'recovery':recovery}))
    else:raise WorldError('database unavailable; retained-audit cleanup or quarantine required')
    if alive:
        os.kill(pid,signal.SIGTERM)
        for _ in range(30):
            try:os.kill(pid,0)
            except ProcessLookupError:break
            time.sleep(.1)
        else:raise WorldError('tracked worker not yet reaped; cleanup remains refused')
    owner.update(pid=0,active=False);(p/MARKER).write_text(dump(owner))
    if quarantine:
        dest=HOMES.parent/'quarantine'
        if dest.is_symlink():raise WorldError('unsafe quarantine root')
        dest.mkdir(exist_ok=True);target=dest/p.name
        if target.exists():raise WorldError('quarantine target already exists')
        p.rename(target);return {'quarantined':str(target),'recovery':recovery,'neverReusable':True}
    return {'recovery':recovery,'runtime':str(p)}


def run_job(database,job,transport='mock',behavior='valid',live=False,experiment='original',store_factory=None,charge_request=None,audit_directory=None):
    opener=store_factory or open_store
    audit_root=Path(audit_directory) if audit_directory is not None else AUDIT
    try:return _run_job(database,job,transport,behavior,live,experiment,store_factory,charge_request,audit_directory)
    except Exception as error:
        # Including a missing install/provider/preflight. Do not leave publication
        # dependent on having reached process construction.
        with opener(database) as w:
            outcome=w.recover_job(job,'runtime_unavailable:'+type(error).__name__)
            w.audit(job,'runtime-unavailable',{'type':type(error).__name__,'reason':str(error)[:400]})
        record={'jobID':job,'transport':transport,'runtimeHome':None,'requests':[],'tools':[],'outcome':outcome,'failures':[type(error).__name__+': '+str(error)[:400]]}
        audit_root.mkdir(parents=True,exist_ok=True);(audit_root/(job+'.unavailable.json')).write_text(json.dumps(record,indent=2));return record
