# STRATEGY-01 explicit backup/contingency qualification — actual commands

Working directory `/Users/blevicki/Documents/poke/pokefirered`, Python3.9.6. User attachment10abf04a… authorizes backup qualification/live acceptance capped5 requests. Latest typed message additionally names Qwen and openrouter/free just-in-case. Treat them as individually selected contingencies within the same aggregate5, never an automatic model chain or Nemotron retry. `.env` remains untouched. It currently supplies Inkling-small and OPENROUTER_API_KEY; Qwen/router assignments were absent and their exact user-provided identifiers were retained as temporary test metadata.

Public metadata only: `public_get('https://openrouter.ai/api/v1/models')` and exact `/api/v1/models/{model}/endpoints` for all three named selectors. Results in models-preflight.json. Inkling-small: zero price/healthy endpoint, tools advertised but `tool_choice` missing and endpoint supports_tool_choice allfalse. Qwen: zero price/healthy ModelRun/function-tools. Router: cannot pass current free exact-model/function-tool endpoint gate. No model request for Inkling/router/Nemotron.

Focused offline pre-live test, exit0,50 tests/0 skips:

```sh
python3 -m unittest tests.test_strategy01 tests.test_strategy01_provider tests.test_strategy01_backup.BackupConfigurationTests tests.test_strategy01_backup.BackupContextTests.test_provider_selection_leaves_model_context_identical > evidence/phase3/strategy01/backup/focused-before-live.log 2>&1
```

Separate private campaign copy, standard SQLite backup API:

```python
with sqlite3.connect('.local/strategy01/world.sqlite3') as old, sqlite3.connect('.local/strategy01-backup/world.sqlite3') as new:
    old.backup(new)
shutil.copy2('.local/strategy01/after-strategy.sav', '.local/strategy01-backup/before-strategy.sav')
with LiveBudget('.local/strategy01-backup/live-budget.json', 5) as budget:
    budget.write(budget.read())
```

Fresh native before-only acceptance harness:

```sh
POKEINFLUENCER_STRATEGY_BACKUP_ACCEPTANCE=1 python3 tools/strategy01_launch.py --start --save .local/strategy01-backup/before-strategy.sav > evidence/phase3/strategy01/backup/native-launch-console.log 2>&1
POKEINFLUENCER_STRATEGY_BACKUP_ACCEPTANCE=1 python3 tools/strategy01_host.py --seconds 1800 > evidence/phase3/strategy01/backup/host-console.log 2>&1
POKEINFLUENCER_STRATEGY_BACKUP_ACCEPTANCE=1 python3 tools/strategy01_scenario.py continue --label backup-before > evidence/phase3/strategy01/backup/continue-before.log 2>&1
```

Actual mGBA0.10.5 GUI: Tools > Scripting > File > Load script; Go to Folder `.local/strategy01-backup/run.lua`; selected Open. First Go to Folder hotkey occurred before the file dialog was ready; repeated after observed ready dialog, then successful script-load/HELLO. Fresh actual Save16 Continue inputs `a 6`, `key 9 0 240`, `key 0 8 360`, `key 1 8 180`, `key 9 0 180`, `shot backup-before`. Frame3236 at field6,7 map6,2; screenshot `evidence/private/strategy01-backup/backup-before.png` visually checked. No battle, no after-live normal Save.

Read-only native opponent party/count capture from inspected source/accepted ELF, before and after attempted generation. No player-party data enters this diagnostic/model input, no memory writes:

```sh
python3 tools/strategy01_party_probe.py before
python3 tools/strategy01_party_probe.py after --compare > evidence/phase3/strategy01/backup/native-party-command.lua.txt
```

Printed Lua is executed in the observed native scripting text field and Run button. Equivalent actual Lua opens private `.local/strategy01-backup/native-party-{before,after}.bin`, writes `emu:read8(33701930)` for count plus600 bytes at `33701932+i`, closes file and logs read-only proof. Before frame8328/after36108;601 bytes equal. Symbol addresses/sizes derive from `arm-none-eabi-nm -S --defined-only .local/pokebook01-enabled/pokefirered.elf`; gEnemyParty600/count1/gTrainers29720. No installed team is claimed; idle field RAM comparison and whole unchanged-ROM hash are non-mutation evidence.

