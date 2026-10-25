"""Bounded presentation codec. Never canonical facts or NPC observations."""
from dataclasses import dataclass
import struct
from .events_wire import Message
COMMAND=struct.Struct('<HHIIHHHH')
RESPONSE=struct.Struct('<HHIIHH')
MAP={' ':0,'!':0xab,'?':0xac,'.':0xad,'-':0xae,"'":0xb4,',':0xb8,'/':0xba,'\n':0xfe}
MAP.update({str(i):0xa1+i for i in range(10)})
MAP.update({chr(65+i):0xbb+i for i in range(26)})
MAP.update({chr(97+i):0xd5+i for i in range(26)})
INV={v:k for k,v in MAP.items()}

def text_encode(text):
    if isinstance(text,bytes):text=text.decode('utf-8','strict')
    if not isinstance(text,str):raise ValueError('UTF-8 text required')
    # Normalize CRLF only; reject lone CR, tabs, control codes and all unknowns.
    text=text.replace('\r\n','\n')
    if not text or any(c not in MAP for c in text):raise ValueError('unsupported character')
    # Two explicit lines; no silent truncation or printer-driven paging.
    lines=text.split('\n')
    if len(lines)==1 and len(text)>24:
        cut=text.rfind(' ',0,25)
        if cut<1:raise ValueError('no bounded word wrap')
        lines=[text[:cut],text[cut+1:]]
    if len(lines)>2 or any(not s or len(s)>24 for s in lines):raise ValueError('line bounds')
    encoded=bytes(MAP[c] for c in '\n'.join(lines))
    if len(encoded)>48:raise ValueError('message bounds')
    return encoded

def text_decode(data):
    try:text=''.join(INV[c] for c in data)
    except KeyError as e:raise ValueError('control/unsupported encoded character') from e
    # Validation must not transform the packet's original line layout.
    if text_encode(text)!=data:raise ValueError('noncanonical encoded lines')
    return text

@dataclass(frozen=True)
class Command:
    command_id:int
    request_id:int
    kind:int
    text:str
    choices:tuple=()
    ttl:int=900
    def payload(self):
        if not 0<self.command_id<=0xffffffff or not 0<self.request_id<=0xffffffff:raise ValueError('identity')
        if not 60<=self.ttl<=900:raise ValueError('expiry')
        if self.kind==1 and not self.choices:ids=(0,0)
        elif self.kind==2 and len(self.choices)==2 and tuple(x[1] for x in self.choices)==('YES','NO'):
            ids=tuple(x[0] for x in self.choices)
            if any(type(x)!=int or not 1<=x<=65535 for x in ids) or ids[0]==ids[1]:raise ValueError('choice IDs')
        else:raise ValueError('choice count/labels/type')
        data=text_encode(self.text)
        return COMMAND.pack(1,self.kind,self.request_id,self.ttl,len(self.choices),*ids,len(data))+data
    def message(self,nonce,run,tag):return Message(4,nonce,run,self.command_id,tag,6,self.payload())
    @classmethod
    def decode(cls,msg):
        if msg.kind!=4 or msg.typ!=6 or msg.result or msg.error or len(msg.payload)<21:raise ValueError('command envelope')
        ver,kind,req,ttl,count,yes,no,n=COMMAND.unpack_from(msg.payload)
        if ver!=1 or n!=len(msg.payload)-20:raise ValueError('schema/length')
        if kind==1 and (count or yes or no):raise ValueError('notice choices')
        if kind==2 and count!=2:raise ValueError('choice count')
        choices=((yes,'YES'),(no,'NO')) if kind==2 else ()
        c=cls(msg.sequence,req,kind,text_decode(msg.payload[20:]),choices,ttl)
        if c.payload()!=msg.payload:raise ValueError('noncanonical command')
        return c

def decode_response(msg,command,nonce,run,tag):
    if (msg.kind,msg.typ,msg.nonce,msg.generation,msg.tag)!=(5,7,nonce,run,tag) or msg.result or msg.error or len(msg.payload)!=16:raise ValueError('response identity/envelope')
    ver,kind,cid,req,result,choice=RESPONSE.unpack(msg.payload)
    if ver!=1 or kind!=command.kind or cid!=command.command_id or cid!=msg.sequence or req!=command.request_id or result not in (0,2,3,4,5,6,7):raise ValueError('response correlation/status')
    allowed=tuple(c[0] for c in command.choices)
    if (result==0 and command.kind==2 and choice not in allowed) or (result!=0 or command.kind==1) and choice!=0:raise ValueError('invalid choice response')
    return {'schemaVersion':1,'recordClass':'ui_response','session':nonce,'run':run,'commandID':cid,'requestID':req,'commandType':kind,'result':result,'choiceID':choice}

class Responses:
    """Launch-bounded duplicate tracking, never world history."""
    def __init__(self):self.seen={}
    def accept(self,msg,command,nonce,run,tag):
        record=decode_response(msg,command,nonce,run,tag);key=(nonce,run,command.command_id)
        raw=msg.encode()
        if key in self.seen:
            if self.seen[key]!=raw:raise ValueError('conflicting duplicate')
            return None
        if len(self.seen)>=256:raise ValueError('response dedupe capacity')
        self.seen[key]=raw;return record
