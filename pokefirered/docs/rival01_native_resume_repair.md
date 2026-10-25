# RIVAL-01 native-resume repair — 2026-10-10

**RIVAL-01 STILL BLOCKED — PRE-BATTLE LOCK REATTACHMENT.** Neither repair acceptance gate passed. This work diagnosed a concrete unsupported save boundary; it did not implement or qualify native reconnection. No new ticket is accepted.

The user explicitly requires, in section14: “If their encounter/branch identity cannot be reconciled: STOP.” Section4 also requires identifying the missing generic capability if durable pre-battle commitments cannot survive parent-checkpoint restart. The isolated retained-data reproduction establishes that condition. Launching the existing runtime would exclude the valued committed memo/lock. No fresh emulator was launched, no gameplay progressed, no model/provider request was sent, and no pairing was fabricated.

## Exact contract failure

Save24 is the accepted normal paired checkpoint `8f162291-19e8-489c-bbf5-62cc858d25b9`, native counter24, canonical cursor880, campaign `a8c24607-48a7-4e47-a204-4221a7367fcc`, branch `6af32bb1-08de-44f1-b7f6-928ebd0f5921`. Native trainer334 maps to persistent actor0326 and the Charmander authored party. The real Dots memo and unchanged preparation committed afterward, with no native Rival battle.

`world/store.py:132`'s `authorize_launch` unconditionally invokes `restore`. The accepted save contract restores each derived projection to its checkpoint cutoff, even if canonical cursor remains880. `strategy/store.py:48`, `prep/store.py:76`, and `system1/store.py:43` enforce independent Strategy/PREP/decision prefixes. `docs/strategy01.md` explicitly says a before-Strategy save excludes future receipts; no same-fingerprint rebinding is allowed. Host-only process reopen reuses existing committed state, but a fresh native parent-save restore is a different operation.

On a verified disposable copy of the real retained committed database:

| Evidence | Before fresh-launch authorization | After ordinary Save24 restore |
|---|---|---|
| Active Rival memo |1, exact live Dots record|0|
| Active preparation lock |Exact committed unchanged party|None|
| Strategy cutoff |16|14|
| PREP cutoff |35|33|
| Canonical cursor |880|880|
| Pending fork |0|1|
| Immutable Strategy/PREP/decision rows |Retained|Byte/value identical|

All seven after-restore hashes match accepted Save24. Five projections already matched; Strategy and decision projections deliberately return to their parent hashes. No history was deleted. The records remain durable but outside the restored active prefix. The lookup cannot be repaired merely by matching trainer display name, reusing an old nonce, replaying the model request, copying receipts, or raising derived cutoffs: those would defeat saved-history isolation or create a false pair.

A second fresh disposable reproduction gives the same result. The existing tests also prove that an ordinary host reopen preserves a memo whereas restoring a before-result save excludes it. This is the earliest failed invariant for the intended fresh-session reattachment. It is a missing generic capability, not evidence of data loss or permission to bypass rollback guards.

## Preserved commitment

Strategy: `strategy-memo:6274d3932fdfb6a36a35e75ff6622ef4031a2cfc6ccf2038ece9e05339f659f9`.
Opportunity: `opening:9f09491588986330ab0c270f95694f8bdc095cde9d1fa3fd627eb78df9e3fb51`.
Commitment: `commitment:0c710308ca07517f885a6c4ace389942460bb1c18b24d5aa981843c90f59ecf6`.
Prepared encounter: `prepared-encounter:0337ba98062034839af87f7504d892ea074f8d9defb43820a8f5714be6fec8f4`.

Exact model is `dots-studio/dots-3-note-preview:free`, serving provider AtlasCloud, historical cost$0. The record retains its original subjective prose, context/material hashes, selected public evidence, policy/version, cutoff880 and original restore epochs/provenance. It still describes imperfect tactics; nothing was rewritten. The source334 Pidgeotto17/Abra16/Rattata15/Charmander18 party, custom moves, IVs, signature/lineages and zero battle items remain locked in the authoritative working state and retained snapshot.

`memo-lock-preservation.json` exports the exact full-record, text, context and lock hashes and trusted IDs. The archived prompt stays7524 bytes,30 eligible public receipts,92 private Rocket receipts excluded, current opposing lead UNKNOWN. This is a read-only audit of the committed prompt, not a new context/opportunity or regeneration.

## Native failure: retained evidence, not fresh acceptance

