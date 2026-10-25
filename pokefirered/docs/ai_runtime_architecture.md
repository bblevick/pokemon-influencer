# AI gameplay architecture — authoritative target v4

## Current System One preparation contract — D33 (2026-10-04)

SYSTEM1-01A is accepted for controlled opening Rick. Implemented provider-neutral `DecisionProvider.decide(state, question, choices)` returns a supplied choice ID, complete optional probabilities/confidence and normalized diagnostics. Preparation uses the exact frozen StrategyMemo in a separate subjective section and all current legal PREP candidates with source-derived neutral mechanics. Semantic approximation never expands the option set or turns prose into facts. A returned choice is recorded before fresh atomic commitment consumes an opportunity, updates finite stock/lineages and locks exact memo/envelope/candidate references. Stored choices replay without credentials or inference.

The native OpenRouter `/api/v1/systemone` adapter supports Jev/Mercury-style text state and one fixed-choice question; no chat/tools/prose parsing or vendor SDK in domain code. Configured Mercury Decide Free remains unchanged; the closed experiment used2 actual POSTs at zero recorded cost. Offline continuity fallback and sole-option selection are distinct sources; no resampling/confidence legality gate. Request/result/commitment schema1 artifacts are in schemas/system1/. Current <=32 choices,32768 request bytes,65536 response bytes and35-second request bounds are preparation-tested, not tactical latency acceptance.

Actual native constructors and paired Save19 reload are proved only for the controlled Rick installation path. BATTLE-01/D34 qualifies the deterministic boundary for controlled Rick singles. SYSTEM1-01B/D35 is accepted for controlled locked Rick ordinary singles at normal speed after actual shadow/enabled battles and paired Save20 reload; broader BATTLE-02 is deferred. Historical battle v1/StrategicPosture fixtures are not silently migrated. Full rematch UX, nonzero items, later acquisitions, other trainers and unsupported battle formats require separate gates. See docs/system1_01a.md, docs/system1_01b_readiness.md and evidence/phase3/system1_01a/completion.json.

The D32 section below records the preceding Strategy-only scope. Its statements that commitment/installation were absent or System One unauthorized are historical; D33 supersedes them for this preparation gate only.


## Current Strategy output contract — D32 (2026-10-04)

Strategy emits a bounded, exact natural-language **StrategyMemo**, not required JSON, tools, enums, evidence IDs or numeric posture. One ordinary completion interprets the existing actor-filtered context and legal preparation constraints. Approximately100–250 words is a prompt target, not a semantic validation requirement. Host validation enforces nonempty strict UTF-8, at most4096 UTF-8 bytes, no unsafe control/format characters (paragraph LF allowed), and the current immutable actor/job/branch grant. The provider also enforces at most1800 output tokens,65536 response bytes,24576 request bytes/conservative input tokens,35 seconds/request and120 seconds/job. A failed completion produces explicitly labeled deterministic prose fallback; no repair loop.

Persist accepted text verbatim with host-generated strategy/job/actor IDs, campaign/branch/generation/cutoffs, context/material hashes, preparation-envelope reference, persona/configuration/prompt versions, timestamp/cursor and provider/model diagnostics. Reuse stored text on restart, UI refresh and repeated decisions. Fresh legitimate opportunities/material precommit evidence may yield different prose; replay does not regenerate it. Future commitment must atomically lock the exact memo reference/hash alongside the team. Commitment/installation is not implemented here.

A memo is subjective interpretation. Even an unsupported prediction remains text: it never becomes canonical truth, actor knowledge, acquisition permission, resources, preparation selection or a battle action. Future System One requests must separate **AUTHORIZED FACTS** from **STRATEGY MEMO — SUBJECTIVE**, pass the exact stored text, and allow only supplied current legal candidate/action IDs. No prose-to-facts or prose-to-numeric-posture conversion is required or implemented.

Historical posture schemas, prompt/config hashes, records and closed experiments remain unchanged. `strategy/memo.py` adds schema3/prompt2 MEMO receipts using the existing paired Strategy cutoff/hash. Historical internal projection key `postures` retains its name to preserve existing checkpoint hashes; `memo_records()` exposes only schema3 text. Explicit MemoStore adoption is limited to the new acceptance working copy; legacy StrategyStore refuses a memo-enabled database. Original databases are not migrated or rewritten. Normal inference remains disabled. No System One, party/resource/ROM change or endgame work is authorized.


Architecture realignment authorized 2026-10-02 (D22). This defines future work; it does not authorize implementing later phases or new live roles. Accepted WORLD/MEMORY/SOCIAL/bridge foundations remain accepted. HERMES-01 implementation is preserved, including accepted native-live v2 closeout, preserved original10-attempt ledger, separate5-attempt closed renewal and stop condition in `hermes01.md`. Normal inference is disabled.

## Roles and authority

