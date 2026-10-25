"""Decode the native sanitized snapshot, never emulate battle legality."""
import struct,hashlib,json
from roster.extract import digest
from system1.domain import symbol as label

def decode(data,abi,allowed_trainers=(102,)):
 size,work,mon,event,own,actions,history,_,_=abi
 if len(data)!=size or size>2048:raise ValueError('native snapshot size')
 ver,n,trainer,phase,count=struct.unpack_from('<HHHBB',data)
 if ver!=1 or n!=size or trainer not in allowed_trainers or phase not in (1,2) or not 0<count<=14:raise ValueError('native header')
 battle,request,nonce,generation=struct.unpack_from('<4I',data,8);turn,battler,active,mask,hcount,foe=struct.unpack_from('<H4BH',data,24)
 if battler!=1 or active>=6 or hcount>16:raise ValueError('native qualified singles state')
 state={'trainerID':trainer,'phase':'NORMAL_TURN' if phase==1 else 'FORCED_REPLACEMENT','battle':battle,'request':request,'nonce':nonce,'generation':generation,'turn':turn,'battler':battler,'activeSlot':active,'moveMask':mask,'opponent':{'species':foe,'hpBar':data[32],'status':data[33],'revealedMoves':list(struct.unpack_from('<4H',data,36))},'weather':struct.unpack_from('<H',data,34)[0],'inventory':list(struct.unpack_from('<4H',data,44)),'own':[],'actions':[],'history':[]}
 for i in range(6):
  off=own+i*mon;species,hp,maxhp,item,*moves=struct.unpack_from('<8H',data,off)
  if not species:continue
  status,status2,status3=struct.unpack_from('<3I',data,off+16)
  state['own'].append({'slot':i,'species':species,'hp':hp,'maxHP':maxhp,'heldItem':item,'moves':moves,'status':status,'status2':status2,'status3':status3,'level':data[off+28],'types':list(data[off+29:off+31]),'ability':data[off+31] if i==active else None,'pp':list(data[off+32:off+36]),'maxPP':list(data[off+36:off+40]),'stages':list(data[off+40:off+48]) if i==active else []})
 for i in range(count):
  id,value,kind,slot,target,flags=struct.unpack_from('<HH4B',data,actions+8*i)
  if kind not in (1,2,3,4,5) or id!=(kind<<8)|slot or id in [a['nativeID'] for a in state['actions']]:raise ValueError('action identity')
  state['actions'].append({'nativeID':id,'kind':{1:'MOVE',2:'SWITCH',3:'ITEM',4:'REPLACE',5:'ENGINE_STRUGGLE'}[kind],'slot':slot,'value':value,'target':target,'flags':flags})
 for i in range(hcount):
  t,move,species,side,kind,hp,status,ownhp,item=struct.unpack_from('<HHH4BHH',data,history+i*event)
  state['history'].append({'turn':t,'move':move,'species':species,'side':side,'nativeActionKind':kind,'opponentHPBar':hp,'opponentStatus':status,'ownHP':ownhp,'item':item})
 return state