First explicit Qwen launch, exit1 **before any POST/job**:

```sh
POKEINFLUENCER_STRATEGY_MODEL_BACKUP_BACKUP='qwen/qwen3.8-27b:free' python3 tools/strategy01_backup.py --model-role backup_backup
```

Retained generation-preflight-credential.log: old configured credential name OPENROUTER_KEY did not match current `.env` OPENROUTER_API_KEY. Add allowlisted host-only alias; do not modify/key-print `.env`. Pre-live regressions, exit0,28 tests:

```sh
python3 -m unittest tests.test_strategy01_backup.BackupConfigurationTests tests.test_strategy01_provider > evidence/phase3/strategy01/backup/configuration-alias-before-live.log 2>&1
```

Actual live execution, exit0 explicitly returning deterministic fallback:

```sh
POKEINFLUENCER_STRATEGY_MODEL_BACKUP_BACKUP='qwen/qwen3.8-27b:free' python3 tools/strategy01_backup.py --model-role backup_backup > evidence/phase3/strategy01/backup/generation.log 2>&1
```

Exactly3 POSTs, one logical job, actual adapterv5. ModelInput equals retained primary packet byte-for-byte; request hashes unchanged across attempts; no models array. HTTP400→429→429; no accepted tool output, model/provider identity or usage/cost receipt. V5 retained status/latency but not HTTP response bodies; first400 cause and specific429 period are unknown, not backfilled. Budget closed3/5. No more calls after post-run improvements.

Post-run v6 targeted changes: bounded redacted HTTP error-body diagnostic and stop400/429 unchanged retries. First targeted30-test run had one bodyless mocked HTTPError failure (`KeyError: file`), retained focused-after.log. Guarded reader corrected; rerun exit0,30 tests:

```sh
python3 -m unittest tests.test_strategy01_provider tests.test_strategy01_backup.BackupConfigurationTests tests.test_strategy01.StrategyTests.test_client_and_rate_errors_stop_without_rapid_retry > evidence/phase3/strategy01/backup/focused-after-final.log 2>&1
python3 -m unittest tests.test_strategy01_backup > evidence/phase3/strategy01/backup/configuration-final.log 2>&1
```

Final backup suite11 tests, exit0. Test fixture class no longer inherits/re-discovers the entire Strategy suite.53 unique focused cases across the scoped runs; historical372 full suite retained, not rerun. V6 made0 live calls.

Read-only authenticated `GET https://openrouter.ai/api/v1/key` (official documented route) returned200. Allowlisted private quota diagnostics contain no credential/label/userID; public key-quota-metadata.json records that deprecated rate_limit metadata does not establish specific429 cause/period. This was0 model calls; no account/key/payment modification.

Cleanup/fresh offline replay, exit0:

```sh
python3 tools/strategy01_cleanup.py > evidence/phase3/strategy01/backup/process-cleanup.json
POKEINFLUENCER_STRATEGY_BACKUP_ACCEPTANCE=1 python3 tools/strategy01.py replay --out evidence/phase3/strategy01/backup/fresh-runtime-fallback-replay.json > evidence/phase3/strategy01/backup/replay-console.log
```

SQLite backup retains attempted.sqlite3; `StrategyStore.restore(save_identity('.local/strategy01-backup/before-strategy.sav'))` returns to known paired-before16, excludes attempted fallback and rejects its old grant. Fresh replay0 inference. This proves fallback-only host replay/restore; no live posture exists for after-live native persistence acceptance. Current services/listeners/jobs/pendingSave absent; hosted default false. Prior77 evidence/config/database/save/ROM/dump/budget files unchanged;244 original protected foundation artifacts rechecked unchanged.

Final evidence assertions:

```sh
python3 tools/verify_strategy01_backup.py
```

34 actual-artifact assertions, exit0. Scoped AST/JSON/whitespace checks recorded separately. No ROM rebuild, proprietary upload, team/resource changes, Hermes/System One inference or later phase. Endgame deferred.
