# Dependency-ordered Codex backlog

Each ticket ends with implementation evidence, tests run, skipped/blocked checks, and an update to `docs/status.md`. Do not mark a ticket complete because a design document describes it.

## Phase 0 - baseline and capabilities

### SETUP-01 - Inventory and safe workspace

Dependencies: none. Create status/capability report, verify handoff files, identify OS/tools/permissions and local dump path, establish ignored local/artifact directories. Inspect local header/checksum without uploading ROM data.

Done: a reproducible environment report and clearly labeled unknowns; no accidental ROM/secret commit.

### SETUP-02 - Pin and build baseline

Dependencies: SETUP-01. Choose source-management strategy, pin actual commits/toolchain, follow upstream build instructions, build a matching target, record checksums/logs, and add real build wrappers.

Done: clean baseline comparison passes on the supported revision; lock manifest contains actual identifiers, not placeholders. Missing dependencies remain blockers, not fictional passes.

### SETUP-03 - Emulator smoke test and source hook map

Dependencies: SETUP-02. Boot, battle, save, reload; probe scripting/memory/socket/snapshot capabilities. Trace actual party, action, first-win, rematch, menu, and save paths in pinned source.

Done: real emulator evidence plus a hook/capability map and a decision on the candidate build.

## Phase 1 - narrow bridge

### BRIDGE-01 - Allocated mailbox and build manifest

Dependencies: SETUP-02, SETUP-03. Allocate safe memory, define generated fixed-width layouts, emit ELF-derived address/build manifest, and implement feature-flagged ping.

Done: size/alignment checks, wrong-build rejection, canaries, and real round trip.

### BRIDGE-02 - Bounded transport and request lifecycle

Dependencies: BRIDGE-01. Implement tested local transport, framing, authentication/session IDs, partial IO, backpressure, deadlines, and stale-response rejection.

Done: real timeout/disconnect/reconnect traces; no frame-blocking host inference.

### BRIDGE-03 - Events and bounded UI exchange

Dependencies: BRIDGE-02. Export one battle-complete event and handle a small text/page payload safely. Add acknowledgment/retry without duplicate effects.

Done: actual event source/sequence trace and in-ROM text rendering; malformed text/payloads rejected.

## Phase 2 - rules, memory, and saves

### STATE-01 - Ledger, projections, and outbox

Dependencies: SETUP-01. Implement typed records, migrations, serialized writer, event identities, transactional projections, durable jobs/outbox, and deterministic replay.

Done: duplicate/conflicting event tests, crash/retry tests, replay equivalence.

### SAVE-01 - Audit and implement save markers

Dependencies: STATE-01, BRIDGE-01, SETUP-03. Audit flash layout/checksums and choose a safe marker or documented alternate pairing scheme.

Done: new-game initialization, save/load consistency, layout and corruption tests; no assumed padding.

### SAVE-02 - Paired checkpoints and branches

Dependencies: SAVE-01, BRIDGE-02. Implement recoverable checkpoint protocol, host cursor restoration, forked history, managed load, and mismatch recovery.

Done: no future memories after load; crash at each checkpoint step preserves a valid pair.

### MEMORY-01 - Deterministic actor evidence and delivery provenance

Dependencies: accepted WORLD-01 (STATE/SAVE foundations), BRIDGE-02. User scope on2026-10-02 supersedes the original confidence/decay/beliefs portion: implement only direct observations, explicit targeted delivery receipts, immutable typed claim provenance, actor-bound retrieval and paired-save/branch cutoffs. No inferred beliefs, confidence, decay, repost mechanics or LLM in this ticket.

Done within that user scope: Rick knows his real loss; Janice knows nothing until one explicitly delivered claim; receipt provenance does not expose Rick's other observations; restart/replay and native-save restore/divergence pass. Confidence/decay/corroboration and social exposure policies remain separately deferred. See repository-root docs/memory01.md and docs/memory_schema.md.

### SOCIAL-01 - Deterministic follows, publication and exposure

Dependencies: accepted WORLD-01, MEMORY-01. User authorization on2026-10-02 scopes this ticket to explicit eligibility/first-win directed follows, supported recap proposals/publication, bounded one-hop feed delivery, separate exposure/attributed MEMORY receipts, replay and three-cutoff managed save pairing. Narrow posting originally listed under SOCIAL-02 is included here by explicit authorization (D20). Friendship/reputation, unique bonuses and broader relationship scoring remain deferred.

Acceptance: new live Rick win creates one follow and a supported loss+Bulbasaur recap; unread Janice feed creates no memory; exposure delivers only those published claims, withholding observed Tackle/private provenance. Restart, retry, offline replay and paired-save restore/social-only divergence must preserve the boundary. Completed within this user scope: new live lifecycle, host restart/retry, three-cutoff native-save restore/social-only divergence and original later checkpoint restoration passed. See repository-root docs/social01.md and docs/social_schema.md.

### SOCIAL-02 - Template PokeBook and puppeteer skeleton

Dependencies: SOCIAL-01, MEMORY-01. Narrow deterministic recap publication/distribution/exposure is authorized under SOCIAL-01; this broader ticket remains deferred. Additional social actions, replies, notifications and UI require separate scope. No belief inference is implemented by SOCIAL-01.

Done: scoped causal chain from event to post to exposure to belief, without any LLM requirement.

## Phase 3 - roster and battle intelligence

### CONTENT-01 - Trainer/region binding manifest

Dependencies: SETUP-03. Map real trainer IDs, original parties, scripts, home/nearby maps, follow exceptions, rematch predicates, and unsupported battle modes.

Done: exhaustive coverage for the slice, explicit exclusions, no invented canonical trainer bindings.

### ROSTER-01 - Export authoritative legality catalog

Dependencies: SETUP-02. Export selected-version encounters, species/moves/evolution, trainer baseline data, and approved move/item acquisition rules.

Done: catalog ties to commit/hash; fixtures detect wrong-version and underlevel/off-region errors.

### ROSTER-02 - Constrained preparation

Dependencies: ROSTER-01, CONTENT-01, MEMORY-01. Stable Pokemon IDs, earned-epoch growth, legal move/acquisition/resource options and bounded diverse validated candidates; coordinate PREP-01. Deterministic fallback selection is required, but rules must not preselect all strategic choices (D22).

Done: mutation-budget and hidden-party metamorphic tests pass; no-change remains valid.

### ROSTER-03 - Rematch lifecycle and frozen plans

Dependencies: ROSTER-02, SOCIAL-01, STATE-01. Implement predicate-based opportunities, readiness, immutable commitment, retries, once-only rewards, and legacy rematch routing.

Done: no flag-reset hacks, no stacked invitations/payouts, no rerolls after party changes or losses.

### BATTLE-01 - Native legal choices and deterministic execution (D34)

