#!/usr/bin/env python3
"""Print bounded read-only Lua audit, resolved from the accepted ELF; no game writes."""
import argparse,json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pokebook01 import manifest
from phase1_events_build import symbols
p=argparse.ArgumentParser();p.add_argument('label',choices=['before','after']);p.add_argument('--compare',action='store_true');p.add_argument('--memo',action='store_true');a=p.parse_args()
m=manifest();s=symbols(ROOT/m['rom_path'].replace('.gba','.elf'));party=s['gEnemyParty'];count=s['gEnemyPartyCount'];table=s['gTrainers']
assert 0<party['size']<=600 and count['size']==1
D=ROOT/('.local/strategy01-memo' if a.memo else '.local/strategy01-backup');E=ROOT/('evidence/phase3/strategy01/memo' if a.memo else 'evidence/phase3/strategy01/backup');path=D/('native-party-'+a.label+'.bin')
metadata={'romSHA256':m['rom_sha256'],'ELFSymbols':{k:s[k] for k in ('gEnemyParty','gEnemyPartyCount','gTrainers')},'operation':'read8 only; no player data; diagnostic never model input'}
(E/'native-party-symbols.json').write_text(json.dumps(metadata,indent=2)+'\n')
command="local f=assert(io.open(%s,'wb'));f:write(string.char(emu:read8(%d)));for i=0,%d do f:write(string.char(emu:read8(%d+i)))end;f:close();PI.log('strategy-party-proof',%s)"%(json.dumps(str(path)),count['address'],party['size']-1,party['address'],json.dumps(a.label+' read-only gEnemyParty 600 bytes and count; ELF-derived addresses'))
print(command)
if a.compare:
 before=(D/'native-party-before.bin').read_bytes();after=(D/'native-party-after.bin').read_bytes();assert len(before)==len(after)==party['size']+1 and before==after
 rom=(ROOT/m['rom_path']).read_bytes();offset=table['address']-0x08000000;assert 0<=offset<offset+table['size']<=len(rom)
 result={'beforeSHA256':hashlib.sha256(before).hexdigest(),'afterSHA256':hashlib.sha256(after).hexdigest(),'comparedBytes':len(before),'unchanged':True,'nativeScope':'idle field opponent party+count only; not a prepared-party installation test','gTrainersROMSpanSHA256':hashlib.sha256(rom[offset:offset+table['size']]).hexdigest(),'wholeROMSHA256':hashlib.sha256(rom).hexdigest()}
 (E/'native-no-mutation.json').write_text(json.dumps(result,indent=2)+'\n')