| Component | Target responsibility | Boundary |
| --- | --- | --- |
| Hermes | Persistent social-memory director: process mandatory completed-battle recaps, retain provenance-backed campaign memory, retrieve continuity and prepare scoped NPC briefings/notes | Never decides whether required posting occurs; cannot turn director knowledge into NPC knowledge without an authorized delivery path |
| PokeBook | Social-memory system and in-world interface over public posts, private observations, delivery/exposure and director views | Views have separate grants; public existence, feed availability, actual NPC exposure and retained knowledge remain separate |
| NPC strategy LLM | Interpret authorized briefing/personality with current companions, finite inventory and legal preparation envelope | Strategic intent/preferences only; no unrestricted party edits or grants |
| System One preparation selector | Select among dynamically generated, validated roster/moveset/item-allocation candidates using accepted intent | Candidate ID only; deterministic service revalidates, spends/reserves resources, commits and locks |
| System One battle controller | Select current legal moves, switches, items and forced replacements using locked preparation/intent and evolving permitted battle context | One current legal action ID; ROM revalidation before execution, no mid-battle roster mutation |
| Deterministic services / ROM | Define feasibility, knowledge permissions, acquisition/resources/progression, validate/install/execute and record actual outcomes | Rules offer meaningful choices; they do not preselect all strategy or delegate legality to a model |

The three model slots remain independently replaceable: Puppeteer, Strategy and System One. System One has two typed responsibilities under its existing slot, not an implicit fourth provider. Current configured Inkling/Nemotron/Mercury providers and environment variables remain unchanged. No new entitlement, API mapping or capability is inferred from this architecture. Preparation choice compatibility and live battle coverage need separately authorized evidence. Offline deterministic providers use the same contracts.

## Event-driven social continuity

Completed supported trainer battles always create durable recap obligations. Hermes processes evidence and persistent memory; bounded deterministic fallback enforces publication on failure. Recap/post processing is part of a director role, not the whole role. Canonical truth, director summaries and actor knowledge remain different stores/projections with provenance. A fresh worker is a fresh conversation/home, not a reset of branch-aware game memory.

PokeBook is the game's information-flow system; its UI reads those services. NPC delivery/exposure scheduling runs from game events/opportunities through deterministic bounded services even when the player never opens the feed. Delivery into an unread feed still does not confer knowledge. A recorded actor-specific exposure or authorized targeted briefing receipt is required before the NPC retains a claim. Player UI access cannot trigger universal knowledge, and closing/hiding a feed cannot erase witnesses' private observations. Current SOCIAL-01 proves service-level explicit exposure; autonomous exposure scheduling and broader briefing delivery are future work, not already accepted gameplay behavior.

Always-on means a durable available director plus bounded event-driven jobs, not continuous model inference, resident unbounded conversations or wall-clock trainer growth. Pause/absence/provider failure does not invent events. Fresh worker cleanup preserves authoritative databases, branch cutoffs, commitments and required audits. Retries have stable semantic identities; saves/restores revoke stale grants and hide inaccessible future memory.

## Preparation and battle flow

```text
Completed battle → mandatory recap + private episode
                              ↓
PokeBook delivery → explicit NPC exposure / authorized briefing receipt
                              ↓
Actor-scoped briefing + personality + own companions/inventory
                              +
Deterministic legal preparation envelope / diverse feasible candidates
                              ↓
NPC strategy → exact persisted subjective StrategyMemo
                              ↓
Legal complete PREP candidates + memo + AUTHORIZED FACTS → System One selection
                              ↓
Deterministic revalidation / resource commit → locked preparation
                              ↓
Safe ROM installation → legal battle actions + evolving permitted context
                              ↓
System One battle selection → current ROM revalidation / actual execution
```

The normative shared contract is [Preparation envelope v2](preparation_envelope.md), defined before STRATEGY-01. Stage/earned-epoch levels, actual move acquisition, native/nearby access, finite resources, change budgets, signature lineages and Gym themes define feasibility. Choices must be tactically meaningful where rules allow; a set of equivalent copies or a single rules-selected strategy fails diversity acceptance. No feasible alternatives is an explicit supported baseline case, not permission to relax rules.

Selected preparation is validated, resource-accounted, committed and locked before encounter readiness/installation. Later posts/player party swaps/losses/feed reloads do not silently rebuild that encounter. Actual resource consumption/replenishment/healing follow explicit game rules. Evidence can change the next eligible preparation, not the current locked snapshot. Event-based invalidation, idempotency and paired-save branch selection govern recovery.

Gym Leaders retain signature companions and primary-theme identity but may have limited mixed-type support through explicit content caps. Bounded first-encounter Gym preparation is an approved target expansion of the authored-first-roster default; it uses stage and finite starting resources, not invented rematch epochs or hidden-player scouting. Ordinary/unconfigured bosses retain authored first rosters. Exact Gym bounds must be authored/tested before integration.

