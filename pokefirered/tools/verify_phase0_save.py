#!/usr/bin/env python3
"""Read-only verification of the private baseline smoke-test battery save.

Uses the actual ELF-derived save layout, not assumed spare space or a new marker.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--manifest',type=Path,default=Path('evidence/phase0/baseline.json'))
parser.add_argument('--save',type=Path,default=Path('.local/emulator-test/pokefirered.sav'))
parser.add_argument('--report',type=Path,default=Path('evidence/phase0/battery-save.json'))
args=parser.parse_args()
baseline=json.loads((root/args.manifest).read_text())
expected_hash=baseline.get('sha256',baseline.get('rom_sha256'))
rom=root/baseline['rom_path']
elf=rom.with_suffix('.elf')
rom_data=rom.read_bytes()
assert hashlib.sha256(rom_data).hexdigest()==expected_hash
symbols=subprocess.check_output(['arm-none-eabi-nm',str(elf)],text=True)
address=next(int(line.split()[0],16) for line in symbols.splitlines() if line.endswith(' sSaveSlotLayout'))
offset=address-0x08000000
layout=list(struct.iter_unpack('<HH',rom_data[offset:offset+14*4]))
save=root/args.save
data=save.read_bytes()
# Pinned mGBA appends a 16-byte RTC footer to ROM-hack saves (savedata.c).
if len(data) not in (131072,131088): sys.exit('Unexpected battery-save size; no data changed')
sectors=[]
for index in range(28):
    sector=data[index*4096:(index+1)*4096]
    section_id,expected,signature,counter=struct.unpack_from('<HHII',sector,4084)
    valid=signature==0x08012025 and section_id<14
    computed=None
    if valid:
        size=layout[section_id][1]
        total=sum(x[0] for x in struct.iter_unpack('<I',sector[:size//4*4]))&0xFFFFFFFF
        computed=((total>>16)+total)&0xFFFF
    sectors.append({'sector':index,'section_id':section_id,'counter':counter,
                    'signature_valid':valid,'stored_checksum':expected,'computed_checksum':computed,
                    'checksum_valid':valid and computed==expected})
slots=[]
for slot in range(2):
    entries=sectors[slot*14:slot*14+14]
    valid=(all(x['checksum_valid'] for x in entries) and
           {x['section_id'] for x in entries}==set(range(14)) and
           len({x['counter'] for x in entries})==1)
    slots.append({'slot':slot,'valid':valid,'counter':entries[0]['counter'] if valid else None})
report={'scope':'actual in-game battery save; not host pairing/marker verification',
        'private_save_path':str(save.relative_to(root)),'size':len(data),'flash_size':131072,'emulator_rtc_footer_bytes':len(data)-131072,
        'sha256':hashlib.sha256(data).hexdigest(),'source_commit':baseline['source_commit'],
        'layout_symbol_address':hex(address),'layout_sizes':[size for _,size in layout],
        'slots':slots,'sectors':sectors,'passed':any(x['valid'] for x in slots)}
(root/args.report).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['scope','size','sha256','slots','passed']},indent=2))
if not report['passed']:sys.exit(1)