Dependencies: accepted SYSTEM1-01A, ROSTER-01, MEMORY-01 and bridge/save foundations. User expanded this ticket to the controlled native battle boundary; no utility scorer/personality scoring or model calls. Enumerate authoritative moves/switches/finite items/replacements/Struggle, export fair bounded history/exact memo, fixed choices, asynchronous deterministic provider, native revalidation/vanilla fallback and paired audit.

Accepted for armed D33 Rick ordinary singles. Live move/switch/sole replacement/delayed fallback/full normal battle/save reload and privacy passed; nonzero item/multiple replacement tests are actual-C controller fixtures, not emulator effect proof. See docs/battle01.md and evidence/phase4/battle01/completion.json. Broader modes/campaign integration remain BATTLE-02; next separate authorization is SYSTEM1-01B for this qualified path.

### BATTLE-02 - ROM battle integration and fallback

Dependencies: BATTLE-01, BRIDGE-02, ROSTER-03. Integrate safe locked-party construction, current legal-action export/execution for moves/switches/items/forced replacements, and fair reduced fallback. Coordinate separate SYSTEM1-01A/B acceptance gates without claiming enum/schema coverage as execution evidence.

Done: actual battles under normal/fast-forward/timeouts; unsupported modes remain safe and explicit.

## Phase 4 - playable slice

### UI-01 - In-ROM PokeBook

Dependencies: BRIDGE-03, SOCIAL-02. Implement menu entry, feed/profile/challenge views, bounded text encoding, optional posting, queued notifications, and safe back navigation.

Done: actual screenshots at text limits; no battle/menu interruption or required cloud wait.

### SLICE-01 - Opening through Brock and return rematch

Dependencies: SAVE-02, UI-01, BATTLE-02, CONTENT-01. Bind 6-10 profiles, author onboarding and fallback text, and complete the entire first causal loop.

Done: vertical-slice acceptance story runs on real ROM with each starter and LLM off; no future-memory leak after restore.

## Phase 5 - bounded model agency

### MODEL-01 - Provider adapter, budgets, and recording

Dependencies: SLICE-01. Add a configurable provider, strict structured validation, fake provider, credentials handling, quotas, timeout, response recording, and template fallback.

Done: failure matrix passes; no real secrets or paid calls in default tests.

### MODEL-02 - Puppeteer/NPC proposals and writing

Dependencies: MODEL-01. Historical broad grouping is superseded for remaining gameplay AI by PREP-01, STRATEGY-01 and SYSTEM1-01A/B below. Later lawful director briefings/social opportunities and generated style require their own scope; preserve HERMES-01 mandatory-recap implementation and stop condition.

Done: model enriches visible behavior; no canonical state effects from unvalidated prose; read tools cannot cross NPC boundaries.

### OPTIONAL-AI-01 - Evaluate a compact learned System 1 policy

Dependencies: stable BATTLE-02 and separately approved research scope. Produce a dataset/evaluation/training plan and a real comparison under identical information limits before promotion.

Done only when actual model artifacts and measured benefits exist. Not required for the first campaign release.

## Phase 6 - campaign expansion

### CONTENT-02 - Regional batches

Dependencies: SLICE-01; MODEL-02 for model-enriched release. Expand trainer profiles, reachability, event coverage, social templates, and rematches in reviewed map batches.

Done per batch: binding completeness, alternate-route predicates, legality tests, playable segment, visual review. Do not load every NPC into simultaneous model sessions.

### CONTENT-03 - First-Champion regression

Dependencies: CONTENT-02. Audit original quest/Pokédex/VS Seeker interactions, remaining special battles, economy, and all required progression.

Done: complete campaign evidence, alternative-order tests, documented unsupported optional content, endgame disabled.

## Phase 7 - release

### RELEASE-01 - Reliability and balance pass

Dependencies: CONTENT-03. Run fault injection, migration/checkpoint tests, candidate coverage, model adversarial tests, performance and human playtests.

Done: critical regressions fixed; evidence distinguishes automated and manual coverage; supported-platform limits explicit.

### RELEASE-02 - Patch and companion packaging

Dependencies: RELEASE-01. Produce a patch for a verified local base, runtime/bridge install, dependency locks, checksum manifest, recovery tools, and clean-machine instructions.

Done: patch reconstructs target, wrong base rejected, no full ROM/secrets/user saves shipped, and clean install/save/reload tested.

## Execution discipline

Host-only state, memory, and catalog work can run in parallel after interfaces are agreed, but parallel contributors must not independently redefine the protocol or migrations. One owner reconciles schema changes. Do not begin campaign-scale content generation before the vertical slice proves the interaction.

Endgame tasks are intentionally absent. Move ideas to `end_game_concept.md`; do not add their implementation under a generic polish ticket.


## User-scoped next milestone after BRIDGE-03: WORLD-01

2026-10-02 user direction: stop adding bridge functionality after supported BRIDGE-03 acceptance. WORLD-01 is the next separately authorized milestone: canonical world state, persistent trainer identities, event ingestion and save/branch pairing, without an LLM. Coordinate STATE-01 and SAVE-01/02 dependencies plus source-backed trainer identity binding; preserve the canonical-facts versus NPC-authorized-knowledge boundary. This note does not mark those tickets complete, implement relationships/follows, or authorize automatic progression beyond BRIDGE-03. Endgame remains deferred.

### WORLD-01 — complete within the separately authorized scope (2026-10-02)

Implemented canonical SQLite history/projections/replay, source-backed persistent trainer families, explicit imported/paired/incomplete lineage, validated normal-save fingerprints, durable checkpoint intents and fresh-process restore/deferred branching. Real Rick102, host restart/dedupe, S1/S2 and divergent normal-save restore evidence are in repository-root `docs/world01.md` and `evidence/phase2/world01/`. This coordinates the persistence work described by STATE-01/SAVE-01/02; no broader legacy ticket or social job worker is separately claimed. Arbitrary savestates remain unsupported. Next separately scoped ticket: **MEMORY-01**, deterministic scoped observation/delivery provenance and authorized retrieval before any NPC interpretation or LLM. Stop after WORLD-01; SOCIAL/Hermes/PokeBook/follows/reputation/AI/endgame remain deferred.

### MEMORY-01 — complete within the separately authorized scope (2026-10-02)

Deterministic trainer actors, whitelisted direct evidence, targeted development delivery/provenance, compact actor-bound retrieval and canonical+subjective checkpoint/branch cutoffs are implemented. New live Rick102 → Rick knowledge / Janice empty → one explicitly delivered result / Janice only that claim, host restart, normal-save rewind/divergence and positive S2 reload passed. See repository-root `docs/memory01.md`, `docs/memory_schema.md`, `evidence/phase2/memory01/`. Canonical truth is still distinct from evidence/knowledge; no interpretation/LLM/social mechanics are claimed. No broader legacy ticket is separately marked complete. Stop MEMORY-01; next separately scoped recommendation **SOCIAL-01**. Endgame stays deferred.


