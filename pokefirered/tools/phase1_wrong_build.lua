-- Live diagnostic: rejected manifest must leave the mailbox untouched.
local address,size=PI.m.mailbox.address,PI.m.mailbox.size
local before=emu:readRange(address,size)
PI_MANIFEST.rom_crc32='00000000'
local ok,err=pcall(function()dofile('/Users/blevicki/Documents/poke/pokefirered/bridge/mgba.lua')end)
local unchanged=before==emu:readRange(address,size)
local passed=not ok and tostring(err):find('ROM CRC/build mismatch') and unchanged
local out=assert(io.open('/Users/blevicki/Documents/poke/pokefirered/evidence/phase1/wrong-build-live.json','w'))
out:write('{"scope":"live Lua bad-manifest CRC refusal before RAM writes","refused":'..tostring(not ok)..',"mailbox_unchanged":'..tostring(unchanged)..',"passed":'..tostring(not not passed)..'}\n');out:close()
console:log('wrong-build refused='..tostring(not ok)..' mailbox_unchanged='..tostring(unchanged))
