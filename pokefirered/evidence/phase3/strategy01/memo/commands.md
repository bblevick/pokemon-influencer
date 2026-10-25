# StrategyMemo D32 commands

Working directory: `/Users/blevicki/Documents/poke/pokefirered`.
Python: system `python3` (3.9.6). Private dump/save/database and credentials are not uploaded.

```sh
python3 -m py_compile strategy/provider.py strategy/memo.py strategy/store.py tools/strategy01.py tools/strategy_memo01.py
python3 -m unittest tests.test_strategy_memo tests.test_strategy01 tests.test_strategy01_provider tests.test_strategy01_backup
python3 -m unittest tests.test_strategy_memo
python3 -m unittest tests.test_strategy_memo.MemoProviderTests
POKEINFLUENCER_STRATEGY_MEMO_ACCEPTANCE=1 python3 tools/strategy_memo01.py replay
python3 tools/strategy_memo01.py smoke
```

Initial broad run imported the legacy ProviderTests class through the memo test module, duplicating its19 cases. The final memo module imports that fixture as a module instead. Logs retain actual counts; unique counts exclude duplicates. The broad historical tests are scoped Strategy/PREP-context checks, not a rerun of the previous full372-test host suite. Temporary SQLite backup used Python sqlite3.Connection.backup into `.local/strategy01-memo/world.sqlite3`; original remained untouched. Protected artifact snapshot is `protected-before.json`.

The fresh two-request window permits one smoke and one production request, no retries/automatic model chain. A failed smoke prevents production and native after-live acceptance; those steps must remain explicitly unrun. No prior ledger is reopened.

Native acceptance commands (all harness commands below set `POKEINFLUENCER_STRATEGY_MEMO_ACCEPTANCE=1`; reviewed Lua load through mGBA native Tools → Scripting → File → Load script/recent `.local/strategy01-memo/run.lua`):

```sh
python3 tools/strategy01_launch.py --start --save .local/strategy01/after-strategy.sav
python3 tools/strategy01_host.py
python3 tools/strategy01_scenario.py continue --label memo-before-continue
python3 tools/strategy01_party_probe.py before --memo
python3 tools/strategy_memo01.py generate
python3 tools/strategy01_scenario.py save --label memo-live-save --menu-cursor 0
python3 tools/strategy01_party_probe.py after --memo
python3 tools/strategy01_party_probe.py after --memo --compare
python3 tools/strategy01_cleanup.py
python3 tools/strategy_memo01.py replay
python3 tools/strategy01_launch.py --start --save .local/strategy01-memo/after-live-memo.sav
python3 tools/strategy01_host.py
python3 tools/strategy01_scenario.py continue --label memo-after-continue
python3 tools/strategy_memo01.py replay
python3 tools/strategy01_cleanup.py
python3 tools/strategy01_launch.py --start --save .local/strategy01/after-strategy.sav
python3 tools/strategy01_host.py
python3 tools/strategy01_scenario.py continue --label memo-rewind-continue
python3 tools/strategy_memo01.py replay
python3 tools/strategy01_cleanup.py
python3 tools/strategy01_launch.py --start --save .local/strategy01-memo/after-live-memo.sav
python3 tools/strategy01_host.py
python3 tools/strategy01_scenario.py continue --label memo-return-continue
python3 tools/strategy_memo01.py replay
python3 tools/strategy01_cleanup.py
python3 tools/strategy_memo01.py close-budget
python3 tools/strategy_memo01.py replay
```

Both party-probe generated commands were inspected and executed in the native scripting console with setValue/Run. They only read ELF-derived opponent-party/count bytes into ignored private audit files. Save17 was copied using shutil.copy2 after task mGBA stopped. SQLite native rewind proof called finish_memo with the prior exact job/context and received stale_strategy_job; it wrote no result.

`memo-return-continue.png` showed title, so it is excluded as a successful field Continue. Final corrected fresh Save17 launch and host were repeated, followed by these observed-state commands:

```sh
python3 tools/strategy01_input.py --label memo-reviewed-start 'key 9 0 1'
python3 tools/strategy01_input.py --label memo-reviewed-menu 'key 0 8 90'
python3 tools/strategy01_input.py --label memo-reviewed-start-button 'key 3 8 120'
python3 tools/strategy01_input.py --label memo-reviewed-final-field 'key 0 8 360' 'key 1 8 180' 'key 9 0 180'
python3 tools/strategy_memo01.py replay
python3 tools/strategy01_cleanup.py
python3 tools/strategy_memo01.py replay
python3 tools/strategy_memo01_audit.py
```

The A-only reviewed-menu image still showed title. Start produced the visible Continue screen, then A/B produced the verified field screenshot. `continue-title` encodes those reviewed Start/A/B components; the combined wrapper has not separately been run. Final image inspection used view_image on actual emulator-created screenshot files. Final audited logs record exact pairing/model/cost/budget hashes, no mock native steps.