### SOCIAL-01 accepted user scope (2026-10-02)

First-win directed follow and evidence-backed recap→one-hop unread feed→explicit exposure→only published reported MEMORY claims are complete. Publication/feed/knowledge remain distinct; private provenance is internal only. New Rick/Bulbasaur/Tackle subset, Janice-only delivery, Doug exclusion, restart/replay and managed three-cutoff save branches passed. Narrow recap posting moved from SOCIAL-02 by explicit authorization; broader SOCIAL-02/reputation/bonuses/fullUI remain deferred. Stop SOCIAL-01. Next separately authorized HERMES-01 uses the scoped services without owning canonical truth, grants or persistence; strategy/battle/rosters/endgame stay deferred.


### HERMES-01 — host implementation complete, native live generation acceptance open (2026-10-02)

Actual pinned official Hermes, durable mandatory recap/fallback obligations, private provenance-backed puppeteer episodes, actor-scoped packets, four-cutoff paired saves/replay and safe fresh-home cleanup are implemented. 209 host tests pass, including actual Hermes with mocked inference and cross-job memory. Real live shadow validated submission and fresh durable recall passed; native enabled generation retrieved serial tools and exhausted three requests, so its post/episode are explicitly deterministic fallback. New native save/restore/privacy and positive S3 reload pass. Ten of ten live attempts are used; v2 bundled retrieval is offline tested only. No full-ticket completion is claimed. Evidence/report: docs/hermes01.md, evidence/phase2/hermes01/. Single next task is HERMES-01 enabled-native v2 acceptance under separately renewed bounded live authorization, not strategy/System One/team changes/full UI/endgame.


## Remaining AI gameplay roadmap — D22 architecture target, not implementation authorization

### PREP-01 — shared envelope and feasible preparation candidates

Dependencies: ROSTER-01, CONTENT-01 and accepted WORLD/MEMORY/SOCIAL substrate; coordinate ROSTER-02 resource/lineage rules without restarting foundations. Normative contract is already defined in docs/preparation_envelope.md before STRATEGY-01. Implement versioned host envelope/candidate schemas, durable companion/resource/opportunity receipts, finite inventory/provenance, stage/earned-epoch bounds, move acquisition, native/nearby access, signatures/theme and bounded first-Gym representations. Generate bounded diverse complete neutral candidates with an unchanged fallback option and rule proof references. PREP-01 selects nothing; intent-conditioned materialization and selection/commitment/installation contracts remain downstream. Close the actual paired native Boulder gate and prove fresh-runtime and before/after restore eligibility.

Acceptance: actual pinned catalog/resource feasibility, meaningful legal alternatives where possible, deterministic generation/replay, no hidden-party dependence, illegal acquisition/resource/epoch rejection and branch/save/retry safety. Author exact Gym mixed-support/first-encounter caps before enabling adaptation. No model role required to validate feasibility.

PREP-01 accepted opening scope (D28):338 host tests,30 actual-evidence assertions and native paired Boulder/restart/before-after restore passed. Rick16 complete host candidates; Doug16 scenario-only; Brock/Janice first1 each. None selected/committed/installed. Report: docs/prep01.md; next separately authorized task STRATEGY-01. Later acquisition remains PREP-ACQ-01.

### STRATEGY-01 — actor-scoped subjective StrategyMemo

Dependencies: PREP-01 implemented contract/candidates, HERMES-01 accepted within scope and separately scoped authorized briefing delivery/context. Personality + actor-authorized briefing + current own companions/inventory + preparation envelope → one bounded exact prose StrategyMemo, with host-owned provenance. No tools/JSON/enums are required. Do not pass raw director knowledge or arbitrary party-edit scripts.

Acceptance: exact bounded text/request fixtures, subjective/factual separation, host provenance/unknowns, personality-directed prose, no grants/hidden scouting/selection, single-attempt fallback, stale/replay/pairing. Actual model memo must survive fresh retrieval and paired native restore; mocks do not close the live gate. Live strategy inference requires separate authorization; current provider selection stays unchanged.

STRATEGY-01/D29 current status: host implementation/offline privacy/fallback/native paired replay completed; live acceptance **blocked** after10 permitted requests with no validated posture (final NVIDIA upstream502). Budget closed; all results are fallback. Next work is separately authorized STRATEGY-01 live closeout, not System One. See docs/strategy01.md and evidence/phase3/strategy01/completion.json.

### SYSTEM1-01 — two independent acceptance gates

**SYSTEM1-01A: preparation selection and installation.** Dependencies: PREP-01, STRATEGY-01 (deterministic neutral intent remains fallback), audited safe party-construction source hooks. Consume exact persisted subjective memo separately from authorized facts; select a current validated candidate ID, revalidate/spend or reserve once, commit/lock a prepared snapshot and install through safe native constructors. Prove actual installed roster/moves/items/hash, signature/theme/resource preservation, retry identity and no rerolls from posts/player swaps/losses; paired restores cannot inherit future spends/commitments. Preparation provider mapping/capability and any live call are separately gated.

**SYSTEM1-01B: live battle control.** Dependencies for controlled Rick acceptance: SYSTEM1-01A and accepted expanded BATTLE-01/D34. BATTLE-02 remains broader campaign integration; its old dependency wording is superseded for the already-qualified controlled path. Use locked preparation/exact subjective memo plus evolving permitted observations/history in a separate AUTHORIZED FACTS section. Separately prove current legal moves, switches, items, forced replacements and Struggle through native normal/fast-forward/timeout/restore tests. Native execution must revalidate branch/battle/turn/phase/action hash. Explicitly exclude unaudited modes; see docs/system1_battle_decisions.md. Passing A does not satisfy B; a model fixture or ordinary vanilla battle satisfies neither live integration gate.

PokeBook autonomous bounded NPC exposure and Hermes general scoped briefing/note delivery remain separately scoped follow-up work; player feed opening is not their trigger. Exposure receipts still precede recipient knowledge. The UI displays services rather than owning information propagation. Always-on is durable event-driven availability, never elapsed-time growth or unbounded inference.

The HERMES-01 statement below records accepted historical closeout. Current work is STRATEGY-01 only under its separate bounded authorization; System One remains unimplemented and requires its own scope.

### HERMES-01 — accepted after targeted closeout (D23)

The previous partial status is historical. A new native completed Rick encounter committed actual live Hermes evidence selections through unchanged domain validation, with no fallback. Runtime cleanup, fresh paired rewind/reload, privacy and fresh actual-Hermes retrieval of the newly retained episode passed.211host tests/39closeout evidence assertions; exactly5additional requests, separate ledger closed, original10preserved. See docs/hermes01.md and evidence/phase2/hermes01/closeout/completion.json. Stop HERMES-01.

