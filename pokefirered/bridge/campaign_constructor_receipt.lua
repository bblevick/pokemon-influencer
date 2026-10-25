-- Observational normal constructor counter only. No party writes or cloud calls.
-- Address from this build's ELF, field offset from the checked native ABI.
local last=0
callbacks:add('frame',function()
 if not PI.authenticated or PI.epoch~=1 then return end
 local count=emu:read32(PI.m.preparation_mailbox.address+64)
 if count==last then return end
 assert(count==last+1,'unexpected authored construction counter')
 last=count
 local payload=string.char(158,1,count%256,math.floor(count/256)%256,math.floor(count/65536)%256,math.floor(count/16777216)%256)
 assert(PI.queue(PI.wire(12,count,PI.epoch,12,payload)),'constructor receipt queue full')
end)
