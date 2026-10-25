#!/usr/bin/env python3
"""Verify retained live smoke evidence. Does not launch or mock an emulator."""
import hashlib
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
log=(root/'evidence/phase0/emulator-runtime.log').read_text()
checks={
 'normal_wild_battle_started':bool(re.search(r'screenshot=ordinary-battle-start .*battleflags=4 outcome=0',log)),
 'normal_wild_battle_won':bool(re.search(r'screenshot=ordinary-battle-result-03 .*battleflags=4 outcome=1',log)),
 'actual_save_callback':'savedataUpdated count=1' in log,
 'valid_battery_sections':json.loads((root/'evidence/phase0/battery-save.json').read_text())['passed'],
 'fresh_launch_recorded':'fresh-process reload: no savestate argument' in log,
 'same_field_reloaded':bool(re.search(r'screenshot=battery-reload-field .*x=18 y=32 mapgroup=3 mapnum=19',log)),
 'same_counter_party_level_hp':('persist-before counter=1 partycount=1 level=5 hp=5' in log and 'persist-after counter=1 partycount=1 level=5 hp=5' in log),
}
images={}
for name in ['ordinary-battle-start','ordinary-battle-result-03','in-game-saved-finished','reload-continue-menu','battery-reload-field']:
 p=root/'evidence/private'/f'{name}.png'
 checks[f'image_{name}']=p.is_file()
 if p.is_file(): images[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
report={'scope':'retained actual live smoke evidence assertions, not a new emulator replay',
        'checks':checks,'screenshot_sha256':images,'passed':all(checks.values())}
(root/'evidence/phase0/emulator-smoke.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
