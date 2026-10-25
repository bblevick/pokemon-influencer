# RIVAL-01 deterministic travel-continuity repair

## Disposition — 2026-10-08

**RIVAL-01 TRAVEL RECOVERY BLOCKED — EXACT CONTINUATION UNPROVABLE.**

The generic managed transport correction passes its scoped host and actual native tests. The historical branch cannot be continued exactly: the emulator process is gone, no corresponding native state was retained, and its battery is still Save20. No historical event was injected, no checkpoint was manufactured, and RIVAL-01 is not accepted. This is stop condition B of the user's travel-repair authorization, within D52, not another campaign milestone.

Machine-readable closeout: `evidence/phase8/rival01-travel-repair/verification.json`. All 21 inventoried protected artifacts remain byte-identical. Original reports, logs, ledger, Josh/Miriam captures and forensic database remain untouched. Hosted calls: **0**. Original allowance remains **0/40**, closed, with unchanged nonfungible limits Strategy1/PREP0/battle32/Hermes4. No metadata/provider route check was made. Owned host, emulator and supervisor are stopped; default inference is disabled.

## Original incident and causal identity

The expired object was the offline writer **process lifetime `--seconds 3600`**, not a model budget or a revoked gameplay-generation lease. Original native ACK297 appeared at emulator frame183647. Transport EOF/disconnection appeared at frame215429. The native wild event was emitted much later, with payload frame1952875 and forwarding at emulator frame1954756. Failures at frames1954817,1954878,1954939 exhausted two retries. A later HELLO at frame1972942 could not retransmit the already-dequeued event. Therefore the failure occurred **before host delivery**, not after durable canonical application.

Identity established from the actual mailbox, launch mapping, canonical stream and retained database:

| Property | Retained value |
|---|---|
| Physical ROM SHA256 | `8600107da864669f61b3977c10193a96458911de3e4c972917668c431d1a9216` |
| Physical build tag | 2285031545 |
| Accepted logical campaign build/tag | `bec6245f354e0846a9e606ba0665d9dabc2e4f9825ba278342755143de56e829` / 2299536521 |
| Native launch nonce / Lua generation | 2493534040 / 1 |
| Launch origin | `ee127f88-a163-4b48-a77a-f324ec51329b` |
| Campaign | `a8c24607-48a7-4e47-a204-4221a7367fcc` |
| Suspended branch / cursor | `481b8552-6800-493e-b254-33baf7c77b41` / 669 |
| Missing sequence / last committed | 298 / 297 |
| Native battle / turn / phase | 10 / 0 / 0 |
| Type / trainer / battle kind | BATTLE_STARTED / 0 / wild |
| Payload checksum | 2627227558 |

Exact payload:

```text
010001002a0100000a000000000000006bcc1d00080000000400000000000000
```

The pinned native event ABI uses a four-entry volatile queue, 60-frame attempt timeout, and two retries (`src/pi_events.c`, `include/pi_events.h`). Native counter298/ACK297/drops1/depth0 and the durable stream ending at297 establish one retained missing event. No later retained sequence exists. This finding is bounded to retained counters/history; it is not permission to invent an unseen event chain.

The accepted native adapter normalizes the physical build tag into the older logical campaign identity and retains native provenance separately. The repair preserves that established distinction; it does not migrate campaign identity. The original transport slot is build/nonce/generation/sequence. No canonical event ID exists for the undelivered event, and none was assigned by this repair.

Read-only forensic validation seeds the actual stream's battle lifecycle into `Consumer`, validates the exact retained message beyond checksum, and proves that sequence298 would be the next causal start. It also confirms the campaign is suspended and the receipt was never committed. This does **not** establish a live native counterpart or authorize replay. Evidence: `incident-durable-state.json`, `incident-transport.json`, `verification.json`, and `HistoricalIncidentTests`.

## Native state, Josh/Miriam and rollback

Josh/source91's outcome1 terminal is `f4e2acbbba1c06b94a52afc57654c7da67a968ce14941a3941c291acb8be819c` at turn38. Miriam/source120's outcome1 terminal is `22e165c67fea894414970e2648f3f82a0b12c5f039abfee71444d2eef3f28276` at turn24. Their actual offline posts/follows/obligations and completed battles remain on the suspended future branch, with pre-gap projection evidence in the original captures. They are not simulations and are not merged into an earlier save.