### POKEBOOK-01 — accepted in the native Rick slice

Dependencies: accepted HERMES-01/WORLD/MEMORY/SOCIAL and existing BRIDGE-03; reuse persisted post/feed/follower services. Define player viewer-safe projection and native in-world history/navigation, bounded text/pages and branch/save-consistent reading. NPC distribution/exposure must remain event-driven and independent of player feed opening; scope any autonomous exposure policy explicitly without conflating unread delivery with knowledge. Readiness/gaps: docs/pokebook01_readiness.md. No UI implementation is performed by HERMES closeout.

Acceptance must show actual persisted/model-sourced and fallback history through authorized views, no private actor/director leakage, save/reload consistency and bounded native UI behavior/absence recovery. The bounded player projection/native screen integration is now accepted in the Rick slice; campaign-scale content remains future work. Later STRATEGY-01 requires executable PREP-01 legality/resource/candidate contracts; SYSTEM1-01A/B retain independent installation/action-coverage gates. Endgame deferred.

POKEBOOK-01 acceptance: native normal-field Start entry, feed/full paginated reader/incoming followers; real offline production battle→recap/follow, labeled stored Hermes/layout rendering, private-history isolation, five measured cleanup cycles, native fault/cancel/absence recovery, fresh paired early/late restores. Report/evidence: docs/pokebook01.md and evidence/phase2/pokebook01/completion.json. No autonomous NPC exposure, player posting/read markers or campaign-scale social content added. **Next dependency task: ROSTER-01**, supplying PREP-01 legality data, coordinating ROSTER/CONTENT dependencies before STRATEGY-01's real envelope consumption; docs/strategy01_readiness.md is planning, not new implementation authorization.

### ROSTER-01 closeout — accepted bounded host qualification

Source catalog and pure eligibility/validation primitives accepted; see docs/roster01.md and evidence/phase3/roster01/completion.json. Broad extraction is not full-campaign authorization. Rick/Brock baselines, FireRed-only routes, individual move/evolution paths, finite resources and fixture-only early contexts are qualified within the documented coverage; missing production stage/inventory/travel/signature/Gym bindings block affected operations. PREP's whole-package/envelope/candidate/commit/install gates remain open.

Single next dependency task: CONTENT-01's actual trainer/region/stage/resource/identity bindings, then PREP-01 coordinated with ROSTER-02. No team, strategy, System One or inference implementation started by this acceptance.

CONTENT-01 accepted opening scope (D26): config/opening_content.json, content.policy and closed schemas bind all four first encounters and Rick/Doug first post-Boulder levels, retained originals/signature, territory, zero resources/acquisitions and exact opening Gym bounds. Pure scenarios are not live flag/ownership/opportunity export. Evidence: evidence/phase3/content01/. **Next: PREP-01**, using this actual pack and implementing trusted current-state adapters, complete envelopes/meaningful candidates and aggregate budget/resource validation in coordination with ROSTER-02. No new live role, commitment/installation or later campaign content was authorized here.

CONTENT-01 D27 addendum: shared configurable acquisition contracts are now separate from opening v2 zero-catch overrides. PREP must not inherit historical acquisition probability/spacing/campaign caps; qualify explicit future profiles, implement reproducible filtered native/nearby weighted origin draws and bounded legal candidates while keeping distant/exceptional grants separate. Active capacity, original/signature retention and versioned commitments apply; no reserves/rotation or live later acquisition was added by CONTENT.

### PREP-ACQ-01 — later acquisition envelope materialization gate

Deferred, inactive follow-up to PREP-01; not part of opening acquisition0. Requires qualified later-stage CONTENT balance (probability/spacing/campaign limit), current capture equipment/history and explicit trainer access. Record eligible-origin draw under configured native/nearby weights, legal capture outcome/identity/history/resource requirements, and validate complete packages with cap1/2 and active-party capacity. Accessible/exceptional origins remain separate explicit grants. Scenario policy/envelope tests are not a live sampler, catch, reserve or team selection. No implementation authorization is granted here.

STRATEGY-01/D30 live closeout status: **LIVE ACCEPTANCE STILL BLOCKED**, renewed3/10 requests all NVIDIA502, ledger closed; original10 preserved. Host/offline40 focused checks pass; no valid live posture. Backup inactive; next separately authorize Strategy model/provider change or later same-model retry. SYSTEM1-01A/B has not started. Evidence: evidence/phase3/strategy01/closeout/completion.json.

STRATEGY-01/D31 backup qualification: **LIVE ACCEPTANCE STILL BLOCKED**. Inkling-small current forced-tool capability gate fails; explicit latest-user Qwen contingency has actual3 failed POSTs400/429/429 within shared5; generic router has no qualifying endpoints. New ledger closed3/5, primary13 unchanged, no accepted live posture/native live persistence.53 unique focused checks/34 artifact assertions pass; next separately authorize a small typed-compatible free-model selection/HTTP400–429 diagnostic benchmark. No System One started. Evidence: evidence/phase3/strategy01/backup/completion.json.


D32 acceptance (2026-10-04): corrected StrategyMemo host runtime and actual free Nemotron smoke/Rick result accepted. Exact model text survives fresh host/native Save17 Continue, paired Save16 rewind excludes it/late grant, and paired Save17 return retrieves it without inference.67 unique focused tests/0 skips and actual-artifact audit passed;16 full Rick option plans, knowledge/history/companions/resources and ROM unchanged. Budget closed2/2; historical records/inputs/evidence preserved and all task processes stopped. See docs/strategy01.md and evidence/phase3/strategy01/memo/completion.json. Next separately authorized SYSTEM1-01A; no selection/commit/install/action or endgame implemented.


## SYSTEM1-01A / D33 — accepted (2026-10-04)

Native Mercury Decide Free chose one of Rick's16 legal PREP candidates from his exact subjective StrategyMemo, with facts kept separate. The actual choice retained the unchanged roster; it was revalidated, committed once, constructed in native FireRed, battled under vanilla AI and paired/reloaded in normal Save19 without reinference. Save17/18/19 restore isolation and stale-result rejection passed.57 unique focused tests/0 skips,37 artifact checks and3 schema checks passed;2 zero-cost calls, closed budget, offline default, workers stopped. Controlled opening Rick installation is not general trainer/item/acquisition support or full campaign rematch UX. SYSTEM1-01B and endgame remain deferred. Next separately authorized dependency task: BATTLE-01, then BATTLE-02/ROSTER-03 before live battle control. See docs/system1_01a.md, docs/system1_01b_readiness.md and evidence/phase3/system1_01a/completion.json. Earlier dated acceptance sections remain historical.


