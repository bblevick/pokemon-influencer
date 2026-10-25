"""BRIDGE-01 bounded binary PING codec and stateless test responder."""
from dataclasses import dataclass
import json
from pathlib import Path
import struct

SCHEMA=json.loads((Path(__file__).with_name('events_protocol.json')).read_text())
HEADER=struct.Struct('<4sHHIIIIHHHHI')
MAX_BODY=132

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
        if len(self.payload)>96:raise ValueError('oversized transport payload')
        body=HEADER.pack(b'PI02',SCHEMA['protocol_version'],self.kind,self.nonce,self.generation,self.sequence,self.tag,self.typ,len(self.payload),self.result,self.error,checksum(self.sequence,self.nonce,self.generation,self.typ,self.payload))+self.payload
        return struct.pack('<H',len(body))+body
    @classmethod
    def decode(cls,body):
        if not HEADER.size<=len(body)<=MAX_BODY:raise ValueError('body bounds')
        magic,version,kind,nonce,gen,seq,tag,typ,n,result,error,crc=HEADER.unpack_from(body)
        data=body[HEADER.size:]
        if magic!=b'PI02':raise ValueError('magic')
        if version!=SCHEMA['protocol_version']:raise ValueError('version')
        if n!=len(data) or n>96:raise ValueError('length')
        if checksum(seq,nonce,gen,typ,data)!=crc:raise ValueError('checksum')
        return cls(kind,nonce,gen,seq,tag,typ,data,result,error)

class Decoder:
    def __init__(self):self.buffer=bytearray()
    def feed(self,data):
        self.buffer.extend(data)
        if len(self.buffer)>512:raise ValueError('bounded receive buffer')
        out=[]
        while len(self.buffer)>=2:
            n=struct.unpack_from('<H',self.buffer)[0]
            if not HEADER.size<=n<=MAX_BODY:raise ValueError('frame bounds')
            if len(self.buffer)<n+2:break
            out.append(Message.decode(bytes(self.buffer[2:n+2])))
            del self.buffer[:n+2]
        return out

