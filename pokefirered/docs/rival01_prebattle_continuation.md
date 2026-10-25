# RIVAL-01 pre-battle continuation repair — 2026-10-24

**RIVAL-01 PRE-BATTLE CONTINUATION REPAIR ACCEPTED.** All three repair gates pass. RIVAL-01's actual battle/social gameplay acceptance remains pending. No Rival battle or travel replay occurred; no new hosted call was used.

## Gates and actual evidence

**A — generic contract:** implemented the versioned host-only descendant journal in `world/continuation.py`, integrated with shared save/launch/store APIs. It references original receipts, retains exact view/lineage/content/encounter bindings and requires settled native sessions before restart. Ordinary Save24 restore still excludes its future work and abandons the journal. No old cutoff, native save or pairing metadata was rewritten. Live and committed fallback durability are both tested. [Contract/state diagram](prebattle_continuations.md).

**B — actual Rival admission:** the complete retained committed host snapshot is a valid descendant of Save24, not a newly paired save. Original checkpoint `8f162291-19e8-489c-bbf5-62cc858d25b9`, campaign `a8c24607-48a7-4e47-a204-4221a7367fcc`, branch `6af32bb1-08de-44f1-b7f6-928ebd0f5921`, cursor880. Sealed continuation:

`prebattle:b31b60a83aa1482495e4c03deb081ece248782de57869f53a746379449e80a39`

Exact opportunity: `opening:9f09491588986330ab0c270f95694f8bdc095cde9d1fa3fd627eb78df9e3fb51`.
Exact Strategy: `strategy-memo:6274d3932fdfb6a36a35e75ff6622ef4031a2cfc6ccf2038ece9e05339f659f9`.
Exact preparation: `commitment:0c710308ca07517f885a6c4ace389942460bb1c18b24d5aa981843c90f59ecf6`.
Prepared encounter: `prepared-encounter:0337ba98062034839af87f7504d892ea074f8d9defb43820a8f5714be6fec8f4`.

The typed context binds native334 to actor0326, Charmander branch. The authored four partners/custom moves/levels/IVs/items/resources remain byte/value identical. The actual Dots/AtlasCloud memo, including imperfect subjective tactics, remains verbatim with original provenance/restore epochs. Context canonical hash `d429055e2cc010ed557448b11b3769b49e74e0ecd603cadfc47da74447d9bfd7`, policy `campaign-public-context-1` version1;7524 bytes,30 public receipts,92 private Rocket receipts excluded. No new context or PREP candidate replaced it.

Native equivalence was established from the retained last accepted input batch ending on a Continue-menu screenshot at frame2970, no later accepted gameplay input, frozen frame3643 and sequence/ACK/depth/drop0. Exact original Save24 identity and pinned-layout decoding establish map3/3 `(22,8)`, starter0, Rival scene0, trainer334 undefeated; legitimate travel flags remain. This is a reviewed native-boundary proof with hashed source evidence, not an inference from zero counters alone. `native-equivalence.json`, `native-compatibility.json` and `admissibility.json` retain it. Future field divergences cannot reuse this narrow witness kind.

