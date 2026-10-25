-- Existing authenticated nonblocking transport, bounded96-byte fragments.
-- Only the named control and native-allocated sanitized snapshot are accessed.
local a=PI.m.battle_control.address
local abi=PI.m.battle_abi
local size,work=abi[1],abi[2]
local last=0;local offset=0;local snapshot=nil;local terminal=0;local client=nil;local allocation=0
function PI_BATTLE_receive(kind,nonce,gen,seq,typ,data)
 if kind~=9 or typ~=10 or #data~=24 then PI.log('battle-response-rejected','schema');return end
 local req,hash,battle,generation,turn,phase,battler,selected,reserved=string.unpack('<I4I4I4I4I2I1I1I2I2',data)
 if not PI.authenticated or nonce~=PI.cfg.nonce or gen~=PI.epoch or reserved~=0 or req~=seq or emu:read16(a+36)~=1 or req~=emu:read32(a+8) or hash~=emu:read32(a+12) or battle~=emu:read32(a+28) or generation~=emu:read32(a+24) or turn~=emu:read16(a+32) or phase~=emu:read8(a+34) or battler~=emu:read8(a+35) then PI.log('battle-response-rejected','stale');return end
 emu:write16(a+38,selected);emu:write32(a+40,req);emu:write16(a+36,2)
 PI.log('battle-response-published',req)
end
function PI_BATTLE_arm()
 assert(PI.authenticated and PI.epoch==1 and emu:read32(a)==0x50425431 and emu:read32(a+4)==PI.m.build_tag and emu:read32(a+16)==0,'safe managed field arm')
 emu:write16(a+36,0x8000)
end
callbacks:add('frame',function()
 if PI.client~=client then client=PI.client;last=0;offset=0;snapshot=nil;terminal=0 end
 if emu:read32(a)~=0x50425431 or emu:read32(a+4)~=PI.m.build_tag or not PI.authenticated then return end
 local p=emu:read32(a+16);local state=emu:read16(a+36);local req=emu:read32(a+8)
 if p~=allocation then PI.log('battle-heap','pointer='..p..' bytes='..(p==0 and 0 or work));allocation=p end
 if p==0 then snapshot=nil;return end
 assert(p>=PI.m.diagnostic_symbols.gHeap and p+work<=PI.m.diagnostic_symbols.gHeap+0x1c000,'allocated heap bounds')
 if state==1 then
  if req~=last then last=req;offset=0;snapshot=emu:readRange(p,size) end
  if snapshot and offset<size and #PI.tx<256 then
   local part=snapshot:sub(offset+1,math.min(offset+80,size))
   local data=string.pack('<I4I4I2I2',req,emu:read32(a+12),size,offset)..part
   if PI.queue(PI.wire(8,req,PI.epoch,9,data)) then offset=offset+#part end
  end
 elseif (state==4 or state==5) and terminal~=req and #PI.tx<256 then
  local source=emu:read8(p+abi[9]);local reason=emu:read8(p+abi[9]+1)
  local data=emu:readRange(a+8,8)..emu:readRange(a+28,8)..string.pack('<I1I1I2',source,reason,emu:read16(a+38))
  if PI.queue(PI.wire(10,req,PI.epoch,11,data))then terminal=req end
 end
end)
