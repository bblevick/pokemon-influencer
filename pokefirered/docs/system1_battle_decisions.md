# System One — preparation selection and battle control target

## Current System One preparation contract — D33 (2026-10-04)

SYSTEM1-01A is accepted for controlled opening Rick. Implemented provider-neutral `DecisionProvider.decide(state, question, choices)` returns a supplied choice ID, complete optional probabilities/confidence and normalized diagnostics. Preparation uses the exact frozen StrategyMemo in a separate subjective section and all current legal PREP candidates with source-derived neutral mechanics. Semantic approximation never expands the option set or turns prose into facts. A returned choice is recorded before fresh atomic commitment consumes an opportunity, updates finite stock/lineages and locks exact memo/envelope/candidate references. Stored choices replay without credentials or inference.

The native OpenRouter `/api/v1/systemone` adapter supports Jev/Mercury-style text state and one fixed-choice question; no chat/tools/prose parsing or vendor SDK in domain code. Configured Mercury Decide Free remains unchanged; the closed experiment used2 actual POSTs at zero recorded cost. Offline continuity fallback and sole-option selection are distinct sources; no resampling/confidence legality gate. Request/result/commitment schema1 artifacts are in schemas/system1/. Current <=32 choices,32768 request bytes,65536 response bytes and35-second request bounds are preparation-tested, not tactical latency acceptance.

Actual native constructors and paired Save19 reload are proved only for the controlled Rick installation path. BATTLE-01/02 fair legal-action observation/export/execution/fallback and SYSTEM1-01B remain unimplemented. Historical battle v1/StrategicPosture fixtures are not silently migrated. Full rematch UX, nonzero items, later acquisitions, other trainers and unsupported battle formats require separate gates. See docs/system1_01a.md, docs/system1_01b_readiness.md and evidence/phase3/system1_01a/completion.json.

The D32 section below records the preceding Strategy-only scope. Its statements that commitment/installation were absent or System One unauthorized are historical; D33 supersedes them for this preparation gate only.


D22 expands the existing System One slot to two responsibilities. **SYSTEM1-01A** selects one candidate from the shared legal preparation envelope, followed by deterministic resource commit/lock and safe ROM installation. **SYSTEM1-01B** controls current legal battle actions using the installed locked preparation, accepted strategic intent and evolving permitted battle context. See `preparation_envelope.md` for the shared input/selection/commitment contracts. Both have deterministic offline fallback; preparation selector support is not established by a battle-provider API. Preparation is now implemented/accepted in schema1 SYSTEM1-01A; this document's historical tactical schemas do not establish live battle control.

## Existing battle packet v1 — preserved skeleton, target migration required

Contracts are `../schemas/ai/battle_request.schema.json`, `battle_result.schema.json`, and `strategic_posture.schema.json`; fictional static examples are under `../schemas/ai/examples/`. They are host-domain JSON, not a wire ABI or emulator observations.

BattleDecisionRequest carries schema/request/battle/turn/trainer IDs, branch/save/session/generation/sequence/phase and observation hash; authorized numeric personality, accepted StrategicPosture, visible state, provenance-backed known opponent claims, recent bounded history and explicit legal action IDs/kinds/visible parameters. Catalog/ROM identity binds the interpretation. Host-only identity is retained for correlation and need not all be sent to a vendor.

The visible schema permits own active species/HP/known moves, opponent revealed species/public HP fraction/revealed moves/status, field weather and authorized history. It excludes opponent unrevealed party, moves, items, exact private stats, private player swaps, future actions and RNG. A claim requires evidence ID and knowledge cutoff; a schema alone cannot establish permission. Context builder must enforce provenance and scope before serialization. Own bench/item actions can be represented only when explicitly authorized by the supported-mode action exporter.

StrategicPosture contains version, posture ID, trainer/branch, evidence cutoff, enumerated objective, bounded aggression/risk/switch/item preferences and evidence IDs. It confers no legality/resource permission and is frozen for the encounter. Neutral posture is the offline fallback. D22 adds envelope-bound strategic intent before preparation selection; this v1 tactical posture alone is not the full future strategy contract. Target battle packet v2 must bind accepted intent ID/hash, preparation commitment ID/snapshot/install hashes and preparation envelope version/hash. The schema remains v1 until explicitly versioned at its integration gate; do not silently inject these fields into v1 closed objects.