The only retained working native battery has fingerprint `8d07886f33eea4d863209f9be626c191f4cf475262ceb5db5c3951f0f1c7d435`, counter20, slot0. Source-bound decoding of that battery confirms Josh and Miriam defeated flags are **both false**. No matching in-progress wild-battle state or later coherent battery was retained. A checksum-valid payload cannot reconstruct RAM, battle state, RNG or intervening native victories.

Last safe accepted pair:

- Native: `.local/rocket01/post-rocket-pair.sav`.
- Host: `.local/rocket01/post-rocket-pair.sqlite3`.
- Checkpoint `fc2eb9f8-d613-4f48-aebf-b2ffa2c44824`, branch `13a44cee-b272-40bb-9cfc-0815e1d386df`, cursor443, normal Save20.
- Seven coherent projection hashes: `verification.json.safeRollback.projectionHashes` and `rollback-context-verification.json`.

Any next campaign continuation must be explicitly **rollback-based**. Fresh-copy this pair, use the managed supervisor, Continue normally at MtMoon_B2F x18,y31, and retrace the normal route toward healing/exit/Miguel/fossil/Cerulean. Josh/Miriam are no longer active completions on that branch; any required challenges happen through legitimate gameplay. Save managed pairs during travel and recheck public context after new posts. Do not splice their suspended host outcomes into Save20. No such active replay was run in this repair.

## Generic correction and recovery contract

`bridge/continuity.py` adds a separate SQLite FULL/WAL durable transport inbox. It retains exact physical wire, payload hash, logical/physical build, campaign/branch/capture cut, launch/run/sequence and native witness before canonical ingestion. Receipt content is immutable. Application calls the existing `w.ingest()` transaction; it never edits domain tables directly. A canonical commit still precedes ACK. A crash between canonical commit and marking the inbox result is handled by existing delivery deduplication on replay.

Recovery requires an active eligible launch, matching campaign and causal prefix, contiguous sequence and battle lifecycle, plus a still-live owned native counterpart with matching build/launch/load/generation, nonregressing frame and zero drops. Different campaigns, abandoned launches, inactive future branches, conflicting duplicates, resets/replacement processes and missing native counterparts fail closed. Expired sockets alone do not invalidate an otherwise valid event. Pending inbox entries are not blindly replayed on startup: a surviving native retransmission or explicitly validated `Inbox.apply` must reestablish the witness.

Recovery audit is separate from gameplay truth: original identity/event ID, payload hash, origin/generation/sequence, campaign/capture branch, attempt UUID, disposition, method/tool/version/time and failure classification. In the live lost-ACK test, the retransmission retains exactly the original event ID. Earlier test audit rows created before the additive provenance column retain their original receipt/witness and NULL provenance; they were not rewritten retrospectively.

`bridge/managed.py`, `bridge/continuity_mgba.lua` and `tools/continuity_supervisor.py` provide an opt-in managed lifetime boundary. The host publishes its durable high-water mark before ACK. The supervisor binds the exact child process identity/launch and freezes the entire owned emulator with SIGSTOP on host exit, stale/disconnected health or native gaps. A launch/generation-bound input lease cancels queued PI_TEST inputs and rejects new ones when unavailable. This stops automatic battle/script progression as well as buttons; there are no gameplay-memory writes.

Explicit reconnect requires the **same surviving native process** and zero drops. The core remains frozen until the replacement writer has opened/validated storage and published fresh matching connection-loop readiness. Only then SIGCONT permits socket handshake/retransmission; input remains unavailable until authenticated transport and high-water checks pass. A fresh paired battery launch uses a new nonce and clears the prior control command while preserving it as retired evidence. Native code, queue size and synchronous-connect behavior are unchanged; Lua continues listening/polling and cloud work never enters callbacks.

This is generic across eligible canonical event types, not a wild or Rival exception. Legacy unmanaged configurations remain unchanged; future campaign runs must select the managed configuration. It does not make arbitrary offline native events disk-durable. Uncaptured events still depend on surviving native RAM, so missing counterparts require rollback. Qualified profile: pinned mGBA0.10.5/macOS at normal speed. Fast-forward, arbitrary input helpers, simultaneous writer/guardian loss and an emulator crash are not claimed recoverable.

## Tests actually run

**39 focused host tests, zero skipped, exit0** in `host-tests-final.log`. The matrix covers retained native events before delivery, durable receipt before commit, transaction failure, commit-before-ACK loss, duplicate delivery, post-ACK restart, causal gaps, conflicting identities, different campaigns, abandoned launch/generation, missing/replaced native state and immutable audit. Native witnesses in these cases are explicit fixtures. The actual historical payload regression is read-only, and its disposition is refusal of exact continuation.

