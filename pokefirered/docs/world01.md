# WORLD-01 implementation and acceptance

Completed **WORLD-01 only**,2026-10-02. A durable deterministic host world now records canonical gameplay facts and supports managed paired **normal in-game saves**. Canonical truth, bounded observations and future NPC knowledge remain different layers. Nothing in this ticket implements remembering, embarrassment, friendship, following, reputation, Hermes, PokeBook, roster adaptation, provider inference, battle control or endgame.

Final ROM remains the accepted BRIDGE-03 ROM:
`739bd3eebb91aaa5210f8f8cd1f357a8272dc98db7060356c649b4c38a0dbc2d`.
Every recorded overlay source checksum matches; no C/ROM/RAM feature changes were made.224 EWRAM bytes remain. The supplied dump SHA256 remains `3d0c79f1627022e18765766f6cb5ea067f6b5bf7dca115552189ad65a5c3a8ac`. ROMs/saves/database/screenshots stay ignored/local; no ROM, save or .env was uploaded. No credential, inference, network request or model configuration change was used.

SQLite is the host authority because its serialized transactions, durable commits, uniqueness and append-only ledger/projection model meet this scope without another service. Schema1/reducer1/protocol2 and the pinned trainer catalog/ROM hashes are explicit. Facts commit before ACK; secondary evidence JSONL is diagnostic. See [schema and reducer](world_schema.md), [trainer identities](trainer_identities.md), and [normal-save/recovery semantics](world_saves.md).

Source-backed registry:742 records,580 world identities,227 explicit families. Rick102=`fr:trainer:0102`, nameRICK/classBug Catcher/ViridianForest, no VS Seeker family. Explicit native rematch/story variants resolve to their stable person; equal names never merge people. Identity does not depend on a battle, launch or party. Unused/special/composite records remain explicit exceptions, not speculative social profiles.

Campaign:`a3f97406-929e-4662-a30f-2d52213bd06f`.
Branch A:`b4ec3f4f-03dc-4327-99a0-1c309c5212a8`.
Branch B:`57be16b8-fcda-4853-8167-1b4dd21cd848`.

| Real normal save | Native counter / physical slot | Canonical checkpoint cursor | Checkpoint ID |
|---|---|---|---|
| Explicit retained pre-Rick import |4 /0|0|Import checkpoint; no earlier history invented|
| S1, pre-Rick native Save |5 /1|0|8849fd8a-995e-4437-913c-afca9cef4538|
| S2, after Rick victory |6 /0|36|218060bb-009c-400c-a1bb-ef2605a865bf|
| S3, final runtime re-save of restored S2 view |7 /1|36|191ac5a1-2451-4cc4-a6ec-2b50e431451f|

S1 fingerprint:`52def1e5bd6ae467de056d61842f3484200bd25fe06aac07427827207efa9351`.
S2:`c755cc23ba64c7d6f9f3a61ba0e6bf9cf84aa509aa40a88f8a05096e0b2f551c`.
S3:`8e5ed538bdde712e6a95089a0eb52f3383e4f8152e7f73fa3f6bfbb23d238d02`.
Algorithm:`fr-save-v1`,SHA256 over validated logical section content plus native counter; source-derived lengths/IDs, physical rotation/slot/RTC/padding excluded. Native S1/S2 alternation and fresh-process stability are real evidence; wrap/sector reorder/footer/corruption/failure cases are host fixtures, not new playthroughs.

Live acceptance used the unchanged final ROM and pinned task-local mGBA0.10.5. Three fresh OS processes used native File→Load/Load recent script; no savestate was loaded or saved. The retained pre-Rick native campaign is an explicit import, not a new full game/golden-path replay.

