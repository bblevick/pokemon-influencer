# CAMPAIGN-EXPANSION-01 actual commands and partial golden path

Working directory: `/Users/blevicki/Documents/poke/pokefirered`. All batteries,
ROMs, databases and images remain local. `input-commands.jsonl` records exact
command queues and screenshot labels; `*-route.json` records source collision
hashes, native positions and bounded button segments. A queued input ACK is not
proof of game execution; screenshots/receipts were inspected afterward.

## Setup, build and host verification

```sh
.venv/bin/python tools/campaign_expansion01_content.py --write
.venv/bin/python tools/campaign_expansion01_content.py
.venv/bin/python tools/campaign_expansion01_build.py
.venv/bin/python tools/campaign_expansion01_setup.py
.venv/bin/python -m unittest discover -s tests -p test_campaign_expansion01.py -v
.venv/bin/python -m unittest discover -s tests -p test_pokebook01.py -v
.venv/bin/python tools/battle01_c_tests.py --manifest evidence/phase6/campaign_expansion01/manifest-native.json
arm-none-eabi-size -A .local/battle-end01-external-v2/pokefirered.elf .local/campaign-expansion01-native/pokefirered.elf
```

Setup/build refuse existing destinations. Initial hash/backup/wrapper failures
are retained; their corrected results are not relabeled as first-attempt success.
Build's exact make argv/cwd/exit status are in `native-build.log`. Matching source
and agbcc pins are retained from Phase0, not repinned upstream.

The SOCIAL and historical budget regression commands/counts are recorded in
`social-regression.log` and `budget-regression.log`. Only those relevant suites
were run; no claim of a full repository regression.

## Actual managed native campaign

```sh
.venv/bin/python tools/campaign_expansion01.py launch --start
.venv/bin/python tools/campaign_expansion01.py host --live --continue-authorized-run --seconds 3600
```

The retained current launch argv points at `.local/campaign-expansion01-native/`
with `hwaccelVideo=0` and the isolated `.local/campaign_expansion01` battery.
The generated `run.lua` was loaded once per fresh process through native mGBA
Tools → Scripting using:

```lua
dofile('/Users/blevicki/Documents/poke/pokefirered/.local/campaign_expansion01/run.lua')
```

Normal title/Continue inputs sometimes reached an intermediate title/quest-log
screen; screenshots were checked and additional normal Start/A/B input was used.
No RAM/flag/savestate manipulation. Native Continue was confirmed in the field.

Actual route segments use the generic source-collision walker. Important native
waypoints: Gym6,14 → Pewter15,17 → Center7,4 → Center7,8 → Pewter17,26 → east exit
47,22 → Route3 entrance1,12 → corridor14,6. The Running Shoes dialogue interrupts
travel and must close before Save. The city is48 tiles wide: initial39,17 goal
was not the exit. The attempted Route3 goal10,3 was nonpassable and rejected.

Representative verified commands (full exact segments in the input/route logs):

```sh
.venv/bin/python tools/campaign_expansion01.py route PewterCity_Gym 6 14 --label gym-exit
.venv/bin/python tools/campaign_expansion01.py route PewterCity_PokemonCenter_1F 7 4 --label center-nurse
.venv/bin/python tools/campaign_expansion01.py save --label c0-ready2 --menu-cursor 0 --resume-intent
.venv/bin/python tools/campaign_expansion01_capture.py C0-ready --battery
.venv/bin/python tools/campaign_expansion01.py input --label pewter-route3 'key 4 50 90'
.venv/bin/python tools/campaign_expansion01.py route Route3 14 6 --label route3-colton-path
```

The upper corridor naturally triggers unexpanded Colton. The test-only player
script was loaded through mGBA's console, using the ELF-derived symbol file:

```lua
dofile('/Users/blevicki/Documents/poke/pokefirered/.local/campaign_expansion01/player.lua')
```

The reusable source is `tools/campaign_expansion01_player.lua`: bounded ordinary
buttons, own HP/PP/menu and visible species only, pauses for Bag healing. It
never reads hidden enemy HP/stats or changes game memory. `a 0` explicitly arms
its bounded sequence; it does not call a model or reset a battle. Post-battle
continuation stops. Do not load the player script for feed/Save checks.