Runtime: Python3.13.12, pinned mGBA0.10.5. Focused suite6.766s; compileall exit0.
`git diff --check` still reports the pre-existing trailing space at
`src/new_menu_helpers.c:670`; this repair did not change that native file.

Existing Rival constructor/terminal/privacy/budget/RAM regressions pass in the same command. Source334/Charmander resolves to actor0326 and exact authored four-party configuration. The previously accepted native constructor and first legal packet remain fixture evidence; no active Rival battle was started.

Actual mGBA qualification used independent copies:

1. First lost-ACK trial exposed premature SIGCONT: native retry exhaustion occurred before the replacement writer was ready. Capture `first-ack-test-disposition.json` preserves drops1; **this trial failed**.
2. Trial2 exposed a test-path environment binding omission; wrong-nonce handshake rejected. Its logs remain, and no gameplay was accepted from it.
3. Trial3 fixed both boundaries. Normal Continue/Quest Log skip and short cave walking encountered Zubat11. A declared transport-only fault committed real sequence2/BATTLE_TURN_STARTED and withheld its ACK, then stopped the writer/core. On explicit reconnect, the identical wire/event ID returned as duplicate=true; buffered sequence3 committed next. Player chose ordinary Run, received “Got away safely!”, and actual native outcome4 terminal committed. Final sequence5/ACK5/drops0/depth0. No trainer0000 actor, follow, recap, Strategy or faction report was created; social/puppeteer hashes match Save20.
4. Normal Start-menu save, prior host intent and actual savedataUpdated receipt produced counter21/slot1, checkpoint `32ea4005-7dbf-4bcf-8a5a-fb220c02402e`, branch `a77a17c9-4381-4ac2-b18c-c7fb7a820e48`, cursor447, fingerprint `cfc8b194c4dc3c1d9bac113040551fd30abaf55c856cd9a6773fab396675aca4`.
5. A real three-second writer lifetime expired. Frame14921 remained unchanged over two seconds, with zero drops and STOPPED input lease. Explicit fresh-writer readiness resumed the same process.
6. Fresh OS emulator/writer launch and normal battery Continue/Quest Log skip returned to the field. All seven projection hashes, native save identity and checkpoint matched. No active battle, pending save, memo change, duplicate event or stale tactical request resumed. `fresh-field-proof.png` was visually inspected, not inferred from title-screen coordinates.

The first fresh-start supervisor attempt correctly rejected a stale previous launch command; logs are retained. The launch wrapper now retires/clears that command before a new nonce. Initial title inputs arriving during the intro did not prove Continue; subsequent reviewed menu/field observations establish it. The intentional paused input sequence timed out when its queued screenshot was canceled; it was not retried as an ambiguous mutation.

Trial3 Save21 is **qualification-only**, not a replacement for the missing historical timeline. Detailed native evidence is in `evidence/phase8/rival01-travel-repair/trial3/`; screenshots remain under `evidence/private/rival01-travel-repair/trial3/`.

## Rival context and resources

On a disposable copy of coherent original Save20, content adoption and the versioned selector retain all22 public receipts and exclude all47 private Rocket receipt IDs. Two full contexts serialize identically at **7,524/8,192 bytes**, with preserved references/hashes; no memory was deleted and no Strategy job/memo was created. Failed-branch Josh/Miriam posts are intentionally inactive. Context must be recomputed after a future legitimate travel replay. Evidence: `rollback-strategy-context.json`, `rollback-context-selection.json`, `rollback-context-verification.json`.

Pinned source `037335f4c725d7c9aecdac87066f2002b4bd7e14`; physical ROM/ELF hashes unchanged. Actual final allocated EWRAM endpoint `0x0203fffc`, headroom4, permanent growth0 (`native-static-verification.json`). No ROM/native/save-layout changes or rebuild were necessary. This does not measure stack/heap peaks.

## Commands and reproduction

Run from the repository root. Trial labels select isolated paths and refuse overwriting seeded saves/databases. Generated configs/scripts contain only local launch authentication and stay under ignored `.local/`; no ROM or battery is uploaded.

