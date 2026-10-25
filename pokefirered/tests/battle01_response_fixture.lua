local a=0;local PI_BATTLE_receive;local writes=0;local memory={[8]=8,[12]=9,[24]=1,[28]=10,[32]=11,[34]=1,[35]=1,[36]=1}
local PI={authenticated=true,cfg={nonce=7},epoch=1,log=function()end}
local emu={read16=function(self,k)return memory[k]end,read32=function(self,k)return memory[k]end,read8=function(self,k)return memory[k]end,write16=function(self,k,v)memory[k]=v;writes=writes+1 end,write32=function(self,k,v)memory[k]=v;writes=writes+1 end}
-- INSERT ACTUAL PI_BATTLE_receive
local body=string.pack('<I4I4I4I4I2I1I1I2I2',8,9,10,1,11,1,1,256,0)
PI_BATTLE_receive(9,7,1,8,10,body);assert(writes==3 and memory[36]==2 and memory[38]==256)
PI_BATTLE_receive(9,7,1,8,10,body);assert(writes==3) -- duplicate cannot republish
memory[36]=5;PI_BATTLE_receive(9,7,1,8,10,body);assert(writes==3) -- post-timeout
memory[36]=1;memory[32]=12;PI_BATTLE_receive(9,7,1,8,10,body);assert(writes==3) -- stale turn
memory[32]=11;PI_BATTLE_receive(9,99,1,8,10,body);assert(writes==3)
PI_BATTLE_receive(9,7,2,8,10,body);assert(writes==3)
PI_BATTLE_receive(9,7,1,9,10,body);assert(writes==3)
PI_BATTLE_receive(9,7,1,8,10,body..'x');assert(writes==3)
local f=assert(io.open('/Users/blevicki/Documents/poke/pokefirered/evidence/phase4/battle01/lua-contract-tests.json','w'));f:write('{"passed":8,"kind":"actual pinned mGBA Lua interpreter; mock named-control memory fixture","physicalMemoryWrites":0,"checks":["one valid publication","duplicate","after timeout","stale turn","wrong nonce","reset generation","wrong request","oversize"]}\n');f:close()
