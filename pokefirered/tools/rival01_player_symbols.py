"""Resolve the player-local callback without conflating duplicate ELF static names."""
from pathlib import Path
import json
from phase1_events_build import symbols

def player_symbols(root,manifest):
 rom=root/manifest['rom_path'];linked=symbols(rom.with_suffix('.elf'));obj=rom.parent/'build/firered/src/battle_controller_player.o';local=symbols(obj)
 base=linked['PlayerHandleChooseAction']['address']-local['PlayerHandleChooseAction']['address']
 callback=base+local['HandleInputChooseAction']['address']
 names=['gBattleOutcome','gBattlerControllerFuncs','gBattleMons','gMoveSelectionCursor','gActionSelectionCursor','gStatuses3','HandleInputChooseMove']
 value={n:linked[n]['address'] for n in names};value.update(HandleInputChooseAction=callback,monSize=88)
 # Public species typing only, derived from the project's pinned legality catalog.
 # This belongs to the ordinary-player test driver, never an NPC observation.
 catalog=json.loads((root/'config/roster_catalog.json').read_text())
 value['grassSpecies']=[row['id'] for row in catalog['species'] if catalog['constants']['TYPE_GRASS'] in row['types']]
 value['damagingMoves']=[[row['id'],row['power']] for row in catalog['moves'] if row['power']>0]
 # Verify the pinned player callback installer actually contains this Thumb pointer.
 installer=base+local['HandleChooseActionAfterDma3']['address'];end=linked['PlayerHandleChooseAction']['address']
 native=rom.read_bytes()[installer-0x08000000:end-0x08000000]
 assert (callback+1).to_bytes(4,'little') in native
 return value,{'object':str(obj),'relocationBase':base,'sourceLocalOffset':local['HandleInputChooseAction']['address'],'linkedPlayerCallback':callback,'installer':installer,'installerContainsThumbPointer':True,'ambiguousGenericLookup':linked['HandleInputChooseAction']['address']}
