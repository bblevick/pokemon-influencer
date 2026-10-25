"""Typed facts vs scoped observations. Deterministic recorder, never an AI consumer."""
import hashlib
import json
import struct
from collections import OrderedDict, deque
from pathlib import Path
from .events_wire import Message
from jsonschema import Draft202012Validator
JSON_VALIDATOR=Draft202012Validator(json.loads((Path(__file__).resolve().parents[1]/'schemas/bridge/event.schema.json').read_text()))
SPEC=json.loads(Path(__file__).with_name('events_protocol.json').read_text())
EVENT_HEADER=struct.Struct('<HHIIHHIHH')
NAMES={v:k for k,v in SPEC['events'].items()}
LENGTHS={1:8,2:0,3:6,4:4,5:4,6:40}
PHASES={1:0,2:1,3:2,4:3,5:3,6:1}

def decode_event(message):
    if message.kind!=1 or message.typ!=3 or message.result or message.error:
        raise ValueError('not event request')
    if len(message.payload)<24:raise ValueError('short event')
    ver,typ,seq,battle,turn,phase,frame,n,flags=EVENT_HEADER.unpack_from(message.payload)
    data=message.payload[24:]
    if ver!=1:raise ValueError('event schema version')
    if typ not in NAMES:raise ValueError('unknown event type')
    if n!=len(data) or n!=LENGTHS[typ] or flags:raise ValueError('event payload bounds/reserved')
    if seq!=message.sequence or not seq or not battle:raise ValueError('event/battle identity')
    if phase!=PHASES[typ] or (typ==1 and turn!=0) or (typ not in (1,5) and turn==0):raise ValueError('event phase/turn')
    record={'transportVersion':2,'schemaVersion':1,'recordClass':'observation' if typ==6 else 'canonical_event',
        'eventType':NAMES[typ],'sequence':seq,'session':message.nonce,'run':message.generation,
        'branch':f'transient:{message.nonce}:{message.generation}','battleID':battle,'turnID':turn,'phase':phase,
        'frameCounter':frame,'buildTag':message.tag,'payloadLength':n,'payload':{}}
    p=record['payload']
    if typ==1:
        bf,trainer,first,reserved=struct.unpack('<IHBB',data)
        if reserved or first>1 or bool(bf&8)!=bool(trainer):raise ValueError('battle kind/trainer')
        p.update(battleFlags=bf,battleKind='trainer' if trainer else 'wild',trainerID=trainer,previouslyUndefeated=bool(first))
    elif typ==3:
        actor,kind,move,species=struct.unpack('<BBHH',data)
        if actor>1 or kind>1 or species==0 or bool(kind)!=bool(move):raise ValueError('action bounds')
        p.update(actorSide=actor,resolutionKind='announced_move' if kind else 'slot_advanced_without_announcement',announcedMoveID=move,visibleActorSpeciesID=species)
    elif typ in (4,5):
        trainer,first,outcome=struct.unpack('<HBB',data)
        if first>1 or not 1<=outcome<=8 or (typ==4 and (not trainer or outcome!=1)):raise ValueError('outcome/trainer defeat')
        p.update(trainerID=trainer,previouslyUndefeated=bool(first),outcome=outcome)
    elif typ==6:
        trainer,species,hp,maxhp,status=struct.unpack_from('<HHHHI',data)
        moves=list(struct.unpack_from('<4H',data,12));pp=list(data[20:24])
        opponent,=struct.unpack_from('<H',data,24);bar,complete=data[26:28]
        revealed=list(struct.unpack_from('<4H',data,28))
        if not species or not opponent or not maxhp or hp>maxhp or bar>48 or complete!=0 or data[36:]!=b'\0'*4:
            raise ValueError('observation bounds/completeness')
        if status & ~0xff:raise ValueError('own status mask')
        p.update(observerSide=1,trainerID=trainer,ownActive={'speciesID':species,'hp':hp,'maxHP':maxhp,'statusMask':status,
            'knownMoveIDs':[x for x in moves if x],'movePP':pp},
            opponentActive={'revealedSpeciesID':opponent,'publicHPBar':bar,'publicHPBarMax':48,'revealedMoveIDs':[x for x in revealed if x]},
            legalActionsComplete=False)
    JSON_VALIDATOR.validate(record)
    return record

