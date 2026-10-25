# SYSTEM1-01A executed commands and reproduction limits

Working directory `/Users/blevicki/Documents/poke/pokefirered`, Python3.9.6, pinned agbcc/pret from config/phase0.lock.json. Scope is only SYSTEM1-01A. No ROM/saves/credentials uploaded. All live inference stopped after one synthetic smoke and one Rick production call; ledger closed. These live commands refuse duplicate smoke and closed budgets; do not rerun inference for replay.

```sh
python3 -m py_compile system1/*.py tools/system1_01a*.py
python3 -m unittest tests.test_system1_preparation -v
python3 -m unittest tests.test_system1_native -v
python3 -m unittest tests.test_strategy_memo.MemoTests tests.test_prep01.PrepTests -v
python3 -m unittest tests.test_system1_preparation.TransportTests tests.test_strategy_memo.MemoProviderTests -v
python3 tools/system1_01a.py smoke
python3 tools/system1_01a.py select
python3 tools/system1_01a.py commit
python3 tools/system1_01a.py close-budget
python3 tools/system1_01a.py replay
python3 tools/system1_01a_build.py
```

Initial build attempts and native v1/v2 variants remain in logs. Final v3 build was executed exactly:

```sh
python3 - <<'PY'
import sys
sys.path.insert(0, 'tools')
import system1_01a_build as b
b.DEST = b.ROOT / '.local/system1-01a-native-v3'
b.main()
PY
```

The builder refuses an existing ROM. Start from a new isolated output directory to rebuild; accepted baseline remains `.local/pokebook01-enabled`. The final source/ROM/ELF hashes, compiled allocation and exact make arguments are in manifest-native.json/native-build.log. The tool copies accepted project sources/toolchain and bundled upstream multiboot resources, never the user's game dump.

The first host-only commitment required explicit audited preparation continuation, never ordinary restore:

```sh
python3 tools/system1_01a_launch.py --continue-preparation --start
```

One script-generation failure occurred before OS launch. `--retry-unstarted-launch --start` recovered its unused active grant; this command now refuses because actual launches exist. After the initial token mismatch/socket-budget failure, both owned processes were stopped and a fresh nonce/launch used. **Load generated `.local/system1_01a/run.lua` through native Tools→Scripting→File→Load recent script before starting the host** so it reads the same final token/config:

```sh
python3 tools/system1_01a_host.py
python3 tools/system1_01a_input.py 'a 6' 'key 9 0 360' 'shot v3-menu'
# Verify CONTINUE visibly before the next input; then skip the native quest-log replay.
python3 tools/system1_01a_input.py 'key 0 8 360' 'key 1 8 180' 'shot v3-field'
python3 tools/system1_01a_input.py 'prepared' 'key 9 0 360' 'shot installed-battle-start'
python3 tools/system1_01a_verify_party.py
python3 tools/system1_01a_input.py 'a 30' 'a 30' 'a 30' 'key 9 0 180' 'shot installed-battle-complete'
```

Individual input commands return queue ACKs, not gameplay completion. Inspect screenshot/frame log and settled queue. The normal-save scenario wrapper waits for actual screenshot receipts and native savedataUpdated/SQLite pairing. The v3 party-observation probe initially omitted gEnemyParty from the launch manifest; actual constructor count1 was read from ELF-derived gPiPreparation, then the read-only capture was rerun with ELF-derived enemy address33701932. The launcher now resolves that named symbol itself. No party bytes were written by the emulator.

```sh
python3 tools/system1_01a_scenario.py save lock-save18 0
# Stop both owned mGBA/host processes before subsequent launches.
python3 tools/system1_01a_launch.py --start
# Load generated script, start host, review Continue→field, then actual constructor proof.
```

Save18 is the first normal paired commitment checkpoint after the failed v2 installation. Final post-installation save/reload commands and fingerprints are reported in completion.json/pairings.jsonl. Older-save branch tests operate only on isolated database/battery copies. Preserve normal restore: no host continuation exception after native history advances. Replay reads recorded choices and never reads credentials or calls the model.

Initial fixture branch test missed a fresh managed nonce, then exposed branch-prefix initialization ordering; both were corrected and the complete host suite rerun. The native validator test now checks all16 choices in both immutable ready/installing packet phases plus corrupted/wrong-tag rejection. Fixture/native-host tests are not emulator evidence; actual constructor observation/battle/normal saves are recorded separately.


Final executed normal save and fresh process reload:

```sh
python3 tools/system1_01a_scenario.py save installed-save19 0
# Save barrier refused early attempts while the native battle was still settling;
# final successful command is save19-command-accepted.txt, paired normal counter19.
# Stop task-owned host/mGBA, then launch ordinary paired restore:
python3 tools/system1_01a_launch.py --start
# Native UI: Tools → Scripting → File → Load recent → .local/system1_01a/run.lua
python3 tools/system1_01a_host.py
python3 tools/system1_01a_input.py 'a 6' 'key 9 0 360' 'shot save19-menu'
# Inspect actual CONTINUE menu screenshot before proceeding.
python3 tools/system1_01a_input.py 'key 0 8 360' 'key 1 8 180' 'shot save19-field'
# First field image was Quest Log playback, not final saved position.
python3 tools/system1_01a_input.py 'key 1 8 360' 'shot save19-field-confirmed'
python3 tools/system1_01a_input.py sample
# Actual persist: counter19, Gym mapgroup6/mapnum2, x6/y7, battle0/turn0, no drops.
# Stop only the two identified task processes (this run: host29832, mGBA29491).
kill -TERM 29832 29491
python3 tools/system1_01a_audit.py
python3 -m py_compile system1/*.py tools/system1_01a*.py
```

The audit creates/overwrites only .local/system1_01a/restore-audit.sqlite3 from a SQLite backup, then restores the actual checksum-valid Save17/18/19 fixtures against their paired checkpoints. It never rewinds the final working database or calls a model. Its source flag expression check follows TRAINER_FLAGS_START=(FLAG_0x4FF+1) rather than guessing a numeric define. Final artifact-checks.json passed37 assertions; tests from the four final logs count57 unique cases (provider retests include2 repeats),0 skips. A fresh audit after documentation/cleanup passes without credentials or running services.

Final native ROM SHA256 1b60bd038c4b8d4e9fff6999573113dde05f06090a4435e2e616cc2b5637c924; ELF64c77739025534705da0c0d7253e77c3d4714686e4fb4d900a37e7757918d4e3. Actual final Save19 checkpoint a4ed907e-dc44-46e7-a786-63aba2350fc0, cursor162, fingerprint255f14d39ac15b0ea0478cc0f9f8264aa61458b43a9a17e089a6548ea2445315. Original Save17 and user dump remain untouched. Native initialization clears the temporary mailbox on fresh launch; durable installation evidence is retrieved from the paired host receipt, not inferred from an idle native opponent buffer. No additional battle was triggered for the reload proof.
