-- Phase 0 diagnostic only, not a ROM mailbox or companion bridge.
-- Load in the pinned mGBA Scripting console with dofile(absolute path).
P0_ROOT = '/Users/blevicki/Documents/poke/pokefirered/'
P0_LOG = assert(io.open(P0_ROOT..'evidence/phase0/emulator-runtime.log','a'))
function p0log(s) console:log(s); P0_LOG:write(s..'\n'); P0_LOG:flush() end
function p0shot(name) emu:screenshot(P0_ROOT..'evidence/private/'..name..'.png'); p0log('screenshot='..name..' frame='..emu:currentFrame()) end
p0log('Lua='.._VERSION..' title='..emu:readRange(0x080000A0,12))
for _,k in ipairs({'read8','read16','read32','readRange','write8','write16','write32','writeRange','saveStateBuffer','loadStateBuffer','setKeys','screenshot'}) do p0log('emu.'..k..'='..type(emu[k])) end
-- ELF-derived gBattleTypeFlags in the verified rev0 baseline, not a mailbox.
-- Same-value stores only, with emulation paused during console execution.
for _,bits in ipairs({8,16,32}) do
 local addr=0x02022B4C; local value=emu['read'..bits](emu,addr)
 emu['write'..bits](emu,addr,value)
 assert(emu['read'..bits](emu,addr)==value)
 p0log('same-value memory read/write'..bits..' passed addr=0x02022B4C value='..value)
end
P0_FRAMES=0
P0_CB=callbacks:add('frame',function() P0_FRAMES=P0_FRAMES+1 end)
p0log('frame callback registered='..tostring(P0_CB))
P0_SAVEDATA=0
P0_SAVE_CB=callbacks:add('savedataUpdated',function() P0_SAVEDATA=P0_SAVEDATA+1; p0log('savedataUpdated count='..P0_SAVEDATA) end)
local state=emu:saveStateBuffer(C.SAVESTATE.ALL)
assert(type(state)=='string' and #state>0)
assert(emu:loadStateBuffer(state,C.SAVESTATE.ALL))
p0log('explicit ALL snapshot roundtrip buffer_bytes='..#state..'; battery inclusion not yet independently tested')
-- Listener test is loopback only, bounded to 64 bytes per receive callback.
P0_SERVER, P0_ERR=socket.bind('127.0.0.1',18765)
assert(P0_SERVER,P0_ERR)
assert(P0_SERVER:listen())
P0_SERVER:add('received',function()
 local client,err=P0_SERVER:accept(); assert(client,err); P0_CLIENT=client
 client:add('received',function()
  local data,err=client:receive(64)
  if data then
   p0log('loopback receive='..data..' bytes='..#data)
   local written=client:send('P0_ACK:'..data); p0log('loopback send_bytes='..tostring(written))
  elseif err~=socket.ERRORS.AGAIN then p0log('loopback error='..tostring(err)); client:close(); P0_CLIENT=nil end
 end)
end)
p0log('loopback listener=127.0.0.1:18765; diagnostic only, no bridge or protocol implemented')
p0shot('boot-probe')
