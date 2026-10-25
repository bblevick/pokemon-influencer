# Gate repair commands and evidence

Run from `/Users/blevicki/Documents/poke/pokefirered`. No hosted generation.
The setup backed up C1 with SQLite's backup API and hashed protected source artifacts;
`protected.json` contains paths/hashes without credentials. A single public metadata
qualification called `strategy.provider.preflight_text` and saved
`current-strategy-route.json`; neither metadata GET used an inference endpoint.

## Repeatable host/source proofs

```sh
.venv/bin/python tools/campaign_expansion01_gate_preflight.py
.venv/bin/python tools/campaign_expansion01_gate_analysis.py
.venv/bin/python -m unittest discover -s tests -p 'test_campaign_gate_*.py'
.venv/bin/python tools/battle01_c_tests.py --manifest evidence/phase6/campaign_expansion01/manifest-native.json
make -C .local/campaign-expansion01-native -j4
.venv/bin/python tools/campaign_expansion01_gate_timing_verify.py
.venv/bin/python tools/verify_campaign_expansion01_gate_repair.py
```

The timing verifier reads the retained abandoned SQLite branch after cleanup.
It does not start a battle, make a request, or accept campaign expansion.

137 relevant regression tests ran with this exact invocation:

```sh
.venv/bin/python - <<'PY'
import unittest
patterns=['test_campaign_expansion01.py','test_strategy01_provider.py','test_strategy_memo.py','test_battle01.py','test_battle_end01.py','test_system1_battle.py','test_world01.py','test_hermes01.py','test_pokebook01.py']
s=unittest.TestSuite(unittest.defaultTestLoader.discover('tests',pattern=p) for p in patterns)
r=unittest.TextTestRunner(verbosity=1).run(s)
raise SystemExit(not r.wasSuccessful())
PY
```

Battle regressions were rerun after final transport/lifecycle guards:

```sh
.venv/bin/python - <<'PY'
import unittest
s=unittest.TestSuite(unittest.defaultTestLoader.discover('tests',pattern=p) for p in ['test_campaign_gate_repair.py','test_battle01.py','test_battle_end01.py','test_system1_battle.py'])
r=unittest.TextTestRunner().run(s)
raise SystemExit(not r.wasSuccessful())
PY
```

The latter35-test run predates only the extra diagnostic test; final focused17-test
run covers that addition. Counts are unique17+137=154, not summed repeated runs.

## Fresh native C1 viewer / pending save

The isolated gate database was seeded once from original C1; the launcher refuses
an unpaired battery or a running emulator. This does not change original campaign
artifacts. The gate wrapper rejects `--live` and continuation authorization flags.

```sh
.venv/bin/python tools/campaign_expansion01_gate_native.py launch --restore .local/campaign_expansion01/C1-sally-recovered.sav
.venv/bin/python tools/campaign_expansion01_gate_native.py host --seconds 1200
.local/mGBA.app/Contents/MacOS/mGBA -C hwaccelVideo=0 -C savegamePath=/Users/blevicki/Documents/poke/pokefirered/.local/campaign_expansion01_gate_repair /Users/blevicki/Documents/poke/pokefirered/.local/campaign-expansion01-native/pokefirered.gba
```

Load the generated `run.lua` using mGBA's native Scripting console. Actual load:

```lua
dofile('/Users/blevicki/Documents/poke/pokefirered/.local/campaign_expansion01_gate_repair/run.lua')
```

Continue was observed visually between the title/menu/field steps:

```sh
.venv/bin/python tools/campaign_expansion01_gate_native.py input --label gate2-continue 'key 3 30 120' 'key 0 8 360' 'key 1 8 180' 'a 6' 'key 1 8 180'
.venv/bin/python tools/campaign_expansion01_gate_native.py input --label gate2-field 'key 0 12 360' 'key 1 8 180' 'key 9 0 360'
.venv/bin/python tools/campaign_expansion01_gate_native.py input --label gate2-menu 'key 3 8 120'
.venv/bin/python tools/campaign_expansion01_gate_native.py input --label gate2-armed-field 'key 1 8 60'
```

The successful test armed `begin_save` through the existing service API in the
ordinary field, recorded `pending-native-intent2.json`, stopped its tracked host
PID with SIGINT and started a new host process. Native Save then used:

```sh
.venv/bin/python tools/campaign_expansion01_gate_native.py host --seconds 600
.venv/bin/python tools/campaign_expansion01_gate_native.py save --label gate2-save --menu-cursor 0 --resume-intent
```

The menu must be closed before this helper, and its cursor must be visually
confirmed. The retained first trial used an already-open menu/cursor7 and failed;
its transcript is not a successful save sequence. No ambiguous file-exists pairing.