The earlier real failed run remains unchanged. It logged authenticated identity and initially advancing frames, then froze at frame3643/sequence0/ACK0/drops0. Explicit writer reconnect was logged, but no new frame telemetry reached readiness. The retained process sample places the CPU thread inside `GBAProcessEvents → audio _sample → mCoreSyncProduceAudio → pthread_cond_wait` for708 samples. That locates a sampled wait before frame callbacks; it does not establish its initiating cause or prove a fix.

Source inspection finds two generic readiness limitations: the supervisor starts emulator before host, and its input lease checks current file time/authentication/host state without requiring multiple increasing native frame samples or corresponding host receipt of those frames. A connected socket/process/window/cached sample therefore cannot satisfy the user's new GateA. No runtime change was made after the mandatory GateB stop, and no running process was presented as proof.

All twelve requested native failure-matrix scenarios, two actual fresh Continues and a new real mGBA reconnect remain **UNRUN**, explicitly listed in `failure-matrix.json`. Existing host stale/gap/lost-ACK/freeze tests passed; they are not emulator acceptance. GateA remains unqualified. GateB fails the actual retained-copy restore contract.

## Preservation, tests and accounting

Before reproduction,18 native/host/commitment/pairing/launch/session/failed-telemetry/ledger/config/ROM artifacts were inventoried and hashed. Only SQLite backup copies under ignored `.local/rival01-native-resume/` were opened with the writable store. Original Save24 native/database files, authoritative working database, committed snapshot/context/memo/lock, launch records and request ledger are byte-identical afterward. All23 older protected artifacts also match. No original pairing metadata or cutoff was edited.

Hosted generation remains **1/40 total**, **0 new**; Mercury0/Hermes0/PREP0. The ledger is still closed and unchanged. No credentials were loaded or network request needed. Providers remain disabled. No task-owned emulator or worker was started or remains running.

21 focused host tests passed,0 skips, exit0, including immutable before/after Strategy restore, host reopen without generation, PREP future exclusion/stale generation, bridge stale identity/gaps/lost-ACK/exactly-once and fail-closed process freeze. Two actual retained SQLite-copy reproductions passed their diagnostic assertions. The first exploratory script referenced a nonexistent `decision_log` table and stopped before launch authorization; correcting it to actual `preparation_decision_log` yielded the retained evidence. This harmless failed diagnostic is not counted as a passed test.

The reusable reproduction helper compiles and runs. No bridge/launcher/domain/ROM implementation changed. Permanent EWRAM growth0, retained headroom4 bytes; unchanged ROM hash proves the existing allocation report still applies. No fresh native build or memory measurement is claimed.

Exact reproducible commands, repository root:

```sh
.venv/bin/python tools/rival01_resume_contract.py --label contract-reproduction
PYTHONPATH=tests:tools .venv/bin/python -m unittest tests.test_strategy_memo.MemoTests.test_restart_and_repeat_no_generation tests.test_strategy_memo.MemoTests.test_pair_restore_excludes_future_exact_reload tests.test_prep01.PrepTests.test_restore_future_opportunity_and_stale_generation tests.test_bridge_continuity -v > evidence/phase8/rival01-native-resume/focused-tests.log 2>&1
.venv/bin/python -m py_compile tools/rival01_resume_contract.py
```

The helper refuses overwriting evidence. Use a new bounded label for another disposable reproduction. It calls the existing actual `authorize_launch` only on that clone; it neither starts an emulator nor creates opportunities. Its synthetic authorization nonce is host-copy diagnostic metadata, not a claimed native session.

Evidence: `evidence/phase8/rival01-native-resume/{preserved-inventory,reattachment-contract,contract-reproduction,memo-lock-preservation,root-cause,failure-matrix,preservation-final,verification}.json` and `focused-tests.log`. All earlier failed-run reports/raw evidence are unchanged. `verification.json` states both gates unaccepted.

## Single next dependency

Define and qualify a **generic durable pre-battle descendant resume contract**, distinct from ordinary saved-timeline rollback. It must prove the exact parent native fingerprint/campaign/branch, absence of later native gameplay or unresolved gaps, committed opportunity/context/actor/native trainer identity, permissible host-only descendants, and immutable exact memo/lock/provenance. It must not change Save24's checkpoint hashes, revive abandoned-future memory, or generate new AI work. If permitted, use explicit reconciliation metadata and a fresh session grant; do not rewrite historical commitment identities.

Only after that capability is specified and qualified can a managed fresh Save24 Continue retain the same encounter and satisfy advancing-frame/host-reception evidence. Then perform the real repeated native restart/failure matrix with inference disabled. Current final-native-battle readiness is **BLOCKED**, not produced as a runnable launch recipe. No Rival battle, travel replay, Strategy reroll, Misty, acquisitions, Rocket leadership, later Rival or endgame may start from this disposition.