BATTLE-01/D34 accepted2026-10-04 for the scoped native boundary, with0 model calls. Current evidence: docs/battle01.md, docs/system1_01b_readiness.md, evidence/phase4/battle01/completion.json. No SYSTEM1-01B or endgame implementation. Earlier acceptance sections remain historical.


## SYSTEM1-01B / D35 blocked closeout —2026-10-04

Host live/shadow provider implementation and independent setup are complete, but SYSTEM1-01B is not accepted. Configured free Mercury native smoke passed; one actual Rick shadow proposal was valid (String Shot,1.687s), two complete-shadow HTTP attempts exceeded1.9/2.05s and one earlier trial hit the2.25s worker deadline.5 total charged requests including smoke; ledger closed, no retry/substitution/other roles. Two returned responses report zero cost; interrupted request usage is unknown. Full shadow715026728 completed normally under vanilla fallback, with sole forced replacement bypassing inference and an offline mandatory recap. Enabled battle was not run because latency qualification failed.

Actual normal Save20/checkpoint5575c709-d8c9-42ef-aee1-6c9fa80906a1/cursor177 was reloaded in a fresh native Continue and host: five audits, exact memo, D33 lock, recap and replay hashes survive; no further requests. Save19 excludes the future shadow history.25 artifact checks,28 retained +10 final focused tests (34 unique/0 skips),524 protected inputs unchanged. Unchanged BATTLE-01 ROM SHA2566582e03a8a2daff55e47d153fc5eee9838c8ea55803ed446f99b8b6a01b0d570. Exact attempts, latch reopenings, failed trials, commands and blocker: docs/system1_01b.md; evidence/phase4/system1_01b/verification.json. Workers stopped; normal hosted default remains disabled.

Completed new ticket IDs: none. Next task: SYSTEM1-01B latency qualification/acceptance closeout, then continuous VERTICAL-SLICE integration under separate authorization. No phase expansion, roster/memo/resource edits or endgame. Shadow save/reload is not enabled acceptance.


## SYSTEM1-01B / D35 acceptance —2026-10-04 (supersedes interim latency-blocked closeout)

SYSTEM1-01B is accepted for locked D33 Rick ordinary singles at normal speed. Full shadow1660475733 passed with4 real unexecuted Mercury proposals; full enabled3468328694 applied all4 meaningful Mercury choices (String Shot/switch/String Shot/String Shot) through unchanged native guards/controllers. The switch and first String Shot resolved; later move selections were interrupted by fainting, correctly recorded separately. Sole replacements bypassed inference. Both battles ended normally with player wins; no predetermined result or optimality override.

13 total charged requests including smoke/errors;10 returned responses reported cost0,3 interrupted responses lack usage. Same configured free Mercury, no other live roles, reroll/resampling/model substitution. Early deadline/startup/trigger/config-label failures and explicit same-ledger reopenings remain recorded. Final HTTP2.35/worker2.55/host2.75s lie within unchanged native180 frames; retained host default2.5s stays unchanged.8 passing shadow/enabled responses: HTTP median0.621s/max0.904s; host median0.820s/max1.017s. No small-sample p90/p95 claim or fast-forward qualification.

Actual normal Save20/checkpoint5cbfae80-800f-419f-9b45-1d42f4afee1b/cursor177 was freshly Continued with no reinference: exact lock/memo,5 enabled audits, offline mandatory recap and replay hashes survive; abandoned shadows/Save19 future exclusion pass.33 artifact checks,35 unique focused tests/0 skips,524 protected inputs unchanged. Native ROM SHA2566582e03a8a2daff55e47d153fc5eee9838c8ea55803ed446f99b8b6a01b0d570 unchanged. Source implementation/evidence/commands: docs/system1_01b.md; evidence/phase4/system1_01b/verification.json and completion.json. Workers/listener stopped,13-request ledger closed, configured providers/default offline unchanged.

Completed ticket: SYSTEM1-01B only. Next separately authorized task: VERTICAL-SLICE continuous managed campaign integration; docs/system1_01b_readiness.md records gaps. No live nonzero items/multiple replacements, general trainer/mode/rematch/Gym/acquisition expansion or endgame is claimed. Earlier blocked report is historical timing qualification, not current status.

## VIRALITY-01 / D36 closeout — 2026-10-04

VIRALITY-01 accepted for the authorized deterministic host scope. Source-bound
native prominence/scouting/faction policies, frozen follower-scaled reach,
qualified campaign-order relevance, explicit delivery/exposure, original-source
corroboration, Rocket privacy and save/branch/idempotent scheduling are implemented.
Actual prebattle Brock reads only Rick's real published result/Bulbasaur, not
private Tackle; this reuses accepted native history without a new playthrough.
30 final focused cases,466 full-suite cases (26 earlier virality cases rerun by
final suite),21 production assertions,26 artifact checks and2,423 protected
inputs pass. No inference, ROM/team/resource change or new emulator/save occurred.
Four-claim Rocket/Potion and fame/prominence scenarios are explicit host fixtures;
native player-item export remains unqualified.

Evidence/commands: docs/virality01.md; evidence/phase4/virality01/completion.json.
Next: separately authorized VERTICAL-SLICE continuous Rick→public post→Brock
scout/memo/first Gym→broad Gym recap loop. docs/vertical_slice_readiness.md lists
launcher, context-version, first-Gym installation/action and native save gaps.
Later Rick rematch remains a secondary longitudinal test; future geography,
explicit balance migration, real Rocket item coverage and endgame are deferred.

## VERTICAL-SLICE-01 evidence closeout — 2026-10-05

Native deterministic integration, actual Rick/Brock Hermes recaps, actual Brock
Mercury execution, public-only downstream exposure, native viewer, normal
S0/S1/S2/S3 restores and divergent branch exclusion are proven. **Ticket remains
open:** Brock's immutable StrategyMemo is fallback after one invalid live response.
The fully live golden acceptance gate is not met. New completed ticket IDs:none.
Next task is this ticket's live Strategy closeout on a legitimate precommitment
branch, preserving the9 charged requests; explicitly account for implemented
Puppeteer6 sub-limit inside the user's unchanged total30/free-only authorization.
Do not overwrite a saved commitment or splice the completed Gym into a new memo.
See docs/vertical_slice01.md and evidence/phase4/vertical_slice01/verification.json.
Subsequent campaign content, acquisitions, rematch UX and endgame remain deferred.


## VERTICAL-SLICE-01 live closeout — 2026-10-05 (current; supersedes prior Strategy blocker)

