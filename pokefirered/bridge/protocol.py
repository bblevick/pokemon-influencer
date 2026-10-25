"""BRIDGE-01 bounded binary PING codec and stateless test responder."""
from dataclasses import dataclass
import json
from pathlib import Path
import struct

SCHEMA=json.loads((Path(__file__).with_name('protocol.json')).read_text())
HEADER=struct.Struct('<4sHHIIIIHHHHI')
MAX_BODY=100

def checksum(seq,nonce,generation,typ,payload):
    h=2166136261
    for byte in struct.pack('<IIIHH',seq,nonce,generation,typ,len(payload))+payload:
        h=((h^byte)*16777619)&0xffffffff
    return h

@dataclass(frozen=True)
class Message:
    kind:int
    nonce:int
    generation:int
    sequence:int
    tag:int
    typ:int
    payload:bytes
    result:int=0
    error:int=0
    def encode(self):
        if len(self.payload)>64:raise ValueError('oversized transport payload')
        body=HEADER.pack(b'PI01',SCHEMA['protocol_version'],self.kind,self.nonce,self.generation,self.sequence,self.tag,self.typ,len(self.payload),self.result,self.error,checksum(self.sequence,self.nonce,self.generation,self.typ,self.payload))+self.payload
        return struct.pack('<H',len(body))+body
    @classmethod
    def decode(cls,body):
        if not HEADER.size<=len(body)<=MAX_BODY:raise ValueError('body bounds')
        magic,version,kind,nonce,gen,seq,tag,typ,n,result,error,crc=HEADER.unpack_from(body)
        data=body[HEADER.size:]
        if magic!=b'PI01':raise ValueError('magic')
        if version!=SCHEMA['protocol_version']:raise ValueError('version')
        if n!=len(data) or n>64:raise ValueError('length')
        if checksum(seq,nonce,gen,typ,data)!=crc:raise ValueError('checksum')
        return cls(kind,nonce,gen,seq,tag,typ,data,result,error)

class Decoder:
    def __init__(self):self.buffer=bytearray()
    def feed(self,data):
        self.buffer.extend(data)
        if len(self.buffer)>256:raise ValueError('bounded receive buffer')
        out=[]
        while len(self.buffer)>=2:
            n=struct.unpack_from('<H',self.buffer)[0]
            if not HEADER.size<=n<=MAX_BODY:raise ValueError('frame bounds')
            if len(self.buffer)<n+2:break
            out.append(Message.decode(bytes(self.buffer[2:n+2])))
            del self.buffer[:n+2]
        return out

class Responder:
    """Only PING; bounded duplicate cache. No persistent or gameplay semantics."""
    def __init__(self,nonce,generation,tag):
        self.nonce=nonce;self.generation=generation;self.tag=tag;self.cache={};self.last=0
    def handle(self,request):
        if (request.nonce,request.generation,request.tag)!=(self.nonce,self.generation,self.tag):raise ValueError('stale session/build')
        if request.kind!=1 or request.typ!=1 or request.payload!=b'POKE' or request.result or request.error:raise ValueError('unsupported test request')
        if request.sequence==0:raise ValueError('zero sequence')
        old=self.cache.get(request.sequence)
        if old:
            if old[0]!=request:raise ValueError('conflicting duplicate')
            return old[1]
        if request.sequence<=self.last:raise ValueError('stale sequence/wraparound')
        response=Message(2,self.nonce,self.generation,request.sequence,self.tag,2,b'PONG')
        if len(self.cache)>=64:raise ValueError('test-session request limit; relaunch')
        self.cache[request.sequence]=(request,response);self.last=request.sequence
        return response
