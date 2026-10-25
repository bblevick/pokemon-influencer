# VERTICAL-SLICE-01 retained commands

Run from `/Users/blevicki/Documents/poke/pokefirered`. Evidence paths are relative
to that repository. These commands describe the actual bounded run and checkpoint
regressions; they are not permission to launch later campaign phases or a new
30-request allowance. Normal host execution is offline.

## Build and independently run checks

```sh
.venv/bin/python tools/vertical_slice01_build.py
.venv/bin/python tools/battle01_c_tests.py --manifest evidence/phase4/vertical_slice01/manifest-native.json
.venv/bin/python -m unittest tests.test_vertical_slice01 tests.test_system1_preparation tests.test_strategy_memo tests.test_system1_battle -v
.venv/bin/python -m unittest tests.test_vertical_slice01 -v
PYTHONPATH=tests .venv/bin/python -m unittest test_virality01 test_pokebook01 -v
PYTHONPATH=tests .venv/bin/python -m unittest test_strategy01_provider test_strategy_memo -v
.venv/bin/python -m py_compile campaign/*.py tools/vertical_slice01_*.py tools/verify_vertical_slice01.py
.venv/bin/python tools/verify_vertical_slice01.py
.venv/bin/python tools/vertical_slice01_golden.py
```

The build intentionally refuses to overwrite an existing isolated build. Retain
that directory/manifest as the reproducibility artifact; do not erase it merely
to rerun this command. The artifact checker reports `liveAcceptance:false` even
when its26 evidence checks pass. Old verifier/import failures remain in their
original logs; corrected successful logs have separate filenames.

## Actual managed launch and main campaign

Initial import and S0 used these commands. The seed command refuses an existing
campaign/database, and must not be used to reset a charged request ledger.

```sh
.venv/bin/python tools/vertical_slice01_launch.py --seed .local/hermes01/S1.sav
.venv/bin/python tools/vertical_slice01_host.py --seconds 1800
.venv/bin/python tools/vertical_slice01_scenario.py save --label s0 --menu-cursor 0
```

Each launch requires the actual mGBA scripting window: Tools → Scripting, enter
this exact Lua command and press Run. The console must show `build-validated`
with the pinned ROM hash and `listening` on127.0.0.1:18782 before native input.

```lua
dofile('/Users/blevicki/Documents/poke/pokefirered/.local/vertical_slice01/run.lua')
```

The clean main run restored S0 after a credential-alias trial that made zero
hosted POSTs. Accepted inputs and all trial/recovery inputs are preserved exactly
in `input-commands.jsonl` and exported native segments in `golden-path.json`.
Native repeated A is `a N` (N presses), not N held frames. `key K H R` is native
button K held H frames then released R frames. Button IDs:0A,1B,3Start,4Right,
5Left,6Up,7Down;9 with hold0 supplies released frames. Screenshots follow each
segment. These inputs never write canonical history, HP, parties or inventory.

```sh
.venv/bin/python tools/vertical_slice01_launch.py --restore .local/vertical_slice01/S0.sav --start
.venv/bin/python tools/vertical_slice01_host.py --live --seconds 3000
.venv/bin/python tools/vertical_slice01_input.py --label clean-s0-field 'a 16' 'key 1 8 180' 'key 9 0 180'
.venv/bin/python tools/vertical_slice01_scenario.py battle --label clean-rick
.venv/bin/python tools/vertical_slice01_scenario.py save --label s1 --menu-cursor 0
.venv/bin/python tools/vertical_slice01_scenario.py save --label s2 --menu-cursor 7
```

Rick's ordinary entry/facing inputs precede `battle`; that helper requires a
real active native battle and does not fabricate a trainer encounter. S1 was
paired before automatic Strategy scheduling; S2 retained the immutable fallback
memo and commitment. Feed inputs were native Start-menu/navigation over actual
social projections.

Travel uses `vertical_slice01_route.py MAP X Y --label LABEL`, bounded
source-collision walking that stops on map changes or actual battles. The25
`*-route.json` files retain actual map/position/steps; `golden-path.json` preserves
the exact344 native segments from clean S0 through the post-Gym reader. Wild
encounters and damage vary, so this is not a blind successful replay claim.
Active wild battles used the bounded native escape helper; Sammy was fought
through the ordinary encounter, loss/blackout and later win. No outcome was
required or overridden. The host time window expired while traveling; continuation
preserved the original ledger and all charges:

