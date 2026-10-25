# Commands and evidence classification

Working directory: `/Users/blevicki/Documents/poke/pokefirered`; Python3.9.6. No ROM/save uploads or downloads, no new ROM build. Offline default/model profiles unchanged. All actual inputs recorded in input-commands.jsonl; callback/fsync/save pairings in save-receipts.jsonl/pairings.jsonl/host.jsonl. Failed commands are retained, not counted as passed evidence.

Baseline: `python3 -m unittest discover -s tests` →338 tests/OK (`baseline-tests.log`).
Implemented checks: `python3 -m unittest tests.test_strategy01 tests.test_strategy01_provider` →28 then34 tests/OK after corrections (`focused-tests.log`, `focused-tests-final.log`).
Full host suite: `python3 -m unittest discover -s tests` →369 then372 tests/OK (`host-tests*.log`, final `host-tests-closeout.log`).
Final changed transport checks: `python3 -m unittest tests.test_strategy01_provider tests.test_strategy01.StrategyTests.test_three_invalid_attempts_fallback tests.test_strategy01.StrategyTests.test_provider_timeout_fallback tests.test_strategy01.StrategyTests.test_deadline_prevents_attempt` →18/OK (`transport-closeout-tests.log`).
The latter run includes two new malformed-root/usage and hard-limit cases after the372-test run. Do not call it a374-test full-suite run.

Setup made a SQLite backup of `.local/prep01/world.sqlite3` into `.local/strategy01/world.sqlite3`; the accepted original remained protected. Native batteries copied only into private task paths. No accepted foundation DB was upgraded.

Public metadata GETs (no key) used urllib with bounded reads/timeouts:
`https://openrouter.ai/api/v1/models`
`https://openrouter.ai/api/v1/models/nvidia/nemotron-3.5-lightning:free/endpoints`
Catalog/endpoints-preflight, route-recheck and live/final-live-preflight JSON files record unavailable→qualified route metadata. Official documentation inspected for tools/provider routing/endpoint listing. Model configuration/key were privately read only through the allowlist; neither .env nor key was printed.

Explicit model commands:
```sh
python3 tools/strategy01.py context --out evidence/phase3/strategy01/rick-context.json
python3 tools/strategy01.py preflight --out evidence/phase3/strategy01/live-preflight.json
python3 tools/strategy01.py generate --live --out evidence/phase3/strategy01/rick-result.json
python3 tools/strategy01.py preflight --out evidence/phase3/strategy01/final-live-preflight.json
python3 tools/strategy01.py generate --live --purpose preparation-live-acceptance --out evidence/phase3/strategy01/rick-live-result.json
python3 tools/strategy01.py generate --live --purpose preparation-live-acceptance --out evidence/phase3/strategy01/rick-live-v2-result.json
python3 tools/strategy01.py generate --live --purpose preparation-live-acceptance --out evidence/phase3/strategy01/rick-live-v3-result.json
python3 tools/strategy01.py generate --live --purpose preparation-live-acceptance --out evidence/phase3/strategy01/rick-live-v4-result.json
python3 tools/strategy01.py close-budget
```
Initial blocked command made0 POSTs; versioned acceptance jobs charged3+3+1+3=10. All results fallback. Three diagnosed upstream502 envelopes are in closed-budget.json. First7 rejected responses lack equivalent error diagnostics. No valid live posture/token-usage receipt and no extra role/model/paid route. The budget is now closed; these commands are history, not renewed live permission.

Native launch and Save (unchanged accepted ROM):
```sh
python3 tools/strategy01_launch.py --start --save .local/prep01/post-boulder.sav
python3 tools/strategy01_host.py --seconds 1800
# Native Tools > Scripting > File > Load .local/strategy01-run.lua.
python3 tools/strategy01_input.py --label initial-continue 'a 6' 'key 9 0 240' 'key 0 8 360' 'key 1 8 180' 'a 3' 'key 9 0 180'
```
That initial finalA3 re-entered Brock's ordinary4-page post-battle dialogue. An unsupported `b 4` command was rejected without mutation. A premature Save attempt had no callback and timed out; its pending intent remained visible. Source text was inspected,4 explicit A8/rest90 presses settled dialogue, then Down16/rest60 and Start8/rest30 reached the visibly confirmed native menu (`settle-brock-precisely.png`). No trainer battle was started.
```sh
python3 tools/strategy01_input.py --label verified-field 'key 1 8 60'
python3 tools/strategy01_scenario.py save --label verified-strategy-save --menu-cursor 0 --resume-intent
python3 tools/strategy01_host.py --seconds 300
python3 tools/strategy01_input.py --label close-confirmed-menu 'key 1 8 60'
python3 tools/strategy01_scenario.py save --label final-fallback-save --menu-cursor 4
python3 tools/strategy01_host.py --seconds 3600
```
Host deadlines had expired around Save attempts; existing complete native receipts/pending intents were recovered by a same-origin idle host restart. Save15 then16 actually wrote and paired. At second recovery the old15 receipt was correctly rejected against the pending16 barrier; the actual16 receipt paired. These command timeouts are not successful live-host continuous-run claims. Native callbacks have counter15/16, ACK=eventCounter=0, depth/drops0.

Fresh native paired restores:
```sh
python3 tools/strategy01_cleanup.py
python3 tools/strategy01_launch.py --start --save .local/prep01/post-boulder.sav
python3 tools/strategy01_host.py --seconds 3600
# Native script load via observed recent .local/strategy01-run.lua.
python3 tools/strategy01_input.py --label restore-before-strategy 'a 6' 'key 9 0 240' 'key 0 8 360' 'key 1 8 180' 'key 9 0 180'
python3 tools/strategy01.py replay --out evidence/phase3/strategy01/before-native-continue.json
python3 tools/strategy01_cleanup.py
python3 tools/strategy01_launch.py --start --save .local/strategy01/after-strategy.sav
python3 tools/strategy01_host.py --seconds 3600
# Native script load through same observed recent menu entry.
python3 tools/strategy01_input.py --label restore-after-strategy 'a 6' 'key 9 0 240' 'key 0 8 360' 'key 1 8 180' 'key 9 0 180'
python3 tools/strategy01.py replay --out evidence/phase3/strategy01/after-native-continue.json
python3 tools/strategy01_cleanup.py
python3 tools/strategy01.py replay --out evidence/phase3/strategy01/post-cleanup-replay.json
```
Before restore:0 active records; after:5 identical fallback records/current revalidation bindings, no new requests. Screenshots are under evidence/private/strategy01 (ignored). Stable Continue sequence is now `strategy01_scenario.py continue --label LABEL`. Cleanup stops task-local host/emulator only and deletes no data. An earlier ad-hoc stop helper also terminated its own shell before launch; the subsequent explicit launch succeeded, and the reusable cleanup helper excludes shells.

Privacy/Gym: actual retained Janice exposure has only Rick-loss/Bulbasaur reports; scoped mock posture is validated without Tackle. A separate controlled host fixture records pre-exposure empty evidence→explicit exposure→only published claims (`janice-exposure-transition-fixture.json`). Brock's retained actual pre-Brock Save13 is queried offline (`brock-offline.json`), with source partners/signature/theme/support0; no new native Brock battle. Future support1 is explicitly a test fixture, never a permission grant.
