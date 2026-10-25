"""Bounded fragment/decision state; fixture or hosted provider work stays off-writer."""
import json,struct,time
from concurrent.futures import ThreadPoolExecutor
from bridge.events_wire import Message
from .domain import decode,request_for,DeterministicProvider
class Handler:
 def __init__(self,manifest,evidence,mode='first_move',provider=None,shadow=False,decision_source='external_test',decision_seconds=2.5):
  if not 0<decision_seconds<3:raise ValueError('bounded tactical host deadline')
  self.decision_seconds=decision_seconds;self.shadow=shadow;self.decision_source=decision_source;self.m=manifest;self.e=evidence;self.provider=provider or DeterministicProvider(mode);self.pool=ThreadPoolExecutor(max_workers=1);self.job=None;self.retired=None;self.mode=mode;self.pending={};self.fragments=None;self.deadline=0;self.store=None;self.awaiting={};self.ended=set();self.recovered=False;self.retired_requests=set()
 def log(self,kind,record):
  with (self.e/'battle-audit.jsonl').open('a') as f:f.write(json.dumps({'event':kind,**record},sort_keys=True)+'\n')
 def disposition(self,record,stage,reason=None):
  packet=record.get('request',{});state=packet.get('nativeState');scope=packet.get('scope')
  if not state or not scope:return
  entry={'stage':stage,'reason':reason,'scope':scope,'session':state['nonce'],'generation':state['generation'],'nativeRequest':state['request'],'battle':state['battle'],'turn':state['turn'],'phase':state['phase'],'battler':state['battler'],'nativeSelected':record.get('nativeSelected'),'source':record.get('source'),'nativeHash':packet['actionSetHash'],'fallbackReason':0}
  if self.store is not None and hasattr(self.store,'record_decision_lifecycle'):
   current=self.store.campaign()
   if (scope['campaign'],scope['branch'])==(current['id'],current['active_branch']):self.store.record_decision_lifecycle(entry)
   elif stage not in ('CANCELED_RESET','CANCELED_RUN_ABORT'):raise ValueError('stale lifecycle branch')
   else:entry['activeProjectionExcluded']=True
  self.log('decision-disposition',entry)
 def recover(self,store):
  """A fresh host never resumes a former process's unfinished tactical result."""
  if self.recovered:return
  self.recovered=True;self.store=store
  if not hasattr(store,'decision_lifecycle'):return
  from .lifecycle import TERMINAL
  groups={}
  for row in store.decision_lifecycle():
   key=(row['session'],row['generation'],row['nativeRequest']);groups.setdefault(key,[]).append(row)
  for key,rows in groups.items():
   if key in self.pending or key in self.awaiting:continue
   self.retired_requests.add(key)
   if any(r['stage'] in TERMINAL for r in rows):continue
   row=rows[-1];reason='CANCELED_BATTLE_ENDED' if self.is_ended(store,row['session'],row['generation'],row['battle']) else 'CANCELED_RUN_ABORT'
   entry={**row,'stage':reason,'reason':'fresh host recovery; prior process result is not resumable'}
   store.record_decision_lifecycle(entry);self.log('decision-disposition',entry)
 def is_ended(self,store,nonce,generation,battle):
  key=(nonce,generation,battle)
  if key in self.ended:return True
  if hasattr(store,'get_canonical_events'):
   for event in reversed(store.get_canonical_events()):
    r=event['record']
    if r.get('eventType')=='BATTLE_ENDED' and (r.get('session'),r.get('run'),r.get('battleID'))==key:
     self.ended.add(key);return True
  return False
 def observe_event(self,message,store):
  from bridge.events import decode_event
  self.store=store;r=decode_event(message)
  if r['eventType']=='BATTLE_ENDED':
   self.ended.add((message.nonce,message.generation,r['battleID']))
   self.cancel('CANCELED_BATTLE_ENDED',session=message.nonce,battle=r['battleID'])
  elif r['eventType']=='BATTLE_ACTION_RESOLVED' and r['payload']['actorSide']==1:
   for key,record in list(self.awaiting.items()):
    state=record['request']['nativeState']
    if (state['nonce'],state['battle'],state['turn'])==(message.nonce,r['battleID'],r['turnID']):
     self.disposition(record,'EXECUTED','canonical NPC action resolution; effects remain native');self.awaiting.pop(key,None)
 def retained_terminal(self,store,record,native_source):
  """Pure historical audit lookup; no launch authority, provider, or write.

  receive() still checks managed launch permission before using this result.
  Recovery inspection may call it on a suspended read-only evidence view.
  """
  key=(record['session'],record['generation'],record['nativeRequest'])
  previous=next((r for r in reversed(store.battle_audit()) if
      r.get('event')!='decision-disposition' and (r.get('session'),r.get('generation'),r.get('nativeRequest'))==key),None) if hasattr(store,'battle_audit') else None
  if previous:
   fields=('nativeHash','battle','turn','phase','battler','fallbackReason','nativeSelected')
   categories={1:('mercury','external_test'),2:('vanilla_fallback',),3:('engine_forced',),4:('canceled_battle_ended',)}
   if any(previous[k]!=record[k] for k in fields) or previous['source'] not in categories.get(native_source,()):raise ValueError('conflicting retained native terminal receipt')
  return previous
 def receive(self,msg,store,sock):
  # Managed run authority also applies to audit/control envelopes, not only facts.
  if hasattr(store,'_launch'):store._launch(msg.nonce,msg.generation)
  self.recover(store);self.store=store
  if msg.kind==8 and msg.typ==9:
   req,h,total,offset=struct.unpack_from('<IIHH',msg.payload);body=msg.payload[12:];now=time.monotonic()
   if req!=msg.sequence or total!=self.m['battle_abi'][0] or not 0<len(body)<=80 or offset+len(body)>total:raise ValueError('battle fragment bounds')
   key=(msg.nonce,msg.generation,req,h,total)
   if not offset:self.fragments=(key,bytearray());self.deadline=now+4
   if not self.fragments or self.fragments[0]!=key or len(self.fragments[1])!=offset or now>self.deadline:raise ValueError('battle fragment identity/order')
   self.fragments[1].extend(body)
   if len(self.fragments[1])<total:return
   data=bytes(self.fragments[1]);self.fragments=None
   crc=2166136261
   for b in data:crc=((crc^b)*16777619)&0xffffffff
   if crc!=h:raise ValueError('battle snapshot hash')
   state=decode(data,self.m['battle_abi'],tuple(self.m.get('qualified_trainers',[102])))
   if state['nonce']!=msg.nonce or state['generation']!=msg.generation or state['request']!=req:raise ValueError('battle snapshot session')
   if key[:3] in self.retired_requests or self.is_ended(store,msg.nonce,msg.generation,state['battle']):
    self.log('obsolete-tactical-packet',{'session':msg.nonce,'generation':msg.generation,'request':req,'battle':state['battle']});return
   packet=request_for(store,state,h);(self.e/f'turn-{msg.nonce}-{req}.json').write_text(json.dumps(packet,indent=2)+'\n');(self.e/f'turn-{msg.nonce}-{req}.txt').write_text(packet['state']+'\n')
   if self.job is not None or (self.retired is not None and not self.retired.done()):
    self.log('provider-busy',{'request':req});return
   if len(self.pending)>=32:
    oldest=self.pending.pop(next(iter(self.pending)));self.disposition(oldest,'CANCELED_UNSUPPORTED','bounded pending audit capacity')
   record={'request':packet,'receivedMonotonic':now,'source':'pending'};self.pending[key[:3]]=record;self.disposition(record,'REQUESTED')
   future=self.pool.submit(self.provider.decide_scoped,packet) if hasattr(self.provider,'decide_scoped') else self.pool.submit(self.provider.decide,packet['state'],packet['question'],packet['choices'])
   self.job={'future':future,'message':msg,'record':record,'deadline':now+self.decision_seconds}
  elif msg.kind==10 and msg.typ==11:
   req,h,battle,turn,phase,battler,source,reason,selected=struct.unpack('<IIIHBBBBH',msg.payload)
   key=(msg.nonce,msg.generation,req);old=self.pending.pop(key,None)
   if self.job and self.job['message'].sequence==req:self.job['future'].cancel();self.retired=self.job['future'];self.job=None
   record={'session':msg.nonce,'generation':msg.generation,'nativeRequest':req,'nativeHash':f'{h:08x}','battle':battle,'turn':turn,'phase':phase,'battler':battler,'source':{1:self.decision_source,2:'vanilla_fallback',3:'engine_forced',4:'canceled_battle_ended'}.get(source,'invalid'),'fallbackReason':reason,'nativeSelected':selected,'selection':old}
   if old and source==1 and selected!=old['nativeSelected']:raise ValueError('selected/executed controller mismatch')
   # Native source1 means externally selected, not the restarted host's mode.
   # An active, identical retained receipt reuses original immutable provenance.
   previous=self.retained_terminal(store,record,source)
   if previous:
    store.record_battle_audit(previous)
    self.log('duplicate-native-terminal',previous);return
   store.record_battle_audit(record);self.log('native-terminal',record)
   if old and source==1:
    self.disposition(old,'CONTROLLER_EMITTED','native revalidation accepted; not yet battle effect')
    self.awaiting[key]=old
   elif old and source in (2,4):self.disposition(old,'CANCELED_BATTLE_ENDED' if source==4 else 'CANCELED_TIMEOUT_FALLBACK','native terminal receipt')
  else:raise ValueError('unexpected tactical envelope')

 def tick(self,store,sock):
  self.recover(store);self.store=store
  job=self.job
  if not job:return
  future=job['future'];record=job['record'];packet=record['request'];msg=job['message']
  state=packet.get('nativeState')
  if state and self.is_ended(store,state['nonce'],state['generation'],state['battle']):
   self.cancel('CANCELED_BATTLE_ENDED',session=state['nonce'],battle=state['battle']);return
  expired=time.monotonic()>=job['deadline']
  if not future.done() and not expired:return
  self.job=None
  if expired:
   future.cancel();self.retired=future;record.update(result=None,source='unavailable',nativeSelected=None);self.log('selection-timeout',record);self.disposition(record,'CANCELED_TIMEOUT_FALLBACK','host deadline');self.pending.pop((getattr(msg,'nonce',None),getattr(msg,'generation',None),getattr(msg,'sequence',None)),None);return
  try:result=future.result()
  except Exception as error:result=None;self.log('provider-rejected',{'reason':type(error).__name__})
  if not isinstance(result,dict):result=None
  selected=result.get('choiceID') if result else None
  if selected is not None and (not isinstance(selected,str) or selected not in packet['nativeActions']):result=None;selected=None
  record.update(result=result,source=('mercury_shadow' if self.shadow else self.decision_source) if result else 'unavailable',nativeSelected=packet['nativeActions'].get(selected),hostLatencySeconds=time.monotonic()-record['receivedMonotonic']);self.log('selection',record)
  if not result:
   self.disposition(record,'CANCELED_TIMEOUT_FALLBACK','provider unavailable or invalid; native fallback remains authoritative');self.pending.pop((getattr(msg,'nonce',None),getattr(msg,'generation',None),getattr(msg,'sequence',None)),None);return
  scope=packet['scope']
  if scope['campaign']!=store.campaign()['id'] or scope['branch']!=store.get_active_branch() or store.campaign()['status'] not in ('paired','imported') or not store._one("SELECT 1 FROM launches WHERE nonce=? AND status='active'",(msg.nonce,)):self.log('late-result-discarded',{'requestID':packet['requestID']});self.disposition(record,'CANCELED_RESET','scope or launch revoked');return
  if self.shadow:self.log('shadow-result',record);return
  state=packet['nativeState'];h=int(packet['actionSetHash'],16);b=struct.pack('<4IHBBHH',state['request'],h,state['battle'],msg.generation,state['turn'],1 if state['phase']=='NORMAL_TURN' else 2,state['battler'],packet['nativeActions'][selected],0)
  sock.sendall(Message(9,msg.nonce,msg.generation,msg.sequence,msg.tag,10,b).encode());self.disposition(record,'RESULT_PUBLISHED')
 def disconnected(self):
  if self.job:
   record=self.job['record'];self.job['future'].cancel();self.retired=self.job['future'];self.job=None
   self.disposition(record,'CANCELED_TIMEOUT_FALLBACK','socket disconnected before result publication')
   for key,value in list(self.pending.items()):
    if value is record:self.pending.pop(key,None)
  self.fragments=None
 def cancel(self,reason='CANCELED_RUN_ABORT',session=None,battle=None):
  def matches(record):
   state=record.get('request',{}).get('nativeState',{})
   return (session is None or state.get('nonce')==session) and (battle is None or state.get('battle')==battle)
  if self.job and matches(self.job['record']):self.job['future'].cancel();self.retired=self.job['future'];self.job=None
  seen=set()
  for collection in (self.pending,self.awaiting):
   for key,record in list(collection.items()):
    if matches(record):
     if key not in seen:self.disposition(record,reason,'explicit lifecycle termination');seen.add(key)
     collection.pop(key,None)
  self.fragments=None
 def close(self):
  self.cancel();self.pool.shutdown(wait=False)
