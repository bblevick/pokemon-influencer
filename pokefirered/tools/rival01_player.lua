-- Test-only ordinary buttons. Own HP/PP/menu and visible species, no hidden NPC state.
assert(PI_PLAYER_SYMBOLS)
if PI_EXP_PLAYER and PI_EXP_PLAYER.cb then callbacks:remove(PI_EXP_PLAYER.cb) end
PI_EXP_PLAYER={frames=0,started=false,enabled=true,terminal=nil}
-- Explicit test-driver a0 arms a fresh ordinary-player sequence; zero game writes.
if not PI_EXP_ORIGINAL_A then PI_EXP_ORIGINAL_A=PI_TEST.a end
function PI_TEST.a(count)
 if PI_CONTINUITY then assert(PI_CONTINUITY.allowInput(),'managed player input lease unavailable') end
 if count==0 then PI_EXP_PLAYER.frames=0;PI_EXP_PLAYER.started=false;PI_EXP_PLAYER.enabled=true;PI_EXP_PLAYER.terminal=nil;PI_EXP_PLAYER.level=nil;PI.log('exp-player-armed','ordinary buttons only')
 else PI_EXP_ORIGINAL_A(count) end
end
PI_EXP_PLAYER.cb=callbacks:add('frame',function()
 local p=PI_EXP_PLAYER;local s=PI_PLAYER_SYMBOLS
 if PI_CONTINUITY and not PI_CONTINUITY.allowInput() then p.enabled=false;return end
 if not p.enabled then return end
 p.frames=p.frames+1
 local outcome=emu:read8(s.gBattleOutcome)
 if not p.started and outcome~=0 then
  if PI_TEST.index>#PI_TEST.queue then PI_TEST.key(0,4,30) end
  return
 end
 local level=emu:read8(s.gBattleMons+42)
 if p.level and level>p.level then p.enabled=false;emu:setKeys(0);PI.log('exp-player-learning-review','own level advanced; ordinary learning/evolution review required');return end
 if p.started and outcome~=0 and not p.terminal then p.terminal=p.frames end
 if p.frames>24000 or (p.terminal and p.frames-p.terminal>900) then p.enabled=false;emu:setKeys(0);PI.log('exp-player-stopped',outcome);return end
 if PI_TEST.index<=#PI_TEST.queue then return end
 local callback=emu:read32(s.gBattlerControllerFuncs)
 if callback==s.HandleInputChooseAction+1 or callback==s.HandleInputChooseMove+1 then
  p.started=true;p.level=p.level or level
  if emu:read16(s.gBattleMons+40)<15 then p.enabled=false;emu:setKeys(0);PI.log('exp-player-heal-review','own HP <15; ordinary Bag required');return end
  local cursor,slot=emu:read8(s.gActionSelectionCursor),0
  if callback==s.HandleInputChooseMove+1 then
   local visibleSpecies=emu:read16(s.gBattleMons+s.monSize)
   local visibleGrass=false
   for _,species in ipairs(assert(s.grassSpecies)) do if species==visibleSpecies then visibleGrass=true end end
   cursor=emu:read8(s.gMoveSelectionCursor)
   local tackle,vine,seed,growl=nil,nil,nil,nil
   local availableAttack,attackPower=nil,0
   for i=0,3 do
    if emu:read8(s.gBattleMons+36+i)>0 then
     local move=emu:read16(s.gBattleMons+12+2*i)
     if move==33 then tackle=i elseif move==22 then vine=i elseif move==73 then seed=i elseif move==45 then growl=i end
     -- Include legitimately learned attacks, using only public base power and
     -- the player's own move/PP. No hidden opponent stats or damage RNG.
     for _,entry in ipairs(s.damagingMoves or {}) do
      if entry[1]==move and entry[2]>attackPower then availableAttack=i;attackPower=entry[2] end
     end
    end
   end
   local visibleSeeded=emu:read32(s.gStatuses3+4)&4~=0
   slot=availableAttack or tackle or vine or 0
   -- Ordinary player sustain against publicly visible non-Grass species.
   if not visibleSeeded and seed and not visibleGrass then slot=seed end
   if not availableAttack and not tackle and not vine then
    if not visibleSeeded and seed and not visibleGrass then slot=seed else slot=growl or 0 end
   end
   if visibleSpecies==11 or visibleSpecies==14 then
    local seeded=emu:read32(s.gStatuses3+4)&4~=0
    if not seeded and seed then slot=seed
    else for i=0,3 do if emu:read16(s.gBattleMons+12+2*i)==22 and emu:read8(s.gBattleMons+36+i)>0 then slot=i end end end
   elseif visibleSpecies==74 or visibleSpecies==95 then
    for i=0,3 do if emu:read16(s.gBattleMons+12+2*i)==22 and emu:read8(s.gBattleMons+36+i)>0 then slot=i end end
   end
   if emu:read8(s.gBattleMons+36+slot)==0 then
    for i=0,3 do if emu:read16(s.gBattleMons+12+2*i)==22 and emu:read8(s.gBattleMons+36+i)>0 then slot=i end end
    -- A depleted damaging move must not trap the ordinary-player driver on
    -- an empty slot while another selectable move still has PP. Once every
    -- slot is exhausted, the native Fight path supplies Struggle itself.
    if emu:read8(s.gBattleMons+36+slot)==0 then
     for i=0,3 do if emu:read8(s.gBattleMons+36+i)>0 then slot=i;break end end
    end
   end
   p.sleepTried=p.sleepTried or {}
   -- Read only the publicly displayed SLP condition, never its remaining timer.
   local visibleAsleep=(emu:read32(s.gBattleMons+s.monSize+76)&7)~=0
   if not visibleAsleep then
    for i=0,3 do if emu:read16(s.gBattleMons+12+2*i)==79 and emu:read8(s.gBattleMons+36+i)>0 then slot=i end end
   end
   PI.log('exp-player-move','visibleSpecies='..visibleSpecies..' ownSlot='..slot)
  end
  if cursor%2~=slot%2 then PI_TEST.key(slot%2==1 and 4 or 5,4,10)
  elseif (cursor>=2)~=(slot>=2) then PI_TEST.key(slot>=2 and 7 or 6,4,10)
  else
   if callback==s.HandleInputChooseMove+1 and emu:read16(s.gBattleMons+12+2*slot)==79 then p.sleepTried[emu:read16(s.gBattleMons+s.monSize)]=true end
   PI_TEST.key(0,4,20)
  end
 else PI_TEST.key(0,4,15) end
end)

PI_EXP_PLAYER.enabled=false