class Consumer:
    """Bounded recent dedupe and battle state; recorder-only, no world projections.

    Caller fsyncs accepted JSONL before ACK. Replay/restore reuses exact messages.
    """
    def __init__(self,nonce,generation,tag):
        self.identity=(nonce,generation,tag);self.last=0;self.cache=OrderedDict();self.battles={};self.gaps=deque(maxlen=64)
    def accept(self,message):
        if (message.nonce,message.generation,message.tag)!=self.identity:raise ValueError('stale session/run/build')
        old=self.cache.get(message.sequence)
        if old:
            if old!=message:raise ValueError('conflicting duplicate')
            return None, self.ack(message)
        if message.sequence<=self.last:raise ValueError('stale sequence/cache evicted')
        r=decode_event(message);seq=r['sequence'];gap=seq-self.last-1
        # Check lifecycle before mutating any recorder state.
        b=self.battles.get(r['battleID']);t=r['eventType'];turn=r['turnID']
        if t=='BATTLE_STARTED':
            if b is not None:raise ValueError('battle ID reused')
            b={'turn':0,'phase':0,'ended':False,'incomplete':bool(gap),'trainer':r['payload']['trainerID'],'defeated':False}
        elif b is None:
            if not gap:raise ValueError('event without battle start')
            b={'turn':turn,'phase':r['phase'],'ended':False,'incomplete':True,'trainer':r['payload'].get('trainerID'),'defeated':False}
        else:
            b=dict(b)
            if b['ended']:raise ValueError('event after battle end')
            if turn<b['turn']:raise ValueError('turn regression')
            if t=='BATTLE_TURN_STARTED':
                if turn!=b['turn']+1 and not gap:raise ValueError('turn order')
            elif turn!=b['turn'] and not gap:raise ValueError('turn without selection')
            if turn==b['turn'] and r['phase']<b['phase']:raise ValueError('illegal phase ordering')
            b['turn']=turn;b['phase']=r['phase'];b['incomplete']|=bool(gap)
        if t in ('TRAINER_DEFEATED','BATTLE_ENDED','BATTLE_OBSERVATION') and b['trainer'] is not None and r['payload']['trainerID']!=b['trainer']:
            raise ValueError('trainer correlation')
        if t=='TRAINER_DEFEATED':
            if b['defeated']:raise ValueError('duplicate defeat under different sequence')
            b['defeated']=True
        if t=='BATTLE_ENDED':b['ended']=True
        evict=None
        if r['battleID'] not in self.battles and len(self.battles)>=32:
            ended=next((k for k,v in self.battles.items() if v['ended']),None)
            if ended is None:raise ValueError('battle tracking capacity')
            evict=ended
        if gap:self.gaps.append({'after':self.last,'before':seq,'missing':gap})
        r.update(sequenceGap=gap,streamIncomplete=b['incomplete'])
        if evict is not None:del self.battles[evict]
        self.battles[r['battleID']]=b
        self.cache[seq]=message
        if len(self.cache)>256:self.cache.popitem(last=False)
        self.last=seq
        return r,self.ack(message)
    def ack(self,message):return Message(2,message.nonce,message.generation,message.sequence,message.tag,4,b'')

def observation_for_context(record):
    """Projection preview only; lacks complete legal actions, never an inference request."""
    if record['recordClass']!='observation':raise ValueError('canonical event cannot be model context')
    p=record['payload'];own=dict(p['ownActive']);own.pop('movePP');mask=own.pop('statusMask');own['status']=next((v for bit,v in [(128,'toxic'),(64,'paralysis'),(32,'freeze'),(16,'burn'),(8,'poison'),(7,'sleep')] if mask & bit),'none')
    other=dict(p['opponentActive']);other['publicHPFraction']=other.pop('publicHPBar')/other.pop('publicHPBarMax')
    return {'battleID':record['battleID'],'turn':record['turnID'],'phase':record['phase'],
            'ownActive':own,'opponentActive':other,'legalActionsComplete':False,
            'observationHash':hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