**Not accepted; new completed ticket IDs: none.** Actual Nemotron produced a valid
Brock StrategyMemo on a legitimate native branch. The exact memo/sole authored
lock entered the real Pewter Gym;18 supplied Mercury choices passed native
acceptance. Turn19 exhausted the battle allocation before HTTP, used explicit
vanilla fallback and ended in a normal player loss. No Boulder flags were awarded.
The older winning/fallback-memo branch is preserved and never spliced into this
result. Actual new Hermes victory recap,79 versus Rick57 deliveries at fame1,
public-only Sally claims, normal paired restores, restored native PokeBook and
fresh scoped Hermes retrieval after cleanup all pass. Retrieval was mock/0POST.

Same ledger closed30:8 Puppeteer/2 Strategy/0 preparation/20 battle; all matched
returned usages cost0. Recommended role limits were explicitly reallocated twice
inside the unchanged hard aggregate30.14 focused tests/0 skips and28 actual-artifact
checks pass; checker explicitly reports accepted:false. Current source/ROM/save
layout unchanged. Owned workers/emulator stopped; normal hosted default disabled.

Current report/risks/exact commands: docs/vertical_slice01_closeout.md and
docs/vertical_slice01_commands.md. Evidence: evidence/phase4/vertical_slice01/
closeout-verification.json, closeout-turn-trace.json, closeout-native-path.json,
closeout-restored-final.json, closeout-restored-viewer-proof.json,
closeout-fresh-recall-proof.json, requests.json, closeout-final-cleanup.json.

Next: same ticket's fully live native Gym/Boulder completion using the retained
pre-Gym memo/lock, **only after an explicit new bounded hosted allowance**. Proposed
ceiling40 in the same ledger (up to10 extra verified-free attempts) is neither
authorized nor implemented. No model output reroll, campaign expansion or endgame.


## VERTICAL-SLICE-01 additional-allowance closeout — 2026-10-05 (current)

**STILL BLOCKED; completed ticket IDs: none.** User authorization extended the
same immutable30-request ledger to a maximum70, partitioning new calls36 battle/
4 successful-victory recap/0 Strategy/0 preparation. Actual additional36 Mercury
calls all returned valid legal selections and cost0; total66,0 new Hermes. Three
retries visibly reached faint/prize-money screens but were restored before
canonical BATTLE_ENDED, so earlier completed-loss language is corrected. Fourth
retry stopped at accepted/unexecuted turn12;35 of36 choices have resolution events.
No successful player win/Boulder/new qualifying recap/downstream/viewer/save gate.

Exact paired prebattle checkpoint d2ae78c2-1bac-4109-9664-a9e61b1d61e6 restored:
seven projection hashes, accepted memo/lock and tactical-audit cutoff match. Raw
abandoned attempts retained, active view excludes their artifacts. Nine focused
host tests/0 skips and78 actual integrity checks pass; accepted:false. Ledger
closed, workers stopped, hosted defaultfalse; four reserved Hermes calls unused.
Current report: docs/vertical_slice01_gate.md. Evidence:
evidence/phase4/vertical_slice01/gate-verification.json, gate-turn-traces.json,
gate-native-path.json, gate-final-clean.json, gate-restored-audit.json,
requests.json, gate-final-cleanup.json, completion.json.

Next: same VERTICAL-SLICE-01 fully-live Gym/Boulder acceptance under separately
scoped player workflow/new battle authorization. No expansion readiness report
or further implementation; endgame remains deferred.


## BATTLE-END-01 — gate repair accepted (2026-10-05)

Dependencies: accepted BATTLE-01/System One plumbing and blocked VERTICAL-SLICE-01.
Scope: zero-inference native trainer terminal receipt, teardown/retry/ACK lifecycle,
explicit tactical dispositions and save/branch isolation. Done: actual vanilla
loss and deterministic external loss/victory, real Brock Gym script/native badge
save, automatic mandatory recap obligation, duplicate/reconnect/reopen evidence,
late/aborted/restore rejection; docs/battle_end01.md and69 artifact checks.

This supersedes the prior next step of spending more Mercury to diagnose missing
ends. Root cause was native presentation abandoned before the finish hook, with
separate terminal retention/tactical cancellation weaknesses now fixed.
VERTICAL-SLICE-01 is still unaccepted. Next separately authorized work is its final
live closeout per docs/vertical_slice01_final_readiness.md, not campaign expansion.


## VERTICAL-SLICE-01 / D39 final acceptance — 2026-10-06 (current)

**VERTICAL-SLICE-01 ACCEPTED**: actual native Brock win,20 live legal Mercury
choices/zero meaningful fallback, one sole native replacement, unchanged memo/lock,
normal Boulder/TM39, automatic live Hermes recap/private episode, production Gym
high-profile reach79 versus Rick57, scoped Sally public intelligence, native
PokeBook and exact fresh paired reload/rollback isolation. All18 gates +5 integrity
checks;26 focused host tests. Ledger101 with35 new zero-cost calls (33 battle/two
Hermes), original66 immutable. Unused allowance closed, workers stopped, hosted
default disabled. This supersedes historical blocked closeouts, not their records.

Next **recommendation only**: small production Route3/Mt. Moon qualification/content
pack starting with Sally; no implementation or new live-role authorization. Wider
battle/item/mode coverage,4-byte EWRAM/stack and general restore/backlog risks remain.
Endgame deferred. Reports: docs/vertical_slice01_final_closeout.md and
docs/campaign_expansion_readiness.md; actual evidence final-verification.json,
final-golden-trace.json and final-accounting.json in evidence/phase4/vertical_slice01.

## CAMPAIGN-EXPANSION-01 / D40 — live-blocked partial closeout (2026-10-06)

Shared Sally117/Greg106/James107/Kent108 pack and generic static/C/native build
qualification complete, zero permanent RAM added. Actual Sally12 Mercury executions/
3 meaningful fallbacks and real Hermes recap/follow/virality; not live-qualified.
Greg fallback Strategy; Greg battle/James/Kent/MtMoon/C2/C3 unrun. Existing API
recovered normal C1, fresh offline native viewer/paired-prefix fixture verified.
Normal inference disabled,16-request ledger closed, original accepted artifacts
unchanged. No new ticket accepted; full report docs/campaign_expansion01.md.

Next scoped task: repair/qualify pending-save host restart/idempotent native receipt
handling and provider recovery, then define live closeout continuation/branch policy
without rewriting completed Sally or Greg history. Keep campaign expansion at this
gate; Rocket/Cerulean/Rival/acquisition readiness comes after pack acceptance.

## CAMPAIGN-EXPANSION-01 gate repair — current

Zero-inference deterministic request, timeout and restart repairs/proofs complete;
full repair acceptance still open at the unrecoverable historical Greg preflight
predicate. See docs/campaign_expansion01_gate_repair.md/verification artifact.
No new ticket accepted; do not advance or spend on live qualification as debugging.
Next: resolve that evidence disposition and the preserved Greg-lock/three-remaining-
actors closeout contract, then readiness only. Keep hosted inference disabled.

