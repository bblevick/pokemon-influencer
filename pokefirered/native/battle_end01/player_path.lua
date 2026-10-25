-- Test-only ordinary button automation; never writes battle/party/flag state.
-- Read only native menu callback and publicly visible opposing species.
assert(PI_END_SYMBOLS)
PI_END_PLAYER={counts={},frames=0,terminalFrame=nil,enabled=true}
callbacks:add('frame',function()
 local p=PI_END_PLAYER;if not p.enabled then return end
 p.frames=p.frames+1
 local outcome=emu:read8(PI_END_SYMBOLS.gBattleOutcome)
 if outcome~=0 and not p.terminalFrame then p.terminalFrame=p.frames end
 if p.frames>18000 or (p.terminalFrame and p.frames-p.terminalFrame>900) then p.enabled=false;emu:setKeys(0);PI.log('player-path-stopped',outcome);return end
 if PI_TEST.index<=#PI_TEST.queue then return end
 local callback=emu:read32(PI_END_SYMBOLS.gBattlerControllerFuncs)
 if callback==PI_END_SYMBOLS.HandleInputChooseAction+1 then
  PI_TEST.key(5,1,3);PI_TEST.key(6,1,3);PI_TEST.key(0,1,12)
 elseif callback==PI_END_SYMBOLS.HandleInputChooseMove+1 then
  local species=emu:read16(PI_END_SYMBOLS.gBattleMons+PI_END_SYMBOLS.monSize)
  local count=p.counts[species] or 0
  local seeded=emu:read32(PI_END_SYMBOLS.gStatuses3+4)&4~=0
  local slot=PI_END_LOSS and 1 or (count<4 and 1 or (not seeded and 2 or 0))
  -- Player-side own move knowledge only: a naturally learned Vine Whip.
  -- No NPC packet/context is changed; do not grant a move or alter PP.
  for i=0,3 do if emu:read16(PI_END_SYMBOLS.gBattleMons+12+2*i)==22 then slot=i end end
  p.counts[species]=count+1
  PI_TEST.key(5,1,3);PI_TEST.key(6,1,3)
  if slot==1 or slot==3 then PI_TEST.key(4,1,3) end
  if slot==2 or slot==3 then PI_TEST.key(7,1,3) end
  PI_TEST.key(0,1,20);PI.log('player-path-choice',species..' slot='..slot)
 else PI_TEST.key(0,1,15) end
end)
