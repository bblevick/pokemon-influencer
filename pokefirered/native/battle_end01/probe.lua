-- Read-only bounded diagnostic; not enabled by production launchers.
local d=PI.m.diagnostic_symbols
local n,tail,last=0,0,nil
callbacks:add('frame',function()
 if n>=1024 and (tail>=128 or emu:read8(d.gBattleOutcome)==0) then return end
 local b=PI.m.battle_control.address
 local key=string.format('%d,%d,%d,%d,%d,%d,%d,%d,%d,%d',emu:read8(d.gBattleOutcome),emu:read32(d.gBattleMainFunc),emu:read32(d.gMain+4),emu:read32(b+8),emu:read16(b+36),emu:read32(b+16),PI.read('event_counter'),PI.read('sequence'),PI.read('state'),PI.read('last_ack'))
 if key~=last then last=key;n=n+1;if n>1024 then tail=tail+1 end;PI.log('battle-end-native',key) end
end)