## CAMPAIGN-EXPANSION-01 gate repair — accepted under D42

Historical criterion amended narrowly to cause recovery OR retained-evidence
irrecoverability + UNKNOWN + healthy current production path + durable diagnostics.
All repaired functional/safety gates retained.104 files hashed; six simulated failure
categories survive actual memo/reopen/fresh process;156 host tests/0 skips; native C/
build and EWRAM4/delta0 verified. No hosted generation. Gate repair accepted; full
CAMPAIGN-EXPANSION-01 remains unaccepted. Original C1/history/Greg lock/ledger preserved.
Next: separately authorized three-actor final live continuation per
`docs/campaign_expansion01_final_readiness.md`, not a new campaign phase. Readiness
budget98 is a recommendation only. No Greg first-opportunity reroll or fourth actor.

## CAMPAIGN-EXPANSION-01 final live closeout — blocked before dispatch

D43 records user additional98 exactly; prepared generic isolated continuation keeps
original16 immutable. Required Nemotron endpoint status-2 fails healthy free-route
qualification; other roles qualify.0 generation, no native battle begun, ledger
closed98 unused, original C1/Greg lock preserved,16 relevant tests/0 skips, RAM4/delta0.
No new ticket completed. Remain on same final closeout; no next milestone until actual
Greg/James/Kent/travel/social/feed/final reload acceptance. Report final_closeout.md.

## STRATEGY-MODEL-02 — blocked replacement qualification

Gemma metadata free/healthy text; two smoke HTTP429 failures. Authorized contingency
Qwen exact slug absent, no endpoints; no generation. Actual2/4 calls, ledger closed,
no active qualified replacement/config change, old Nemotron explicitly blocked.
Current text adapter nullable-uptime tests and preserved candidate local serialization
complete; actual synthetic memo/quality gate unrun. Preserve C1/Greg/closed campaign
ledger/final98 allowance, RAM4/delta0. No gameplay or next phase. Report strategy_model02.md.

## STRATEGY-MODEL-03 — accepted, next final campaign continuation

Live catalog-ranked explicitfree Dots3-Note Preview through AtlasCloud qualifies smoke
and synthetic production-shaped memo; active `.env` new-job selector updated.3/6 calls
including rejected Liquid secondary; stop after first complete success.49 tests/0 skips,
James/Kent local preflight, exact historical/Greg C1 restore and RAM4/delta0 pass.
No real campaign requests, Mercury/Hermes or gameplay. Model02 blocker superseded;
original98 allowance unchanged. Next same C1→Greg→James→Kent final live closeout,
not new feature phase. Preview expiration/availability risks recorded in strategy_model03.md.

## D46 — actual final continuation, Greg/James proved; Kent blocked

Current disposition supersedes prior pre-dispatch/readiness status: full
CAMPAIGN-EXPANSION-01 remains **unaccepted**. Greg15/James16 live Mercury choices,
actual Hermes recaps/follows/virality, C2 fresh Continue and C3 offline fresh Continue
proved. Greg frozen memo/lock unchanged, James actual Dots memo frozen; Sally not
replayed. Ordinary incidental Ben encounter retained honestly, zero hosted calls.
Kent metadata TimeoutError before Strategy POST committed fallback/lock; later Dots
check healthy, no model swap/reroll. Required Kent live gate, Mt. Moon and final
feed/save/reload unrun. C3 nearest coherent save includes fallback state. New36/98
calls, cost receipts0, unused62 closed; permanent RAM4/delta0, workers off/default
inference disabled. Offline viewer Home/old posts proved, later page unavailable;
no full browsing acceptance. No new ticket completed or next-phase readiness claim.
Next Kent preflight/fallback recovery then same remaining closeout, with explicit
frozen-opportunity disposition before generation. Details/evidence/commands in
`docs/campaign_expansion01_final_closeout.md`; endgame deferred.

## D47 current Kent closeout disposition

Kent's frozen production Strategy fallback is accepted for this encounter; no reroll.
Actual Kent native live Mercury battle and actual Hermes/social subgates passed.
CAMPAIGN-EXPANSION-01 remains blocked by retained terminal provenance conflict on
offline host restart; current world is suspended. Final real feed, pairing and fresh
offline Continue remain unrun.46/98 calls used, workers stopped, inference disabled.
Next: zero-inference validated recovery of retained Kent victory, then final viewer
and paired Continue. No new phase/endgame. Details: [Kent closeout](campaign_expansion01_kent_closeout.md).

## D48 — final retrospective recovery accepted (2026-10-07)

CAMPAIGN-EXPANSION-01 ACCEPTED. Retained Kent native save and suspended DB proved the
same causal cut (nonce720367614/run1, contiguous stream75, native counter18, cursor398,
all seven hashes and all domain rows). Explicit retrospective checkpoint
`fc4b6afd-9935-4cbb-b248-72c2b454b436` on verified copies changes pairing metadata
only; original unpaired/suspended evidence remains unchanged. Fresh native offline
Continue and real ten-post/five-follower PokeBook passed without inference or browsing
side effects. Isolated C3 rollback excludes Kent and final restore returns exact hashes.
Kent fallback/lock and all eight live Mercury executions/actual Hermes recap remain
immutable. The prompt's eight-post target was stale; preserve all ten retained posts.

33 focused tests pass/0 skips, EWRAM before4/after4/delta0, ledger46/98 unchanged/$0
incremental, workers stopped/default inference disabled. Normal managed saves remain
preferred; retrospective pairing is exceptional and requires retained causal proof.
Next recommended ticket ROCKET-01 (readiness only; no implementation/calls authorized).
Current active copy `.local/campaign_expansion01_recovery/world.sqlite3` +
`recovered-post-Kent.sav`; originals remain historical evidence. Endgame deferred.
See [final recovery](campaign_expansion01_final_recovery.md) and
[next-step readiness](early_kanto_next_step_readiness.md).


## D49 — ROCKET-01 authorized, in progress (2026-10-07)

User a0b57b8b authorizes first natural Mt. Moon member battle and complete legitimate private ROCKET_INTEL, independent mandatory public recap. Start accepted D48 post-Kent pair; selected source352 via nearest descending ladder, canonical leadership actor348. Explicit hostile non-follow exception; grunt ordinary/not globally scouting. Additive content/qualification only, fixed RAM delta0/headroom4. New nonfungible50-call ceiling Strategy4/preparation4/battle36/Hermes6; no leader inference, new ordinary architecture, acquisition or endgame. See docs/rocket01.md and docs/rocket_intel.md. Live/save/rollback gates pending; this is authorization, not acceptance.


### D49 outcome — ROCKET-01 live-Hermes blocked (2026-10-07)

