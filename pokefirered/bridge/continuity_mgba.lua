-- Managed continuity diagnostics/input lease. No permanent native allocation.
-- Local telemetry is not canonical truth or an NPC observation grant.
assert(PI_CONFIG.continuity and PI_TEST)
if PI_CONTINUITY and PI_CONTINUITY.cb then callbacks:remove(PI_CONTINUITY.cb) end
PI_CONTINUITY={last=-1}
local c=PI_CONFIG.continuity
function PI_CONTINUITY.allowInput()
 local f=io.open(c.permit,'r');if not f then return false end
 local s=f:read(96);f:close()
 return s==string.format('%d:%d:ACTIVE\n',PI.cfg.nonce,PI.epoch)
end
function PI_CONTINUITY.cancelInput()
 PI_TEST.queue={};PI_TEST.index=1;emu:setKeys(0)
end
local key,mask=PI_TEST.key,PI_TEST.mask
function PI_TEST.key(...)
 assert(PI_CONTINUITY.allowInput(),'managed host input lease unavailable');return key(...)
end
function PI_TEST.mask(...)
 assert(PI_CONTINUITY.allowInput(),'managed host input lease unavailable');return mask(...)
end
-- Re-register the ordinary input callback so every queued frame checks the lease.
callbacks:remove(PI_TEST.cb)
PI_TEST.cb=callbacks:add('frame',function()
 if not PI_CONTINUITY.allowInput() then PI_CONTINUITY.cancelInput();return end
 local item=PI_TEST.queue[PI_TEST.index]
 if not item then PI_TEST.queue={};PI_TEST.index=1;return end
 PI_TEST.index=PI_TEST.index+1
 if item.shot then emu:screenshot(PI.cfg.screenshots..'/'..item.shot..'.png');PI_TEST.sample(item.shot)
 else emu:setKeys(item.mask)end
end)
PI_CONTINUITY.cb=callbacks:add('frame',function()
 local frame=emu:currentFrame()
 if frame-PI_CONTINUITY.last<10 then return end;PI_CONTINUITY.last=frame
 local f=assert(io.open(c.native..'.tmp','w'))
 f:write(string.format('{"build":"%s","nonce":%d,"run":%d,"origin":"%s","frame":%d,"eventCounter":%d,"ack":%d,"drops":%d,"depth":%d,"state":%d,"authenticated":%s}\n',
 PI.m.rom_sha256,PI.read('nonce'),PI.read('generation'),PI.cfg.origin,frame,PI.read('event_counter'),PI.read('last_ack'),PI.read('drops'),PI.read('queue_depth'),PI.read('state'),tostring(PI.authenticated)))
 f:flush();f:close();assert(os.rename(c.native..'.tmp',c.native))
end)
PI.log('continuity-guard','input lease and source-bound native telemetry installed')
