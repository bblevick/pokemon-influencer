-- Pokémon Influencer BRIDGE-01: bounded PING transport, no gameplay policy.
-- Launch tool prefixes the generated manifest/config tables into this file.
assert(PI_MANIFEST and PI_CONFIG, 'Load the generated bridge-run.lua')
if PI and PI.stop then PI.stop() end
PI={m=PI_MANIFEST,cfg=PI_CONFIG,epoch=1,rx='',tx='',authenticated=false}
local m,c=PI.m,PI.cfg
assert(m.schema_version==1 and m.protocol_version==1 and m.bridge_version==1, 'unsupported manifest')
local f=m.mailbox.fields
local function read(name)
 local a=m.mailbox.address+f[name].offset
 return f[name].size==2 and emu:read16(a) or emu:read32(a)
end
local function write(name,value)
 local a=m.mailbox.address+f[name].offset
 if f[name].size==2 then emu:write16(a,value) else emu:write32(a,value) end
end
local function payload() return emu:readRange(m.mailbox.address+f.payload.offset,read('length')) end
local function checksum(seq,nonce,gen,typ,data)
 local h=2166136261
 local bytes=string.pack('<I4I4I4I2I2',seq,nonce,gen,typ,#data)..data
 for i=1,#bytes do h=((h ~ bytes:byte(i))*16777619)&0xffffffff end
 return h
end
local function hex(s) return (s:gsub('.',function(x)return string.format('%02x',x:byte())end)) end
PI.logfile=assert(io.open(c.log,'a'))
function PI.log(event,detail)
 local line=string.format('{"event":"%s","frame":%d,"detail":"%s"}',event,emu:currentFrame(),tostring(detail or ''):gsub('["\\\n]','_'))
 PI.logfile:write(line..'\n');PI.logfile:flush();console:log(line)
end
local crc=hex(emu:checksum(C.CHECKSUM.CRC32))
assert(crc==m.rom_crc32, 'ROM CRC/build mismatch: no memory writes')
assert(emu:read32(m.build_tag_address)==m.build_tag, 'ROM build tag mismatch')
PI.log('build-validated',m.rom_sha256)
function PI.valid()
 return read('magic')==m.protocol.magic and read('version')==m.protocol_version
 and read('size')==m.mailbox.size and read('build_tag')==m.build_tag
end
function PI.drop(reason)
 if PI.client then PI.client:close();PI.client=nil end
 PI.authenticated=false;PI.rx='';PI.tx=''
 if PI.pending and PI.valid() and read('state')==2 and read('sequence')==PI.pending.seq then
  write('error',m.protocol.errors.DISCONNECTED);write('state',4)
 end
 PI.pending=nil
 PI.log('disconnected',reason)
end
function PI.stop()
 if PI.client then PI.client:close() end
 if PI.server then PI.server:close() end
 if PI.framecb then callbacks:remove(PI.framecb) end
 if PI.resetcb then callbacks:remove(PI.resetcb) end
 if PI.logfile then PI.logfile:close() end
end
local function wire(kind,seq,gen,typ,data,result,error)
 local body=string.pack('<c4I2I2I4I4I4I4I2I2I2I2I4','PI01',1,kind,c.nonce,gen,seq,m.build_tag,typ,#data,result or 0,error or 0,checksum(seq,c.nonce,gen,typ,data))..data
 return string.pack('<I2',#body)..body
end
local function queue(data)
 if #PI.tx+#data>256 then PI.drop('bounded TX full');return false end
 PI.tx=PI.tx..data;return true
end
local function receive(body)
 if #body<36 then PI.drop('short envelope');return end
 local magic,ver,kind,nonce,gen,seq,tag,typ,len,result,err,sum=string.unpack('<c4I2I2I4I4I4I4I2I2I2I2I4',body)
 local data=body:sub(37)
 if magic~='PI01' or ver~=1 or tag~=m.build_tag or nonce~=c.nonce or len~=#data or len>64 or sum~=checksum(seq,nonce,gen,typ,data) then
  PI.drop('malformed/version/build/nonce envelope');return
 end
 if not PI.authenticated then
  if kind~=0 or typ~=0 or seq~=0 or gen~=0 or data~=c.token..m.rom_sha256_binary or not PI.valid() or read('state')~=0 then
   PI.drop('HELLO rejected');return
  end
  write('nonce',c.nonce);write('generation',PI.epoch)
  PI.authenticated=true;queue(wire(3,0,PI.epoch,0,''));PI.log('hello',PI.epoch);return
 end
 local p=PI.pending
 if kind~=2 or not p or gen~=p.gen or seq~=p.seq or gen~=read('generation') or seq~=read('sequence') or read('nonce')~=c.nonce or read('state')~=2 then
  PI.log('stale-response-rejected',seq);return
 end
 if typ~=2 or len~=4 or data~='PONG' or result~=0 or err~=0 then PI.drop('invalid PONG');return end
 -- Bytes and identity first; publish RESPONSE_READY last. No range-write API assumed.
 for i=1,#data do emu:write8(m.mailbox.address+f.payload.offset+i-1,data:byte(i)) end
 write('response_sequence',seq);write('response_nonce',nonce);write('response_generation',gen)
 write('message_type',typ);write('length',len);write('result',result);write('error',err);write('checksum',sum)
 write('state',3);PI.pending=nil;PI.log('response-published',seq)
end
PI.server=assert(socket.bind('127.0.0.1',c.port));assert(PI.server:listen(1))
PI.server:add('received',function()
 local client,err=PI.server:accept()
 if not client then PI.log('accept-error',err);return end
 if PI.client then client:close();PI.log('extra-client-rejected');return end
 PI.client=client;PI.rx='';PI.tx='';PI.connectedFrame=emu:currentFrame()
 client:add('received',function()PI.readable=true end)
 client:add('error',function(_,err)PI.drop(err)end)
 PI.log('accepted')
end)
PI.server:add('error',function(_,err)PI.log('listener-error',err)end)
PI.resetcb=callbacks:add('reset',function()
 PI.epoch=PI.epoch+1;PI.lastHeartbeat=nil;PI.drop('emulator reset');PI.log('reset-epoch',PI.epoch)
end)
PI.framecb=callbacks:add('frame',function()
 if not PI.valid() then
  if PI.authenticated then PI.drop('mailbox incompatible/reset') end
  return
 end
 local heartbeat=read('heartbeat')
 if PI.lastHeartbeat and heartbeat<PI.lastHeartbeat and PI.lastHeartbeat-heartbeat<0x80000000 then
  PI.epoch=PI.epoch+1;PI.drop('ROM reset detected')
 end
 PI.lastHeartbeat=heartbeat
 if PI.client then
  if not PI.authenticated and emu:currentFrame()-PI.connectedFrame>120 then PI.drop('HELLO timeout');return end
  if PI.readable then
   PI.readable=false
   local part,err=PI.client:receive(128)
   if not part then if err~=socket.ERRORS.AGAIN then PI.drop(err) end
   else
    PI.rx=PI.rx..part
    if #PI.rx>256 then PI.drop('bounded RX full');return end
    for _=1,2 do
     if #PI.rx<2 then break end
     local n=string.unpack('<I2',PI.rx)
     if n<36 or n>100 then PI.drop('oversized/short frame');return end
     if #PI.rx<n+2 then break end
     local body=PI.rx:sub(3,n+2);PI.rx=PI.rx:sub(n+3);receive(body)
     if not PI.client then break end
    end
   end
  end
  if PI.client and #PI.tx>0 then
   local sent,err=PI.client:send(PI.tx)
   if sent then PI.tx=PI.tx:sub(sent+1) elseif err~=socket.ERRORS.AGAIN then PI.drop(err) end
  end
 end
 if PI.pending and read('state')~=2 then PI.log('request-expired',PI.pending.seq);PI.pending=nil end
 if read('state')==1 and PI.authenticated and not PI.pending then
  local seq,gen,len=read('sequence'),read('generation'),read('length')
  if len>m.protocol.payload_max or len~=4 or read('message_type')~=1 then
   write('error',2);write('state',4);PI.log('malformed-mailbox');return
  end
  local data=payload()
  if data~='POKE' or checksum(seq,c.nonce,gen,1,data)~=read('checksum') then
   write('error',2);write('state',4);PI.log('checksum-mailbox');return
  end
  PI.pending={seq=seq,gen=gen};write('state',2)
  queue(wire(1,seq,gen,1,data));PI.log('request-forwarded',seq)
 end
 local successes,failures=read('successes'),read('failures')
 if PI.lastSuccess~=successes or PI.lastFailure~=failures then
  PI.log('ROM-status',string.format('ack=%d successes=%d failures=%d error=%d heartbeat=%d',read('last_ack'),successes,failures,read('error'),heartbeat))
  PI.lastSuccess=successes;PI.lastFailure=failures
 end
end)
PI.read=read;PI.write=write
PI.log('listening','127.0.0.1:'..c.port)
