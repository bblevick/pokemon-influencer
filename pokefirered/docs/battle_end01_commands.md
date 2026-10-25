# BATTLE-END-01 commands and reproducible native path

Run from `/Users/blevicki/Documents/poke/pokefirered`. All hosted requests:0.
Original inputs are read-only. SQLite backup and battery copies live under
`.local/battle_end01/`; private screenshots under `evidence/private/battle_end01/`.
Commands below create real artifacts; the verifier only reads retained evidence.

## Isolated setup/build

```sh
.venv/bin/python tools/battle_end01.py init
.venv/bin/python tools/battle_end01_build.py
.venv/bin/python tools/battle_end01_build.py --vanilla
.venv/bin/python tools/battle_end01_build.py --revision2
.venv/bin/python tools/battle_end01_build.py --vanilla --revision2
```

Each build refuses to overwrite its retained source tree; do not rerun into it.
The builder runs fresh objects with the pinned matching toolchain:

```sh
make -j8 rom PI_BRIDGE=1 PI_BRIDGE_TEST=0 PI_EVENTS=1 PI_UI=1 PI_UI_TEST=1 GAME_VERSION=FIRERED GAME_REVISION=0 GAME_LANGUAGE=ENGLISH MODERN=0
```

Cwd is `.local/battle-end01-external[-v2]` or vanilla counterpart. Exact argv/cwd
and exit0 appear in build-{external,vanilla}[-v2].log. Initial revision1 actual
comparison is retained; final revision2 fixes reason encoding without changing
legality, ABI or Gym script. Vanilla revision2 was built, not emulator-run.

## Actual final external victory

```sh
.venv/bin/python tools/battle_end01.py launch > evidence/phase4/battle_end01/launch-external-v2-win.log
.venv/bin/python tools/battle_end01.py host --terminal-delay-test > evidence/phase4/battle_end01/host-external-v2-win.log
.local/mGBA.app/Contents/MacOS/mGBA -C hwaccelVideo=0 -C savegamePath=/Users/blevicki/Documents/poke/pokefirered/.local/battle_end01 /Users/blevicki/Documents/poke/pokefirered/.local/battle-end01-external-v2/pokefirered.gba
```

Host/emulator run in separate processes. In the native mGBA Tools → Scripting
console, load the launch-bound scripts once:

```lua
dofile('/Users/blevicki/Documents/poke/pokefirered/.local/battle_end01/run.lua')
dofile('/Users/blevicki/Documents/poke/pokefirered/.local/battle_end01/probe.lua')
```

The Lua listener is nonblocking; hosted roles are replaced by Hold (no-op), and
only the deterministic BATTLE-01 provider runs. `--terminal-delay-test` commits
first terminal, closes the socket, withholds ACK4 seconds, then re-ACKs the exact
duplicate. This is test-only behavior. Normal host ACK is immediate after commit.

```sh
.venv/bin/python tools/battle_end01.py input --label external-v2-continue 'a 16' 'key 1 8 180' 'key 9 0 180' 'key 6 8 30'
```

Then ordinary player-button callback:

```lua
dofile('/Users/blevicki/Documents/poke/pokefirered/.local/battle_end01/player.lua')
```

Test-only source `native/battle_end01/player_path.lua` uses the actual ELF's menu
callback addresses and player-owned moves; finite18000-frame bound, no battle
state/party/flag/RNG writes. Four Growls, Leech Seed until applied, Tackle; naturally
learned Vine Whip takes priority. RNG/idle timing can change success; a legitimate
loss must complete as loss. This is not a guaranteed fastest/balance path.

The callback stops after native outcome plus900 frames. Brock's long text still
needs explicit ordinary inputs; do not restore merely because outcome/prize UI
appeared. Exact actual completion inputs:

```sh
.venv/bin/python tools/battle_end01.py input --label external-v2-finish 'a 14' 'key 9 0 180'
.venv/bin/python tools/battle_end01.py input --label external-v2-return 'a 20' 'key 9 0 240'
.venv/bin/python tools/battle_end01.py capture --label external-v2-terminal
.venv/bin/python tools/battle_end01.py input --label external-v2-gym-script 'a 20' 'key 9 0 120'
.venv/bin/python tools/battle_end01.py input --label victory-field 'key 0 8 60' 'key 7 10 60' 'key 1 8 60' 'key 7 10 60'
.venv/bin/python tools/battle_end01.py save --label victory-paired --resume-save
.venv/bin/python tools/battle_end01.py capture --label victory-paired-final
```

