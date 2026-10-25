#!/usr/bin/env python3
"""Generate a UI-loaded input observer for the compiled BRIDGE=0 ROM."""
import json
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'evidence/phase1/manifest-disabled.json').read_text())
assert m['static_passed'] and not m['target']['bridge_enabled']
private=ROOT/'.local/phase1-disabled-test';private.mkdir(exist_ok=True)
shutil.copy2(ROOT/'.local/phase1-emulator/pokefirered.sav',private/'pokefirered.sav')
s=m['diagnostic_symbols']
script='''DT={queue={},index=1}
DT.logfile=assert(io.open(%s,'a'))
function DT.log(s)DT.logfile:write(s..'\\n');DT.logfile:flush();console:log(s)end
local crc=(emu:checksum(C.CHECKSUM.CRC32):gsub('.',function(x)return string.format('%%02x',x:byte())end))
assert(crc==%s,'disabled ROM checksum mismatch')
DT.log('disabled-build-boot CRC='..crc)
function DT.key(k,h,r)
 assert(k<10 and h<=360 and r<=600)
 for _=1,h do table.insert(DT.queue,{mask=1<<k})end
 for _=1,r do table.insert(DT.queue,{mask=0})end
end
function DT.a(n)for _=1,n do DT.key(0,20,15)end end
function DT.shot(name)assert(name:match('^[a-z0-9%%-]+$'));table.insert(DT.queue,{shot=name})end
DT.cb=callbacks:add('frame',function()
 local e=DT.queue[DT.index];if not e then return end;DT.index=DT.index+1
 if e.shot then
  emu:screenshot(%s..'/'..e.shot..'.png')
  local b=emu:read32(%d)
  DT.log('shot='..e.shot..' frame='..emu:currentFrame()..' counter='..emu:read32(%d)..' x='..emu:read16(b)..' y='..emu:read16(b+2)..' mapgroup='..emu:read8(b+4)..' mapnum='..emu:read8(b+5))
 else emu:setKeys(e.mask)end
end)
DT.shot('disabled-boot')
'''%(json.dumps(str(ROOT/'evidence/phase1/disabled-emulator.log')),json.dumps(m['rom_crc32']),json.dumps(str(ROOT/'evidence/private/phase1')),s['gSaveBlock1Ptr'],s['gSaveCounter'])
(ROOT/'.local/disabled-smoke.lua').write_text(script)
print('Load .local/disabled-smoke.lua through native Scripting > File > Load script; then DT.a(12); DT.key(1,20,600); DT.shot("disabled-field")')
