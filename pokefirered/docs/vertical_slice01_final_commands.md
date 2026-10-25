# Final live closeout execution record

Run from `/Users/blevicki/Documents/poke/pokefirered`. These are historical executed commands, not permission to reopen the closed hosted experiment. The original66-request prefix was backed up, `CampaignBudget.authorize_final_closeout()` invoked once, and its explicit authorization/hash recorded in `requests.json`. Final cap150: +80 battle/+4 Hermes, no new Strategy/preparation.

## Managed live attempts

For each clean restore (launch logs `final-launch-attempt1/2/3/4.log`):

```sh
.venv/bin/python tools/vertical_slice01_launch.py --manifest evidence/phase4/battle_end01/manifest-external.json --restore .local/vertical_slice01/closeout-gym-ready.sav
.venv/bin/python tools/vertical_slice01_host.py --manifest evidence/phase4/battle_end01/manifest-external.json --live --gym-closeout --continue-authorized-run --seconds 3600
.local/mGBA.app/Contents/MacOS/mGBA -C hwaccelVideo=0 -C savegamePath=/Users/blevicki/Documents/poke/pokefirered/.local/vertical_slice01 /Users/blevicki/Documents/poke/pokefirered/.local/battle-end01-external-v2/pokefirered.gba
```

The exact native input commands/timestamps are append-only `input-commands.jsonl`, exported by segment in `final-native-path.json`. mGBA Tools→Scripting loaded the bridge once per fresh process:

```lua
assert(loadfile('/Users/blevicki/Documents/poke/pokefirered/.local/vertical_slice01/run.lua'))()
```

Reviewed normal Continue used the ordinary `a 6`, wait240frames, `a 2`, wait240frames and quest-replay skip/advance inputs captured in the path. Fresh titles were visually inspected; early title sequences and a blocked route were not counted as completed milestones. Attempts1/2 were actual losses, with seven/six hosted choices. Setup3 entered Liam dialogue and was abandoned without a battle/inference; setup4 used the east aisle and won.

The winning ordinary Mart/Gym walking uses `tools/vertical_slice01_route.py`'s pinned source-collision route, with verified `reached` checks at Gym(10,6)→(10,11)→exit, Mart(4,3), then Gym(10,11)→(10,6)→Brock(6,6). All directions are native buttons. Native shop selected Potion, bought one, then nine at quantity×09/₽2,700, confirmed Yes; the shop showed ₽140. Read-only actual SaveBlock diagnostics confirmed item13 quantity10. The verified map/source offsets are retained in symbol/resource evidence.

Player input automation loaded only after returning to Brock:

```lua
assert(loadfile('/Users/blevicki/Documents/poke/pokefirered/.local/vertical_slice01/final-player.lua'))()
```

`final-player.lua` is generated from `tools/vertical_slice01_player.lua` and actual ELF symbols. It supplies ordinary buttons, not a model or game-memory writes. Native static names are not unique: the reviewed player ChooseAction is0x0802E4BC, ChooseMove0x0802EA94, from:

```sh
arm-none-eabi-nm -an .local/battle-end01-external-v2/pokefirered.elf
```

The initial symbol ambiguity/pause correction is recorded in emulator events; the move-menu guard is the reliable reviewed low-HP stop. Automatic inputs were paused, Bag opened through Right/A, Potion selected→Use→Bulbasaur→A, healing12/29→29/29. Screenshots confirm×10 before consumption. Input resumed; natural level-up taught Vine Whip. No game HP/party/item/flag write or RNG control was used. Live workers were stopped after the first winning result; no subsequent live battle occurred.

## Native UI and normal Save

```sh
.venv/bin/python tools/vertical_slice01_capture.py final-published
.venv/bin/python tools/vertical_slice01_viewer.py CLOSEOUT --menu-cursor 0 --label final-viewer
.venv/bin/python tools/vertical_slice01_scenario.py save --label final-success --menu-cursor 7
.venv/bin/python tools/vertical_slice01_scenario.py save --label final-success-resume --menu-cursor 7 --resume-intent
.venv/bin/python tools/vertical_slice01_capture.py final-success --battery
```