## Roadmap and current limits

Define/implement PREP-01 shared envelope and lawful candidate generation before STRATEGY-01 consumes it. Separate SYSTEM1-01A selection/resource commitment/safe installation from SYSTEM1-01B live battle control. `backlog.md` gives dependency and acceptance gates; neither part is completed by a provider fixture or model alias. Retain deterministic BATTLE-01 baseline and source/export/integration gates, rather than restarting foundation tickets.

Current bridge observations report `legalActionsComplete=false`. Host StrategyMemo runtime is implemented. No complete legal-action exporter, locked party installer or System One gameplay controller is implemented. [Battle coverage](system1_battle_decisions.md) records moves, switches, items, forced replacement, Struggle and special-mode gaps. AI JSON packets remain host contracts, not a new wire ABI. Current ROM allocation/headroom and unsupported unmanaged load limitations remain unchanged.

[Conflict/migration report](architecture_realignment.md) distinguishes older contracts, deliberate changes and outstanding schema/API/content decisions. Runtime/provider correlation records exact authorized inputs, versions, scope/cutoffs, actual output/fallback and usage; replay never re-infers history. No provider SDK/model ID belongs in game-domain or ROM code. No endgame expansion.

POKEBOOK-01 native viewer is accepted under D24: scoped public participant history/incoming followers, read-only pages, resource/fault/paired-restore proof, no new inference or NPC exposure. It does not implement strategy/preparation/full campaign content. Current readiness: docs/strategy01_readiness.md; next dependency task ROSTER-01 supplies PREP-01 legality data, with CONTENT-01 required before executable preparation.

CONTENT-01/D26 opening bindings now exist: source-preserving first encounters, Rick10/Doug11 first post-Boulder, finite zero supplies/acquisitions, explicit regions and Onix/Geodude opening Gym bounds. They are pure policies, not trained or installed parties. PREP-01 can consume them; trusted flag/current-state issuance and executable envelopes/candidates remain prerequisite work. Mixed-type future Gyms, Strategy and System One A/B remain separately gated.

D27 separates supported campaign adaptation contracts from conservative opening activation. Shared configurable acquisition allowances0/1/2 and aggregate move budgets preserve identity, finite resources and active capacity; later probability/spacing/campaign caps await explicit qualification. PREP will implement a reproducible weighted draw among filtered native/nearby origin pools before System One selection/no-change; accessible/exceptional grants remain separate. CONTENT supplies pure expressiveness/constraint tests only, with no sampler, acquisition execution or later content activation.

## PREP-01 implementation boundary (D28)

The neutral first-pass feasibility service is implemented in prep/ against accepted source catalog and opening policies; final live qualification is recorded in evidence/phase3/prep01/completion.json. It exports separate envelope/candidate-set identities and complete zero-acquisition host plans, with no choice, commitment, installation or strategy inference. `trainer_packet(actor)` remains the separate scoped briefing interface; PREP does not retrieve it or director knowledge for generation. Intent-conditioned materialization, actual commitment/installation and System One battle coverage remain their separate gates. Later cap1/cap2 envelopes are scenario-only; PREP-ACQ-01 explicitly gates origin sampling and complete acquisition packages. See prep01_readiness.md.


D32 acceptance (2026-10-04): corrected StrategyMemo host runtime and actual free Nemotron smoke/Rick result accepted. Exact model text survives fresh host/native Save17 Continue, paired Save16 rewind excludes it/late grant, and paired Save17 return retrieves it without inference.67 unique focused tests/0 skips and actual-artifact audit passed;16 full Rick option plans, knowledge/history/companions/resources and ROM unchanged. Budget closed2/2; historical records/inputs/evidence preserved and all task processes stopped. See docs/strategy01.md and evidence/phase3/strategy01/memo/completion.json. Next separately authorized SYSTEM1-01A; no selection/commit/install/action or endgame implemented.


Current accepted tactical experiment: docs/system1_01b.md (D35), with separately scoped HTTP2.35/worker2.55/host2.75-second bounds and unchanged native180 frames. Preparation35-second and retained BATTLE host2.5-second defaults are unchanged. Actual enabled native control and paired persistence are proved; early shadow/fallback timing failures remain excluded and recorded. Ledger closed/default hosted disabled.

## D36: information quality before strategic interpretation

VIRALITY-01 adds follower-scaled public discovery, explicit chronically-online
scouting exposure and privately authorized Rocket observation delivery.
Deterministic source/path/campaign-order quality belongs to host services;
Strategy interprets scoped claims subjectively. `strategy/social_context.py`
provides an offline v3 social projection without changing accepted v2 input
hashes/memos or enabling any provider. Adoption by inference requires an explicit
new prompt/context version. Delivery, exposure, private observation and director
memory remain distinct. Native-ID prominence and frozen post distribution epochs
never authorize hidden player state. Contracts and limits: docs/virality01.md.