```sh
.venv/bin/python tools/vertical_slice01_scenario.py escape --label forest-escape-final
.venv/bin/python tools/vertical_slice01_scenario.py battle --label sammy-retry
.venv/bin/python tools/vertical_slice01_host.py --live --continue-authorized-run --seconds 1800
.venv/bin/python tools/vertical_slice01_route.py PewterCity_Gym 8 13 --label gym-east-aisle
.venv/bin/python tools/vertical_slice01_route.py PewterCity_Gym 8 6 --label gym-brock-aisle
.venv/bin/python tools/vertical_slice01_route.py PewterCity_Gym 6 6 --label gym-brock-facing
```

The native doorway route and ordinary Brock dialogue precede those Gym inputs;
actual dialogue/move menu actions are retained in native segments, not a parallel
scripted battle. Player chose Vine Whip via the native menu. Mercury chose the
opponent actions. After the normal badge/TM script, an early Save attempt was
still in dialogue and timed out without writing a save. Field input settled it;
**the same pending save intent** then completed normally:

```sh
.venv/bin/python tools/vertical_slice01_scenario.py save --label s3-recovered --menu-cursor 0 --resume-intent
```

Do not recreate that pending-intent command outside the compatible recorded
state: the helper verifies nonce/branch/cursor/old fingerprint before resuming.

## Fast native checkpoint regression

Stop only this task's host/emulator before replacing the active battery. For
stage S0, S1, S2 or S3, restore its ignored local normal save with this pattern:

```sh
.venv/bin/python tools/vertical_slice01_launch.py --restore .local/vertical_slice01/S3.sav --start
.venv/bin/python tools/vertical_slice01_host.py --seconds 1200
.venv/bin/python tools/vertical_slice01_input.py --label restore-s3-field 'a 16' 'key 1 8 180' 'key 9 0 180'
.venv/bin/python tools/vertical_slice01_verify.py S3
.venv/bin/python tools/vertical_slice01_viewer.py S3 --menu-cursor 0
```

Load the pinned Lua via the scripting window before those native inputs. `verify`
is specific to this recorded campaign's actual IDs, not a fabricated generic
scenario. `viewer` requires ordinary field/paired save and the explicit current
Start cursor; it asserts all seven history hashes and exact ledger immutability.
All four fresh restores ran; the combined retained viewer helper ran on S3.
Native screenshots show restored Rick, Brock and actual Followers. S0 divergence
was an actual Rick battle start, not a manually appended event.

With no host/worker active, after S3 restore:

```sh
.venv/bin/python tools/vertical_slice01_recall.py
```

This launches the actual pinned Hermes process but uses explicitly mocked model
transport. It retrieves the real durable Brock episode and cleans up its own
runtime home. It makes zero hosted POSTs and verifies all-layer immutability.
It is not live inference acceptance. Its original actual live recap source and
cleanup remain separately evidenced.

Final state: S3 paired battery/history retained; no task-owned worker/listener/
emulator running; ledger closed at9, hosted default disabled. New Game/starter,
post-Brock preparation and follower rematch are not implemented by these commands.


## Current live-memo closeout and offline completion (2026-10-05)

These are the actual continuation commands, not a new authorization. The request
ledger is now closed/exhausted30, so the live continuation command must refuse
another run. Rebalances were performed only while the same ledger was closed,
through `CampaignBudget.rebalance_closeout()` then, after20 charges,
`reallocate_remaining_to_tactics()`. All prior charges were preserved. Their
exact from/to/count/time receipts are in requests.json. No budget reset occurred.

