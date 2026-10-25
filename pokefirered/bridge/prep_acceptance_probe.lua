-- PREP-01 acceptance automation only. Read-only position/map, no preparation
-- data, player party or strategy/model packet. Addresses from accepted ELF.
local previous=PI_TEST.sample
PI_TEST.sample=function(label)
 local result=previous(label)
 local s=PI.m.diagnostic_symbols
 local index=emu:read8(s.gPlayerAvatar+5)
 assert(index<16,'invalid current player object')
 local object=s.gObjectEvents+index*36
 PI.log('prep-position',label..' x='..(emu:read16(object+16)-7)..' y='..(emu:read16(object+18)-7))
 local save=emu:read32(s.gSaveBlock1Ptr)
 PI.log('prep-map',label..' group='..emu:read8(save+4)..' num='..emu:read8(save+5))
 return result
end
