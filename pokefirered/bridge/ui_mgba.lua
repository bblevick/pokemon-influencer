-- Dedicated presentation mailbox. No text rendering, domain facts, inference or connect().
local u=PI.m.ui_mailbox
PI_UI={lastState=-1,lastCommand=0,lastRun=0,sentRequest=0,sentResponse=0,responseFrame=0}
function PI_UI.read(n)
 local x=u.fields[n];local a=u.address+x.offset
 return x.size==2 and emu:read16(a) or emu:read32(a)
end
function PI_UI.write(n,v)
 local x=u.fields[n];local a=u.address+x.offset
 if x.size==2 then emu:write16(a,v) else emu:write32(a,v)end
end
local r,w=PI_UI.read,PI_UI.write
function PI_UI.boundary(reason)
 PI.epoch=PI.epoch+1;PI.lastHeartbeat=nil;PI.drop(reason)
 -- Publish new authority immediately after managed load, before a ROM frame.
 w('run_nonce',PI.cfg.nonce);w('run_generation',PI.epoch)
 PI_UI.lastRun=0;PI.log('ui-managed-boundary',reason..' run='..PI.epoch)
end
function PI_UI_receive(kind,nonce,gen,seq,typ,data,result,err,sum)
 if gen~=PI.epoch or gen~=r('run_generation') or nonce~=r('run_nonce') then PI.log('ui-stale-rejected',seq);return end
 if kind==6 and typ==8 and #data==0 and result==0 and err==0 and seq==r('command_id') and r('state')==6 then w('state',0);return end
 if kind~=4 or typ~=6 or result~=0 or err~=0 then PI.log('ui-envelope-rejected',seq);return end
 -- No unsolicited commands, queue, pointer values or Lua evaluation.
 if seq==0 or seq<=PI_UI.lastCommand or r('state')~=2 then PI.log('ui-duplicate-or-phase-rejected',seq);return end
 if #data>96 or #data<8 or string.unpack('<I4',data,5)~=r('request_id') then PI.log('ui-request-rejected',seq);return end
 PI_UI.lastCommand=seq
 for i=1,#data do emu:write8(u.address+u.fields.payload.offset+i-1,data:byte(i))end
 w('command_id',seq);w('length',#data);w('checksum',sum);w('state',3)
 PI.log('ui-command-published',seq)
end
PI_UI.cb=callbacks:add('frame',function()
 if r('magic')~=0x50495531 then return end
 -- Reset/heartbeat boundary authority is independent of reconnect/HELLO.
 w('run_nonce',PI.cfg.nonce);w('run_generation',PI.epoch)
 if PI_UI.lastRun~=PI.epoch then
  PI_UI.lastCommand=0;PI_UI.sentRequest=0;PI_UI.sentResponse=0;PI_UI.lastRun=PI.epoch
 end
 local state=r('state')
 if state~=PI_UI.lastState then
  PI.log('ui-state',string.format('state=%d request=%d command=%d result=%d choice=%d run=%d deadline=%d',state,r('request_id'),r('command_id'),r('result'),r('choice_id'),PI.epoch,r('deadline')))
  PI_UI.lastState=state
 end
 if not PI.authenticated then return end
 if state==1 then
  local req=r('request_id');local data=string.pack('<I2I2I4',1,r('kind'),req)
  if r('kind')==3 then
   if r('length')~=24 then w('state',0);return end
   local bytes={}
   for i=0,23 do bytes[#bytes+1]=string.char(emu:read8(u.address+u.fields.payload.offset+i))end
   data=table.concat(bytes)
  end
  if PI.queue(PI.wire(1,req,PI.epoch,5,data)) then w('state',2);PI.log('ui-request-forwarded',req)end
 elseif state==5 or (state==6 and emu:currentFrame()-PI_UI.responseFrame>=60) then
  local data=string.pack('<I2I2I4I4I2I2',1,r('kind'),r('command_id'),r('request_id'),r('result'),r('choice_id'))
  if PI.queue(PI.wire(5,r('command_id'),PI.epoch,7,data))then w('state',6);PI_UI.responseFrame=emu:currentFrame();PI.log('ui-response-forwarded',r('command_id'))end
 end
end)
