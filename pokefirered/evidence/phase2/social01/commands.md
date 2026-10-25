# SOCIAL-01 commands actually executed

Working directory: `/Users/blevicki/Documents/poke/pokefirered`. Python: `.venv/bin/python`3.13.12. All commands below exited0 except the explicitly recorded battle bound. CLI snapshots/replay tools are trusted administrative inspection, not NPC tools.

Setup (separate new social database; accepted WORLD/MEMORY databases preserved):
```sh
.venv/bin/python tools/social01.py import --save .local/memory01/S1.sav --output evidence/phase2/social01/import.json
.venv/bin/python tools/social01.py activate --output evidence/phase2/social01/activation.json
.venv/bin/python tools/social01_launch.py --start --save .local/memory01/S1.sav
.venv/bin/python tools/social01.py activate --output evidence/phase2/social01/live-activation.json
.venv/bin/python tools/social01_host.py --seconds 1800
```
The first activation preceded restoration of the imported social0 checkpoint and was correctly rewound. The second activation created a social-only child atworld0 inheriting social0. It is the accepted live graph; the dormant root records are retained. The launcher is long-running until native Quit. First launch nonce2882539620/origin23afeae9-a866-40a5-800f-8d55dc163f2e; all actual argv/nonces/origins/save fingerprints are in `launches.jsonl`.

Native script load was performed once per fresh process via mGBA Tools→Scripting→File→Load script (first chooser) or the observed File→Load recent script→exact `.local/social01-run.lua` item (later processes). No savestate, arbitrary script reload, RAM battle intervention or synchronous Lua socket connect was used.

First launch/native battle:
```sh
.venv/bin/python tools/social01_input.py --label fresh-continue 'a 4' 'key 9 0 180'
.venv/bin/python tools/social01_input.py --label fresh-field 'key 0 10 150' 'key 1 10 500'
.venv/bin/python tools/social01_scenario.py save --label social-s1 --menu-cursor 0 > evidence/phase2/social01/S1-checkpoint.json
cp .local/social01/pokefirered.sav .local/social01/S1.sav
.venv/bin/python tools/social01_input.py --label rick-intro 'key 6 16 300' 'a 3' 'key 9 0 300'
.venv/bin/python tools/social01_scenario.py battle --label social-rick --steps 40 > evidence/phase2/social01/rick-battle.log
.venv/bin/python tools/social01_scenario.py battle --label social-rick-end --steps 20 > evidence/phase2/social01/rick-end.log
```
The40-step run exited1 at its explicit bound, at the inspected native Rick-victory dialogue, before canonical end emission. After inspection the20-step continuation exited0 after3segments,8turns. Bound failure and screenshots are retained, not counted as a complete battle. `input-commands.jsonl` and `emulator.jsonl` record commands/completion/frame evidence. Normal-save helper stdout includes input status before checkpoint JSON (the `.json` filename of S1 output does not imply pure JSON).

Lifecycle/checkpoints/restart:
```sh
.venv/bin/python tools/social01.py snapshot --output evidence/phase2/social01/publication-live.json
.venv/bin/python tools/social01.py tick --tick 1 --output evidence/phase2/social01/feed-unread.json
.venv/bin/python tools/social01_scenario.py save --label social-s2 --menu-cursor 4 > evidence/phase2/social01/S2-checkpoint.log
cp .local/social01/pokefirered.sav .local/social01/S2.sav
.venv/bin/python tools/social01.py expose --output evidence/phase2/social01/exposure-live.json
.venv/bin/python tools/social01_scenario.py save --label social-s3 --menu-cursor 4 > evidence/phase2/social01/S3-checkpoint.log
cp .local/social01/pokefirered.sav .local/social01/S3.sav
kill -TERM 4952
.venv/bin/python tools/social01.py snapshot --output evidence/phase2/social01/host-reopen.json
.venv/bin/python tools/social01.py retry --output evidence/phase2/social01/idempotent-retry.json
.venv/bin/python tools/social01_host.py --seconds 1800
```
Clean host restarts use recorded SIGTERM PIDs and a single flock writer; actual open/hello/close records are in host.jsonl. mGBA was native Quit before each battery copy/restore; launcher refuses a running task-local mGBA.