def request_for(store,state,hash32):
 if hasattr(store,'observe_native_preparation'):store.observe_native_preparation(state)
 actor='trainer:'+store.registry['mapping'][str(state['trainerID'])] if hasattr(store,'registry') else 'trainer:fr:trainer:%04d'%state['trainerID']
 lock=store.locked_preparation(actor)
 if not lock:raise ValueError('locked preparation required')
 scope={'campaign':store.campaign()['id'],'branch':store.get_active_branch(),'nativeROM':store.compatibility['nativeROM'],**{k:state[k] for k in ('nonce','generation','battle','turn','battler','phase','request')}}
 choices={};ids={}
 for a in state['actions']:
  identity=f"{state['battle']}:{state['turn']}:{state['phase']}:{state['battler']}:{state['request']}:{hash32:08x}:{a['kind']}:{a['slot']}";ids[identity]=a['nativeID']
  if a['kind']=='MOVE':
   mon=next(p for p in state['own'] if p['slot']==state['activeSlot']);row=store.content.cat.lookup('moves',a['value']);desc=f"Use {label(store.content.cat,'moves',a['value'])} (move {a['value']}, slot {a['slot']}, PP {mon['pp'][a['slot']]}/{mon['maxPP'][a['slot']]}, type {row.get('type')}, power {row.get('power')}, accuracy {row.get('accuracy')}, effect {row.get('effect')}, target battler {a['target']})."
  elif a['kind'] in ('SWITCH','REPLACE'):
   p=next(p for p in state['own'] if p['slot']==a['slot']);lineage=lock['candidate']['order'][a['slot']] if a['slot']<len(lock['candidate']['order']) else 'fixture-only';desc=f"{a['kind'].title()} with own slot {a['slot']} lineage {lineage}: {label(store.content.cat,'species',p['species'])}, level {p['level']}, HP {p['hp']}/{p['maxHP']}, status {p['status']}, types {p['types']}, moves {p['moves']}, PP {p['pp']}."
  elif a['kind']=='ITEM':desc=f"Use allocated native item {a['value']} from finite inventory slot {a['slot']}, native supported class {a['target']}, usable effect flags {a['flags']}, on own active companion."
  else:desc='Engine forced Struggle path; no synthetic move slot or inference required.'
  choices[identity]=desc
 facts=store.trainer_packet(lock['actor']);allowed={'unknowns':facts['unknowns'],'directObservations':[],'reportedClaims':[],'retainedEpisodes':[]}
 for name in ('directObservations','reportedClaims'):
  for row in facts[name][-8:]:
   allowed[name].append({k:(v[-2:] if isinstance(v,list) else v) for k,v in row.items() if k in ('mode','claim','sender','evidenceIDs','deliveryIDs','exposureIDs','occurrencesInWindow')})
 for row in facts['retainedEpisodes'][-2:]:
  allowed['retainedEpisodes'].append({k:(v[-2:] if isinstance(v,list) else v) for k,v in row.items() if k in ('episodeID','battleID','summary','sourceEvidenceIDs')})
 # Context bounds independent of long-term deduplicated knowledge. No arbitrary SQL/provider tool.
 if 'authorizedPrebattleFacts' in lock:allowed=lock['authorizedPrebattleFacts']
 authorized=json.dumps(allowed,sort_keys=True,separators=(',',':'))
 if len(authorized.encode())>8192:raise ValueError('authorized context exceeds explicit bound')
 behavior=store.battle_behavior(lock) if hasattr(store,'battle_behavior') else None
 text='TRAINER / OWN STATE\n'+json.dumps({'trainerID':state['trainerID'],'commitmentID':lock['commitmentID'],'activeSlot':state['activeSlot'],'own':state['own'],'finiteInventory':state['inventory']},sort_keys=True)+'\n\nSTRATEGY MEMO — SUBJECTIVE\n'+lock['strategyText']+'\n\nAUTHORIZED FACTS\n'+authorized+'\n\nCURRENT BATTLE\n'+json.dumps({'opponent':state['opponent'],'weather':state['weather'],'turn':state['turn'],'phase':state['phase']},sort_keys=True)+'\n\nRECENT HISTORY — CHRONOLOGICAL, AT MOST 16 RESOLVED ACTIONS\n'+json.dumps(state['history'],sort_keys=True)+'\n\nLEGAL ACTIONS\n'+'\n'.join(k+' — '+v for k,v in choices.items())
 if behavior:text+='\n\nAUTHORED TRAINER PERSONALITY — FROZEN STRATEGY CONTEXT\n'+json.dumps(behavior,sort_keys=True)
 if len(text.encode())>32768:raise ValueError('future model text bound')
 return {'schemaVersion':2,'requestID':'battle-decision:'+digest(scope),'scope':scope,'actionSetHash':f'{hash32:08x}','strategyID':lock['strategyID'],'strategySHA256':hashlib.sha256(lock['strategyText'].encode()).hexdigest(),'commitmentID':lock['commitmentID'],'state':text,'choices':choices,'nativeActions':ids,'nativeState':state,'question':'Which supplied legal action best pursues this trainer’s subjective strategy?'}

class DeterministicProvider:
 def __init__(self,mode='first_move'):self.mode=mode;self.switched=set()
 def decide(self,state,question,choices):
  if self.mode in ('unavailable','timeout'):return None
  keys=list(choices)
  if self.mode=='switch_once' and ':SWITCH:' in '\n'.join(keys):
   battle=keys[0].split(':')[0]
   if battle not in self.switched:self.switched.add(battle);return {'choiceID':next(k for k in keys if ':SWITCH:' in k),'probabilities':None,'confidence':None,'diagnostics':{'provider':'deterministic_test','model':None,'latencySeconds':0}}
  return {'choiceID':next((k for k in keys if ':MOVE:' in k),keys[0]),'probabilities':None,'confidence':None,'diagnostics':{'provider':'deterministic_test','model':None,'latencySeconds':0}}

class DelayedTestProvider:
 """One deliberately late, pure deterministic result; never a network call."""
 def __init__(self):self.first=True;self.inner=DeterministicProvider('first_move')
 def decide(self,state,question,choices):
  import time
  if self.first:self.first=False;time.sleep(4)
  return self.inner.decide(state,question,choices)