```sh
PYTHONPATH=tests:tools .venv/bin/python -m unittest tests.test_bridge_continuity tests.test_rival01_budget tests.test_rival01_prerequisites -v > evidence/phase8/rival01-travel-repair/host-tests-final.log 2>&1
.venv/bin/python -m compileall -q bridge/continuity.py bridge/managed.py tools/continuity_supervisor.py tools/rival01_travel_repair.py tools/strategy01_host.py
POKEINFLUENCER_CONTINUITY_TRIAL=trial3 .venv/bin/python tools/rival01_travel_repair.py seed
POKEINFLUENCER_CONTINUITY_TRIAL=trial3 .venv/bin/python tools/rival01_travel_repair.py launch
.venv/bin/python tools/continuity_supervisor.py --config .local/rival01-travel-repair-trial3/launch.json
```

Through native Tools → Scripting, load the generated script:

```lua
dofile("/Users/blevicki/Documents/poke/pokefirered/.local/rival01-travel-repair-trial3/run.lua")
```

Actual bounded inputs, including the reviewed title, Quest Log, cave loop and Run, are recorded exactly in trial3 `input-commands.jsonl` and `emulator.jsonl`. The acceptance-driving transport/save commands were:

```sh
POKEINFLUENCER_CONTINUITY_TRIAL=trial3 .venv/bin/python tools/rival01_travel_repair.py fault-ack 2
POKEINFLUENCER_CONTINUITY_TRIAL=trial3 .venv/bin/python tools/rival01_travel_repair.py input --label cave-loop 'key 5 16 180' 'key 6 48 90' 'key 7 32 90' 'key 4 32 90' 'key 6 64 90' 'key 7 64 120' 'key 9 0 240'
POKEINFLUENCER_CONTINUITY_TRIAL=trial3 .venv/bin/python tools/rival01_travel_repair.py input --label wild-turn 'key 0 8 120' 'key 9 0 300'
POKEINFLUENCER_CONTINUITY_TRIAL=trial3 .venv/bin/python tools/rival01_travel_repair.py control restart-host
POKEINFLUENCER_CONTINUITY_TRIAL=trial3 .venv/bin/python tools/rival01_travel_repair.py input --label ordinary-run 'key 4 8 20' 'key 7 8 20' 'key 0 8 180'
POKEINFLUENCER_CONTINUITY_TRIAL=trial3 .venv/bin/python tools/rival01_travel_repair.py input --label leave-wild 'key 0 8 180' 'key 9 0 120'
POKEINFLUENCER_CONTINUITY_TRIAL=trial3 .venv/bin/python tools/rival01_travel_repair.py save --label travel-save --menu-cursor 0
POKEINFLUENCER_CONTINUITY_TRIAL=trial3 .venv/bin/python tools/rival01_travel_repair.py control restart-host --seconds 3
POKEINFLUENCER_CONTINUITY_TRIAL=trial3 .venv/bin/python tools/rival01_travel_repair.py control restart-host --seconds 900
POKEINFLUENCER_CONTINUITY_TRIAL=trial3 .venv/bin/python tools/rival01_travel_repair.py control stop
.venv/bin/python tools/rival01_travel_repair_verify.py > evidence/phase8/rival01-travel-repair/verification-console.log 2>&1
```

The timed test first terminated only the task-owned current writer PID from matching `host-health.json`; restart commands require it to be dead and the native core frozen. A fresh reload repeated `launch`/supervisor/script load after stopping both children, without reseeding. Separate captures and SQLite read-only backups preserve the paired test checkpoint. Context/native measurement code was offline and source-bound; evidence records its outputs. Future random encounters are ordinary game RNG, not a promised deterministic Zubat recreation.

## Conditional live-resume readiness

Historical branch recovered: **no**. Historical wild298 disposition: validated forensic evidence, never applied. Josh/Miriam active after rollback: **no**. Safe campaign continuation pair: original accepted Save20, not trial3 Save21. Context/privacy/constructor regressions pass; active Rival gameplay and fresh provider checks remain unrun. Original40-call ceiling unused, ledger still closed; this repair does not reopen it.

Completed work: generic managed inbox/lifetime/reconnect correction, 39-test matrix, retained-incident classification, isolated native travel/save/expiry/restart proof, rollback context and preservation checks. Outstanding blocker: original native continuation unavailable. Next single task requires separate scope: **rollback-based RIVAL-01 continuation from Save20 using the managed supervisor**, normal healing/travel, bounded current public context and previously authorized Rival gates. No later campaign phase or endgame work.
