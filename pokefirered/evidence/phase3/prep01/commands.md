# PREP-01 commands and evidence boundaries

All commands run from `/Users/blevicki/Documents/poke/pokefirered`, using Python3.9.6. No model credentials, cloud inference, ROM upload/download or new ROM build was used. Protected inputs listed in `protected-before.json` remain read-only. Private battery/database/screenshots live under `.local/prep01/` and `evidence/private/prep01/`.

## Host checks

```sh
python3 -m unittest discover -s tests > evidence/phase3/prep01/baseline-host-tests.log 2>&1
python3 -m unittest discover -s tests > evidence/phase3/prep01/host-tests.log 2>&1
python3 tools/prep01_fixture_report.py
python3 tools/prep01_report.py --database .local/prep01/world.sqlite3 --actor trainer:fr:trainer:0102 --out evidence/phase3/prep01/rick-report.json
python3 tools/verify_prep01.py
```

The baseline ran315 tests. Final count/result is in host-tests.log. `doug-fixture-report.json` is an explicitly labeled host scenario, not a native Doug playthrough. The fixture report script creates `PrepTests`, calls eligible(103), uses the production report adapter and tears down its private temporary database; it does not touch the game test database. The verifier reads actual native artifacts and refuses missing/failed acceptance; it does not run or manufacture a game.

## Source compiler layout check

```sh
arm-none-eabi-cpp -I include -I tools/agbcc/include -I tools/agbcc -nostdinc -undef -std=gnu89 -DFIRERED -DENGLISH -DREVISION=0 -DMODERN=0 .local/prep01/layout_probe.c -o .local/prep01/layout_probe.i
 tools/agbcc/bin/agbcc -mthumb-interwork -Wimplicit -Wparentheses -Werror -O2 -fhex-asm .local/prep01/layout_probe.i -o .local/prep01/layout_probe.s
arm-none-eabi-as -mcpu=arm7tdmi .local/prep01/layout_probe.s -o .local/prep01/layout_probe.agbcc.o
arm-none-eabi-objcopy -O binary --only-section=.rodata .local/prep01/layout_probe.agbcc.o .local/prep01/layout_probe.agbcc.bin
```

GNU default EABI's15528-byte SaveBlock1 was **rejected** against the actual accepted ELF serialization. Pinned agbcc and GNU `-mabi=apcs-gnu` agree on15720, offset3808 and288 flag bytes. `save-layout-probe.json` records the results. The probe produces only an object/rodata binary, never a replacement ROM.

## Managed native run

```sh
python3 tools/prep01_launch.py --start --save .local/prep01/pre-boulder.sav > evidence/phase3/prep01/launch-recovery.log
python3 tools/prep01_host.py --seconds 3600 > evidence/phase3/prep01/host-process-recovered-game.log
python3 tools/prep01_route.py PewterCity 15 16 --label prep-gym-return2 > evidence/phase3/prep01/gym-return2.log
python3 tools/prep01_route.py PewterCity_Gym 6 6 --label prep-liam-approach2 > evidence/phase3/prep01/liam-approach2.log
```

The launcher records the exact emulator argv, ROM/script hashes, battery identity, origin and nonce in launches.jsonl. In native mGBA Tools→Scripting→File, load the observed recent `.local/prep01-run.lua`. This UI step uses CUA; a fresh process/Continue is mandatory, and same-process script reload is unsupported. Existing transport listens nonblocking. `prep01_input.py` commands issue native keys, not party/flag writes. Every key/held-frame/rest-frame and screenshot sample is preserved in emulator.jsonl; deliveries.jsonl preserves exact canonical/observation wires.

Source-driven bounded route commands and collision hashes are in `*-route.json`; battles pause the route. Wild encounter RNG and battle damage are real native outcomes, not guaranteed deterministic replay. Reviewed inputs become recorded reproducible segments rather than an asserted universal route.

One initial host-restart attempt during an advancing wild battle lost three records and was suspended. `abandoned-reconnect-attempt.json` records the failure. That entire unsaved attempt was discarded by fresh managed restore of the paired pre-Boulder battery. It is not accepted milestone evidence. The recovered timeline includes an actual first loss to Liam; mandatory offline recap settlement and no preparation grant are retained.

Native Save commands/capture and fresh before/after restore commands are appended below as executed. A Save receipt alone is insufficient: pairings.jsonl must bind the intent, zero-drop drained barrier, incremented counter and PREP checkpoint hash. No mock/fixture milestone substitutes for native Brock victory and the actual flags.

## Executed native checkpoint and Brock run