After actual Colton victory, normal native approach to Sally:

```sh
.venv/bin/python tools/campaign_expansion01.py route Route3 14 3 --label north-corridor
.venv/bin/python tools/campaign_expansion01.py route Route3 24 3 --label sally-approach
.venv/bin/python tools/campaign_expansion01.py input --label sally-challenge 'key 4 16 120' 'a 8'
.venv/bin/python tools/campaign_expansion01.py input --label sally-resume 'a 0'
```

Sally's battle used four ordinary player Potions at reviewed low-HP action menus.
The verified native Bag pattern was Right/A, Potion/A, Use/A, Pokémon/A, dialogue
A. Each operation was followed by a screenshot and ordinary player sequence
rearming. Exact timings/labels for `sally-potion`, `sally-potion2`,
`sally-potion3`, `sally-potion4` are in the input log. No prescribed NPC choices.

Read-only captures:

```sh
.venv/bin/python tools/campaign_expansion01_capture.py sally-ended
.venv/bin/python tools/campaign_expansion01_capture.py sally-social-check
```

## Save recovery and offline reload — actual, not automatic acceptance

The first `save --label c1-sally --menu-cursor 0` entered Pokédex (actual cursor4).
The corrected field/menu flow produced native counter15 using:

```sh
.venv/bin/python tools/campaign_expansion01.py save --label c1-sally-real --menu-cursor 0 --resume-intent
```

Its host was already suspended after pending-save restart. The CLI timed out;
the **native Save itself succeeded**, evidenced by battery/receipt and UI.
With owned host/emulator stopped, SQLite backup and normal battery were preserved.
A separately labeled isolated fixture proved unchanged service-API recovery.
Then:

```sh
.venv/bin/python tools/campaign_expansion01_recover_save.py
.venv/bin/python tools/campaign_expansion01_capture.py C1-sally-recovered --battery
.venv/bin/python tools/campaign_expansion01.py launch --restore .local/campaign_expansion01/C1-sally-recovered.sav
.venv/bin/python tools/campaign_expansion01.py host --seconds 1800
.local/mGBA.app/Contents/MacOS/mGBA -C hwaccelVideo=0 -C savegamePath=/Users/blevicki/Documents/poke/pokefirered/.local/campaign_expansion01 .local/campaign-expansion01-native/pokefirered.gba
```

Loaded generated bridge through native scripting, normal Continue to field.
No hosted flags, credentials or historical re-inference. Capture/replay:

```sh
.venv/bin/python tools/campaign_expansion01_capture.py C1-before-viewer
.venv/bin/python tools/campaign_expansion01_replay.py
```

The replay tool creates an isolated SQLite fixture, restores actual C0/C1 pairs,
uses a labeled host-only divergent social tick, verifies seven hashes, and refuses
overwriting an existing fixture. It is not another native playthrough.

## Native viewer and shutdown

With fresh field Start cursor0, open Start, Down seven times, A. Native PokeBook
home shows followers2. Feed/A shows page1 Rick/Sammy/Brock; Down twice/A opens
Brock; B/Right shows page2 Colton/Sally; Down/A opens Sally. B/B/Down/A opens
followers Rick/Sally. B/B/B returns to field. Exact commands and native images:
`c1-pokebook-home`, `c1-feed-page1`, `c1-brock-post`, `c1-feed-page2`,
`c1-sally-post`, `c1-followers`, `c1-viewer-field2`.

```sh
.venv/bin/python tools/campaign_expansion01_capture.py C1-after-viewer
.venv/bin/python tools/campaign_expansion01_closeout.py
```

Owned PIDs were stopped with SIGINT and verified absent. The closeout script
attaches actual provider/native receipts to the same closed16-attempt ledger,
checks original protected hashes and native trainer flags/RAM, safely removes only
Sally's settled owned Hermes home, and verifies durable projections remain.
It is a retained audit command, not idempotent runtime orchestration or permission
for further inference. `verification.json` explicitly records failed/unrun gates.
