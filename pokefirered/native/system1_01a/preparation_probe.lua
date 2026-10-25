-- Named allocated mailbox only; never writes live Pokemon structures.
local a=PI.m.preparation_mailbox.address
function PI_PREP_publish()
 assert(PI.authenticated and PI.valid() and PI.read('nonce')==PI.cfg.nonce and PI.epoch==1,'current authenticated session required')
 assert(#PI_PREP_PACKET==168 and emu:read32(a)==0x50525031 and emu:read32(a+4)==PI.m.build_tag,'named native preparation layout/build')
 assert(emu:read8(a+59)==0,'no repeat or in-battle installation')
 for i=1,#PI_PREP_PACKET do if i~=60 then emu:write8(a+i-1,PI_PREP_PACKET:byte(i))end end
 emu:write8(a+59,1);emu:write32(a+60,1);PI.log('prepared-packet-published',PI.cfg.nonce)
end
local observed=false
callbacks:add('frame',function()
 if observed or emu:read32(a+64)~=1 then return end
 observed=true
 -- Existing observation decoder reads only the installed opponent roster.
 local enemy=PI.m.diagnostic_symbols.gEnemyParty
 local rows={}
 for slot=0,1 do
  local base=enemy+slot*100
  rows[#rows+1]=string.format('{"slot":%d,"level":%d,"pokemonBytes":"%s"}',slot,emu:read8(base+84),(emu:readRange(base,80):gsub('.',function(x)return string.format('%02x',x:byte())end)))
 end
 local f=assert(io.open(PI.cfg.screenshots..'/native-party-private.json','w'))
 f:write('{"nativeConstructorCount":1,"state":'..emu:read8(a+59)..',"nonce":'..PI.cfg.nonce..',"generation":'..PI.epoch..',"nativeROM":"'..PI.m.rom_sha256..'","commitmentDigest":"'..(emu:readRange(a+24,32):gsub('.',function(x)return string.format('%02x',x:byte())end))..'","party":['..table.concat(rows,',')..']}\n');f:close()
 PI.log('native-preparation-installed',emu:read32(a+64))
end)