The first Save attempt occurred while still talking to Brock and timed out without
writing a battery. After dismissing dialogue/moving away, the same pending intent
was resumed and completed normally; `victory-save.log` and paired receipts retain
the result. A fresh reproduction in confirmed field state uses `save` without
`--resume-save`. Inspect screenshots before mutation; never arm a second intent
or simulate a native savedataUpdated receipt.

## Actual reload, rollback and abort

Stop **tracked owned PIDs** with SIGTERM; wait for exit before launch. Actual final
victory host/emulator PIDs35917/36291 were stopped. The fresh saved-victory test used:

```sh
.venv/bin/python tools/battle_end01.py launch --restore-save .local/battle_end01/victory-paired.sav > evidence/phase4/battle_end01/launch-victory-reload.log
.venv/bin/python tools/battle_end01.py host > evidence/phase4/battle_end01/host-victory-reload.log
```

Same external-v2 emulator argv above, fresh scripts once; ordinary Continue:

```sh
.venv/bin/python tools/battle_end01.py input --label victory-reload 'a 16' 'key 1 8 180' 'key 9 0 180'
.venv/bin/python tools/battle_end01.py capture --label victory-reload-state
```

PIDs47520/47561 stopped. Fresh pre-Brock `launch` restores the original pair by
default; `pre-brock-restored.json` proves future exclusion. The actual abort run
used normal Continue/Up and player inputs, then stopped the test player callback
and native host/emulator before request5 resolved. Console:

```lua
PI_END_PLAYER.enabled=false
emu:setKeys(0)
```

```sh
.venv/bin/python tools/battle_end01.py capture --label abort-immediate-before
kill -TERM 47660 47698
.venv/bin/python tools/battle_end01.py capture --label abort-after-stop
.venv/bin/python tools/battle_end01.py launch > evidence/phase4/battle_end01/launch-abort-paused.log
.venv/bin/python tools/battle_end01.py capture --label abort-restored
```

The attempted menu-pause helper missed first menu transitions and is not a
qualified pause automation. Actual before/after captures instead prove request5
accepted/emitted/unresolved → CANCELED_RUN_ABORT. No native action is retrospectively
invented. Final post-abort launch was prepared but not emulator-booted; its empty
host PID47921 was stopped. Final active test-copy state is the original clean pair.
Future abandoned obligation rejection and source-bound prominence were checked in
fresh local Python against this actual restored DB, without creating a new job.

Vanilla comparison used `launch --mode vanilla`, `host --mode vanilla` and its
revision1 ROM/script, with ordinary button automation. `launches.jsonl`,
`input-commands.jsonl`, `emulator.jsonl` and `vanilla-result.json` retain the exact
session. The earlier failed player slot3 selection used Tackle rather than intended
Vine Whip; it is a completed **loss**, not victory evidence.

## Checks actually run

```sh
.venv/bin/python tools/battle_end01_c_tests.py > evidence/phase4/battle_end01/native-tests-final.log 2>&1
.venv/bin/python -m unittest tests.test_battle_end01 tests.test_system1_battle tests.test_battle01 -v > evidence/phase4/battle_end01/final-host-tests.log 2>&1
.venv/bin/python -m unittest tests.test_vertical_slice01 tests.test_vertical_slice_closeout tests.test_virality01 -v > evidence/phase4/battle_end01/campaign-regression.log 2>&1
PYTHONPATH=tests .venv/bin/python -m unittest tests.test_virality01 -v > evidence/phase4/battle_end01/virality-regression.log 2>&1
.venv/bin/python tools/battle_end01_verify.py
.venv/bin/python -m py_compile battle/transport.py battle/lifecycle.py campaign/store.py tools/strategy01_host.py tools/battle_end01.py tools/battle_end01_build.py tools/battle_end01_c_tests.py tools/battle_end01_verify.py
```

Host focused23 pass. Campaign invocation passed28 but failed importing virality's
bare `test_world01` dependency; corrected tests-path invocation passed30. C27 plus
pinned controller matrix pass; artifact checker69 pass. Earlier stub-fixture and
helper CLI failures were corrected, not hidden as passing checks. Builder now has
real argparse `--help`; the initial unparsed help invocation refused an existing
build and did not rebuild it.

No full-suite, vanilla-v2 gameplay, arbitrary state-load, power-loss, worst-case
stack, new live AI, recap publication or virality execution is claimed. Original
ledger and private inputs are hash-checked unchanged. Workers/listeners are stopped.
