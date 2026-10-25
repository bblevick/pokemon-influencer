-- Read-only persistence observations; no snapshot load or memory writes.
P0_ROOT='/Users/blevicki/Documents/poke/pokefirered/'
P0_LOG=assert(io.open(P0_ROOT..'evidence/phase0/emulator-runtime.log','a'))
function p0log(s) console:log(s); P0_LOG:write(s..'\n'); P0_LOG:flush() end
p0log('fresh-process reload: no savestate argument')
dofile(P0_ROOT..'tools/phase0_inputs.lua')
function p0persist(label)
 p0log(label..' counter='..emu:read32(0x03005390)..' partycount='..emu:read8(0x02024029)..' level='..emu:read8(0x02024284+84)..' hp='..emu:read16(0x02024284+86))
end