After stopping the emulator/host, the real counter16 pair was launched through
normal Continue with the same two-step title/field sequence. Actual proof:
`native-pending-save-proof.json`, `save16-fresh-projections.json`, native screenshots
`gate3-continue.png` / `gate3-field.png`. Test pair is separate from original C1.

## Actual five-case emulator timing trial

Fresh isolated C1 was restored again. The hosted roles were replaced by no-generation
services; the only decision provider was a bounded deterministic test provider.

```sh
.venv/bin/python tools/campaign_expansion01_gate_native.py launch --restore .local/campaign_expansion01/C1-sally-recovered.sav
.venv/bin/python tools/campaign_expansion01_gate_timing.py --case matrix
```

Launch mGBA/load generated Lua as above; visually reviewed normal Continue:

```sh
.venv/bin/python tools/campaign_expansion01_gate_native.py input --label timing-continue 'key 3 30 120' 'key 0 8 360' 'key 1 8 180' 'a 6' 'key 1 8 180'
.venv/bin/python tools/campaign_expansion01_gate_native.py input --label timing-field 'key 0 12 360' 'key 1 8 180' 'key 9 0 360'
.venv/bin/python tools/campaign_expansion01_gate_native.py input --label timing-greg-intro 'key 7 1 30' 'a 4' 'key 9 0 360'
.venv/bin/python tools/campaign_expansion01_gate_native.py input --label timing-fight-menu 'a 6' 'key 9 0 360'
.venv/bin/python tools/campaign_expansion01_gate_native.py input --label timing-player-moves 'key 0 8 60'
.venv/bin/python tools/campaign_expansion01_gate_native.py input --label timing-turn1-growl 'key 4 8 30' 'key 0 8 120' 'a 4' 'key 9 0 360'
.venv/bin/python tools/campaign_expansion01_gate_native.py input --label timing-turn2 'a 4' 'key 9 0 360'
.venv/bin/python tools/campaign_expansion01_gate_native.py input --label timing-turn3 'a 4' 'key 9 0 360'
.venv/bin/python tools/campaign_expansion01_gate_native.py input --label timing-turn4 'a 4' 'key 9 0 360'
.venv/bin/python tools/campaign_expansion01_gate_native.py input --label timing-turn5 'a 4' 'key 9 0 360'
.venv/bin/python tools/campaign_expansion01_gate_native.py input --label timing-final-effect 'a 1' 'key 9 0 360'
.venv/bin/python tools/campaign_expansion01_gate_timing_verify.py
```

Do not continue the battle. Actual scoped providers were1/2.65/2.85/4 seconds and
never-returning. All five legal player actions were Growl45; this deliberately
avoided completing a future campaign encounter. Verify actual receipts, not queued
key count. Stop tracked host/emulator PIDs, retain a SQLite backup of the test branch,
then restore original C1 through the normal store API and copy its original battery.
`post-timing-C1-restored.json` proves all seven projections returned and all former
launches are inactive. The fake never-returning worker is released on shutdown;
no HTTP session, live ledger or user history is resumed.

Early incorrect `press` input commands were rejected; the protocol uses `key`.
All failed commands remain in input/console evidence. No such attempt is a passed
acceptance step.

## Historical-evidence closeout (D42)

Current local request proof uses the retained zero-price metadata snapshot, no GET
or POST. It does not imply future provider availability. New actual adapter tests
mock all HTTP; isolated real SQLite memo commit and fresh Python process reload
retain six categories. No campaign fixture or original historical artifact is edited.

```sh
.venv/bin/python tools/campaign_expansion01_gate_preflight.py
.venv/bin/python -m unittest discover -s tests -p 'test_campaign_gate_*.py'
.venv/bin/python tools/campaign_expansion01_content.py
.venv/bin/python tools/battle01_c_tests.py --manifest evidence/phase6/campaign_expansion01/manifest-native.json
make -C .local/campaign-expansion01-native -j4
.venv/bin/python tools/campaign_expansion01_historical_closeout.py
.venv/bin/python tools/verify_campaign_expansion01_gate_repair.py
```

The unchanged137-test regression invocation above was rerun after production
instrumentation changes. Closeout logs are `closeout-{gate-tests,regression-tests,
native-tests,native-build}.log`;19+137=156 unique tests,0 skips. Initial six-case
test passed with an unclosed test log warning; corrected context-managed test sink
then passed without warnings. A later rerun adds a fresh process reader for each
case. No diagnostic test creates an actual completed campaign battle.

`greg-historical-incident.json` records the exact retained artifact list and hashes,
primary trace, surviving class/fallback and missing fields. Verifier asserts those
hashes, original protected hashes, diagnostics/fresh-process proofs, all test logs,
closed ledger, retained native/save proofs, unchanged RAM and no owned workers.
Historical source artifacts remain unchanged. Final readiness JSON copies exact
original C1 checkpoint/battery/projection identities and states generation permission
false. The recommendation does not open an authorization ledger.
