# MEMORY-01 implementation and acceptance

Completed **MEMORY-01 only**, 2026-10-02. The deterministic subjective layer now answers what a trainer directly witnessed or was explicitly delivered. Canonical history remains separate. No Hermes/OpenRouter/inference, interpretation/beliefs/personality, PokeBook/feed, social graph/propagation, follows/friends/reputation, roster preparation, battle policy/control, generated dialogue or endgame was implemented. Hosted inference remains disabled; `.env` and user dump were not read for credentials, modified or uploaded.

The implemented domain contract, actors, schemas, provenance, checkpoint cutoffs, retrieval limits and future Hermes boundary are in [memory_schema.md](memory_schema.md). The unchanged canonical contract remains [world_schema.md](world_schema.md), normal-save restrictions [world_saves.md](world_saves.md).

Four claim types: BATTLE_PARTICIPATION, TRAINER_BATTLE_RESULT, POKEMON_SEEN, MOVE_REVEALED. Only the actual participant gets direct evidence; bounded BRIDGE-02 observations and explicitly classified visible announcements supply the minimum revealed fields. A delivery is one referenced typed claim, fixed development-fixture channel, with sender/recipient/source chain/idempotency identity and exact active campaign/branch/cursor. It never copies the sender's unrelated memories. Context does not contain private player state, raw NPC battle snapshots or inferred conclusions.

Canonical schema/reducer remain1; memory schema/reducer are independently1. Six additive authority/history tables plus a processed-source table provide immutable actor evidence and subjective checkpoint/branch cutoffs. No original canonical rows, flags, save sectors or ROM hooks change. MemoryStore commits canonical facts and evidence together before ACK. WorldStore now refuses memory-enabled writes, including an already-open legacy writer, so old ingestion cannot bypass this layer. Migration is additive/explicit when opening MemoryStore; canonical-only databases retain the old behavior. Migration acceptance used a SQLite backup of accepted WORLD history; original WORLD database/evidence remain preserved.

Trainer actors reuse the existing stable WORLD registry: Rick102=`trainer:fr:trainer:0102`, Janice116/507/508=`trainer:fr:trainer:0116`. Janice's constants were inspected in the pinned source; equal names do not merge actors. Future player/faction namespaces require a new explicit migration. Registry identity is shared/stable; knowledge is additionally campaign/branch/cutoff scoped.

## New live acceptance

Final ROM remains BRIDGE-03 SHA256:
`739bd3eebb91aaa5210f8f8cd1f357a8272dc98db7060356c649b4c38a0dbc2d`.
The same actual ELF/full-build manifest is verified before launch. No ROM rebuild is needed: source overlay hashes remain unchanged. Source pret037335f4c725d7c9aecdac87066f2002b4bd7e14, agbccda598c1d918402c42c0c0d7128ba14567f3175e9, pinned task-local mGBA0.10.5/26b7884bc25a5933960f3cdcd98bac1ae14d42e2. No new bridge behavior or blocking Lua socket connection was added.

This is a **new MEMORY live battle**, not reuse of WORLD's battle log. Its starting battery is an explicit import of retained native pre-Rick S1; no new full opening playthrough is claimed. New campaign `5e026045-5a18-4381-93c7-00ee6949ae6f`; branch A `f141209b-c618-46f5-ae33-2475790fbfb8`; divergent B `ec0260eb-948f-4586-b5dd-4ad7de47c61a`.

| Step | Actual evidence |
|---|---|
| Fresh native Continue and new pre-Rick S1 Save | Native counter6/slot0; canonical cursor0, subjective cutoff0; `S1-pair.json` / `S1-fingerprint.json` |
| Ordinary native Rick battle victory | 35 transport records:27 canonical facts +8 bounded observations,8 turns, one defeat and end; `rick-live.json`, deliveries/input/emulator traces |
| Rick knowledge | 25 immutable direct records → four compact claims: participation, trainer loss, visible Bulbasaur1, revealed Tackle33; Janice zero; `rick-live.json` |
| Clean host stop/reopen | Exact snapshot/hash equality; `host-reopen.json`, host close/open records |
| Explicit host fixture | One Rick result claim delivered to Janice; zero direct knowledge/no Pokémon/move claims; receipt→Rick result→canonical end source; duplicate is a no-op; `targeted-delivery.json` / `duplicate-delivery.json` |
| New post-battle S2 native Save | Counter7/slot1; canonical cursor27, memory cutoff26; `S2-pair.json` / `S2-fingerprint.json` |
| Fresh OS-process normal S1 Continue | Counter6, Bulbasaur7/HP24 and pre-Rick field returned; active cursor0/cutoff0; Rick and Janice empty; historical A retained; `restored-s1-field.json` |
| New native wild start from S1 | B fork0/head1; parent subjective cutoff0; no Rick/Janice knowledge; A retains26 historical records; `divergent-branch.json` / `branch-audit.json` |
| Positive fresh S2 Continue | Counter7, Bulbasaur8/HP17/native post-Rick field; same Rick context and exactly one Janice receipt restored; `s2-positive-reload.json` |

