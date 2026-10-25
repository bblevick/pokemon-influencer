# BATTLE-01 commands actually used

Pinned pret037335f4c725d7c9aecdac87066f2002b4bd7e14 and agbccda598c1d918402c42c0c0d7128ba14567f3175e9. Working directory /Users/blevicki/Documents/poke/pokefirered. No ROM download/upload, credential display or model call.

Isolated overlay builder tools/battle01_build.py copied the accepted .local/system1-01a-native-v3 source. Actual inner build command, cwd .local/battle01-native-v3:

```sh
make -j8 rom PI_BRIDGE=1 PI_BRIDGE_TEST=0 PI_EVENTS=1 PI_UI=1 PI_UI_TEST=1 GAME_VERSION=FIRERED GAME_REVISION=0 GAME_LANGUAGE=ENGLISH MODERN=0
```

The wrapper refuses an existing build; reproduce in a fresh destination by overriding its DEST, rather than overwriting retained evidence. Actual build logs and ROM/ELF/source hashes are native-build.log and manifest-native.json. Failed initial compilations and v1/v2 trials remain retained and excluded.

Fresh ordinary paired launch and offline host:

```sh
python3 tools/battle01_launch.py --start
python3 tools/battle01_host.py --policy switch_once
```

mGBA Tools -> Scripting -> Run executed:

```lua
dofile('/Users/blevicki/Documents/poke/pokefirered/.local/battle01/run.lua')
```

Actual bounded input sequences (waited for native screenshot receipts):

```sh
python3 tools/battle01_input.py 'a 20' 'key 9 0 360' 'shot gym-v3'
python3 tools/battle01_input.py 'prepared' 'key 9 0 360' 'a 12' 'shot turn1-v3'
python3 tools/battle01_input.py 'a 20' 'key 9 0 180' 'shot turn2-v3'
python3 tools/battle01_input.py 'a 20' 'key 9 0 180' 'shot turn3-v3'
```

Those prove switch/replacement but are not a complete battle claim. Key9 with hold0 is idle, not an L-button press. Early malformed `a20` attempts were rejected, made no input mutation, and are retained in input-commands.jsonl.

A new fresh paired Save19 launch used --policy delayed. Its first pure result slept4 seconds, expired on host/native, and vanilla executed String Shot81. This trial was aborted before battle completion. See session2594744355/native-terminal and selection-timeout records. No inference/network provider was used.

Final fresh paired Save19 launch used --policy first_move. Actual inputs:

```sh
python3 tools/battle01_input.py 'a 20' 'key 9 0 360' 'shot move-gym'
python3 tools/battle01_input.py 'prepared' 'key 9 0 360' 'a 8' 'shot move-menu'
python3 tools/battle01_input.py 'a 2' 'key 9 0 240' 'shot move-prompt'
python3 tools/battle01_input.py 'a 1' 'key 9 0 60' 'shot move-prompt2'
python3 tools/battle01_input.py 'key 4 6 20' 'key 0 8 180' 'shot growl-selected'
python3 tools/battle01_input.py 'a 2' 'key 9 0 120' 'shot native-poisonsting'
python3 tools/battle01_input.py 'a 2' 'key 9 0 180' 'shot move-turn-end'
python3 tools/battle01_scenario.py
```

The bounded completion script confirmed canonical BATTLE_ENDED (player lost), not a queued-input ACK/faint screenshot. Five selected Poison Sting actions resolved. Host method-name collision stopped recap settlement; after renaming the tactical audit method, the same offline host command restarted and recovered the pending mandatory recap. This failure/recovery is explicit, not hidden acceptance evidence.

Actual normal save:

```sh
python3 tools/battle01_save.py
python3 tools/battle01_input.py 'key 1 8 120' 'key 1 8 120' 'shot save-field-ready'
python3 tools/battle01_save.py --resume
```

The first save path did not save because the nurse dialogue was still open; save-path.log records the timeout. Dialogue was closed, the same reviewed intent resumed, and actual Save20 callback/checksum/checkpoint paired. Battery retained privately as .local/battle01/completed-save20.sav. Fresh launch/--policy unavailable host/dofile harness then:

```sh
python3 tools/battle01_input.py 'a 20' 'key 9 0 360' 'shot paired20-restored'
python3 tools/battle01_input.py 'key 1 8 120' 'key 1 8 120' 'shot paired20-field'
```

Fresh native sample showed counter20, Pokémon Center, no battle/events; durable audit/post remained correctly paired.

Checks actually run:

```sh
python3 -m unittest tests.test_battle01 -v
python3 -m unittest tests.test_system1_native tests.test_strategy_memo -v
python3 tools/battle01_c_tests.py
python3 tools/verify_battle01.py
arm-none-eabi-objdump -d .local/battle01-native-v3/pokefirered.elf --disassemble=PiBattle_Select
python3 -m py_compile battle/domain.py battle/store.py battle/transport.py tools/battle01_build.py tools/battle01_host.py tools/battle01_scenario.py tools/battle01_save.py tools/verify_battle01.py
```

The actual Lua response fixture ran through mGBA Scripting:

```lua
dofile('/Users/blevicki/Documents/poke/pokefirered/.local/battle01/lua-contract-tests.lua')
```

tools/battle01_lua_tests.py reproduces that fixture from actual receive-source + tests/battle01_response_fixture.lua. Eight assertions use mock named-control memory inside the actual pinned interpreter, with no game-memory writes. They are fixture evidence, not eight live protocol scenarios. Original test compile/layout failures are diagnostic trials; final10 focused tests and18 retained regression tests pass,0 skips. No whole-suite/campaign/fast-forward claim.

All actual detailed input/receipt/host/native decision traces are input-commands.jsonl, emulator.jsonl, host.jsonl, deliveries.jsonl and battle-audit.jsonl. Exact live contexts are turn-*.json/txt. Task-owned processes were stopped by PID using SIGINT for host and process termination for emulator; cleanup.json records final absence and pending-job status.
