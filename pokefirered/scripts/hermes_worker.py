#!/usr/bin/env python3
"""Actual pinned AIAgent loop, in a new process; no SQL/source/keys in tools."""
import argparse,json,os,socket
from pathlib import Path
from urllib.request import Request,urlopen
p=argparse.ArgumentParser();p.add_argument('--job-config',type=Path,required=True);args=p.parse_args()
cfg=json.loads(args.job_config.read_text());home=Path(cfg['home'])
if os.environ.get('HERMES_HOME')!=str(home) or Path.cwd()!=home/'work':raise RuntimeError('fresh home/cwd required')
# Enforce loopback-only networking in the runtime, including auxiliary SDK calls.
_original_getaddrinfo=socket.getaddrinfo
def getaddrinfo(host,port,*args,**kwargs):
    if host not in ('127.0.0.1','localhost','::1') or int(port)!=_port:raise RuntimeError('non-game DNS disabled in Hermes child')
    return _original_getaddrinfo(host,port,*args,**kwargs)
socket.getaddrinfo=getaddrinfo
_original_connect=socket.socket.connect
_original_connect_ex=socket.socket.connect_ex
_port=int(cfg['endpoint'].rsplit(':',1)[1])
def guard_address(address):
    if not isinstance(address,tuple) or address[0] not in ('127.0.0.1','localhost','::1') or address[1]!=_port:raise RuntimeError('non-game network disabled in Hermes child')
def connect(self,address):guard_address(address);return _original_connect(self,address)
def connect_ex(self,address):guard_address(address);return _original_connect_ex(self,address)
socket.socket.connect=connect;socket.socket.connect_ex=connect_ex
from hermes_constants import get_hermes_home
if get_hermes_home().resolve()!=home.resolve():raise RuntimeError('Hermes home resolution mismatch')
from run_agent import AIAgent
import model_tools  # finish built-in discovery before removing the entire registry
from tools.registry import registry
from toolsets import create_custom_toolset
NAMES=('get_battle_evidence','recall_puppeteer_memory','get_actor_context','submit_recap_and_memory_result')
# Builtins are discovered at import by upstream. Remove them before construction.
for entry in registry.get_all_entries():registry.deregister(entry.name);registry.deregister(entry.name,scope=registry.current_scope_key())
allowed_names=(NAMES[1],) if cfg['purpose']=='recall' else NAMES
for name in allowed_names:
    params={'type':'object','properties':{},'additionalProperties':False,'required':[]}
    if name==NAMES[-1]:params.update(properties={'result':cfg['recapContentSchema']},required=['result'])
    def handler(arguments,tool_name=name,**kwargs):
        req=Request(cfg['endpoint']+'/tool/'+tool_name,data=json.dumps(arguments).encode(),headers={'Authorization':'Bearer '+cfg['token'],'Content-Type':'application/json'})
        try:
            with urlopen(req,timeout=16) as r:output=r.read().decode()
            outcome=json.loads(output)
            qualified=cfg.get('qualificationOnly') and outcome.get('qualificationValid') and outcome.get('committed') is False
            if tool_name==NAMES[-1] and cfg.get('stopAfterSubmission') and (outcome.get('postID') or qualified):
                # Pinned official interrupt control safely stops further inference
                # only after the trusted domain service returned a committed outcome.
                reason='qualification_valid_discard_only' if qualified else 'game_recap_committed'
                agent.interrupt(hard_cancel=True,tool_reason=reason)
                print(json.dumps({'completionReason':reason,'postID':outcome.get('postID')}))
            return output
        except Exception as e:return json.dumps({'error':type(e).__name__,'message':'Game tool rejected the scoped request.'})
    registry.register(name,'pokemon_recap',{'name':name,'description':{'get_battle_evidence':'Retrieve this trainer battle evidence and publication policy. No selectors.', 'recall_puppeteer_memory':'Retrieve durable prior episodes owned by this actor. No selectors.', 'get_actor_context':'Retrieve filtered actor knowledge and persona. No selectors.', 'submit_recap_and_memory_result':'Validate and atomically publish the mandatory recap and retain private memory.'}[name],'parameters':params},handler,max_result_size_chars=24000)
create_custom_toolset('pokemon_recap','Scoped mandatory battle recap',list(allowed_names))
class GameAgent(AIAgent):
    # The upstream generic prompt includes local profile paths. This reviewed
    # prompt hook changes only prompt construction; inference/tools use Hermes.
    def _build_system_prompt(self,system_message=None):
        if cfg['purpose']=='recall':return 'You are Hermes in a fresh actor-restricted memory inspection job. First call recall_puppeteer_memory. Then briefly describe the retrieved observed species/player moves/own actions and finish. You have exactly two model requests. Never request another tool or publication. This read-only grant cannot publish or modify gameplay. No strategies or inference of hidden data.'
        return Path(cfg['prompt']).read_text()
agent=GameAgent(base_url=cfg['endpoint']+'/v1',api_key=cfg['token'],provider='custom',api_mode='chat_completions',model=cfg['model'],max_iterations=cfg.get('maxRequests',3),enabled_toolsets=['pokemon_recap'],save_trajectories=False,quiet_mode=True,skip_context_files=True,load_soul_identity=False,skip_memory=True,skip_background_review=True,session_db=None,max_tokens=1200,run_budget_seconds=45,fallback_model=None,cwd=str(home/'work'))
for entry in registry.get_all_entries():
    if entry.name not in allowed_names:registry.deregister(entry.name);registry.deregister(entry.name,scope=registry.current_scope_key())
print(json.dumps({'resolvedTools':sorted(agent.valid_tool_names),'registryTools':sorted(e.name for e in registry.get_all_entries())}))
if set(agent.valid_tool_names)!=set(allowed_names) or {e.name for e in registry.get_all_entries()}!=set(allowed_names):raise RuntimeError('actual registered tools widened')
if agent.compression_enabled or agent._auto_recovery_cycles or agent._api_max_retries!=1:raise RuntimeError('auxiliary inference/retry guard mismatch')
# Set the official transport SDK retry limit too; parent counts every HTTP attempt.
if hasattr(agent,'client') and hasattr(agent.client,'max_retries'):agent.client.max_retries=0
print(json.dumps({'effectiveHomeID':home.name,'actualRegisteredTools':sorted(agent.valid_tool_names),'compressionEnabled':agent.compression_enabled,'skipMemory':True,'freshConversation':True}))
task='Call recall_puppeteer_memory once, then summarize its authorized durable battle memory and finish without submitting.' if cfg['purpose']=='recall' else 'Process the bound completed battle. Call get_battle_evidence once to retrieve its complete authorized actor/prior-memory bundle, then submit one valid mandatory recap. Finish after successful submission.'
result=agent.run_conversation(task,conversation_history=[])
print(json.dumps({'finished':True,'apiCalls':getattr(agent,'api_calls',None),'resultKeys':sorted(result) if isinstance(result,dict) else []}))