Native352 completed naturally at turn10/cursor443; live Dots memo + sole source roster + eleven Mercury decisions all have canonical execution receipts, no tactical fallback. Automatic member→Giovanni348 reporting committed all47 legitimate direct receipts with exact claims/provenance before any Hermes POST. Private seven semantic claims versus public two; ordinary recipients received only published claims, public reach12 discoveries+54 public scouts at five followers/district, no hostile follow. Leadership offline projection preserves public/private/unknown; no leader job/model/preparation. Native RAM delta0/headroom4.

Hermes called four times (one retrieval, three invalid submissions missing required result.schemaVersion). Strict validation retained the failure and mandatory deterministic recap; this is not accepted live Hermes evidence. Do not reroll its published outcome or replay the real battle to conceal it. ROCKET-01 remains unaccepted under the explicit live-Hermes gate; no paid/provider substitution. Ledger closed16/50 (S1/P0/B11/H4), all retained zero cost. Stop conditionB applies; remaining34 not spent.

Normal managed Save20 checkpoint fc2eb9f8-d613-4f48-aebf-b2ffa2c44824/fingerprint8d07886f33eea4d863209f9be626c191f4cf475262ceb5db5c3951f0f1c7d435, original campaign/branch, cursor443. Fresh OS-process offline Continue and native11-post/follower traversal preserve all seven hashes and exact public/private IDs; isolated pre-battle restores remove future information and deny stale work, post restore recovers it. Originals unchanged; owned runtime cleaned, all task workers stopped/default inference disabled. Private retained pair .local/rocket01/post-rocket-pair.sav + post-rocket-pair.sqlite3.

Evidence: docs/rocket01.md, docs/rocket_intel.md, evidence/phase7/rocket01/verification.json, observation-matrix.json, golden-causal-trace.json, hermes-failure.json, requests.json, post-rocket-reloaded.json, rocket-reloaded-viewer-proof.json, native-memory.json, shutdown.json. Host tests12 Rocket +30 virality +23 battle +16 PokeBook +43 campaign, separately labeled from the one native encounter. Next scope is a narrow Hermes submission/acceptance disposition preserving this committed branch, not Cerulean/Rival/acquisition/Giovanni/endgame implementation. Conditional post-Rocket readiness is deferred until acceptance.


## D50 — ROCKET-01 Hermes disposition accepted (2026-10-07)

User bf5ff62a explicitly amends only the Hermes gate: qualify the repaired live production path in a non-committing synthetic job while retaining the actual Rocket fallback as terminal history. Generic host-owned envelope derives version1 from the unchanged schema and binds actor/battle/obligation; prompt v3 supplies content only. Forged metadata, unsupported versions and invalid/private evidence still reject. Historical raw responses14–16 omitted version; 14/15 pass forensic adaptation,16 still fails participant-action coverage. No historical proposal or battle was replayed/replaced.

ROCKET-01 ACCEPTED. Actual battle: live Dots Strategy, eleven Mercury executions, deterministic47-receipt private Giovanni report, authoritative two-claim public fallback. Later actual Inkling/Hermes synthetic qualification passed/discarded with four verified-free calls and cost0; fifth finish request refused before POST. Same ledger20/50 closed (previous16/new4), no other roles. Campaign seven hashes and all domain rows remain unchanged; fresh native offline Continue/PokeBook and private-copy rollback pass. Two fresh launch/restore epochs are expected metadata changes, not new world knowledge. Native delta0/headroom4. 97 focused host tests pass; workers stopped, owned runtime cleaned, default inference disabled.

Evidence: [disposition](rocket01_hermes_disposition.md), `evidence/phase7/rocket01/hermes-disposition/disposition.json`, `qualification.json`, fresh `disposition-verified-restored.json`, and protected original observation matrix/golden trace. Original BLOCKED verification remains historical; amended acceptance is separate. Next recommendation exactly RIVAL-01, planning only and requiring separate authorization: [readiness](post_rocket_early_kanto_readiness.md). No subsequent phase or endgame implementation.


## D51 — RIVAL-01 opportunity context and scripted prerequisite qualification (2026-10-07)

User c1bf4847 authorizes deterministic prerequisite repair only, zero hosted inference and no active-campaign advancement. Adopt a separate versioned opportunity context policy, not a changed global diffusion policy: Cerulean source map3/3/order8; all old epochs, receipts, jobs and commitments stay frozen. Durable actor knowledge is not deleted when a bounded context selects/compacts claims. Policy/hash/opportunity/selected references and full inputs persist in job scope; frozen preparations reuse those inputs. Public reported claims remain distinct from direct knowledge and subjective predictions.

RIVAL-01 PREREQUISITES ACCEPTED. Real22 public receipts retained; full StrategyContext7524 bytes with3 normalized claims/full references. Private47 Rocket delivery receipt IDs excluded; subtracting2 public semantic claims cannot establish45 private semantic observations. Generic scripted singles content binds source starter0→334/Charmander,1→333/Bulbasaur,2→332/Squirtle and all27 definitions→0326. Native observer uses the registry instead of formatting a native ID as actor identity. Trusted subtype rival retains existing HIGH_PROFILE treatment. Authored first party stays sole/no PREP inference.

Actual isolated mGBA source-script trigger, constructor count1, exact4-party/custom moves/items, canonical BATTLE_STARTED0326 and sanitized first turn pass. Fixture placement changes location/Continue warp only and imports a separate database; it is not accepted campaign travel/pairing. Generic actual-byte constructor replay uses a synthetic lock scope, not a production installation. Typed terminal/duplicate fixtures plus unchanged BATTLE-END-01 source qualify compatibility; actual live Rival completion remains unrun/deferred. Native permanent RAM delta0/headroom4. Protected active campaign, original pair, historical jobs and20/50 closed call ledger unchanged. Workers stopped/inference disabled.

See [prerequisites](rival01_prerequisites.md), [policy](context_selection_policy.md), `evidence/phase8/rival01-prerequisites/verification.json`. RIVAL-01 READY FOR LIVE IMPLEMENTATION, requiring separate authorization; recommended55 (S1/P0/B50/H4), not spent. No Misty/acquisition/endgame expansion.

### D52 — RIVAL-01 travel-repair disposition (2026-10-08)

RIVAL-01 remains unaccepted. Generic managed transport correction passes39 focused
host tests and isolated native lost-ACK/reconnect/wild travel/normal save/fresh
offline Continue. Historical sequence298 cannot safely recover: no corresponding
native state survived, and the working battery remains Save20. Josh/Miriam remain
suspended future history. Exact safe rollback is original Save20/cursor443;
separate test Save21 is qualification-only. No new ticket,0 hosted calls, original
ledger closed, protected artifacts unchanged, workers stopped, native RAM delta0.
Next separately scoped work: rollback-based RIVAL-01 normal continuation using
managed host lifetime and paired travel checkpoints. [Repair report](rival01_travel_continuity_repair.md).