1. Fresh imported campaign native Continue, then native S1 Save. Its complete counter5 slot paired to cursor0.
2. Native Rick102 encounter/victory:47 transport records over11 turns,36 canonical facts and11 separate bounded observations. Defeat event46/end47, one completed encounter and one defeat. No follows/memory were derived.
3. Host stop/reopen and exact duplicate final wire delivery preserved the state/hash. An initial interrupted host stop is retained; subsequent signal-handled clean stops/opens prove identical state across clean runtime restart.
4. Native S2 Save paired counter6 to cursor36. Host absence allowed native movement; reconnect retained campaign/run and no new branch. A later ordinary wild start advanced A to cursor37; it is deliberately retained as an unfinished historical encounter, not a claimed victory.
5. Stop emulator/host; copy private S1 battery through managed launcher; fresh native Continue. S1 fingerprint stayed identical, native counter5/Bulbasaur7HP24/field42,46 returned, canonical view became cursor0 with no Rick fact. A's37 events stayed inspectable. Merely restoring/reconnecting/moving did not fork.
6. With the host stopped, native full-tile motion42,46→43,46→42,46 was captured and privately sampled; clean reconnect preserved cursor0/pending fork.
7. A new native wild start in restored S1 created branch B at cursor1. Rick defeat remained absent from B; A's Rick victory and37 events remained intact/inactive. Both histories replay deterministically offline.
8. A third fresh process loaded S2 and restored Rick's same stable identity/one victory at cursor36, with unchanged S2 fingerprint. Final runtime native S3 Save paired that historical view at cursor36 without inventing a new branch. Current active view is A/cursor36 with a deferred fork; A/head37 and B/head1 remain retained. Task processes/listeners were stopped at completion.

The S1 live pair preceded the later explicit host fsync hardening; its persistence was independently verified through a fresh-process native load and stable fingerprint. S2 and the final-code S3 save exercised the fsync gate. Lifecycle receipt crash-tail handling and injected transaction failures are automated host tests; physical power-loss/filesystem corruption were not induced. Re-saving a restored cursor was added and tested so native Save alone does not create a divergent branch.

Actual checks:

-113 combined host tests:75 retained bridge/UI plus38 WORLD tests, including separate observations, lifecycle/order/version/identity failures, duplicate/conflicting wins, source variants, replay/reopen, unknown/incompatible saves, transaction rollback/pending recovery, receipt crash tails, fingerprints/rotation/footer/wrap and historical re-save/deferred fork.
-63 actual-C sanitizer cases re-run:15 PING,13 event,7 observation,28 UI. Native UI renderer is excluded from those C stubs; earlier accepted live rendering evidence remains separate.
-Existing ARM/manifest/layout/source checks and disabled checksum; no new ROM build was necessary. Every accepted source overlay hash remains unchanged.
-43 final architecture/static checks;60 handoff checks/9 reference fixtures.
-Retained earlier live evidence verifiers12/27/53/144 passed. These are evidence regressions, not newly repeated earlier gameplay.
-63 WORLD retained live assertions passed, binding the actual source/ROM, checkpoints/receipts, Rick/dedupe/reopen, fresh battery restore, inactive histories, divergent branch, movement and offline replay.

Exact repository-root commands:

```sh
.venv/bin/python tools/world_registry.py
.venv/bin/python tools/world01.py fingerprint --save .local/phase1-ui-emulator/bridge03-native-counter4.sav
.venv/bin/python tools/world01.py import --save .local/phase1-ui-emulator/bridge03-native-counter4.sav
.venv/bin/python tools/world01_launch.py --start --save .local/phase1-ui-emulator/bridge03-native-counter4.sav
# Native Tools > Scripting > File > Load .local/world01-run.lua once.
.venv/bin/python tools/world01_host.py --seconds 1800
.venv/bin/python tools/world01_input.py --label world-title 'a 2' 'key 0 10 400'
.venv/bin/python tools/world01_input.py --label world-field 'key 0 10 150' 'key 1 10 500'
.venv/bin/python tools/world01.py save-begin
# Native S1 Save input; four Down inputs select Save from cursor0:
.venv/bin/python tools/world01_input.py --label s1-save-menu 'key 3 8 30' 'key 7 6 10' 'key 7 6 10' 'key 7 6 10' 'key 7 6 10' 'key 0 8 60'
.venv/bin/python tools/world01_input.py --label s1-save-overwrite 'a 4' 'key 9 0 240'
.venv/bin/python tools/world01_input.py --label s1-save-writing 'key 0 8 300' 'key 9 0 300'
.venv/bin/python tools/world01_input.py --label rick-opening 'key 6 16 300'
.venv/bin/python tools/world01_input.py --label rick-battle-ready 'a 3' 'key 9 0 300'
.venv/bin/python tools/world01_scenario.py battle --label rick-native --steps 40
# After the limit, inspect the actual battle screen before continuing:
.venv/bin/python tools/world01_scenario.py battle --label rick-reviewed-finish --steps 20
.venv/bin/python tools/world01_input.py --label rick-victory-field 'a 3' 'key 9 0 300'
# S2 starts from remembered Save cursor4; exact inputs are in the trace.
.venv/bin/python tools/world01.py save-begin
.venv/bin/python tools/world01_input.py --label s2-save-prompt 'key 3 8 30' 'key 0 8 60'
.venv/bin/python tools/world01_input.py --label s2-overwrite 'a 4' 'key 9 0 240'
.venv/bin/python tools/world01_input.py --label s2-complete 'key 0 8 300' 'key 9 0 300'
# Preserve the paired private battery copies, stop task processes before restore:
.venv/bin/python tools/world01_launch.py --start --save .local/world01/S1.sav
.venv/bin/python tools/world01_host.py --seconds 1800
.venv/bin/python tools/world01_input.py --label s1-reviewed-continue 'a 4' 'key 9 0 180'
.venv/bin/python tools/world01_input.py --label s1-reviewed-field 'key 0 10 150' 'key 1 10 500'
.venv/bin/python tools/world01_scenario.py encounter --label divergent-wild --steps 20
# Final positive S2 restart; fresh File > Load recent script/Continue:
.venv/bin/python tools/world01_launch.py --start --save .local/world01/S2.sav
.venv/bin/python tools/world01_host.py --seconds 1800
.venv/bin/python tools/world01_input.py --label s2-reviewed-continue 'a 4' 'key 9 0 180'
.venv/bin/python tools/world01_input.py --label s2-positive-field 'key 0 10 150' 'key 1 10 500'
.venv/bin/python tools/world01_scenario.py save --label s3-final-runtime --menu-cursor 0
.venv/bin/python tools/world01_regression.py
make -f Makefile.phase2 world-test
.venv/bin/python tools/world01_replay.py --database .local/world01/world.sqlite3 --export evidence/phase2/world01/rick-canonical-fixture.json
.venv/bin/python tools/world01_replay.py --fixture evidence/phase2/world01/rick-canonical-fixture.json
.venv/bin/python tools/verify_world01.py
.venv/bin/python tools/validate_ai_contracts.py
.venv/bin/python pokemon_influencer_handoff/tools/validate_handoff.py
git diff --check
```