```sh
.venv/bin/python tools/vertical_slice01_launch.py --restore .local/vertical_slice01/S1.sav --start
.venv/bin/python tools/vertical_slice01_host.py --live --continue-authorized-run --seconds 1800
.venv/bin/python tools/vertical_slice01_scenario.py save --label closeout-r1 --menu-cursor 0
.venv/bin/python tools/vertical_slice01_capture.py closeout-r1 --battery
.venv/bin/python tools/vertical_slice01_scenario.py save --label closeout-r2 --menu-cursor 4
.venv/bin/python tools/vertical_slice01_capture.py closeout-r2 --battery
.venv/bin/python tools/vertical_slice01_scenario.py save --label closeout-gym-ready --menu-cursor 4
.venv/bin/python tools/vertical_slice01_capture.py closeout-gym-ready --battery
```

Commands between these saves, including source-collision travel, battle move
inputs, ordinary PC healing and actual Brock dialogue, are retained exactly in
input-commands.jsonl and closeout-native-path.json (each frame hold/release and
screenshot label). Actual selections/native events are closeout-turn-trace.json.
The detailed capture for r1 is later than its Save; its fresh restore correctly
contains no future memo. No restore receipt is synthesized from the late snapshot.

After turn19 fallback/player loss and actual Hermes completion, only the tracked
live host81760 was terminated. The ledger closed30. The offline host finished
normal blackout dialogue; verified PC field precedes the normal final save:

```sh
.venv/bin/python tools/vertical_slice01_host.py --seconds 1200
.venv/bin/python tools/vertical_slice01_input.py --label closeout-pc-cancel 'key 1 8 180' 'key 1 8 180' 'key 7 8 120'
.venv/bin/python tools/vertical_slice01_scenario.py save --label closeout-final --menu-cursor 4
.venv/bin/python tools/vertical_slice01_capture.py closeout-final --battery
.venv/bin/python tools/vertical_slice01_viewer.py CLOSEOUT --menu-cursor 4
```

The immediately preceding A/dialogue attempts are also retained; extra A could
re-enter the nurse prompt and was not blindly followed by Save. Each input
segment waited for its actual queued screenshot. The battery helper refuses
overwriting any retained battery. Tool initialization was through the actual
mGBA Tools/Scripting window and the validated Lua command given above.

Fresh normal launch/Continue was run for each of closeout-r1, closeout-gym-ready
and closeout-final with offline hosts and fresh emulator sessions. Between
restores, terminate only the tracked task host/emulator, never unrelated apps.
Example exact final sequence (replace battery/label for the earlier stages):

```sh
.venv/bin/python tools/vertical_slice01_launch.py --restore .local/vertical_slice01/closeout-final.sav --start
.venv/bin/python tools/vertical_slice01_host.py --seconds 1200
.venv/bin/python tools/vertical_slice01_input.py --label closeout-restore-final-continue 'a 16' 'key 1 8 180' 'key 9 0 180'
.venv/bin/python tools/vertical_slice01_capture.py closeout-restored-final
```

The actual Hermes runtime home was cleaned with
`puppeteer.runtime.cleanup(audit['runtimeHome'], dry_run=False)` after its grant
and owned worker settled. Paths/ownership checks/results are
closeout-hermes-cleanup.json. With the campaign host stopped, a fresh pinned
Hermes process retrieved real restored durable episodes using mock transport:

```sh
.venv/bin/python tools/vertical_slice01_recall.py --closeout
```

It proves retrieval/branch/actor scope, not live inference. Its temporary home
was also cleaned through the strict helper. A further fresh final launch and
Continue used label closeout-restored-viewer-continue, then:

```sh
.venv/bin/python tools/vertical_slice01_viewer.py CLOSEOUT --menu-cursor 0 --label closeout-restored-viewer
.venv/bin/python -m unittest tests.test_vertical_slice01 -v
.venv/bin/python tools/vertical_slice01_receipts.py
.venv/bin/python tools/vertical_slice01_closeout_trace.py
.venv/bin/python tools/verify_vertical_slice01_closeout.py
.venv/bin/python -m py_compile campaign/budget.py tools/vertical_slice01_capture.py tools/vertical_slice01_viewer.py tools/vertical_slice01_recall.py tools/vertical_slice01_receipts.py tools/vertical_slice01_closeout_trace.py tools/verify_vertical_slice01_closeout.py tests/test_vertical_slice01.py
```

