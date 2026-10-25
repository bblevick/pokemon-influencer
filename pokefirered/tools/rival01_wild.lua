-- Test-only ordinary Run buttons, own menu cursor/callback only; no memory writes.
assert(PI_PLAYER_SYMBOLS)
if PI_WILD_RUN and PI_WILD_RUN.cb then callbacks:remove(PI_WILD_RUN.cb) end
PI_WILD_RUN={enabled=false,started=false}
local priorA=PI_TEST.a
function PI_TEST.a(count)
 if PI_CONTINUITY then assert(PI_CONTINUITY.allowInput(),'managed wild input lease unavailable') end
 if count==30 then PI_WILD_RUN.enabled=true;PI_WILD_RUN.started=false;PI_WILD_RUN.frames=0;PI_EXP_PLAYER.enabled=false;PI.log('wild-run-armed','ordinary buttons; authenticated host verified wild encounter') else priorA(count) end
end
PI_WILD_RUN.cb=callbacks:add('frame',function()
 local p=PI_WILD_RUN;if not p.enabled or PI_TEST.index<=#PI_TEST.queue then return end
 if PI_CONTINUITY and not PI_CONTINUITY.allowInput() then p.enabled=false;return end
 local s=PI_PLAYER_SYMBOLS;p.frames=p.frames+1
 if p.frames>2400 then p.enabled=false;emu:setKeys(0);PI.log('wild-run-stopped','bounded');return end
 local outcome=emu:read8(s.gBattleOutcome)
 if p.started and outcome~=0 then
  p.enabled=false;emu:setKeys(0);PI_TEST.key(0,0,600);PI_TEST.key(0,4,180);PI_TEST.key(0,4,180);PI.log('wild-run-terminal',outcome);return
 end
 local cb=emu:read32(s.gBattlerControllerFuncs)
 if cb==s.HandleInputChooseAction+1 then
  p.started=true;local cursor=emu:read8(s.gActionSelectionCursor)
  if cursor%2~=1 then PI_TEST.key(4,4,10)
  elseif cursor<2 then PI_TEST.key(7,4,10)
  else PI_TEST.key(0,4,60) end
 elseif cb==s.HandleInputChooseMove+1 then PI_TEST.key(1,4,20)
 else PI_TEST.key(0,4,30) end
end)
