-- Observation-only native resource audit; never gameplay permissions.
local sample=PI_TEST.sample
function PI_TEST.sample(label)
 local result=sample(label);local s=PI.m.diagnostic_symbols
 local heap=s.gHeap;local ptr=heap;local free,largest,used,blocks=0,0,0,0
 repeat
  assert(ptr>=heap and ptr+16<=heap+0x1c000 and ptr%4==0,'heap block address')
  assert(emu:read16(ptr+2)==0xa3a3,'heap magic')
  local n=emu:read32(ptr+4);assert(n<=0x1c000,'heap size')
  blocks=blocks+1;assert(blocks<=2048,'heap cycle')
  if emu:read16(ptr)==0 then free=free+n;largest=math.max(largest,n)else used=used+n end
  ptr=emu:read32(ptr+12)
 until ptr==heap
 local tasks,windows,sprites=0,0,0
 for i=0,15 do if emu:read8(s.gTasks+i*40+4)~=0 then tasks=tasks+1 end end
 for i=0,31 do if emu:read8(s.gWindows+i*12)~=255 and emu:read32(s.gWindows+i*12+8)~=0 then windows=windows+1 end end
 for i=0,63 do if emu:read16(s.gSprites+i*68+0x3e)&1~=0 then sprites=sprites+1 end end
 local f=assert(io.open(PI.cfg.log..'.resources','a'))
 f:write(string.format('{"label":"%s","frame":%d,"free":%d,"largest":%d,"allocated":%d,"blocks":%d,"tasks":%d,"windows":%d,"sprites":%d,"viewerOwner":%d}\n',label,emu:currentFrame(),free,largest,used,blocks,tasks,windows,sprites,emu:read32(s.sPb)))
 f:flush();f:close();return result
end