Focused test log: closeout-final-focused-tests.log,14 tests/0 skips/exit0.
Final artifact check:28 checks/exit0/**accepted:false**. It explicitly checks
the actual loss/no flags and missing fully-live gate, not a waived win criterion.
Receipt reconciliation adds no request, matches exact attempt/hash/job and leaves
existing outcomes immutable; prior9 rows are unchanged. Original verifier expects
the old9-attempt scenario and is historical, not the current checker.

Native input bound720 was rejected (maximum600); the earlier accepted commands
and error remain logged. An intermediate verifier initially assumed a win and
all-live decisions; it was corrected to the actual loss/fallback. Its receipt
lookup also needed to account for nested System One usage and unresolved Hermes
ledger outcomes already backed by completed audits. Native terminal duplicate
counts from managed restarts were corrected to complete request identities.
These corrections alter evidence interpretation, not native history/model output.

Final tracked hosts/listeners/emulator are stopped, actual runtime homes cleaned,
configured hosted default remains false, and all30 charges persist. See
closeout-final-cleanup.json. More hosted work requires explicit additional
bounded authorization; no such increase has been made.

## Additional-allowance gate (D37; closed, not permission to run more inference)

Current results: docs/vertical_slice01_gate.md. All paths below are repository
relative. One-time host authorization was invoked through
`CampaignBudget(LEDGER).authorize_gym_closeout()` after copying requests.json to
requests-original30.json. It does not itself reopen the ledger. Explicit live
Gym hosts used `--live --gym-closeout --continue-authorized-run`; they were stopped
between restores, and final shutdown closed the ledger. Each fresh emulator used
the exact argv, origin, nonce and script hash in gate-prebattle-launch.log and
gate-attempt{2,3,4}-launch.log. The native argv was:

```sh
.local/mGBA.app/Contents/MacOS/mGBA -C hwaccelVideo=0 -C savegamePath=/Users/blevicki/Documents/poke/pokefirered/.local/vertical_slice01 /Users/blevicki/Documents/poke/pokefirered/.local/vertical-slice01-native/pokefirered.gba
```

Each attempt restored the same normal paired battery through
`tools/vertical_slice01_launch.py --restore .local/vertical_slice01/closeout-gym-ready.sav`,
then fresh native script load and Continue. Input-driver exact command/argument
arrays are retained in gate-native-path.json (57 segments); raw acknowledgements
are in input-commands.jsonl. They can be replayed through vertical_slice01_input.py
against the specified milestone, but are not a qualified blind winning script.
No current replay is authorized to reopen hosted inference. No saved state or
forced outcome was substituted. Screenshot-specific observations are private.

Actual final offline commands (exit0):

```sh
.venv/bin/python tools/vertical_slice01_receipts.py
.venv/bin/python tools/vertical_slice01_launch.py --restore .local/vertical_slice01/closeout-gym-ready.sav
.venv/bin/python tools/vertical_slice01_capture.py gate-final-clean
.venv/bin/python -m unittest tests.test_vertical_slice_closeout.AdditionalAllowanceTests tests.test_vertical_slice_closeout.CleanRestoreTests.test_gym_closeout_scheduler_cannot_generate_missing_strategy tests.test_vertical_slice_closeout.ScopeTests tests.test_system1_battle -v
.venv/bin/python tools/verify_vertical_slice01_gate.py
.venv/bin/python -m py_compile campaign/budget.py campaign/runtime.py campaign/provider.py battle/transport.py tools/vertical_slice01_host.py tools/vertical_slice01_worker.py tools/verify_vertical_slice01_gate.py tests/test_vertical_slice_closeout.py
```

The receipt tool made0 requests and settled36 returned usage records; the output
was copied to gate-receipt-reconciliation.json. Newly run focused tests:9/0 skips,
0.506s. The final actual checker:78 checks, accepted:false. Its initial completed-
loss assertion failed and exposed the reporting error; a later audit-artifact
serialization Row error was corrected to dict without changing stored facts.
Final restore matched seven hashes and separately the checkpoint tactical-audit
cutoff. No successful post-victory save/reload was run. Current completion.json
supersedes completion-before-gate.json; prior failures and successes remain
inspectable. No build/full historical test suite was rerun in this window.
