"""Read only two native flags from the checksum-valid, WORLD-paired battery."""
import json,struct
from pathlib import Path
from world.saves import fingerprint,layout_from_build
from roster.extract import file_hash,digest
ROOT=Path(__file__).resolve().parents[1]
FLAGS={'FLAG_DEFEATED_BROCK':0x4B0,'FLAG_BADGE01_GET':0x820}

def read_boulder(data,build,layout=None):
    layout=layout or json.loads((ROOT/'config/prep_save_layout.json').read_text())
    if build!=layout['romSHA256']:raise ValueError('progression ROM mismatch')
    rom=ROOT/layout['romPath']
    if file_hash(rom)!=build or file_hash(rom.with_suffix('.elf'))!=layout['elfSHA256']:raise ValueError('native progression build unavailable/mismatched')
    if list(layout_from_build(rom))!=layout['sectionSizes']:raise ValueError('native save section layout mismatch')
    if any(file_hash(ROOT/p)!=sha for p,sha in layout['sourceFiles'].items()):raise ValueError('stale native flag layout')
    identity=fingerprint(data,layout['sectionSizes'])
    sections={}
    for index in range(identity.slot*14,(identity.slot+1)*14):
        sector=data[index*4096:(index+1)*4096]
        sid=struct.unpack_from('<H',sector,4084)[0]
        sections[sid]=sector[:layout['sectionSizes'][sid]]
    # Source sSaveSlotLayout sections1..4 serialize SaveBlock1 in order.
    block=b''.join(sections[i] for i in (1,2,3,4))
    if len(block)!=layout['saveBlock1Bytes']:raise ValueError('SaveBlock1 size mismatch')
    offset=layout['flagsOffset'];size=layout['flagBytes']
    if offset+size>len(block) or any(n//8>=size for n in FLAGS.values()):raise ValueError('flag bounds')
    values={name:bool(block[offset+number//8] & (1<<(number&7))) for name,number in FLAGS.items()}
    if len(set(values.values()))!=1:raise ValueError('partial/inconsistent Boulder milestone')
    return {'save':identity.as_dict(),'flags':values,'layoutSHA256':digest(layout),
            'source':'validated native battery SaveBlock1, WORLD pairing required',
            'sourceCommit':layout['sourceCommit'],'romSHA256':build}