BattleDecisionResult carries version/request ID, selected legalActionID, optional action probabilities/scores, provider/model, latency and status/error/fallback. Provider diagnostics are normalized by the trusted adapter; fallback records both the error and the actual fallback provider/model. Selected action is still required for fallback. If the legal list is empty, do not call a provider: use the native battle-mode path. Forced replacements and Struggle must be exported as explicit actions when appropriate.

Validation order: bounded schema → request correlation/model policy → current branch/battle/turn/phase/generation/hash → selected ID and diagnostics keys in current legal set → deterministic domain validation → bounded ROM command → ROM revalidation immediately before execution. Do not interpret model prose as a move ID, item, script or mutation. Reject duplicate/conflicting replies, and recompute/export legality when state changes. JSON Schema cannot enforce cross-packet membership, uniqueness by ID, summed probabilities, current state or evidence permissions; future domain validators must.

Host assembles and stores each packet/history, never relies on provider sessions. Result plus accepted/fallback decision is durably recorded for branch-aware replay. A provider timeout must not delay canonical gameplay indefinitely. Existing BRIDGE-01 PING timeout is not the battle budget. Future battle deadline/p50/p95 goals must be measured in normal/fast-forward play; hosted native decisions remain experimental and fallback first.

Initial selected hosted candidate is `inception/mercury-decide:free`, overriding the earlier Jev selection in the user attachment. A deterministic utility/seeded-tie policy remains the offline implementation target. Neither exists as gameplay AI today. [Model evaluation](model_evaluation.md) gates promotion, and BATTLE-01/02 precede live battle integration. Wild/double/link/Safari/special modes preserve native behavior until audited separately.

BRIDGE-02 supplies a distinct partial NPC-side observation, described in `bridge02.md`. Unknown opponent status and field weather are optional in the request schema; omission does not mean `none`. The current wire observation explicitly reports `legalActionsComplete=false`. Its projection can populate the corresponding visible-state subset, but cannot create a BattleDecisionRequest without a later audited legal-action exporter, host identities/provenance and context builder. Canonical event logs are never automatically NPC knowledge.


## Outstanding legal-action coverage

The current ROM still uses vanilla battle AI. Exported observations have `legalActionsComplete=false`; no inference battle command lane or complete legal-action builder exists. Existing enum/schema examples are fictional static validation, not any of the following execution proofs. Existing ordinary battle smoke tests do not satisfy SYSTEM1-01B.

| Path | Outstanding exporter/executor and acceptance coverage |
| --- | --- |
| Moves | Current usable slots/PP/targets, status/lock/disable constraints, action-ID mapping, priority/phase and immediate native revalidation |
| Voluntary switches | Living own bench choices, trapping/forced-state constraints, stable lineage/slot mapping and actual native switch execution |
| Items | Own finite usable inventory, target/phase applicability, per-encounter rules and acknowledged actual consumption without duplication |
| Forced replacements | Distinct replacement phase, living candidates, loss/no-candidate native path, stale move/item reply rejection |
| Struggle / no usable move | Explicit mandatory legal action/native path, no fabricated usable move; test before hosted selection |
| Empty legal set | No provider call; audited native transition/termination rather than selecting an invented action |
| Special modes | Double/multi/link/Safari/scripted/special cases remain explicitly native/excluded until individually audited |
| Lifecycle | Normal/fast-forward deadline measurement, timeout/host absence, duplicate/conflicting reply, current action-set change, branch/restore rejection and recorded replay |

SYSTEM1-01A must prove selected candidate membership, one-time resources, locked encounter preservation and actual installed party equivalence. SYSTEM1-01B must separately prove supported paths in real emulator battles with fair information and native legality revalidation. Existing BATTLE-01/02 baseline and source/export gates remain dependencies, not completed work to restart. More detailed move/status/item exclusions require a pinned-source coverage manifest before activation; this table deliberately does not claim comprehensive battle mechanics support.
