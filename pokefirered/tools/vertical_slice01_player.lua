-- FINAL LIVE CLOSEOUT: ordinary player buttons only.
-- Ordinary defensive play: reduce Attack, seed for sustain, then attack.
-- Naturally learned Vine Whip takes priority; no granted move/items/stats.
-- Read only native menu callback and publicly visible opposing species.
assert(PI_END_SYMBOLS)
PI_END_PLAYER={counts={},frames=0,terminalFrame=nil,enabled=true}
callbacks:add('frame',function()
 local p=PI_END_PLAYER;if not p.enabled then return end
 p.frames=p.frames+1
 local outcome=emu:read8(PI_END_SYMBOLS.gBattleOutcome)
 if p.started and outcome~=0 and not p.terminalFrame then p.terminalFrame=p.frames end
 if p.frames>18000 or (p.terminalFrame and p.frames-p.terminalFrame>900) then p.enabled=false;emu:setKeys(0);PI.log('player-path-stopped',outcome);return end
 if PI_TEST.index<=#PI_TEST.queue then return end
 local callback=emu:read32(PI_END_SYMBOLS.gBattlerControllerFuncs)
 if callback==PI_END_SYMBOLS.HandleInputChooseAction+1 then
  p.started=true
  if emu:read16(PI_END_SYMBOLS.gBattleMons+0x28)<23 then p.enabled=false;emu:setKeys(0);PI.log('player-heal-review','ordinary Bag input needed');return end
  PI_TEST.key(5,4,3);PI_TEST.key(6,4,3);PI_TEST.key(0,4,12)
 elseif callback==PI_END_SYMBOLS.HandleInputChooseMove+1 then
  if emu:read16(PI_END_SYMBOLS.gBattleMons+0x28)<23 then p.enabled=false;emu:setKeys(0);PI.log('player-heal-review','ordinary Bag input needed from move menu');return end
  local species=emu:read16(PI_END_SYMBOLS.gBattleMons+PI_END_SYMBOLS.monSize)
  local count=p.counts[species] or 0
  local seeded=emu:read32(PI_END_SYMBOLS.gStatuses3+4)&4~=0
  local slot=count==0 and 1 or ((not seeded and emu:read8(PI_END_SYMBOLS.gBattleMons+0x24+2)>0) and 2 or (count<7 and 1 or 0))
  -- Player-side own move knowledge only: a naturally learned Vine Whip.
  -- No NPC packet/context is changed; do not grant a move or alter PP.
  for i=0,3 do if emu:read16(PI_END_SYMBOLS.gBattleMons+12+2*i)==22 then slot=i end end
  p.counts[species]=count+1
  PI_TEST.key(5,4,3);PI_TEST.key(6,4,3)
  if slot==1 or slot==3 then PI_TEST.key(4,4,3) end
  if slot==2 or slot==3 then PI_TEST.key(7,4,3) end
  PI_TEST.key(0,4,20);PI.log('player-path-choice',species..' slot='..slot)
 else PI_TEST.key(0,4,15) end
end)
