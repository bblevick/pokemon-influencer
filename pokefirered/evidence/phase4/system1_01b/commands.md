# Actual SYSTEM1-01B commands and evidence

Working directory `/Users/blevicki/Documents/poke/pokefirered`; Python3.9.6, pinned mGBA0.10.5. All game/save files stayed local. `.env` values were read only through the existing credential allowlist; no key is in a command. No new ROM build/download occurred.

```sh
python3 tools/system1_01b_preflight.py --smoke
python3 -X importtime -c 'import system1.provider' 2> evidence/phase4/system1_01b/worker-import-time.log
# After unchanged helper extraction:
python3 -X importtime -c 'import system1.provider' 2> evidence/phase4/system1_01b/worker-import-time-corrected.log
python3 -m unittest tests.test_system1_battle tests.test_battle01 tests.test_system1_preparation.TransportTests tests.test_strategy_memo.MemoProviderTests -v
python3 -m unittest tests.test_battle01 tests.test_system1_native tests.test_strategy_memo -v
python3 tools/system1_01b_launch.py --start
python3 tools/system1_01b_host.py shadow
```

The existing private working DB was SQLite-backed up from the accepted BATTLE-01 DB; initial battery copied from `.local/system1_01a/installed-save19.sav`. `authorize_launch` restored the actual paired save. Each fresh launch used the same reviewed native ROM and exact locked plan. In mGBA Tools→Scripting, CUA entered and ran:

```lua
dofile('/Users/blevicki/Documents/poke/pokefirered/.local/system1_01b/run.lua')
```

The first trial had a hard worker deadline; reconnect after stopping the host exposed a canonical gap and suspended the world. Another restart sent `prepared` before the queued title/Continue inputs finished; it never installed or made a model call. Both are excluded. Exact full input commands/receipts are `input-commands.jsonl` and `emulator.jsonl`; launches are `launches.jsonl`. Latch reopening records are in the same `requests.json`, preserving every charge; no duplicate turn inference.

Complete real shadow715026728 sequence (separate command completion receipts checked before dependent actions):

```sh
python3 tools/system1_01b_input.py 'a 20' 'key 9 0 360' 'shot shadow-field-ready'
python3 tools/system1_01b_input.py 'prepared' 'key 9 0 360' 'a 12' 'shot shadow-live-turn1'
python3 tools/system1_01b_input.py 'a 4' 'shot shadow-next-menu'
python3 tools/system1_01b_input.py 'a 3' 'shot shadow-menu2'
python3 tools/system1_01b_input.py 'a 2' 'shot shadow-menu3'
python3 tools/system1_01b_input.py 'a 3' 'shot shadow-caterpie'
python3 tools/system1_01b_scenario.py
python3 tools/system1_01b_input.py 'key 1 8 60' 'key 1 8 60' 'shot shadow-post-field'
python3 tools/system1_01b_save.py
```

The scenario confirmed actual canonical BATTLE_ENDED, not screenshot/queue ACK. Normal Save20 produced a validated checkpoint. The battery was copied locally to `.local/system1_01b/completed-shadow-save20.sav`; `persistence-before.json` records the actual pair/replay/audit state. Owned host/mGBA were stopped, then fresh launcher/host/script as above (budget remained closed):

```sh
python3 tools/system1_01b_input.py 'a 20' 'key 9 0 360' 'shot shadow-save20-reload'
python3 tools/verify_system1_01b.py
python3 -m unittest tests.test_system1_battle tests.test_system1_preparation.TransportTests tests.test_strategy_memo.MemoProviderTests -v
```

`fresh-reload.json` compares exact pair/memo/commitment/replay/audit/request count. The verifier also restores Save19 in an isolated temporary DB to prove future shadow audit/recap exclusion. Source tests are mocks/compiled fixtures where labeled; only the recorded shadow was a real emulator battle. This narrower first shadow was not promoted; its first-verification/persistence reports remain preserved. A later fresh shadow was qualified before enabled, as recorded below. Final cleanup uses SIGINT for owned host and SIGTERM for owned mGBA; `cleanup.json` verifies no remaining task workers/listener and default hosted disabled.


Final passing qualification after reviewing the unchanged native180-frame window:

```sh
python3 -m unittest tests.test_system1_battle tests.test_battle01 -v
python3 tools/system1_01b_launch.py --restore .local/system1_01a/installed-save19.sav --start
python3 tools/system1_01b_host.py shadow
# Load run.lua through mGBA Tools→Scripting, as above.
python3 tools/system1_01b_input.py 'a 20' 'key 9 0 360' 'shot shadow-wide-field'
python3 tools/system1_01b_input.py 'prepared' 'key 9 0 360' 'a 12' 'shot shadow-wide-turn1'
python3 tools/system1_01b_scenario.py
```

Actual complete shadow1660475733 had4 valid unexecuted proposals,0 errors. `shadow-accepted.json` verified complete canonical battle, native-only receipts, exact submitted-state hashes, legal distributions, exact memo, zero stock and latency before enabled. All earlier charges remain in the SAME ledger. Native ROM/180-frame guards unchanged; host default2.5s preserved, explicit live wrapper2.75s; child2.55/HTTP2.35s. No old resolved decision was retried.

After stopping that owned host/emulator and restoring paired Save19 again:

```sh
python3 tools/system1_01b_launch.py --restore .local/system1_01a/installed-save19.sav --start
python3 tools/system1_01b_host.py enabled
# Load run.lua through mGBA Tools→Scripting.
python3 tools/system1_01b_input.py 'a 20' 'key 9 0 360' 'shot enabled-field'
python3 tools/system1_01b_input.py 'prepared' 'key 9 0 360' 'a 12' 'shot enabled-turn1'
python3 tools/system1_01b_scenario.py
python3 tools/system1_01b_input.py 'key 1 8 60' 'key 1 8 60' 'shot enabled-post-field'
python3 tools/system1_01b_save.py
python3 tools/system1_01b_persistence.py before
```

Canonical enabled3468328694 ended normally. SAME ledger closed at13, no further POSTs. Normal paired Save20 produced the actual checkpoint; local `completed-enabled-save20.sav` preserved. Stop host/emulator, fresh launch/host (shadow transport with closed ledger; no preparation arm or battle):

```sh
python3 tools/system1_01b_launch.py --start
python3 tools/system1_01b_host.py shadow
# Load run.lua; ordinary fresh Continue only.
python3 tools/system1_01b_input.py 'a 20' 'key 9 0 360' 'shot enabled-save20-reload'
python3 tools/system1_01b_persistence.py after
python3 tools/verify_system1_01b.py
python3 -m unittest tests.test_system1_battle tests.test_system1_preparation.TransportTests tests.test_strategy_memo.MemoProviderTests -v
```

Private constructor bytes/checksum/species/levels/moves/full initial PP/personality match D33. Selected turn3/4 String Shot never announces because faster player Tackle faints the actor; no success/hit claim is made. Full input receipts, chronological model/native/canonical audit and mode sessions are retained. The attempted model-profile descriptive-label edit triggered stored identity mismatch and was reverted before game/model calls; configured profile bytes remain unchanged. Final owned PIDs87913(host)/87902(mGBA) received SIGINT/SIGTERM, then process/listener/default/closed-ledger audit `cleanup.json` passed. No emulator worker remains running.