The divergence scenario's wild encounter was started to prove a branch, **not completed or claimed a win**. Final active view is paired A/cursor27/memory26, no active battle or pending save; B's unfinished wild start remains historical. Three actual fresh mGBA processes used native script load/Continue and battery saves; no savestate/reset/rewind was used. Screenshots were inspected privately. Final task processes/listeners are stopped.

Tackle's context count15 means **15 evidence sources** (8 visible action announcements plus7 subsequent bounded observations), not15 move uses. Eight species sightings are grouped into one compact claim. Every immutable source is retained; the context exposes at most8 evidence IDs per group. Raw bounded own HP/moves/PP do not enter retained claims or actor context.

S1 fingerprint `92ac18d67590de57130d36e31a4e5334ea0edf0307bd5034504eddd1a821dd65`; checkpoint `761f7391-4a2e-4430-bf07-8917ff14adee`.
S2 fingerprint `9e5030e975968753bdb4809b150098dee39d06f951945ed64e0b0f9d7c7e3136`; checkpoint `0977aa1c-1917-4f1d-a850-c82ebb23d38b`.
World-save fingerprints remain fr-save-v1; no ROM memory marker was added. A checkpoint also binds subjective sequence, preventing same-world-cursor later deliveries from surviving restore. That timing case, failed transactions and malformed provenance are host tests, not additional claimed live playthroughs.

## Exact commands and verification

All commands below run from repository root. Launch config/private Lua contain a local token, not an API key; reports redact it. Native GUI: Tools→Scripting→File→Load `.local/memory01-run.lua` once per fresh process; subsequent launches used Load recent. Retained listen/input sockets remain127.0.0.1:18772/18773; all Lua socket acceptance/polling is nonblocking.

```sh
.venv/bin/python tools/memory01.py import --save .local/world01/S1.sav
.venv/bin/python tools/memory01_launch.py --start --save .local/world01/S1.sav
.venv/bin/python tools/memory01_host.py --seconds 1800
.venv/bin/python tools/memory01_input.py --label fresh-continue 'a 4' 'key 9 0 180'
.venv/bin/python tools/memory01_input.py --label fresh-field 'key 0 10 150' 'key 1 10 500'
# Initial helper invocation used an uppercase label and failed only on screenshot:
.venv/bin/python tools/memory01_scenario.py save --label memory-S1 --menu-cursor 0
# Its save intent and native menu inputs were already accepted; do not repeat them.
.venv/bin/python tools/memory01_input.py --label memory-s1-prompt-reviewed 'key 9 0 30'
.venv/bin/python tools/memory01_input.py --label memory-s1-overwrite 'a 4' 'key 9 0 240'
.venv/bin/python tools/memory01_input.py --label memory-s1-complete 'key 0 8 300' 'key 9 0 300'
cp .local/memory01/pokefirered.sav .local/memory01/S1.sav
.venv/bin/python tools/memory01.py snapshot --output evidence/phase2/memory01/pre-rick.json
.venv/bin/python tools/memory01_input.py --label rick-opening 'key 6 16 300'
.venv/bin/python tools/memory01_input.py --label rick-battle-ready 'a 3' 'key 9 0 300'
.venv/bin/python tools/memory01_scenario.py battle --label rick-native --steps 40
# Bound reached; reviewed actual victory dialogue before continuing:
.venv/bin/python tools/memory01_input.py --label battle-reviewed 'key 9 0 30'
.venv/bin/python tools/memory01_scenario.py battle --label rick-reviewed-finish --steps 20
.venv/bin/python tools/memory01.py snapshot --output evidence/phase2/memory01/rick-live.json
.venv/bin/python tools/memory01_input.py --label rick-victory-field 'a 3' 'key 9 0 300'
kill -TERM 95137
.venv/bin/python tools/memory01_host.py --seconds 1800
.venv/bin/python tools/memory01.py snapshot --output evidence/phase2/memory01/host-reopen.json
.venv/bin/python tools/memory01.py fixture-deliver --output evidence/phase2/memory01/targeted-delivery.json
.venv/bin/python tools/memory01.py fixture-deliver --output evidence/phase2/memory01/duplicate-delivery.json
.venv/bin/python tools/memory01_scenario.py save --label memory-s2 --menu-cursor 4
cp .local/memory01/pokefirered.sav .local/memory01/S2.sav
# Native mGBA Quit, then stop its host before managed restore:
kill -TERM 95944
.venv/bin/python tools/memory01_launch.py --start --save .local/memory01/S1.sav
.venv/bin/python tools/memory01_host.py --seconds 1800
.venv/bin/python tools/memory01_input.py --label s1-restored-continue 'a 4' 'key 9 0 180'
.venv/bin/python tools/memory01_input.py --label s1-restored-field 'key 0 10 150' 'key 1 10 500'
.venv/bin/python tools/memory01.py snapshot --output evidence/phase2/memory01/restored-s1-field.json
.venv/bin/python tools/memory01_scenario.py encounter --label divergent-wild --steps 20
.venv/bin/python tools/memory01.py snapshot --output evidence/phase2/memory01/divergent-branch.json
# Native Quit again:
kill -TERM 96182
.venv/bin/python tools/memory01_launch.py --start --save .local/memory01/S2.sav
.venv/bin/python tools/memory01_host.py --seconds 1800
.venv/bin/python tools/memory01_input.py --label s2-positive-continue 'a 4' 'key 9 0 180'
.venv/bin/python tools/memory01_input.py --label s2-positive-field 'key 0 10 150' 'key 1 10 500'
# First capture still title; second capture Continue. Only this third proves field:
.venv/bin/python tools/memory01_input.py --label s2-reviewed-field 'key 0 10 150' 'key 1 10 500'
.venv/bin/python tools/memory01.py snapshot --output evidence/phase2/memory01/s2-positive-reload.json
# Native Quit; clean final host shutdown:
kill -TERM 96582
.venv/bin/python tools/memory01_replay.py --database .local/memory01/world.sqlite3 --export evidence/phase2/memory01/final-fixture.json
.venv/bin/python tools/memory01_replay.py --fixture evidence/phase2/memory01/final-fixture.json
.venv/bin/python tools/memory01_regression.py
.venv/bin/python tools/verify_world01.py
.venv/bin/python tools/verify_memory01.py
git diff --check
```

