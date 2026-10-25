-- Temporary loopback emulator input diagnostic, NOT a ROM bridge.
-- Only bounded button sequences and sanitized screenshot names; no arbitrary code/memory commands.
P0_DRIVER=assert(socket.bind('127.0.0.1',18766)); assert(P0_DRIVER:listen())
P0_DRIVER:add('received',function()
 local c=assert(P0_DRIVER:accept()); local buffer=''
 c:add('received',function()
  local part,err=c:receive(1024)
  if not part then if err~=socket.ERRORS.AGAIN then c:close() end; return end
  buffer=buffer..part
  if #buffer>4096 then c:close(); return end
  while buffer:find('\n') do
   local line,remaining=buffer:match('^(.-)\n(.*)$'); buffer=remaining
   local key,hold,rest=line:match('^KEY (%d+) (%d+) (%d+)$')
   local count=line:match('^A (%d+)$'); local name=line:match('^SHOT ([a-z0-9%-]+)$')
   if key and tonumber(key)<10 and tonumber(hold)<=360 and tonumber(rest)<=600 then
    p0tap(tonumber(key),tonumber(hold),tonumber(rest)); c:send('OK\n')
   elseif count and tonumber(count)<=30 then p0a(tonumber(count)); c:send('OK\n')
   elseif name and #name<64 then p0shot(name); c:send('OK\n')
   else c:send('REJECT\n') end
   p0log('driver command='..line)
  end
 end)
end)
p0log('bounded input diagnostic listening=127.0.0.1:18766')
