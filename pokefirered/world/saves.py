"""FireRed rev0 validated persisted-content fingerprint, algorithm fr-save-v1."""
import hashlib,json,struct,subprocess
from dataclasses import dataclass
from pathlib import Path
ALGORITHM='fr-save-v1'
@dataclass(frozen=True)
class SaveIdentity:
 fingerprint:str
 content_sha256:str
 counter:int
 slot:int
 footer_bytes:int
 algorithm:str=ALGORITHM
 def as_dict(self):return self.__dict__.copy()
def layout_from_build(rom):
 rom=Path(rom);symbols=subprocess.check_output(['arm-none-eabi-nm',str(rom.with_suffix('.elf'))],text=True)
 address=next(int(x.split()[0],16) for x in symbols.splitlines() if x.endswith(' sSaveSlotLayout'))
 data=rom.read_bytes();rows=list(struct.iter_unpack('<HH',data[address-0x08000000:address-0x08000000+56]))
 sizes=tuple(size for _,size in rows)
 if len(sizes)!=14 or any(not 0<size<=3968 or size%4 for size in sizes):raise ValueError('unsupported save layout')
 return sizes
def fingerprint(data,sizes):
 if len(data) not in (131072,131088) or len(sizes)!=14:raise ValueError('unsupported flash/footer/layout')
 slots=[]
 for slot in range(2):
  sections={};counter=None
  for index in range(slot*14,(slot+1)*14):
   sector=data[index*4096:(index+1)*4096];sid,crc,sig,c=struct.unpack_from('<HHII',sector,4084)
   if sig!=0x08012025 or sid>=14 or sid in sections:break
   size=sizes[sid]
   if not 0<size<=3968 or size%4:raise ValueError('unsupported section size')
   words=struct.unpack('<'+'I'*(size//4),sector[:size]);total=sum(words)&0xffffffff
   if ((total>>16)+total)&0xffff!=crc or (counter is not None and c!=counter):break
   counter=c;sections[sid]=sector[:size]
  if len(sections)==14:slots.append((slot,counter,sections))
 if not slots:raise ValueError('no complete checksum-valid slot')
 # Match pinned GetSaveValidStatus special wrap transition, otherwise greatest.
 latest=next((s for s in slots if s[1]==0),None) if {s[1] for s in slots}=={0,0xffffffff} else max(slots,key=lambda s:s[1])
 if len(slots)==2 and slots[0][1]==slots[1][1] and slots[0][2]!=slots[1][2]:raise ValueError('ambiguous equal-counter slots')
 slot,counter,sections=latest
 payload=b''.join(struct.pack('<HH',i,sizes[i])+sections[i] for i in range(14))
 content=hashlib.sha256(payload).hexdigest()
 identity=hashlib.sha256(ALGORITHM.encode()+b'\0'+struct.pack('<I',counter)+payload).hexdigest()
 return SaveIdentity(identity,content,counter,slot,len(data)-131072)