**C — real managed runtime:** two separate mGBA OS processes booted the exact accepted ROM, loaded the project Lua bridge, used normal Continue and dismissed native quest-log replay. Both reached the correct field before the Rival trigger. Read-only native checks recorded `(22,8)`, map3/3, starter0, scene0 and defeat-flag byte1 (trainer334's bit6 unset). No flag/RAM/party/RNG/map injection or savestate/turbo was used.

| Actual session | Nonce / native origin | Host-received frame progression |
|---|---|---|
| Fresh Continue1 |2948085033 / a083b1d0-3a63-4d7b-9f86-2b40880ef346|1122→12722;969 samples across clean running periods and reconnect|
| Fresh Continue2 |2751080579 / a7905f75-1425-41da-9ae7-bfd0bccb28c7|2643→7293;383 samples|

A harmless Down2-frame press then Up2-frame press returned22,9→22,8, observed in native position samples/screenshots. No north-trigger crossing occurred. Both streams retained captured0/ACK0/depth0/drops0 and host cursor880. Native and host matched exact current build/nonce/origin/run1; the second launch rejected readiness from the prior session's cached telemetry until its own increasing frames arrived.

The first run also exercised actual fail-closed freeze at frame10732 during lost progression. Old host61513 was stopped; replacement65835 reached readiness before SIGCONT. New frames10752 onward reached the host and only then restored the lease. This contrasts with the retained failed reconnect; the new video-paced process actually resumed. The second run had no such freeze. Neither a running PID nor an accessibility timeout was counted as health. `native-host-telemetry.jsonl`, `telemetry-verification.json`, `supervisor.jsonl` and `emulator.jsonl` retain the trace.

After **each** normal managed stop, a durable exact native closure was recorded. `restart-one.json` and `restart-two.json` prove all seven gameplay projection hashes equal the pre-repair committed world and the frozen lookup returns the exact original memo/lock. Both session grants/closures are recorded; no open native session remains. Planning `recorded_strategy()` intentionally cannot reconstruct a spent PREP opportunity, so frozen retrieval uses the explicit continuation API instead. No Strategy job was created to work around that distinction.

## Tests, preservation and limits

75 unique focused host tests passed/0 skipped across the retained logs (66 initial regression checks,22 final focused checks with overlap, and final schema checks). These include actual retained-data copies, fallback durability, normal parent rollback, same actor/different encounter, wrong opportunity/campaign/branch, incomplete work, transaction interruption, unsettled crash, stale sessions, native consumption/completion fixtures, no generation, repeated restart, frame regression/freshness and future-schema rejection. These host fixtures are distinct from the two actual emulator runs. Initial schema-name/hash and transient test expectation mistakes were corrected; early failed logs are retained, not counted as acceptance.

The first draft called memory replay's SQLite backup inside a writer transaction and stalled; the owned diagnostic process was stopped and rolled back. The final seal binds immutable receipts and current view metadata inside the transaction, while full seven-projection replay checks run outside it. No unbounded backup wait remains in the API. Two development-only descriptors/databases were archived before the final v1 sealed descriptor. They were never accepted campaign state or replacements for the original memo/lock.

All23 newly inventoried inputs and23 earlier protected artifacts are byte-identical. Original Save24 native save, host database/checkpoint metadata, authoritative old working branch, retained live memo/lock/context, old launch/failure records and authoritative ledger are unchanged. Only isolated `.local/rival01-prebattle-continuation/` state and new evidence were used for execution. The continued host world has exactly the original seven committed-world hashes; the parent still has its original seven different saved hashes.

Authoritative ledger remains **1/40**, closed, **0 new** calls. Aggregate39 remains; the inherited stricter role caps leave battle32/Hermes4 and no new Strategy/PREP slot. No extra budget or role transfer was created. Configured providers and `.env` were unchanged and unused. Both owned supervisors/hosts/emulators are stopped; default inference remains disabled.

ROM SHA-256 remains `8600107da864669f61b3977c10193a96458911de3e4c972917668c431d1a9216`. No ROM/native permanent allocation changed; growth0/headroom4 bytes, supported by unchanged accepted ROM/linker evidence. No new native build is claimed. Metadata-only immutability/version hardening was additionally checked after native runs without changing the native handshake or domain behavior.

Limits: v1 rejects unproved field divergence; a crashed/unsettled native session blocks fresh launch until qualified revalidation. One-second freshness can safely freeze on heavy scheduling or deliberate pause; use the explicit tested reconnect. Lua loading remains an explicit GUI step. This repair does not establish live battle, recap, HIGH_PROFILE diffusion or post-battle paired-save acceptance.

## Exact reproducible runtime procedure

From repository root, with the retained isolated working directory and explicit continuation:

```sh
.venv/bin/python tools/prebattle_runtime.py prepare --private .local/rival01-prebattle-continuation --evidence evidence/phase8/rival01-prebattle-continuation --manifest evidence/phase8/rival01-prebattle-continuation/manifest-native.json --continuation prebattle:b31b60a83aa1482495e4c03deb081ece248782de57869f53a746379449e80a39
.venv/bin/python tools/continuity_supervisor.py --config .local/rival01-prebattle-continuation/launch.json
```

In the owned mGBA Scripting window:

```lua
dofile("/Users/blevicki/Documents/poke/pokefirered/.local/rival01-prebattle-continuation/run.lua")
```

The generic wrapper never constructs hosted services. Its normal input/stop commands require the same `--private`, `--evidence`, `--manifest` paths. `input --label fresh-two-field -- 'key 0 2 90' 'key 0 2 90' 'key 0 2 90' 'key 0 2 180' 'key 1 2 90' 'key 1 2 120' 'key 9 0 90'` reproduced the second field Continue. Inspect the actual screen before any further input. Exact accepted input commands/timestamps are in `input-commands.jsonl`; no ambiguous mutation was retried.

`stop` performs managed shutdown and seals a native session closure only with a valid advancing pre-stop witness. For the actual same-native trial, `kill -TERM 61513` stopped the owned writer, then the wrapper's `restart-host --seconds 900` caused readiness-gated reconnect; new PID65835/frame10752 proved recovery. Do not replay those historical PIDs as commands.

Focused checks:

```sh
PYTHONPATH=tests:tools .venv/bin/python -m unittest tests.test_prebattle_continuation tests.test_managed_progress -v
PYTHONPATH=tests:tools .venv/bin/python -m unittest tests.test_prebattle_continuation tests.test_strategy_memo tests.test_bridge_continuity tests.test_rival01_prerequisites tests.test_rival01_rollback -v
```

Evidence namespace `evidence/phase8/rival01-prebattle-continuation/` contains machine verification, exact admissibility/receipt tails, two restart audits, privacy/native/preservation checks, crash/failure matrices, telemetry, tests, source hashes and memory report. Private screenshots and saves remain ignored/local. No game ROM or save was uploaded.

## RIVAL-01 FINAL BATTLE RESUME READINESS

**READY for a separately authorized live continuation of the same pending encounter.** The repair itself stops here.

- Working descendant: `.local/rival01-prebattle-continuation/world.sqlite3` + native `pokefirered.sav`; parent remains Save24. Campaign/branch above, original logical restore/PREP/Strategy generation65; fresh native run1 with new nonce/origin per launch. Two previous sessions are settled.
- Use the explicit sealed continuation launch command above, not an ordinary Save24 rollback launcher. Last successful fresh native identity is nonce2751080579/origin a7905f75-1425-41da-9ae7-bfd0bccb28c7; the next launch must receive another fresh identity.
- Exact Strategy ID/hash, lock ID/hash, opportunity, encounter, context and policy references are exported in `verification.json`/`admissibility.json`. No new Dots Strategy, PREP selection or candidate construction is required.
- Live execution must bind the already-accepted Rival services/battle handler to this same workspace and **existing** authoritative ledger under the next live authorization. The qualification wrapper stays offline; do not cross the trigger with a host lacking the live handler. This is service configuration over the existing interfaces, not permission to rebuild Strategy or party.
- After fresh current Mercury/Hermes metadata checks and advancing telemetry/frozen lookup pass, normal Up presses22,8→22,7→22,6 reach the existing left-lane Rival trigger. No warp or direct battle injection. Native334/actor0326 constructor attribution and exact authored party must be checked at the real battle boundary.
- Expected sequence: frozen memo/party → engine legal actions → live Mercury → native revalidation/execution → canonical terminal → mandatory Hermes recap/fallback → HIGH_PROFILE public distribution → read-only native PokeBook → normal **new** paired gameplay save → fresh offline Continue/seven projections/rollback isolation. None ran in this repair.
- Budget39 aggregate remains, with currently stricter battle32/Hermes4 role slots. No Strategy is needed. Stop on concrete failures rather than reroll commitments or spend model calls debugging deterministic continuity.

Misty, acquisitions, Rocket leadership, later Rival encounters and endgame remain deferred.
