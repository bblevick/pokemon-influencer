-- Generic observational receipt. Addresses originate in this build's ELF.
-- Existing cumulative counter proves one constructor increment per receipt.
local last=0
callbacks:add('frame',function()
 if not PI.authenticated or PI.epoch~=1 then return end
 local count=emu:read32(PI.m.preparation_mailbox.address+64)
 if count==last then return end
 assert(count==last+1,'unexpected authored construction counter')
 last=count
 local trainer=emu:read16(PI.m.diagnostic_symbols.gTrainerBattleOpponent_A)
 assert(PI.queue(PI.wire(12,count,PI.epoch,12,string.pack('<I2I4',trainer,count))),'constructor receipt queue full')
end)
