-- Explicitly separate test automation; no game-domain or provider logic.
-- Only bounded input/screenshot/lifecycle commands, no arbitrary eval or RAM edits.
if PI_INPUT then
 if PI_INPUT.server then PI_INPUT.server:close()end
 if PI_INPUT.client then PI_INPUT.client:close()end
 if PI_INPUT.cb then callbacks:remove(PI_INPUT.cb)end
 if PI_INPUT.idlecb then callbacks:remove(PI_INPUT.idlecb)end
end
PI_INPUT={server=assert(socket.bind('127.0.0.1',18773)),rx='',retired={}}
function PI_INPUT.closeClient(client)
 assert(#PI_INPUT.retired<512,'test socket budget exhausted')
 PI_INPUT.retired[#PI_INPUT.retired+1]=client._s;client:close()
end
assert(PI_INPUT.server:listen(1))
PI_INPUT.server:add('received',function()
 if #PI_INPUT.retired>=511 then callbacks:remove(PI_INPUT.server._onframecb);PI_INPUT.server._onframecb=nil;return end
 local client=PI_INPUT.server:accept()
 if not client then return end
 if PI_INPUT.client then PI_INPUT.closeClient(client);return end
 PI_INPUT.client=client;PI_INPUT.rx=''
 client:add('error',function()if PI_INPUT.client==client then PI_INPUT.closeClient(client);PI_INPUT.client=nil end end)
end)
PI_INPUT.cb=callbacks:add('frame',function()
 if not PI_INPUT.client then return end
 local part,err=PI_INPUT.client:receive(256)
 if not part then
  if err~=socket.ERRORS.AGAIN or PI_INPUT.client:hasdata() then PI_INPUT.closeClient(PI_INPUT.client);PI_INPUT.client=nil end
  return
 end
 PI_INPUT.rx=PI_INPUT.rx..part
 if #PI_INPUT.rx>1024 then PI_INPUT.closeClient(PI_INPUT.client);PI_INPUT.client=nil;return end
 local line,rest=PI_INPUT.rx:match('^([^\n]+)\n(.*)$');if not line then return end
 PI_INPUT.rx=rest
 local cmd,a,b,d=line:match('^(%S+)%s*(%S*)%s*(%S*)%s*(%S*)$')
 local ok=pcall(function()
  if cmd=='a' then PI_TEST.a(assert(tonumber(a)))
  elseif cmd=='key' then PI_TEST.key(assert(tonumber(a)),assert(tonumber(b)),assert(tonumber(d)))
  elseif cmd=='mask' then PI_TEST.mask(assert(tonumber(a)),assert(tonumber(b)),assert(tonumber(d)))
  elseif cmd=='shot' then PI_TEST.shot(a)
  elseif cmd=='sample' then PI_TEST.sample('events-input');PI_TEST.persist('events-input')
   PI.log('events-diagnostics',string.format('captured=%d drops=%d retries=%d depth=%d battle=%d turn=%d',PI.read('event_counter'),PI.read('drops'),PI.read('retries'),PI.read('queue_depth'),PI.read('battle_id'),PI.read('turn_id')))
  elseif cmd=='reset' then emu:reset()
  elseif cmd=='checkpoint' then assert(emu:saveStateFile(PI.cfg.checkpoint,C.SAVESTATE.ALL));PI.log('checkpoint-test','explicit ALL; not host-paired')
  elseif cmd=='reload' then assert(emu:loadStateFile(PI.cfg.checkpoint,C.SAVESTATE.ALL));PI.log('reload-test','explicit ALL; heartbeat regression detection only')
  else error('unknown input command')end
 end)
 PI.log('input-command',line..' ok='..tostring(ok))
 if PI_INPUT.client then PI_INPUT.client:send(ok and 'OK\n' or 'ERROR\n')end
end)