```sh
python3 tools/prep01_scenario.py save --label prep-before-brock --menu-cursor 0 > evidence/phase3/prep01/save-before-brock.log
python3 tools/prep01_capture.py before
python3 tools/prep01_launch.py --start --save .local/prep01/before-brock.sav > evidence/phase3/prep01/launch-before-brock.log
python3 tools/prep01_host.py --seconds 1800 > evidence/phase3/prep01/host-before-brock.log
python3 tools/prep01_input.py --label prep-before-brock-continue 'a 6' 'key 9 0 240' 'key 0 8 360' 'key 1 8 180' 'a 3' 'key 9 0 180'
python3 tools/prep01_route.py PewterCity_Gym 6 6 --label prep-brock-approach > evidence/phase3/prep01/brock-approach.log
python3 tools/prep01_scenario.py battle --label prep-brock-geodude --steps 30 > evidence/phase3/prep01/brock-geodude.log
python3 tools/prep01_scenario.py battle --label prep-brock-finish --steps 30 > evidence/phase3/prep01/brock-finish.log
```

Task-owned host/emulator processes were stopped between paired launches. The first full native Liam attempt lost, the second won with native Growl/Leech Seed/Tackle/Vine Whip; player level-ups and move learning were native. No trainer development was installed. Battle loops were deliberately paused for inspected transitions. Native input segments, including actual Brock dialogue/Vine Whip and final script settlement, are recorded with exact frame counts in emulator.jsonl. `brock-finish.log` is the confirmed two-turn native win; victory text before BattleEnded was not treated as completion.

## Executed after-Boulder and restore closeout

```sh
python3 tools/prep01_scenario.py save --label prep-after-boulder --menu-cursor 0 > evidence/phase3/prep01/save-after-boulder.log
python3 tools/prep01_capture.py after
python3 tools/prep01_rejections.py
python3 tools/prep01_launch.py --start --save .local/prep01/post-boulder.sav > evidence/phase3/prep01/launch-fresh-after.log
python3 tools/prep01_host.py --seconds 300 > evidence/phase3/prep01/host-fresh-after.log
python3 tools/prep01_input.py --label prep-fresh-after-continue 'a 6' 'key 9 0 240' 'key 0 8 360' 'key 1 8 180' 'a 3' 'key 9 0 180'
python3 tools/prep01_capture.py freshAfter --label prep-fresh-after-continue
python3 tools/prep01_launch.py --start --save .local/prep01/before-brock.sav > evidence/phase3/prep01/launch-restore-before.log
python3 tools/prep01_host.py --seconds 300 > evidence/phase3/prep01/host-restore-before.log
python3 tools/prep01_input.py --label prep-restore-before-continue 'a 6' 'key 9 0 240' 'key 0 8 360' 'key 1 8 180' 'a 3' 'key 9 0 180'
python3 tools/prep01_capture.py beforeRestore --label prep-restore-before-continue
python3 tools/prep01_launch.py --start --save .local/prep01/post-boulder.sav > evidence/phase3/prep01/launch-restore-after.log
python3 tools/prep01_host.py --seconds 300 > evidence/phase3/prep01/host-restore-after.log
python3 tools/prep01_input.py --label prep-restore-after-continue 'a 6' 'key 9 0 240' 'key 0 8 360' 'key 1 8 180' 'a 3' 'key 9 0 180'
python3 tools/prep01_capture.py afterRestore --label prep-restore-after-continue
kill -TERM 38943
kill -TERM 38945
lsof -nP -iTCP:18772 -iTCP:18773 -sTCP:LISTEN
python3 tools/prep01_report.py --database .local/prep01/world.sqlite3 --actor trainer:fr:trainer:0102 --out evidence/phase3/prep01/rick-report.json
python3 tools/verify_prep01.py
```

Fresh launch commands run in separate sessions; before each one, the previous task-owned emulator/host were stopped **at an idle paired checkpoint**. Native script loading uses the observed recent entry in each fresh process. Final SIGTERM PIDs are specific to this run; discover the task's actual PIDs before repeating cleanup. Intentional SIGTERM may make the launcher wrapper report a subprocess termination; this is expected cleanup, not a failed boot. Final lsof exits1 with no listeners. cleanup.json independently audits owned processes and both ports.

Final result:338 host tests/zero skips and30 actual-artifact assertions passed. Native Save13/cursor117 before, Save14/cursor126 after, fresh retrieval, exact canonical before/after prefixes, no future grant on before restore, original grant on after restore, old candidate rejection, preserved stock/lineages and no selection/installation. Native snapshots and all three Continue screenshots were inspected. Doug is explicitly fixture-only. No live model or trainer-preparation installation proof is claimed.