The first viewer navigation was before field and its artifacts were renamed `final-viewer-misrun-*`; native screenshots from the later run are the accepted UI proof. The first Save navigation exited an already-open Start menu and timed out; it did not save. The same pending intent was resumed from actual field and paired successfully, counter13/checkpoint `b67c97e6-46b4-410f-87c3-6a1ebb696fa0`. The helper now sends a third B on viewer exit to close Start. Native progression and valid battery data—not a mocked save callback—prove Boulder and TM39.

Owned live host55786 and emulator55830 were stopped by `kill -TERM` after the completed paired save. The runtime cleanup guard rejected a relative target; the reviewed absolute owned home succeeded:

```sh
.venv/bin/python scripts/clean_hermes_runtime.py /Users/blevicki/Documents/poke/pokefirered/.runtime/hermes/jobs/f9f20ab8-87d4-4f8d-98f0-9711ee3cbb21 --delete
```

## Fresh offline reload, UI, prefix isolation and durable retrieval

```sh
.venv/bin/python tools/vertical_slice01_launch.py --manifest evidence/phase4/battle_end01/manifest-external.json --restore .local/vertical_slice01/final-success.sav
.venv/bin/python tools/vertical_slice01_host.py --manifest evidence/phase4/battle_end01/manifest-external.json --gym-closeout --seconds 3600
.local/mGBA.app/Contents/MacOS/mGBA -C hwaccelVideo=0 -C savegamePath=/Users/blevicki/Documents/poke/pokefirered/.local/vertical_slice01 /Users/blevicki/Documents/poke/pokefirered/.local/battle-end01-external-v2/pokefirered.gba
.venv/bin/python tools/vertical_slice01_input.py --label final-restored-native-continue 'a 6' 'key 9 0 240' 'a 2' 'key 9 0 240' 'key 1 20 360' 'key 9 0 360'
.venv/bin/python tools/vertical_slice01_capture.py final-restored-success
.venv/bin/python tools/vertical_slice01_viewer.py CLOSEOUT --menu-cursor 0 --label final-restored-viewer
```

The Lua bridge was manually loaded once in this fresh process. No live option was supplied. Seven hashes, memo, decisions, audit and lifecycle matched exactly; native restored posts/followers were inspected. Host58214/emulator58266 were then stopped by `kill -TERM`. The remaining checks are host+battery restoration, not an additional claimed emulator playthrough:

```sh
.venv/bin/python tools/vertical_slice01_launch.py --manifest evidence/phase4/battle_end01/manifest-external.json --restore .local/vertical_slice01/closeout-gym-ready.sav
.venv/bin/python tools/vertical_slice01_capture.py final-restored-prefix
.venv/bin/python tools/vertical_slice01_launch.py --manifest evidence/phase4/battle_end01/manifest-external.json --restore .local/vertical_slice01/final-success.sav
.venv/bin/python tools/vertical_slice01_capture.py final-current-clean
.venv/bin/python tools/vertical_slice01_recall.py --closeout --label final
```

The fresh pinned Hermes process uses explicitly mocked model transport/0POST and actual restored durable Brock memory. Its owned home is cleaned within the recall helper. All inference workers and port18782 listeners are absent; normal configuration remains disabled.

## Evidence/check commands

```sh
.venv/bin/python tools/vertical_slice01_final_account.py
.venv/bin/python tools/vertical_slice01_final_trace.py
.venv/bin/python tools/verify_vertical_slice01_final.py
.venv/bin/python -m unittest tests.test_final_closeout_budget tests.test_vertical_slice_closeout tests.test_battle_end01
```

Results: actual18 gates+five integrity checks;26 focused host tests/0 skips (resource warnings preserved);33 new Mercury/two Hermes/0 Strategy/preparation,101 aggregate, actual new cost0. The initial verifier incorrectly required reason0 for a sole engine replacement; actual unchanged source3/reason4 and the next fair snapshot establish the explicitly allowed sole-action bypass. This was a verifier classification correction, not an engine/fallback change.

No ROM rebuild/new gameplay phase or full New Game replay was run. Preserve earlier accepted evidence and the final winning battery. The final ledger is closed; replay should remain offline unless a new explicit scope is authorized.