Fresh S2 launch/unread restore/social-only branch:
```sh
kill -TERM 6513
.venv/bin/python tools/social01_launch.py --start --save .local/social01/S2.sav > evidence/phase2/social01/S2-launch.log
.venv/bin/python tools/social01_host.py --seconds 1800
.venv/bin/python tools/social01_input.py --label s2-continue 'a 4' 'key 9 0 180'
.venv/bin/python tools/social01_input.py --label s2-field 'key 0 10 150' 'key 1 10 500'
.venv/bin/python tools/social01.py snapshot --output evidence/phase2/social01/restored-s2-unread.json
.venv/bin/python tools/social01.py expose --output evidence/phase2/social01/social-only-divergence.json
```
Native Continue and field screenshots were inspected. No new ROM gameplay record occurred; only exposure creates branchB atworld27.

Fresh S1 launch/empty future tick:
```sh
kill -TERM 6647
.venv/bin/python tools/social01_launch.py --start --save .local/social01/S1.sav > evidence/phase2/social01/S1-restore-launch.log
.venv/bin/python tools/social01_host.py --seconds 1800
.venv/bin/python tools/social01_input.py --label s1-restore-continue 'a 4' 'key 9 0 180'
.venv/bin/python tools/social01_input.py --label s1-restored-field 'key 0 10 150' 'key 1 10 500'
.venv/bin/python tools/social01.py snapshot --output evidence/phase2/social01/restored-s1.json
.venv/bin/python tools/social01.py tick --tick 1 --output evidence/phase2/social01/s1-divergent-empty-tick.json
```
Native Continue and pre-Rick field screenshots inspected. Empty tick forksC atworld0, with no future jobs/posts/knowledge.

Original later checkpoint positive restore:
```sh
kill -TERM 6849
.venv/bin/python tools/social01_launch.py --start --save .local/social01/S3.sav > evidence/phase2/social01/S3-positive-launch.log
.venv/bin/python tools/social01_host.py --seconds 1800
.venv/bin/python tools/social01_input.py --label s3-positive-continue 'a 4' 'key 9 0 180'
.venv/bin/python tools/social01_input.py --label s3-positive-field 'key 0 10 150' 'key 1 10 500'
.venv/bin/python tools/social01.py snapshot --output evidence/phase2/social01/s3-positive-reload.json
kill -TERM 7067
```
Native post-Rick field inspected; original A/exposure/receipts restored unchanged. Native Quit precedes final host stop. No test processes/listeners remain.

Verification (all0):
```sh
.venv/bin/python -m unittest discover -s tests -p test_social01.py -q
.venv/bin/python tools/social_species_catalog.py
.venv/bin/python tools/social01_regression.py > evidence/phase2/social01/final-regression-run.log 2>&1
.venv/bin/python tools/social01_audit.py --output evidence/phase2/social01/branch-audit.json
.venv/bin/python tools/verify_social01.py > evidence/phase2/social01/verify-run.log
.venv/bin/python tools/social01_replay.py --database .local/social01/world.sqlite3 --export evidence/phase2/social01/final-fixture.json > evidence/phase2/social01/final-replay-snapshot.json
.venv/bin/python tools/social01_replay.py --fixture evidence/phase2/social01/final-fixture.json > evidence/phase2/social01/final-offline-replay.json
```
The same replay export/import commands were executed with exposure-* and divergent-* evidence paths at those active views. Regression results contain exact compiler/build-verifier/retained-check argv and logs.184combined host tests (145prior+39SOCIAL);63actual-C sanitizer cases; audited unchanged existing ARM builds/disabled baseline;43architecture/60handoff+9fixtures; retained12/27/53/144/63/117 earlier live assertions.96SOCIAL evidence assertions inspect this new live run. Unit fault injection is not a live emulator fault or physical power-loss test.