The fixture export command is an example: the retained Rick fixture was exported at cursor36 before the later wild start. Do not overwrite evidence with a different current state. Use new labels/paths for replays. Exact actual commands/replies, signal stops, failures, RNG-dependent grass steps and native scene timing are in `evidence/phase2/world01/input-commands.jsonl`, scenario logs, `host.jsonl`, `emulator.jsonl` and `launches.jsonl`. Early S1 reload captures named `s1-restored-*` still show intro/title; only the reviewed subsequent captures prove field reload. A first unready battle invocation, the40-segment limit and a regression-runner import error are retained as exploratory failures, not successes. Final reports exclude them.

Files: `world/{store,reducer,saves,receipts}.py`, `world/migrations/001.sql`, registry/config and generator, `tools/world01*.py`, `tools/verify_world01.py`, `tests/test_world01.py`, `Makefile.phase2`; this report/schema/identity/recovery/source-map/status/decision/backlog and a factual AI architecture correction. No .env, model profile, battle source, UI product, ROM save struct or controller was changed.

Evidence index: `evidence/phase2/world01/{completion,runtime-lock,emulator-integration,managed-restore-and-fork,host-reopen,S2-after-fresh-continue,trainer-source-audit}.json`, fingerprints, pairings/receipts/launch/host/input traces, canonical-only replay fixtures/results, `final-host-regression.log`, `regressions/results.json`, final handoff/architecture/source audits. Actual database/battery backups and screenshots are private under `.local/world01/` and `evidence/private/world01/`.

Remaining risks: no arbitrary savestate/rewind, hot load or controller-only reset support; normal pairing requires an armed intent and trusted lifecycle receipt, with detectable unpaired saves if the host is absent or receipts are lost; no perfect distributed atomicity or real power-loss/disk-corruption qualification; unbounded emulator duration/reconnect/script reload and high playback remain unqualified; pinned native socket close guards remain launch-bounded; worst stack depth/224-byte ROM headroom and clean-machine provisioning remain earlier open risks. Canonical battle exporter scope remains the five existing event types; no general progression/roster identity/Pokemon lineage events or NPC knowledge system are invented. Full campaign/golden path and rematch gameplay are not claimed.

Stop after WORLD-01. Next recommended separately scoped task: **MEMORY-01**, deterministic observation/delivery provenance and scoped retrieval, before anyone can turn “Rick lost” into “Rick remembers losing.” No automatic SOCIAL/LLM/endgame progression.
