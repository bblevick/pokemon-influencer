-- Debug-only emulator test helpers; intentionally separate from transport.
if PI_TEST then
 if PI_TEST.cb then callbacks:remove(PI_TEST.cb)end
 if PI_TEST.savecb then callbacks:remove(PI_TEST.savecb)end
end
PI_TEST={queue={},index=1}
function PI_TEST.key(key,hold,rest)
 assert(key>=0 and key<10 and hold>=0 and hold<=360 and rest>=0 and rest<=600)
 for _=1,hold do table.insert(PI_TEST.queue,{mask=1<<key}) end
 for _=1,rest do table.insert(PI_TEST.queue,{mask=0}) end
end
function PI_TEST.a(count) assert(count<=30);for _=1,count do PI_TEST.key(0,20,15)end end
function PI_TEST.shot(name)
 assert(name:match('^[a-z0-9%-]+$') and #name<64)
 table.insert(PI_TEST.queue,{shot=name})
end
function PI_TEST.sample(label)
 local s={label=label,frame=emu:currentFrame(),state=PI.read('state'),heartbeat=PI.read('heartbeat'),sequence=PI.read('sequence'),ack=PI.read('last_ack'),successes=PI.read('successes'),failures=PI.read('failures'),error=PI.read('error'),generation=PI.read('generation'),nonce=PI.read('nonce')}
 PI.log('sample',string.format('%s state=%d heartbeat=%d sequence=%d ack=%d successes=%d failures=%d error=%d generation=%d',label,s.state,s.heartbeat,s.sequence,s.ack,s.successes,s.failures,s.error,s.generation))
 return s
end
function PI_TEST.ping()assert(PI.valid() and PI.read('state')==0);PI.write('debug_trigger',1);PI.log('debug-trigger','ROM will construct request')end
PI_TEST.cb=callbacks:add('frame',function()
 local item=PI_TEST.queue[PI_TEST.index];if not item then PI_TEST.queue={};PI_TEST.index=1;return end;PI_TEST.index=PI_TEST.index+1
 if item.shot then emu:screenshot(PI.cfg.screenshots..'/'..item.shot..'.png');PI_TEST.sample(item.shot)
 else emu:setKeys(item.mask)end
end)
PI_TEST.savecb=callbacks:add('savedataUpdated',function()PI.log('savedataUpdated','actual battery write')end)
function PI_TEST.mask(mask,hold,rest)
 assert(mask>=0 and mask<1024 and hold>=0 and hold<=360 and rest>=0 and rest<=600)
 for _=1,hold do table.insert(PI_TEST.queue,{mask=mask})end
 for _=1,rest do table.insert(PI_TEST.queue,{mask=0})end
end
function PI_TEST.persist(label)
 local s=PI.m.diagnostic_symbols
 local b=emu:read32(s.gSaveBlock1Ptr)
 PI.log('persist',label..' counter='..emu:read32(s.gSaveCounter)..' partycount='..emu:read8(s.gPlayerPartyCount)..' level='..emu:read8(s.gPlayerParty+84)..' hp='..emu:read16(s.gPlayerParty+86)..' x='..emu:read16(b)..' y='..emu:read16(b+2)..' mapgroup='..emu:read8(b+4)..' mapnum='..emu:read8(b+5))
end
