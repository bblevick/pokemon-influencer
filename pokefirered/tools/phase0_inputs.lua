-- Uses normal emulation frames. runFrame() is invalid in the desktop console context.
P0_QUEUE={}; P0_INDEX=1; P0_REMAIN=0
function p0tap(key,hold,rest)
 for i=1,(hold or 2) do table.insert(P0_QUEUE,{mask=1<<key,frames=1}) end
 for i=1,(rest or 30) do table.insert(P0_QUEUE,{mask=0,frames=1}) end
 p0log('queued input key='..key..' hold='..(hold or 2)..' rest='..(rest or 30))
end
function p0a(n) for i=1,n do p0tap(C.GBA_KEY.A,20,15) end end
function p0shot(name) table.insert(P0_QUEUE,{shot=name}) end
P0_INPUT_CB=callbacks:add('frame',function()
 if P0_REMAIN>0 then P0_REMAIN=P0_REMAIN-1; return end
 local entry=P0_QUEUE[P0_INDEX]
 if not entry then return end
 P0_INDEX=P0_INDEX+1
 if entry.shot then
  emu:screenshot(P0_ROOT..'evidence/private/'..entry.shot..'.png')
  p0log('screenshot='..entry.shot..' frame='..emu:currentFrame())
 else emu:setKeys(entry.mask); P0_REMAIN=entry.frames-1 end
end)
if P0_CLIENT then P0_CLIENT:close(); P0_CLIENT=nil end
if P0_SERVER then P0_SERVER:close(); P0_SERVER=nil end
p0log('socket diagnostic closed; async input helper installed')

P0_ORIG_LOG=p0log
function p0log(s)
 if s:find('screenshot=') then
  local b=emu:read32(0x03005008) -- ELF-derived gSaveBlock1Ptr, resolved at runtime
  s=s..' x='..emu:read16(b)..' y='..emu:read16(b+2)..' mapgroup='..emu:read8(b+4)..' mapnum='..emu:read8(b+5)..' battleflags='..emu:read32(0x02022B4C)..' outcome='..emu:read8(0x02023E8A)
 end
 P0_ORIG_LOG(s)
end