PIDs above are **historical evidence**, not reusable commands to stop future processes. For a new run inspect task-owned PIDs before signaling. The input/emulator/host/save/launch traces preserve actual commands, replies, native frames and receipt barriers. Failed uppercase-label screenshots, battle40-step bound and prematurely named S2 field/title captures remain exploratory evidence, not accepted saves/reloads. Driver now validates lowercase labels before sending mutation or arming save. General new-game/golden-path timing/RNG is not qualified; grass encounter took14 bounded segments in this run. Retained scenario helpers provide reusable reviewed paths, not a claim of bit-identical future RNG outcomes.

Final checks:145 host tests (113 prior +32 MEMORY), including firewall, revelation/private exclusions, duplicate/conflicting delivery, migration/reopen/replay, provenance rejection/depth bounds, atomic rollback, branch grants and same-cursor delivery rewind.63 actual-C sanitizer cases re-run (15PING/13event/7observation/28UI), existing ARM/source/full-build/disabled baseline checks;60 handoff checks/9fixtures and43 architecture checks; retained earlier live assertions12/27/53/144 plus63 WORLD assertions. These retained verifiers are evidence regressions, not new earlier-phase playthroughs. MEMORY's117 retained acceptance assertions bind the **new** live evidence and authoritative database. Offline typed JSON replay reconstructs isolated SQLite stores and rederives direct evidence, checks targeted parent ownership/claim/branch/order and compares contexts; no emulator/ROM/provider is needed. Administrative replay fixtures include bounded raw source history and must never become model context.

Files changed: new `memory/{__init__,store}.py`, explicit memory migration, `tests/test_memory01.py`, `tools/memory01{,_launch,_host,_input,_scenario,_replay,_regression}.py`, `tools/verify_memory01.py`; two compatibility guards in `world/store.py`, additional Makefile.phase2 targets, this report/schema/status/backlog/decision/source-map and future Hermes/AI boundary pointers. No C/ROM, model config or save serializer changes. `evidence/phase2/memory01/` contains the runtime lock/changed-files/completion,117checks, snapshots/provenance/checkpoints/fingerprints/migration/branches, replay fixtures/results, regression logs and actual JSONL traces. Battery/SQLite backups and screenshots remain ignored/private.

Open risks: arbitrary savestates/hot load/reset/rewind remain unsupported; host-absent/unarmed saves and lost receipts still require explicit recovery; no real disk/power-loss qualification or perfect cross-process atomicity; unchanged224-byte EWRAM headroom/unmeasured worst stack and launch-bounded native sockets/manual script loading; only audited single participant/revealed species/moves/outcomes are supported. Context's earliest256-record window is conservative and explicitly truncated; relevance/salience/forgetting and independent-origin corroboration are deferred. A provenance chain identifies an origin, not truth/confidence or permission for public dissemination. Host-issued actor capabilities are a trusted application boundary, not a sandbox for arbitrary Python. Future adapters must not expose the grant factory, writer, SQL or administrative fixtures.

MEMORY-01 is sufficient as the deterministic evidence/delivery substrate for **SOCIAL-01**, which must separately implement authored eligibility and bounded explicit exposure/follow rules before any broader distribution. Stop here; next recommended separately scoped ticket is SOCIAL-01. No automatic SOCIAL, Hermes, inference, battle AI or endgame work is authorized by this completion.
