# Decisions and open questions

## Locked by the current product direction

| ID | Decision | Reason |
|---|---|---|
| D01 | Title: Pokemon Influencer; in-world social network: PokeBook | User's concept |
| D02 | FireRed/Kanto is the base | Preserve desired world/content; avoid a Kanto port project |
| D03 | Hybrid emulator + local runtime | Rich memory/models are external to the ROM |
| D04 | Every eligible ordinary trainer follows after the first loss to the player | Preserve the user's recurring-cast mechanic |
| D05 | Friends, followers, respect, and rivalry are distinct | Avoid instant friendship and a single karma score |
| D06 | Gym/region-gated restrained rematches | Campaign progression rather than dramatic counter-teams |
| D07 | Most adaptation is moves/tactics; catches are local and infrequent | Explicit toned-down campaign request |
| D08 | Endgame is deferred | User requested a separate later concept file |
| D09 | Agent authority is bounded; truth and subjective belief are separate | Protect continuity and fairness |
| D10 | Do not require cloud inference for campaign completion | Latency, cost, reliability, and testability |

## Proposed engineering defaults, changeable with evidence

Python host, SQLite ledger, mGBA scripting candidate, deterministic utility System 1 baseline, direct provider adapter rather than a required general agent framework, simple JSON content/configuration, small in-ROM feed, and one supported desktop configuration first.

Numeric mutation/growth limits are tuning defaults, not user-approved final balance or measured performance. Changes must explain their effect on the restrained adaptation promise.

## Questions to resolve by inspection or experiment, not by guessing

| Question | Owner/gate | Required evidence |
|---|---|---|
| User's FireRed language/revision and checksum | SETUP-01 | Local header/hash report; no ROM upload |
| Exact upstream commit and toolchain | SETUP-02 | Lock manifest, clean build, baseline comparison |
| Exact emulator package and script capability | SETUP-03 / BRIDGE-01 | API probe and real ping/response test |
| Safe mailbox placement and available RAM | BRIDGE-01 | Linker map, size/alignment checks, runtime canaries |
| Safe extended save marker layout | SAVE-01 | Save-sector audit and serialization tests |
| Party-construction and action-selection hooks | SETUP-03 / BATTLE-02 | Source call path plus emulator validation |
| Which ordinary trainers and special battles are eligible | CONTENT-01 | Exhaustive binding/exclusion manifest |
| Nonlinear regional Gym predicates and travel barriers | CONTENT-01 | Map/story review and route tests |
| Compact UI text budgets | UI-01 | Measured font widths and screenshot review |
| LLM provider/model/cost configuration | MODEL-01 | Explicit configuration and current provider docs |
| Learned System 1 model benefit | Optional research subphase | Reproducible baseline comparison and fairness tests |

## Changes to earlier brainstorming

- Illustrative Pokemon availability is not canonical. Export the selected FireRed data and apply travel/resource rules.
- Ordinary followers are not randomly limited to 20-30%; processing is sparse, persistence is broad.
- Do not treat accidental LLM hallucination as an automatically valid rumor. Deliberate rumors have provenance and explicit validation.
- Do not use player losses as a level-growth clock or give every rival an immediate perfect counter.
- Do not assume a shared Hermes home is a safe memory store for multiple NPCs.
- Do not claim a standalone ROM can provide the complete external-agent experience.
- Baseline source builds and the user's patch base are separate concerns; inspect the selected build's actual input requirements.

## Change protocol

For a material change record the problem, considered alternatives, chosen behavior, affected invariants, compatibility implications, tests, and rollback approach. Do not resolve an architectural contradiction by quietly adding another framework or service.

## Phase 0 evidence decisions — 2026-10-01

### D11 — Source and matching build pin

Use local project branch `pokemon-influencer/phase0` over pret commit `037335f4c725d7c9aecdac87066f2002b4bd7e14`, with fresh unmodified source exports for baseline builds. Pin existing agbcc `da598c1d918402c42c0c0d7128ba14567f3175e9` and actual tool/header/library hashes in `config/phase0.lock.json`. The clean English FireRed revision-0 comparison and SHA-256/size checks passed, and the confirmed user dump is byte-identical. This is sufficient evidence for the local matching toolchain; compiler rebuild and clean-machine provisioning are not claimed. Do not switch to a modern target to hide a mismatch. Updating the source requires a reviewed diff, new lock and baseline/emulator checks; the pinned export remains the rollback reference.

### D12 — Emulator candidate remains subject to runtime evidence

Retain official mGBA 0.10.5 (`26b7884bc25a5933960f3cdcd98bac1ae14d42e2`) as the Phase 1 candidate. Real desktop boot, Lua 5.4, memory primitives, frame callbacks, input, loopback TCP and explicit-ALL snapshot primitives were exercised. Prefer the tested `hwaccelVideo=0` diagnostic configuration after intermittent black framebuffer results in the first run; causality is not established. `runFrame()` is invalid in the tested console context. A file-loaded listener logged success without an open port; direct console definition worked. This is a capability result, not an implemented bridge or release compatibility claim. BRIDGE-01 must verify supported script loading, build identity and safe mailbox allocation before promoting it. Persistence pairing, battery rollback, state-load detection, framing/authentication, timeout, reconnect and fast-forward evidence remain later gates. Original AI and unsupported battle modes are unchanged.

### D13 — Handoff path reconciliation

Keep specification files under `pokemon_influencer_handoff/`, repository-root AGENTS canonical and implementation status at `docs/status.md`. Root PLAN and requested docs paths link to the authoritative handoff files. Adapt the checker to the relocated AGENTS file, whose supplied digest was verified before edits. Preserve SHA256SUMS as the delivery receipt and keep the original checksum/relocation failure evidence. Existing reference fixtures remain illustrative, with no ROM trainer bindings invented.

D12 completion evidence: ordinary Route 1 wild battle won, actual in-game save produced a checksum-valid 14-section slot, and a fresh launch without a savestate resumed the same map/party/HP/counter. See `evidence/phase0/emulator-smoke.json` and `battery-save.json`. Accept this package for Phase 1 investigation with the recorded script-loading risk; no bridge compatibility guarantee is implied.

### D14 — BRIDGE-01 transient ABI and listener test transport

Reserve a separately linked EWRAM mailbox after upstream's entire EWRAM section, preserving all existing RAM records. Use initialized section-attributed storage because the pinned agbcc otherwise emitted COMMON. Generate ABI assertions and compiler/ELF-derived manifest; a content tag plus emulator CRC checks identify the ROM, while host tooling verifies SHA-256. Default flags preserve the exact matching baseline. Rollback is PI_BRIDGE=0 / the private known-good export.

Protocol1 is deliberately only one debug PING, with request/session/generation correlation, FNV corruption detection and a nonblocking 60-tick ROM timeout. A Lua localhost listener avoids the pinned API's blocking connect; a random-token HELLO and bounded binary envelope are local test scaffolding. No domain business logic enters Lua. Native File script loading worked across fresh launches; CLI autoload is absent, and dofile lifetime is not promoted as supported.

Actual evidence: four correlated round-trips, absence/disconnect/delayed/duplicate/fragmented faults, bad manifest refusal without writes, soft reset, in-game save/fresh reload, disabled boot/Continue; see `evidence/phase1/emulator-integration.json`. Pinned mGBA's ROM-hack fallback adds RTC metadata to battery saves; report the 16-byte footer separately rather than modifying flash or inventing a marker. BRIDGE-02 production transport and later paired persistence remain independent gates. No endgame/model/gameplay scope was expanded.

### D15 — Three-role provider-neutral AI contracts (documentation only)

User requested Hermes as intended orchestration harness, independently configured Strategic LLM, and native System One BattleDecisionProvider. Keep canonical world/battle memory in the host with deterministic authority and scoped stateless context. Supersede conceptual-only/direct-adapter defaults only for future harness integration; no installation/runtime in this work. Latest user free-only selections override the attachment's initial Jev: Inkling puppeteer, Nemotron strategy, Mercury Decide System One. Existing config/model_profiles.yaml is authoritative; config.yaml was absent. OPENROUTER_KEY presence was checked without exposing or using its value.

Anonymous public catalog/endpoint GET evidence confirms zero input/output pricing for selected candidates; native Mercury is omitted from the general text catalog but present in endpoint metadata. Jev's nonzero input pricing excludes it from active free-only profiles. Keep offline default and hosted disabled; development is blocked pending verified pins, and free-alias inference is reserved for the explicit experimental profile. Versioned Jev/floating latest are inactive references. Free aliases are not immutable serving revisions. Configuration stays a valid JSON subset of YAML to avoid adding dependencies. Contracts/schema examples/static checks are design artifacts, not functioning AI or measured battle performance.

Affected invariants: fairness, offline completion, bounded latency, host authority and secret isolation remain mandatory. ROM and BRIDGE-01 PING ABI unchanged; future transport/save identities need versioned bounded integration. Rollback: offline profile/current PING; architecture cannot activate a provider. Evidence: evidence/architecture/. Live credential entitlement, native adapter fixtures, Hermes pin/embedding, deadline and save strategy remain unresolved. See docs/ai_runtime_architecture.md.

### D16 — User-scoped BRIDGE-02 facts, knowledge boundary and transient runs

User explicitly expanded BRIDGE-02 to real typed battle events and bounded NPC-side observations. Keep five canonical lifecycle/action types separate from the observation type and future exposure/provenance. The ROM exports an audited allowlist, not a BattlePokemon dump; hidden selected action category is omitted. Announced moves authorize reveal tracking only after the native text command. Exact own state and coarse/public player-active state do not grant unrelated NPC knowledge. No model/provider/AI/game-domain memory implementation is authorized.

Use a new compact protocol2/196-byte mailbox and bounded four-record queue, independently retaining BRIDGE-01 protocol1 with PI_EVENTS=0. Full ELF-derived allocation audit and zero-feature exact baseline build remain gates. A launch nonce/Lua run tag distinguishes transient streams; it is explicitly not a durable save branch. Reconnect restores recent dedupe from accepted bytes; reset invalidates authentication; eventual SAVE-01 must own branch markers/projections. Arbitrary rewind remains unresolved.

Small schema correction: opponent status and field weather in the future AI request are optional because the current exporter has no audited visibility producer for them. Omit unknowns rather than inventing none. `legalActionsComplete=false` prevents presenting this partial observation as a tactical request. Hosted profiles remain disabled, .env and user dump untouched. Experimental mGBA SIGPIPE/EOF findings and exact supported launcher are documented in docs/bridge02.md. Subsequent source review added a flags allowlist (including Poke Dude exclusion), turn-exhaustion export cutoff and ACK error/reserved validation. Native coverage is13 transport and7 observation cases. Bounded closed-native-object retention is verified with16 authenticated reconnects plus forced Lua GC; unlimited reconnect and script reload remain unsupported.

Final live verification completed2026-10-02 on ROM SHA256 eb8ce46de923e3d85216754ec880d50e8fdc2c95efa31a1dff73d4cbd6df6214: native wild/trainer victory, absent-host progress, gap recovery, duplicate/stale ACKs, pending reset and rollback.53 retained assertions bind67 final-build receipts. Reset from the test-input callback can lose its reply; verify callback/cleared IDs through a new read-only connection, never resubmit an ambiguous reset. The separate input socket failure remains an explicit prototype risk. Mailbox generation is handshake-assigned and may be stale while offline after rollback; restored queued records acquire a transport lifetime, not a durable origin. No NPC memory/world projection may consume this as solved save pairing. The next scoped ticket is BRIDGE-03 UI exchange; no AI/endgame expansion is authorized.


### D17 — BRIDGE-03 native presentation lane and bounded managed lifecycle

User authorized BRIDGE-03 only and named WORLD-01 as the next milestone, without an LLM. Keep UI commands/player replies in a separate protocol2 lane and sink; displaying host text cannot mint canonical history or NPC knowledge. Allocate148-byte mailbox plus64-byte private state after the existing event section; preserve all original RAM/heap/IWRAM records.436-byte prior headroom rules out a large second UI framework. Use the inspected native field printer and yes/no menu, with stable IDs distinct from the fixed YES/NO labels. Generic2–4 choices are deferred behind a future version/variant. The explicit ASCII-to-FireRed conversion and independent ROM allowlist prohibit placeholders/control codes/pointers/scripts. Two24-character lines,48bytes and900ticks bound native presentation.

Reject busy states immediately; acquire controls only in the inspected ordinary overworld callback with no scripts, fade, playback, motion or modal. The exploratory quest-log case exposed prolonged validation; final source checks the full safe state at ingestion and excludes playback-last/running playback. Deadline cancellation closes only owned windows/printer/locks. PI_UI/PI_UI_TEST defaultoff provide rollback; disabled builds match the baseline.

Use the tested nonblocking localhost listener with the existing mGBA SIGPIPE/EOF/closed-object guards. A managed snapshot load advances transient authority before another ROM frame; restored UI closes and old responses cannot cross runs. This does not fix arbitrary unmanaged rewind/equal-or-higher-heartbeat rollback, restored gameplay-record origin, or durable save pairing. The observed reset input-socket reply loss/reset is recovered through read-only readiness checks without repeating reset. These are supported-prototype limits, not a native socket fix. Final live acceptance/evidence is recorded in docs/bridge03.md and evidence/phase1/bridge03/. No models, world projections, trainer adaptation, battle AI or endgame work is authorized here.

### D18 — WORLD-01 host authority and persisted-content normal-save pairing

2026-10-02: user authorized WORLD-01 only. SQLite append-only canonical facts, separate observations/provenance, deterministic projections, explicit schema/reducer/registry versions and durable save intents now provide the host authority. Trainer identities bind explicit pinned source families; equal names and transient battle IDs never identify a person. Canonical possession grants no NPC knowledge, memory, social effect or model access.

Keep the accepted B3 ROM unchanged:224 EWRAM bytes are insufficient justification for a ROM world/save marker when validated host-side content works. Fingerprint the complete latest primary14-section slot in logical order using actual compiled lengths, source checksums and counter; exclude rotation/slot/padding/RTC metadata. Pair only a prior durable intent with a new complete save and a matching drained-stream lifecycle receipt. Host fsync/read validation precedes transactional checkpoint publication. Cross-process atomicity is not claimed; failed/incomplete operations remain detectable and recoverable through known pairs or explicit import.

Supported restore is a **fresh OS-process normal battery Continue**. Reconstruct the paired canonical cursor, preserve later history inactive, and fork only on a fresh canonical battle start. Re-saving a historical view without new facts does not fork. Unmanaged reset/load, gaps, restored RAM queues and arbitrary savestates/rewind remain unsupported and suspend enhanced ingestion. Same-launch host restart preserves durable dedupe/state. Final live S1/Rick/S2/later-wild/restore-S1/divergent-wild/S2-positive-restart/S3 evidence and limits are recorded in repository-root docs/world01.md and evidence/phase2/world01/. No additional bridge features, AI/Hermes/provider calls, friendship/reputation/followers, roster or endgame implementation is authorized.

### D19 — MEMORY-01 actor evidence and dual checkpoint cutoffs

2026-10-02: user separately authorized MEMORY-01 only. Preserve canonical WORLD schema/reducer and append an explicitly versioned subjective schema. Trainer actor IDs reuse source-backed world families, never names or transient battle IDs. Derive only participant start/result and bounded revealed opponent species/moves or audited visible announcement fields. Canonical possession and RAM diagnostics grant no unrelated-NPC knowledge. Immutable evidence is not inferred belief, confidence, personality or strategy.

Targeted development receipts reference exactly one authorized sender claim and preserve its origin chain. Recipient provenance cannot expand sender-private evidence. The trusted host issues an actor-bound read capability; future model tools cannot select another actor/branch, advance a cutoff or issue SQL. Canonical-only writers fail closed on extended databases, including connections opened before migration. Ingestion/evidence/cutoff commits precede ACK.

Canonical cursors do not advance for deliveries, so normal-save checkpoints bind an independent monotonic subjective cutoff. Restore deactivates later evidence even at an identical canonical cursor; canonical divergence still occurs only on a new battle start. The child branch inherits both cutoffs. Pending save/restore-fork/suspended state rejects fixture delivery. Original WORLD evidence/database is preserved; explicit migration acceptance used a private SQLite backup. Retrieval uses a conservative bounded chronological window with truncation and immutable provenance retained; interpretation/salience/forgetting remain deferred.

New live Rick victory, zero Janice knowledge, clean host restart, one result receipt/duplicate no-op, native counter6 S1/counter7 S2, fresh S1 Continue/empty memories/new wild B with no leak and positive S2 Continue passed. Details/limits: repository-root `docs/memory01.md`, `docs/memory_schema.md`, `evidence/phase2/memory01/`. B3 ROM unchanged. No Hermes/inference/social propagation/PokeBook/follows/reputation/strategic or battle AI/endgame implemented. Next separately scoped task SOCIAL-01; stop MEMORY-01.

## D20 — SOCIAL-01 deterministic publication and explicit exposure (2026-10-02)

The user's SOCIAL-01 authorization includes narrow evidence-backed recap publication previously parked under SOCIAL-02. Complete that loop within SOCIAL-01; defer friendship/reputation, social bonuses, full PokeBook UI, virality and AI. This clarifies rather than silently completes those broader backlog items. Rick alone is explicitly eligible; Janice→Rick is an authored slice tie, Doug is a nonrecipient. No vanilla social graph is claimed.

Use additive committed social schema/reducer1, explicit activation/no backfill, policy/template1 supported 1–2 claim recap, bounded deterministic follower ticks and separate exposure. Publication and feed entries grant no retained claim. Exposure and MEMORY receipts share SQLite's transaction. Public provenance ends at reported post attribution; full author evidence linkage remains internal. Future Hermes choices enter the existing actor-bound proposal validator and never receive unrestricted grants/storage.

Managed native checkpoints bind three independent cutoffs. SOCIAL-01 explicitly requires same-canonical-cursor host divergence; extend D18/D19's deferred-fork mechanism to social mutations, capturing parent MEMORY/SOCIAL cutoffs before writing. Restores never execute pending future jobs and revoke social handles. Original future branches/checkpoints remain immutable/restorable. This does not broaden normal-save workflow into unmanaged state/reset/rewind support. No ROM or battle-AI change is needed.

## D21 — HERMES-01 mandatory recaps and durable puppeteer continuity (2026-10-02)

The user supersedes optional Hermes posting: every supported confirmed completed single-trainer encounter requires one factual public recap, on trainer victory/loss/rematch, separately from first-win follows. A durable obligation has one authoritative processing outcome; Hermes or deterministic fallback handles the same identity. No NO_POST/optional-publication business outcome remains in the current Hermes path. SOCIAL-01 history and its original narrower policy are retained as historical evidence, not rewritten.

Install/pin actual official Hermes separately from fresh disposable execution homes. Register only bound game tools; retrieve durable actor/director summaries explicitly from additive game-owned storage. Canonical facts, puppeteer/director summaries and trainer knowledge are separate projections. Public posts, unread feeds, exposures and receipts stay distinct. Inference must run outside ROM callbacks/SQLite transactions, with bounded free-only live authorization and recorded outcomes. Extend managed checkpoint/branch selection with a puppeteer cutoff and pending obligations; preserve prior unsupported unmanaged-state limits. Host implementation and actual-Hermes/mock integration pass; live shadow submission and fresh durable recall pass. Enabled native generation exhausted the three-request cap before submission and used fallback; prompt v2 bundles authorized retrieval, offline tested but live untested. All ten live attempts are consumed. HERMES-01 remains partial pending a separately budgeted enabled-native v2 acceptance test; no downstream phase is authorized. See docs/hermes01.md and retained audit artifacts.

## D22 — persistent director and two-stage System One gameplay architecture (2026-10-02)

User-authorized architecture realignment only. Hermes is a persistent event-driven social-memory director with mandatory recaps and provenance-backed scoped briefings/notes. PokeBook is the social-memory system and interface; NPC exposure runs independently of player feed opening while publication/unread delivery/exposure/retained claims remain distinct. Director knowledge never implies NPC permission. Always-on availability uses bounded fresh sessions and branch-aware durable memory, not continuous inference or wall-clock growth.

Define shared PreparationEnvelope v1 before STRATEGY-01: deterministic services provide stage/earned-epoch levels, actual move acquisition, native/nearby permissions, finite inventory/resources, change budgets, signatures and theme feasibility, with meaningful diverse candidates. Strategy consumes authorized briefing/personality/own companions/inventory/envelope and emits strategic intent. System One uses the same replaceable model slot for preparation candidate selection and current legal battle selection. Split SYSTEM1-01A selection/resource commit/lock/safe installation from SYSTEM1-01B actual legal-action battle control. Selected preparation locks; later posts/player changes do not rebuild it. Actual resource changes require explicit game rules.

This explicitly expands authored-first-roster defaults for bounded first-Gym preparation and limited mixed-type support while retaining signature/primary-theme identity. Numerical content caps/starting resources and supported action mechanics remain future acceptance gates. Unconfigured ordinary/boss first rosters stay authored. Existing v1 AI schemas are preserved skeletons; envelope-bound intent and locked preparation correlation require versioned schemas before runtime integration.

Authoritative docs: ai_runtime_architecture.md v2, preparation_envelope.md v1, system1_battle_decisions.md, model_provider_contracts.md; conflicts/migration in architecture_realignment.md and dependencies in backlog.md. Preserve HERMES-01 implementation, partial native-live acceptance and exhausted10-attempt stop condition. No foundation restart, new gameplay implementation, provider changes, extra live role/call or endgame authorization.

## D23 — HERMES-01 closeout acceptance and bounded renewal stop

Separate closeout authorization grants at most10additional Puppeteer attempts/4requests per job, preserving original consumed10. Use existing v2 scoped bundle; no replacement harness or expanded grants. Actual pinned AIAgent.interrupt stops the tool loop only after the domain service returns a committed post, avoiding a gratuitous finished request. Separate persistent closeout ledger is closed at5/10 after native proof; old ledger stays10/10. Token/byte/tool/deadline/free-only limits remain unchanged; providers and normal offline default preserved.

Actual native Rick completed through the normal event pipeline; three live requests included strict rejection of an extra maxItems field and successful corrected submission. Exactly one model-sourced recap/private episode committed, no fallback. Safe runtime deletion, controlled disclosure, normal paired save, native S1 rewind/delayed-grant rejection, positive reload and fresh live durable recall (two more requests) passed. New evidence is under evidence/phase2/hermes01/closeout; earlier fallback outcomes/reports remain historical. HERMES-01 is accepted within its narrow scope, not a claim that general director briefings or any strategic/preparation/battle consumer is implemented.

Next separately authorized phase is POKEBOOK-01, then STRATEGY-01 and SYSTEM1-01A/B under D22; shared PREP envelope must be executable before real preparation consumers. The conflict ownership/readiness audit does not implement future schema/candidate/resource/roster/action/provider work. All task processes stopped; no automatic renewal or next-phase execution.

## D24 — POKEBOOK-01 player projection and native read-only pages

Authorize only normal-field native Start-menu PokeBook over accepted domain records. Where no player feed issuer existed, validated public completed-battle participation grants narrow player discovery; incoming follows never create reciprocal follows. Serializer allowlists published identity/author/body only. Counts obey the same policy. Snapshot references do not grant visibility, and branch/restore/player scope is checked each query. No read markers, NPC exposures, recaps, follows or model calls arise from browsing. Unread distribution and explicit actor exposure retain their existing service boundaries.

Schema2/kind3 adds bounded paging in the existing presentation mailbox without relaxing schema1 field safety. Native owns checked short-lived BG/window/ListMenu resources and cancellation; unsupported text fails closed rather than summarizing/truncating. Four-byte owner pointer leaves220static EWRAM bytes; actual native heap/cycle measurements are distinct from allocation-failure C substitutes. Preserve native Save/actions/story/AI/source pin and exact disabled baseline. New ROM uses a separate managed explicit-import lineage; old Hermes text is an explicitly labeled stored fixture, not migrated/live generation. Fresh paired saves restore history and advance grant epochs; abandoned nonce payloads are rejected.

Actual final native Rick offline recap/follow/full reader, stored/layout pages, privacy, repeated cleanup, faults/cancel/restart and paired early/late reload accepted; details and excluded navigation attempts in docs/pokebook01.md. No new inference authorization or budget reuse. Existing Hermes private evidence remains unchanged and fact-deduplicated, not a complete turn transcript. PREP-01 remains executable feasibility prerequisite for STRATEGY-01, with independently gated System One preparation/installation and live battle control. Stop POKEBOOK-01; endgame deferred.

D24 final acceptance clarification: native three-row testing caught the mistaken interpretation of FireRed's parameter names. Actual implementation treats cursorPos as scroll offset/itemsAbove as visible row. Final viewer reads second getter output and initializes(0,row); actual-C row3/post3 and final native row3/author/back-selection proof pass. Candidate96e/ae4 histories are preserved/superseded. Final build bec6245f… passed real offline battle/viewer, resources, faults, restart and paired early/late restore. Single next dependency task ROSTER-01 supplies PREP-01's catalog; CONTENT-01 and executable PREP gates precede strategic consumption. No new phase or inference authorization.

## D25 — ROSTER-01 mechanics, policy and trusted individual state

2026-10-02: separately authorized ROSTER-01 only. Compile the effective pinned FireRed table initializers and preserve selected-version encounters/generated tables, source fingerprints and narrow exact baseline properties. Independently verify against the accepted ARM build and actual native default-move algorithm. Keep mechanics, separate authored policy and trusted branch-scoped current ownership/resources/earned stage distinct. Existing registry world IDs map through the implemented actor_id function; no display-name/personality joins or new identities.

Pure prerequisite/element services expose possibilities and structured rejections, never rank/select/install or mutate campaign history/resources. Learnset membership is not free relearning; retained pre-evolution/authored moves require exact individual provenance. TM compatibility is not inventory; finite allocations distinguish teaching/held/bag/evolution/capture and reusable HMs from consumable TMs. Unsupported methods and missing stage/resource/permission/Gym bindings fail closed. Baseline/fixture proofs are partial, fully_legal=false, not whole prepared teams.

Minimal early policy explicitly classifies Rick's Forest native/Route2 nearby (travel issuer pending). Existing defaults supply restraint budgets; no new production stage targets or Gym support caps are invented. D22 remains authoritative: first-Gym mixed support is permitted architecturally, unqualified until CONTENT-01 supplies explicit bounds. Current broad extraction includes unused/endgame data without enabling campaign permissions. Fixture-only profiles cannot bind live contexts. Next is CONTENT-01 before PREP-01's actual envelope/candidate service. No new inference, ROM/gameplay modification, bridge work, strategic interpretation, complete package generation/selection or endgame authorization follows.

Report: docs/roster01.md; consumer gates: docs/roster01_prep_readiness.md; evidence: evidence/phase3/roster01/. Current ROM and exact save/build guards preserved. Carry forward the deduplicated Hermes evidence limit; no frequency/sequence inference or history reconstruction here.

## D26 — CONTENT-01 opening production playtest bindings (2026-10-03)

Separately authorized CONTENT-01 only. Production opening-kanto v1 binds source identities/companions/resources from the accepted ROSTER catalog. Rick6/6→10/10 and Doug7/7/7→11/11/11 on one prior-own-win+source-Boulder opportunity, ceiling14, +4 maximum, two total elective move changes including evolution learning, all original individuals retained. Janice's source116 first encounter requires Boulder and grants no forest opportunity. First encounters keep source species/levels. No catches, replacements/reserves/additions, supplies/teaching/evolution items/tutor entitlements/exceptional grants or restock. Forest native/Route2 nearby with explicit trusted actor travel grant; Janice Route3 and Brock Pewter Gym only. No ordinary ace is invented.

Author Onix as Brock's signature and Geodude as core. Opening Rock Gym bounds are minimum two core/maximum two active/zero support/empty support permissions/support ceiling14. D22 approved broader mixed-type support architecture but no numeric bounds: narrow opening zero does not revoke later explicitly bounded mixed support or global first-Gym preparation. Original order/retention remain lawful choices; never invent resources to force diversity.

Boulder means both pinned native FLAG_DEFEATED_BROCK0x4B0 and FLAG_BADGE01_GET0x820, not trainer result or social claim alone. Current bridge lacks trusted flag export. Pure resolution uses active paired host-issued evidence, fails specifically when missing, and does not implement a hook/issuer. One stable campaign+actor+stage logical opportunity with branch-scoped consumption inherits prefix use at forks; early restores exclude future consumption. No query initializes inventory, grants growth or changes locked encounters. Future activation/version adoption is explicit; prior history/resources/decisions remain bound to their original versions.

Report: docs/content01.md; balance: docs/content01_balance.md; production: config/opening_content.json and schemas/content/; evidence: evidence/phase3/content01/. Existing foundation/catalog/ROM/save/database/providers/budgets preserved; no inference or subsequent implementation. PREP-01 is next, with live trusted state and complete envelope/candidate/aggregate validation gates still outstanding. Endgame deferred.

## D27 — CONTENT-01 clarification: configurable acquisitions, inactive later balance

Authorized CONTENT-01 addendum only. Opening no-catch is an override for the first earned preparation, not a global trainer-acquisition ban. Shared adaptation contract1 supports profile-specific0/1/2 acquisition allowances and aggregate move budgets (default2 across existing companions), explicit named stage/access/species/resource/spacing/party constraints, four distinct territory tiers, original/signature retention and same lineage through evolution. Opening packv2 pins this contract while retaining all actual opening settings and zero supplies. No qualified later production profile or gameplay is activated.

Latest later allowance1 or2 per opportunity supersedes the draft1/opportunity and2/campaign as intended campaign direction. Probability, minimum spacing and campaign-wide cap remain explicitly unresolved future versioned balance decisions. Do not inherit25%, spacing2 or other draft acquisition numbers silently; no unlimited fallback. Historical ROSTER acquisition fixtures/policy remain archived facts, not future campaign balance authority. Later unqualified profiles are inactive, not proof of unsupported acquisition mechanics.

80/20 means probabilities for eligible ordinary origin categories after all filtering, normalized over nonempty native/nearby pools. Future seeded origin draw precedes System One species/no-change choice within that origin. Accessible/exceptional maps require explicit separate trainer grants; never relabel them nearby or invent access when a local pool is empty. Contract/query tests do not claim an implemented draw or empirical final selection rate.

Active capacity is bounded by source six and the trainer/stage limit, with no reserve/rotation system. Future version changes affect uncommitted opportunities only; stored commitments/save history retain prior policy versions. Current tests are scenario-only pure policy expressiveness/constraint resolution, not qualified later content, captures, spends, selection, inference or installed-team locking. docs/content01_addendum.md and evidence/phase3/content01/addendum/ record the distinction. Preserve CONTENT-01 stop condition; PREP-01 next, endgame deferred.

## D28 — PREP host envelopes and paired native progression (2026-10-03)

Under PREP-01 authorization, consume accepted ROSTER/CONTENT and add an append-only preparation timeline to a separate managed test database. Initial authored companion/resource records are explicit once-only receipts; canonical own victory plus a paired native Boulder flag snapshot earns the first qualified forest opportunity. Read the two existing flags from checksum-valid WORLD-paired normal battery data rather than adding a bridge ABI, RAM allocation or ROM save field. This is host progression authority, never NPC knowledge. Exact source offsets use pinned agbcc/APCS, not GNU EABI assumptions. Preserve managed fresh-process normal-save restrictions and refuse gaps.

Implement neutral bounded complete zero-acquisition opening packages, source history validation, whole-team elective edit accounting, retention/signature/theme/resource checks, stable IDs and current-scope revalidation. Separate constraint-envelope and candidate-set hashes to avoid circular identities. Source-fixed first-party declarations are valid opening representations; two-pass intent-conditioned generation remains downstream. An unchanged fallback option is not a selection. Abstract exclusive reservations do not spend stock. Pure committed/consumed lifecycle fixtures do not authorize a live commitment writer.

Keep cap1/cap2 scenario envelope flow and filtered origin/grant semantics expressible without activating later content. Name PREP-ACQ-01 for qualified later balance, recorded origin draws and complete acquisition packages. Do not restore historical probability/spacing/campaign caps, invent items, add reserves, call Strategy/System One, install a party or implement endgame. Updated versions apply to future explicitly adopted opportunities; existing receipts/locks are not rerolled. Final native acceptance and readiness evidence reside in docs/prep01.md, docs/prep01_readiness.md and evidence/phase3/prep01/; this decision alone does not mark unrun tests complete.

D28 acceptance closeout:338 unskipped host tests and30 evidence assertions passed. Actual unchanged-ROM Brock victory, native Save13→14, fresh runtime retrieval and paired before/after Continue restore prove the milestone grant once and remove future eligibility on rewind. Rick16/Doug-fixture16/Brock-first1/Janice-first1 complete host options; none selected, reserved, consumed, committed or installed in the native campaign. First-encounter order remains authored.114 protected artifacts preserved and task processes stopped. PREP-01 is accepted within this scope; STRATEGY-01 is next only under separate authorization.

## D29 — STRATEGY-01 scoped intent and bounded provider failure (2026-10-03)

Implement host StrategicPosture v2 over the existing actor-filtered Hermes/MEMORY briefing and executable opening PREP bundle. Rick's authored behavior bands are explicit playtest design, not inferred personality. Strategy receives own companions/resources/constraints and aggregate legal capabilities, never candidate IDs, player hidden state, director-wide memory or tactical turn input. Controlled assumption kinds/evidence references preserve direct/report/uncertainty distinctions and exclude unsupported chronology/frequency. A normalized summary is host-formatted; no chain-of-thought stored. Historical AI v1/configured model slots and foundations remain unchanged.

Separate append-only derived opportunities/grants/postures bind actual campaign/branch/cutoffs/generations/envelope/profile/provider versions. Restore pairs their cutoff/hash, revokes active context grants and preserves per-job attempts. Late submissions require the original immutable context ID as well as job ID. Material authorized context permits exact historical replay with a separate current envelope binding; it does not rewrite historical decisions or select/commit/lock a roster. Future System One commitment must lock the historical posture/context and revalidate its current grant atomically.

The user authorized only ten free Strategy POST attempts, <=3/job, one live request at a time. Default hosted inference remains disabled. Exact configured model remains nvidia/nemotron-3.5-lightning:free. Initial status-2 availability failed closed; later status0/zero-price/function-tool route qualified. Explicit acceptance-purpose jobs and versioned transport corrections preserved failed history and the shared ledger. Canonical returned aliases must be proven by equal catalog canonical_slug; the requested free route and explicit zero returned usage cost still govern success. Real substitutions remain rejected.

Live gate did not pass:10 requests consumed; no validated live posture. Last3 HTTP200 envelopes explicitly carry NVIDIA upstream error502/Internal server error and no usage/model result. First7 had incomplete diagnostic normalization (classified as mismatches when no model identifier was present); do not retrospectively claim proven substitution or identical502 for them. Adapter v4 now records bounded error diagnostics, rejects malformed root/usage and separates provider failures from identity mismatches. No paid fallback/substitution, extra role or authorization renewal occurred. All accepted results in this session are labeled deterministic fallback.

Native Save14 before/Save15 first fallback/Save16 all fallback attempts use the existing actual callback/fsync/checksum gate. Fresh native before/after Continue proves fallback history pairing/replay only, not the missing actual-model acceptance. STRATEGY-01 remains implemented but not accepted until a separately authorized live closeout passes. SYSTEM1-01A/B and endgame stay deferred. Independent host tests and accepted foundation preservation are recorded under evidence/phase3/strategy01; the ten-call ledger is closed and all task-owned workers are stopped at closeout.

## D30 — renewed Strategy closeout, upstream outage stop (2026-10-03)

Separate renewed authorization allows <=10 additional exact configured free Nemotron POSTs, <=3/job/$0, same-model provider failover only. Do not read/use the newly supplied backup model as automatic fallback. Preserve original closed10 and old immutable fallback results. Classify first7 underlying failures unknown because diagnostics are insufficient; final3 old failures conclusively NVIDIA502. v4 already fixed error-envelope misclassification. v5 adds verified zero-price/tool provider allowlist failover, bounded5/10-second upstream backoff and sanitized request/response audit; schema/prompt/persona/configuration and authority boundaries remain unchanged.

Current model catalog/free tools and healthy NVIDIA route qualify, but only one eligible provider exists. Exactly3 new requests again return NVIDIA502 inside HTTP200 error envelopes, no model/tool result or usage/cost receipt. Stop after the consecutive upstream failures; close renewed ledger3/10 without spending unused7 or changing model. A separate acceptance copy and versioned purpose preserve old fallback decisions. No valid live posture: STRATEGY-01 remains live-blocked, not accepted. Entry into inference is unknown, never inferred from listed availability or fallback cost0.

40 focused pre-live tests/18 post-live transport tests/27 artifact assertions pass;77 prior protected artifacts unchanged; historical372 full suite retained. Real paired Save16 native Continue and fresh fallback/host restore proof are explicitly limited; no after-live paired native acceptance is claimed. No candidate chosen, resource/opportunity spent, party/ROM/AI action changed or other role called. All task-owned processes/listeners stopped; hosted default false. Next recommendation is separately authorized Strategy model/provider change (or later renewed exact-model retry), never automatic SYSTEM1-01A/endgame work. See docs/strategy01.md and evidence/phase3/strategy01/closeout/.

## D31 — explicit backup qualification, named contingencies and failed API acceptance (2026-10-03)

Separate attachment authorizes backup selection <=5 requests/<=3 per job/$0. Later typed instruction additionally names Qwen backup_backup and openrouter/free last resort. Resolve these as explicit single-model test roles within the same aggregate5, never primary automatic fallback. Preferred Nemotron/profile preserved; no primary retry. Inkling-small is free/healthy but lacks advertised tool_choice/function choice; reject before POST rather than change the contract. Qwen exact free ModelRun/function-tool route qualifies; user-supplied temporary process value supplies missing .env assignment. Free router has no endpoint records for existing exact-model/function-tool gate and remains unqualified/uninvoked.

Add only host selection plumbing and persistently enforced5 cap. Existing credential config names OPENROUTER_KEY but current file contains OPENROUTER_API_KEY; allowlist that standard alias privately, preserving .env. Initial missing-name launch consumed0 requests and was regression-tested before generation. Same Rick scoped modelInput/PREP16, schema2/prompt1/persona1/owned stock/companions/evidence. Actual v5 Qwen3 POSTs:HTTP400,429,429; no valid typed output. Because v5 discarded HTTP bodies, first400 cause and precise429 reason remain unknown; do not retroactively classify400 as schema/model/application fault. Post-run v6 records bounded redacted HTTP error messages and stops400/429 unchanged retries;0 new calls. Bodyless mocked error reader exposed KeyError/file, guarded and tests passed. Budget closes3/5, no second blind job/new fallback selector.

No valid live result or acceptance. Preserve old13 primary attempts and all historical fallback receipts/evidence.53 unique focused tests across scoped runs,34 artifact assertions; old372 full suite retained.77 current historical and244 original foundation artifacts unchanged. Exact primary-equivalent Rick input/16 options, upstream hashes and native601-byte idle opponent-party/count/static ROM unchanged; Janice reports only and Doug empty. Fresh native before Save16 Continue and host fallback replay/restore are explicitly not after-live native persistence proof. Services/listeners stopped, no jobs/pendingSave, known paired view16, hosted disabled and private attempted audit copy retained.

STRATEGY-01 LIVE ACCEPTANCE STILL BLOCKED. Recommend separately scoped small typed-compatible free-model selection/HTTP400–429 diagnostic benchmark, not automatic production fallback or quality claims. No schema weakening, resources/team/action changes, new role, System One or endgame work. See docs/strategy01.md and evidence/phase3/strategy01/backup/.


## D32 — subjective StrategyMemo and actual text acceptance (2026-10-04)

Strategy emits a bounded, exact natural-language **StrategyMemo**, not required JSON, tools, enums, evidence IDs or numeric posture. One ordinary completion interprets the existing actor-filtered context and legal preparation constraints. Approximately100–250 words is a prompt target, not a semantic validation requirement. Host validation enforces nonempty strict UTF-8, at most4096 UTF-8 bytes, no unsafe control/format characters (paragraph LF allowed), and the current immutable actor/job/branch grant. The provider also enforces at most1800 output tokens,65536 response bytes,24576 request bytes/conservative input tokens,35 seconds/request and120 seconds/job. A failed completion produces explicitly labeled deterministic prose fallback; no repair loop.

Persist accepted text verbatim with host-generated strategy/job/actor IDs, campaign/branch/generation/cutoffs, context/material hashes, preparation-envelope reference, persona/configuration/prompt versions, timestamp/cursor and provider/model diagnostics. Reuse stored text on restart, UI refresh and repeated decisions. Fresh legitimate opportunities/material precommit evidence may yield different prose; replay does not regenerate it. Future commitment must atomically lock the exact memo reference/hash alongside the team. Commitment/installation is not implemented here.

A memo is subjective interpretation. Even an unsupported prediction remains text: it never becomes canonical truth, actor knowledge, acquisition permission, resources, preparation selection or a battle action. Future System One requests must separate **AUTHORIZED FACTS** from **STRATEGY MEMO — SUBJECTIVE**, pass the exact stored text, and allow only supplied current legal candidate/action IDs. No prose-to-facts or prose-to-numeric-posture conversion is required or implemented.

Historical posture schemas, prompt/config hashes, records and closed experiments remain unchanged. `strategy/memo.py` adds schema3/prompt2 MEMO receipts using the existing paired Strategy cutoff/hash. Historical internal projection key `postures` retains its name to preserve existing checkpoint hashes; `memo_records()` exposes only schema3 text. Explicit MemoStore adoption is limited to the new acceptance working copy; legacy StrategyStore refuses a memo-enabled database. Original databases are not migrated or rewritten. Normal inference remains disabled. No System One, party/resource/ROM change or endgame work is authorized.



D32 acceptance (2026-10-04): corrected StrategyMemo host runtime and actual free Nemotron smoke/Rick result accepted. Exact model text survives fresh host/native Save17 Continue, paired Save16 rewind excludes it/late grant, and paired Save17 return retrieves it without inference.67 unique focused tests/0 skips and actual-artifact audit passed;16 full Rick option plans, knowledge/history/companions/resources and ROM unchanged. Budget closed2/2; historical records/inputs/evidence preserved and all task processes stopped. See docs/strategy01.md and evidence/phase3/strategy01/memo/completion.json. Next separately authorized SYSTEM1-01A; no selection/commit/install/action or endgame implemented.


## SYSTEM1-01A / D33 — accepted (2026-10-04)

The separately authorized preparation gate is accepted. Native Mercury Decide Free received Rick's exact D32 StrategyMemo, actor-authorized facts and all16 source-derived PREP candidates. One production request selected the legal unchanged candidate, preserving both level6 Weedle/Caterpie, Tackle/Poison Sting and String Shot, with no held/bag items, acquisitions or spend. This is an actual model decision, not fallback; it does not prove a changed roster. The imperfect memo remains verbatim, and its questionable move references never became permissions or installed moves. Full probabilities/confidence are retained; no resampling or rerun forced a different answer.

Selection is separate from one-time revalidation/atomic opportunity, stock and companion-lineage commitment. The immutable memo/candidate lock is installed through CreateMon/SetMonData in an isolated controlled native encounter. Actual constructor count1, decrypted opponent checksum/species/levels/four moves/PP/items matched the commitment. An ordinary battle completed under unchanged FireRed tactical AI. Native normal Save19/fresh Continue returned the saved Gym position and exact decision/commitment/installation without inference. An isolated database restore audit excludes future decisions/commitments at actual Save17, returns the lock without installation at Save18, and restores all receipts at Save19; stale results cannot recommit. Rick's native defeated flag stays set.

Evidence: `evidence/phase3/system1_01a/completion.json`, `selection.json`, `commitment.json`, `native-installation.json`, `fresh-runtime-replay.json`, `paired-restore-audit.json`, `artifact-checks.json`, `commands.md`; implementation and scope in `docs/system1_01a.md`.57 unique focused host/compiled-contract/regression cases (0 skips),37 actual-artifact checks,3 schema checks passed;326 protected inputs unchanged. Actual final ROM SHA256 `1b60bd038c4b8d4e9fff6999573113dde05f06090a4435e2e616cc2b5637c924`, source pret `037335f4c725d7c9aecdac87066f2002b4bd7e14`. This is a focused result, not an entire-suite or campaign playthrough claim.

Two native System One POSTs total (synthetic smoke + Rick), both usage.cost0; ledger closed. Configured providers/models and default offline policy are unchanged. No new Strategy/Hermes or tactical inference. Workers/listeners stopped, private batteries/databases/screenshots retained. Final pair: Save19/checkpoint `a4ed907e-dc44-46e7-a786-63aba2350fc0`, canonical cursor162, fingerprint `255f14d39ac15b0ea0478cc0f9f8264aa61458b43a9a17e089a6548ea2445315`.

Remaining boundaries: controlled opening Rick installation is not full campaign rematch invitations/reward handling. Nonzero items, later acquisitions and general trainers lack native installation acceptance. Source-qualified new move names avoid a legacy MOVE_EFFECT alias collision; historical catalog/memo inputs remain preserved pending an explicit migration. The dedicated168-byte mailbox leaves52 bytes in the reserved EWRAM region. Native build compatibility and initial prep-only unsaved continuation are explicit narrowly validated adapters, not general save migration. SYSTEM1-01B action enumeration/execution/fairness/latency is deferred; see `docs/system1_01b_readiness.md`.

**Completed ticket: SYSTEM1-01A only. Next dependency task: separately authorized BATTLE-01 fair observation, legal-action and deterministic fallback groundwork; then audited BATTLE-02/ROSTER-03 lifecycle integration before SYSTEM1-01B.** No subsequent phase or endgame is implemented.

## D34 — BATTLE-01 expanded scope and native authority (2026-10-04, in progress)

The user's supplied BATTLE-01 request supersedes the earlier utility-evaluator-only ticket wording for this work: qualify native authoritative moves/switches/items/forced replacement, fair bounded chronology, deterministic external controller commands, revalidation and vanilla timeout fallback. Do not score strategy or call any model. Native engine helpers/state remain legality authority; isolate preference heuristics from usability, explicitly document the source Arena Trap heuristic discrepancy. Use an allocated48-byte control plus lifetime-managed1036-byte heap work to preserve prior RAM addresses, subject to actual lifecycle measurements. Accepted D33 locked preparation and exact subjective memo remain unchanged. Passing host/C matrices is not live acceptance. See docs/battle01.md; no SYSTEM1-01B or broader campaign/rematch/endgame authorization.


## BATTLE-01 / D34 acceptance —2026-10-04

Expanded BATTLE-01 is accepted only for armed D33 Rick ordinary singles: source-authoritative legal moves/switches/finite-item/replacement/Struggle boundary, fair snapshot/exact subjective memo/chronological history, asynchronous deterministic fixed choices, native execution/revalidation and vanilla fallback. Actual external switch and five Poison Sting resolutions passed; sole replacement skipped the provider. Delayed deterministic output fell back without stopping frames/events. Full normal battle ended with player loss (outcome2), mandatory offline recap recovered/settled, and unchanged lock. Actual-C fixtures cover finite item command/decrement/disappearance and multiple replacements; item animation/HP effects are not claimed as emulator proof.28 focused unittest cases/0 skips,8 actual-Lua mock-control assertions,23 artifact checks passed.452 protected inputs unchanged;0 model calls. Exact evidence/failures/exclusions: docs/battle01.md and evidence/phase4/battle01/completion.json.

Save20 checkpoint f1633a24-d4ae-42c0-b586-a8a35eb47452/cursor179 was normally saved and reloaded. Five completed battle audits/post survive the pair; isolated Save19 restore excludes future audit/post. ROM SHA2566582e03a8a2daff55e47d153fc5eee9838c8ea55803ed446f99b8b6a01b0d570.48-byte fixed control plus1036-byte heap payload (freed),4 reserved bytes remain; save layout/prior RAM unchanged. Host publication latency6.4–211.2ms; hosted/fast-forward latency unqualified. Workers/listeners stopped, default hosted inference offline.

Completed ticket: BATTLE-01 only. Next separately authorized task: SYSTEM1-01B live native-provider acceptance for this qualified path; docs/system1_01b_readiness.md records remaining gates. No general rematch UX, new strategy/roster/resource behavior or endgame. Broader BATTLE-02 remains separate. This supersedes the earlier utility-only BATTLE-01 and broad BATTLE-02 prerequisite for controlled Rick model acceptance; foundations are not restarted.

## D35 — SYSTEM1-01B scoped live authorization (2026-10-04)

Configured free Mercury only, controlled D33 Rick ordinary singles, shadow first then enabled;30 total hosted requests maximum (smoke also counted), one per decision/no retry by default. No confidence escalation, resampling, model substitution, strategic override, Strategy/Hermes calls, preparation reroll or campaign expansion. Reuse BATTLE-01's exact legal/execution/persistence path. Existing preparation adapter defaults remain unchanged; tactical child-process deadline is explicit and bounded below native timeout. Actual free-route metadata and durable ledger required; provider failure disables further live calls and leaves vanilla fallback. Acceptance requires actual shadow/enabled completion, scoped evolving state, native selected/resolved agreement and normal post-battle save/reload. This authorization is not acceptance. Endgame and subsequent tickets remain deferred.


## SYSTEM1-01B / D35 blocked closeout —2026-10-04

Host live/shadow provider implementation and independent setup are complete, but SYSTEM1-01B is not accepted. Configured free Mercury native smoke passed; one actual Rick shadow proposal was valid (String Shot,1.687s), two complete-shadow HTTP attempts exceeded1.9/2.05s and one earlier trial hit the2.25s worker deadline.5 total charged requests including smoke; ledger closed, no retry/substitution/other roles. Two returned responses report zero cost; interrupted request usage is unknown. Full shadow715026728 completed normally under vanilla fallback, with sole forced replacement bypassing inference and an offline mandatory recap. Enabled battle was not run because latency qualification failed.

Actual normal Save20/checkpoint5575c709-d8c9-42ef-aee1-6c9fa80906a1/cursor177 was reloaded in a fresh native Continue and host: five audits, exact memo, D33 lock, recap and replay hashes survive; no further requests. Save19 excludes the future shadow history.25 artifact checks,28 retained +10 final focused tests (34 unique/0 skips),524 protected inputs unchanged. Unchanged BATTLE-01 ROM SHA2566582e03a8a2daff55e47d153fc5eee9838c8ea55803ed446f99b8b6a01b0d570. Exact attempts, latch reopenings, failed trials, commands and blocker: docs/system1_01b.md; evidence/phase4/system1_01b/verification.json. Workers stopped; normal hosted default remains disabled.

Completed new ticket IDs: none. Next task: SYSTEM1-01B latency qualification/acceptance closeout, then continuous VERTICAL-SLICE integration under separate authorization. No phase expansion, roster/memo/resource edits or endgame. Shadow save/reload is not enabled acceptance.


## SYSTEM1-01B / D35 acceptance —2026-10-04 (supersedes interim latency-blocked closeout)

SYSTEM1-01B is accepted for locked D33 Rick ordinary singles at normal speed. Full shadow1660475733 passed with4 real unexecuted Mercury proposals; full enabled3468328694 applied all4 meaningful Mercury choices (String Shot/switch/String Shot/String Shot) through unchanged native guards/controllers. The switch and first String Shot resolved; later move selections were interrupted by fainting, correctly recorded separately. Sole replacements bypassed inference. Both battles ended normally with player wins; no predetermined result or optimality override.

13 total charged requests including smoke/errors;10 returned responses reported cost0,3 interrupted responses lack usage. Same configured free Mercury, no other live roles, reroll/resampling/model substitution. Early deadline/startup/trigger/config-label failures and explicit same-ledger reopenings remain recorded. Final HTTP2.35/worker2.55/host2.75s lie within unchanged native180 frames; retained host default2.5s stays unchanged.8 passing shadow/enabled responses: HTTP median0.621s/max0.904s; host median0.820s/max1.017s. No small-sample p90/p95 claim or fast-forward qualification.

Actual normal Save20/checkpoint5cbfae80-800f-419f-9b45-1d42f4afee1b/cursor177 was freshly Continued with no reinference: exact lock/memo,5 enabled audits, offline mandatory recap and replay hashes survive; abandoned shadows/Save19 future exclusion pass.33 artifact checks,35 unique focused tests/0 skips,524 protected inputs unchanged. Native ROM SHA2566582e03a8a2daff55e47d153fc5eee9838c8ea55803ed446f99b8b6a01b0d570 unchanged. Source implementation/evidence/commands: docs/system1_01b.md; evidence/phase4/system1_01b/verification.json and completion.json. Workers/listener stopped,13-request ledger closed, configured providers/default offline unchanged.

Completed ticket: SYSTEM1-01B only. Next separately authorized task: VERTICAL-SLICE continuous managed campaign integration; docs/system1_01b_readiness.md records gaps. No live nonzero items/multiple replacements, general trainer/mode/rematch/Gym/acquisition expansion or endgame is claimed. Earlier blocked report is historical timing qualification, not current status.

## D36 — VIRALITY-01 deterministic public diffusion and organizational evidence (2026-10-04)

User separately authorized VIRALITY-01 only. Add a save-paired virality log without
rewriting accepted SOCIAL1 or Strategy v2 identities. Ordinary reach freezes
actual branch-scoped player incoming followers at the first distribution epoch;
versioned opening bands are 0/5/20 followers, discovery budgets2/12/64 and campaign
windows1/3/7. Direct author relationships and chronically-online public scouting
are separate access paths; explicit exposure remains necessary for knowledge.
Trusted native encounter IDs classify prominent events, including shared
Rival/Champion/Giovanni identities. High-profile discovery is independent of
low ordinary fame. Meaningful publication/domain ticks replace wall-clock/feed
polling, with bounded idempotent work and no inference.

Keep old evidence; provide deterministic source-quality/current-relevance bands,
original-source identity, path/order/distance and independent-origin accounting.
Reposts/forwarding do not multiply corroboration. Rocket membership/leadership
permits complete legitimately observed battle claims through private ROCKET_INTEL,
not other private memories or unseen state. Public consumers retain only published
subsets. Typed four-claim Rocket/Potion proof is a domain fixture; native player
item observation export is still unqualified. Strategy social context v3 is an
additive offline projection; existing memos/locks/providers are preserved.

Primary next vertical slice: first Rick battle/public post → Brock scouting →
Brock memo/first-Gym bounded preparation/control → Gym recap/downstream knowledge.
Post-Boulder Rick rematch is secondary. No VERTICAL-SLICE, hosted inference,
Brock strategy/team change, live Rocket battle, ROM edit or endgame is authorized
by this decision. Details/proofs/remaining gaps: docs/virality01.md and
docs/vertical_slice_readiness.md.

## D37 — VERTICAL-SLICE-01 scoped integration authorization (2026-10-05, in progress)

The user authorizes one continuous first Rick → actual mandatory Hermes recap →
public virality/scouting → Brock's scoped subjective strategy → sole authored
first-Gym commitment → native Pewter Gym Brock/System One → Gym recap/downstream
exposure loop. Reuse accepted domain services; no manual social/AI stitching,
new roster options, general battle modes, Rocket live battle or endgame.

One shared durable ledger bounds all hosted POST attempts to30 total, with role
caps6 Puppeteer/4 Strategy/2 preparation/20 tactics. Sole first-Brock preparation
uses no model request. Use configured verified-free providers; no silent fallback
model, rerun of valid output, resampling, escalation or tactical optimization
substitution. Offline gameplay is separate from live acceptance.

First Gym commitment is a declarative first-encounter opportunity, not an earned
rematch/growth token. It must replay without inventing an earned allowance.
Scouting context/prompt3 explicitly adopts typed public evidence quality/order;
old memo configuration/hashes remain unchanged. Prebattle knowledge freezes with
commitment; native permitted battle observations evolve separately. Brock's
vanilla party constructor and actual Gym script remain authoritative; an
observational constructor counter reuses existing allocated fields. Isolated
campaign ROM allocation/save audit and host fixtures are not acceptance of the
continuous emulator/live loop. See docs/vertical_slice01.md as evidence develops.

### D37 evidence closeout — 2026-10-05

The actual native Rick→public-only Brock scouting→authored first-Gym→downstream
loop and normal S0/S1/S2/S3 restore/branch privacy are proven. Actual Rick/Brock
Hermes recaps and two native Mercury selections are live, but the sole Brock
Strategy response was invalid and an immutable labeled fallback memo was locked.
Acceptance criterion7 therefore remains open. A different memo cannot be attached
retroactively to this encounter; a future closeout needs a legitimate new
precommitment branch/opportunity and that branch's full native proof.

The supplied prompt calls role sub-bounds *recommended*, with total30 taking
precedence. This implementation conservatively made6/4/2/20 hard sub-limits;
those remain unchanged. Current ledger is closed9 total, Puppeteer6/6. This is
not a user-mandated aggregate-budget exhaustion or proof of external outage.
Any further bounded run must preserve all9 attempts and explicitly account for
that stricter implementation choice; never reset a ledger to obtain more calls.

A managed host continuation after its first runtime window expired retained the
same ledger/charges, branch, native session and locks. Immutable frozen authored
personality and public facts are retrieved from the committed Strategy context,
not mutable configuration. Native constructor observation validates Brock's
sole authored candidate without replacing the real Gym script or story awards.
All-layer restored browsing and fresh pinned Hermes retrieval after cleanup
preserve durable history; retrieval uses labeled mock transport/zero hosted POSTs.

The retained golden artifacts start at a real imported pre-Rick battery and
include route RNG/recovery. They do not qualify New Game/starter selection,
blind full replay, post-Brock preparation/rematch or a fully live accepted slice.
No campaign-expansion readiness is declared before the remaining live gate.
Evidence and exact commands: docs/vertical_slice01.md,
docs/vertical_slice01_commands.md, evidence/phase4/vertical_slice01/verification.json.

### D37 live closeout continuation — 2026-10-05

The user requested continuation. Explicitly reallocate the prompt's recommended
role sub-bounds in the same durable ledger: Puppeteer10/Strategy4/preparation2/
battle16, unchanged hard aggregate30. `rebalance_closeout` requires the original
closed ledger, preserves all9 prior charges/outcomes, records the change and
refuses any reduction below existing charges. Five focused budget tests pass,
including unchanged aggregate exhaustion. This corrects the stricter-than-prompt
implementation choice; it is not a model/price/authorization or ledger reset.
Restore S1, create a legitimate branch through native gameplay, normally Save,
then allow one newly qualified automatic Strategy job before commitment. Preserve
original fallback branch/encounter evidence and never attach its Gym result to a
new memo. Current closeout evidence is in the same directory with closeout labels.


### D37 live closeout result — 2026-10-05

The second explicit closed-ledger reallocation freezes unused Strategy/preparation
slots:10/4/2/16→10/2/0/20; all existing charges retained and aggregate30 unchanged.
A genuine new native branch obtained one valid live Nemotron memo, preserved
verbatim including subjective mistakes/unavailable intent. The sole authored
Brock roster and frozen facts remain game-owned; no invented tactic manifested.

Real first Gym produced18 valid Mercury choices and one turn19 vanilla fallback
after the battle allocation was exhausted before HTTP. Player loss/blackout/no
Boulder is actual native history. Two final Hermes calls committed a real victory
recap/private episode and public-only broader exposure. The ticket remains open
for fully live Gym completion/Boulder evidence on the live-memo branch. Do not
reuse the old fallback-memo branch's win. All30 aggregate attempts are now closed.
Matched provider receipts were reconciled read-only into unset ledger outcomes
without adding/replacing charges; first9 outcomes remain exact. Native terminal
duplicates after managed restarts agree and count once by request identity.

Normal earlier/final fresh restores, all-layer native viewer immutability and
scoped fresh Hermes retrieval (explicit mock model transport,0POST) pass. Durable
state survives actual home cleanup. A further at-most10-request/ceiling40 window
is a proposal requiring explicit user authorization, not a silent budget reset.
See docs/vertical_slice01_closeout.md and closeout-verification.json.


## D37 — bounded additional live Gym closeout (2026-10-05)

User attachment67416101 explicitly authorizes +40 verified-free requests in the
existing ledger, partitioned36 battle/4 Hermes successful-victory recap,0 Strategy
or preparation. This supersedes D36's unauthorised proposed +10 window. Preserve
original30 immutable rows, exact pre-Brock memo/lock and checkpoint; scope charges
to Brock identities, forbid other roles and permit recap only after confirmed
fully-live player victory. No legal-action/prompt/timeout/ROM change is justified
by player losses. This experimental scope does not redefine production repeated
Gym learning or mandatory completed-battle posts.

Result:36 additional valid Mercury calls,0 new Hermes,66 total cost0 receipts.
No confirmed completed victory. Three visible fainting attempts lack BATTLE_ENDED
receipts (corrected from intermediate completed-loss wording); fourth stops at
pending turn12. Final paired prebattle restore proves seven hashes and separate
tactical-audit cutoff; append-only abandoned evidence remains isolated. Nine
focused tests and78 actual integrity checks pass without waiving missing gates.
Ticket remains STILL BLOCKED; ledger closed, offline default, no campaign
expansion/endgame or new inference. See docs/vertical_slice01_gate.md.


## D38 — authoritative terminal receipts and tactical dispositions (2026-10-05)

BATTLE-END-01 is a zero-hosted-inference prerequisite to final VERTICAL-SLICE-01
acceptance. Native outcome plus the FinishBattle TRY_FINISH/FINISHED guard is
canonical authority; prize/faint/badge-looking text cannot substitute. Existing
PiEvents_End-before-PiBattle_End hook timing is correct and retained. Old gate
screenshots show player-loss payments; the earliest failure was harness abandonment
before terminal cleanup, not a proven Mercury or reducer defect.

Stable transport-owned terminal bytes retain the same identity through bounded
per-frame retries until ACK/reset, without blocking game play. Queue capacity and
incomplete-stream validation remain explicit limits. Host commit precedes ACK;
normal Gym scripts/save flags remain authoritative. Tactical controller emission
is not execution: code-owned append-only lifecycle records give every request an
executed/canceled terminal disposition, fresh-host recovery never resumes old
choices, and terminal/branch guards dominate provider scheduling/publication.
Teardown leaves copied receipt metadata in existing fixed control, not heap pointers.

Actual no-model external Brock win/loss and vanilla loss, short disconnect/duplicates,
normal Gym/Boulder save/reload, automatic pending recap and rollback prove the
narrow gate. Closed66 ledger, accepted memo/lock/source content/config preserved.
No new inference, post/diffusion, battle policy or endgame implementation. Future
live closeout budget in readiness is a proposal requiring separate authorization;
it does not reopen the ledger. Fixed allocation remains at0x0203FFFC (4 bytes free).
See docs/battle_end01.md and docs/battle_terminal_contract.md.


## D39 — final live vertical slice accepted (2026-10-06)

User attachment54a7d48c authorized +80 verified-free Mercury battle calls and four
reserved Hermes calls on the same immutable66-charge ledger, with ordinary
competent player inputs and no new engineering phase/model/preparation inference.
Accepted BATTLE-END-01 ROM was adopted by explicit manifest binding; source,
policies, prompts and exact memo/lock stayed unchanged. Setup/ledger/test-navigation
helpers only; no battle AI, roster, story, virality or save-layout change.

Two real player losses (seven/six calls) were abandoned by exact clean checkpoint
restore. The winning native Brock battle then executed20 live legal choices with
zero meaningful vanilla fallback. One sole forced Onix replacement used native
source3/reason4/count==1; it is not a provider fallback. Normal Growl/Seed/Tackle,
one legally purchased Potion and naturally learned Vine Whip produced the win.
The native end committed once, Gym awarded Boulder/TM39, and automatic live Hermes
(two calls) published factual public claims plus a separate private director episode.
Unmodified highProfile Gym policy delivered79 versus Rick57 at fame1; upcoming
Sally learned only the two Brock-public claims before the player opened PokeBook.

Native feed/posts/followers were visually inspected and read-only. Final ordinary
counter13 checkpoint b67c97e6-46b4-410f-87c3-6a1ebb696fa0 survived a fresh offline
emulator/host reload with seven hashes, memo/lock/audit/lifecycle identical. Prefix
rollback excludes all future state; winning branch restored. Fresh actual Hermes
process after cleanup retrieves one durable Brock episode with explicitly mocked
transport/0POST. All18 gates plus5 integrity checks and26 focused host tests pass.

Ledger101:33 new battle/two Hermes/0 Strategy/preparation,35 zero-cost receipts;
first66 immutable, unused47+2 allowance closed after first success. All owned
workers/listeners stopped, default inference disabled. No additional live role,
campaign expansion or endgame began. Recommend only a small Route3/Mt. Moon
qualification pack beginning with Sally. Existing saturated/offline/hot-state,
4-byte EWRAM/stack, broader mode/item and provider risks remain; player Potion
identity is not a specific canonical/social claim in this run.

Current acceptance supersedes older VERTICAL-SLICE-01 blocked closeouts without
rewriting their evidence. Report: docs/vertical_slice01_final_closeout.md;
evidence/phase4/vertical_slice01/final-verification.json. Readiness recommendation:
docs/campaign_expansion_readiness.md.

## D40 — additive early ordinary-trainer pack and blocked live qualification (2026-10-06)

User attachment5eed1f3e authorizes only CAMPAIGN-EXPANSION-01, from accepted D39
post-Brock state, max60 verified-free POSTs (12 Puppeteer/10 Strategy/6 preparation/
40 battle), zero new permanent EWRAM. Select existing Sally117, Greg106, James107,
Kent108 native singles/source-empty items. Shared campaign content plus generated
ROM qualification reuses generic hooks; no trainer-specific controller. First
parties retain exact authored partners/levels/moves/resources, no acquisitions.
Existing Route3/MtMoon progression bindings are validated, not unnecessarily
reversioned. PREP CONTENT_ADOPTED binds additive content to checkpoint prefixes;
legacy writers fail closed. Historical opening content/model slots unchanged.

Actual Sally mixed live/fallback victory is not full live acceptance. Preserve
actual memo/decisions/history and automatic live Hermes recap/follow/virality.
One tactical deadline exposed a process-wide provider latch; scope it to encounter
identity without retries in the failed battle. This host fix is tested, not live
qualified. Greg preflight failure's committed fallback remains immutable; no
model substitution or reroll. Closed ledger16 POSTs; one timed-out cost receipt
unknown,15 confirmed zero. Stop further inference at concrete gate failure.

A pending-save restart suspended host pairing; retain failed evidence and recover
only through existing normal-save receipt validation/restoration APIs, never SQL
status/cursor edits. Actual recovered counter15/C1 survives fresh offline Continue;
automatic restart receipt idempotence still needs its gate repair. Larger PokeBook
feed sorts by publication order, not post hash; no social write/read exposure.
Actual all-RAM symbol triples/end unchanged,4-byte headroom; ROM extra+56 bytes.
Unmeasured stack/heap and wider modes/items remain risks.

CAMPAIGN-EXPANSION-01 stays live-blocked. New later trainer/MtMoon/branch-live
qualification requires scoped closeout, with existing history protected. Do not
advance to Rocket, Cerulean, Rival, acquisition or endgame under this authorization.
See docs/campaign_expansion01.md and evidence/phase6/campaign_expansion01.

## D41 — zero-inference campaign gate safeguards and historical evidence limit

User attachment1f2e983d authorizes deterministic CAMPAIGN-EXPANSION-01 gate repair
only, zero hosted generation. Preserve C1/Sally outputs/Greg fallback+lock/closed16
ledger, no permanent RAM. Expose the unchanged ordinary-text request serializer for
pure production preflight; record boundary/symbolic errors before future workers.
Do not infer a historical error code from today's healthy free route.

Classify save callbacks before strict pairing; finish valid native save before
job/audit recovery. Permit only visible identical audit/lifecycle duplicates through
a save barrier, reject conflicting/future/abandoned envelopes, recover constructor
counter from durable installation prefix. Interrupted Strategy transport never
resumes; revoked logical work waits for future authorization. No automatic extra POST.

Retain hard tactical deadlines; poll active tactical work10ms instead of idle200ms.
Real deterministic emulator matrix proves two timely external executions and three
safe fallbacks/late isolation. Deliberately abandon that test encounter before its
completion and restore exact C1. No campaign result is fabricated. Actual pending
save restart/fresh Continue passes; zero EWRAM delta/headroom4 remains.

Gate repair acceptance is withheld at the historical preflight evidence gap; all
retained104 experiment files lack its specific code. Future Greg first Strategy
reroll would conflict with its preserved lock. Kent108 already denotes MtMoon;
a fourth actor requires separate content scope. No new live budget, new campaign
phase, provider/model replacement or endgame authorization.

## D42 — historical telemetry evidence disposition (2026-10-06)

User attachment `a56f32ee-bba4-4d8e-b400-28d28e7f088b/Pasted text.txt` replaces only
CAMPAIGN-EXPANSION-01 gate criterion1 with: exact retained primary cause OR a proven
retained-evidence irrecoverability disposition, explicit UNKNOWN, current production
preflight and repaired durable future diagnostics. Functional/privacy/save/deadline/
RAM evidence is still mandatory. Missing historical telemetry is not reconstructable
evidence. This is not a general exception for missing functional proof.

104 retained artifacts contain no correlated exact Greg code/failed metadata; retain
the generic ProviderError/fallback unchanged. Historical classification **UNKNOWN —
insufficient retained telemetry**. Current requests pass; actual adapter mocked400/
429/timeout/transport/malformed/preflight failures retain six distinct categories
through guarded memo commit and a fresh process reload. Preserve worker diagnostic
scope in parent history. No diagnostic text is delivered as NPC knowledge. No key,
provider prose or full request is added to incident records.

**GATE REPAIR ACCEPTED**, superseding D41's historical evidence blocker only.156
host tests/0 skips, native C/incremental build, retained actual emulator/save proofs,
all original protected hashes and permanent EWRAM4 bytes/delta0. Zero generation;
workers stopped; normal inference disabled. Full expansion remains unaccepted.

Readiness documents the real three remaining actors Greg106/James107/Kent108;
Kent is already MtMoon, not a fourth actor. Preserve Greg first memo/lock; no reroll.
Recommend Strategy2/preparation0/battle84/Hermes12 =98 future calls, not authorization.
A fourth actor or new Greg live strategy requires separate legitimate content or
opportunity scope. Stop at evidence closeout/readiness; no campaign run/new phase/
endgame. See docs/campaign_expansion01_final_readiness.md and incident JSON.

## D43 — final pack authorization and verified-free health stop

User41409a11 authorizes exact additional98: Strategy2/preparation0/battle84/Hermes12.
Preserve original closed16 ledger; isolated final continuation ledger copies the16
immutable rows, freezes their hash/outcomes and numbers future calls17 onward. Max114
includes historical16. Caps are nonfungible and unused slots stay closed on stop.
Generic host/provider paths use an explicit final opt-in evidence/private root;
no native hook, trainer special case, model/provider substitution or config-default
inference change. Same Greg→James→Kent scope, same frozen Greg memo/commitment.

Stop before live gameplay when required configured Nemotron route cannot qualify:
metadata endpoint status-2 fails accepted status0 predicate despite zero pricing.
Mercury/Hermes qualify; no POST was made. Initial symbolic failure retained plus
separate subsequent metadata observation. Do not claim a remote HTTP subtype or
use this incident to explain Greg's old UNKNOWN. Source C1/original artifacts unchanged,
16 relevant tests pass, headroom4/delta0; final ledger closed with0/98 new calls.
Full pack remains blocked, gate repair remains accepted, next is this same final
closeout once role qualification is possible. No new engineering ticket or endgame.

## D44 — explicit Strategy replacement window and nullable health telemetry

User3e7d2a32 approves Gemma exactfree primary, Qwen exactfree only after primary concrete
failure, max4 qualification calls, no campaign/Mercury/Hermes or random/paid routing.
Gemma published text endpoint has accepting status0, price0 and daily uptime while
short-window uptime null. Generic text-route health selection uses first known valid
5m/30m/1d metric, records its window, rejects measured0/unknown/statusnot0/paid.
No trainer/model-specific predicate or JSON/tool requirement. This retains status-2
Nemotron rejection. Record initial null TypeError and fix without calling it a remote
provider error.

Gemma two tiny smoke POSTs return429 (one bounded transient retry); contingency Qwen
exact catalog/endpoints empty. Qualification blocked; actual2/4, unused2 closed.
No replacement activated or .env/model-profile edit, no silent fallback to old
known-blocked Nemotron. Future explicit .env selector swap preserves historical
model_profiles-derived Strategy identity; never rewrite prior memos/models to match.
Original C1/Greg/history/ledgers remain byte-identical, headroom4/delta0, no gameplay.
Cost receipts absent from error responses: unknown reported cost rather than fabricated0.
Next bounded model qualification decision, not new campaign phase or endgame.

## D45 — live-catalog Strategy qualification and explicit new-job selector

Userf63d85f4 authorizes live-catalog qualification max6 calls/max3 candidates, one
ordinary completion per Strategy job, no campaign/Mercury/Hermes or random router.
Preferred Ling/LingFin free IDs absent. Section6 general secondary selection ranked
Liquid first from current free healthy catalog; one400 rejected disabled mandatory
reasoning. Section7 single contingency Dots next diverse general route passed both
smoke and fictional memo; stop selection there.3 calls, no retry/fourth model.

**STRATEGY-MODEL-03 ACCEPTED**; active .env Strategy selector Dots explicitfree through
AtlasCloud. Keep model_profiles.yaml identity unchanged to preserve historical stores;
per-job providerConfiguration reflects new selector. No fallback chain/trainer-specific
logic/tools/JSON redesign. Historical memos/metadata/Greg lock/C1/both ledgers unchanged;
49 tests/0 skips, local James/Kent and normal restore/reopen proofs, RAM4/delta0.
Synthetic questionable Effect Nightmare reference remains subjective prose; downstream
legality does not adopt it. Two successful cost0 receipts, one400 cost receipt absent.
Ledger closed, hosted defaults disabled, gameplay0; next same final98 campaign ticket.
Provider page/model card show ordinary-use compatibility; expiry2026-12-31 is explicit
maintenance risk. Catalog uptime is not an inference-availability guarantee; fresh
metadata before every future dispatch and recorded fallback remain required. No endgame.

## D46 — final campaign continuation retains Kent metadata failure and frozen fallback

Under userf93dfac2 existing98 ceiling, Greg/James actual native live battles and
Hermes/social/reload subgates completed. No architecture/model-selection change.
Kent new Dots Strategy preflight failed with retained route_metadata TimeoutError
before POST. HTTP/provider/requestID/elapsed latency absent, not inferred. Follow-up
metadata passed0.402s. Production fallback+PREP lock remains durable; later health
is not authority to overwrite it or manufacture an opportunity. Full ticket remains
blocked per user section18. Nearest actual paired C3 preserved/offline restored with
seven matching hashes; no Kent battle/Mt. Moon/final acceptance or next phase.

Additional36 calls (battle31/Hermes4/Strategy1/preparation0), all receiptscost0;
unused62 closed, old16 immutable. Ordinary incidental Ben defeat retained (no hosted
roles), not erased. Two Greg replacements native-confirmed by next snapshots but
lack resolved-action lifecycle receipts; classify honestly. Offline Home/old posts
shown, later pagination unavailable; knowledge/history unchanged, full browsing unproven.
Native RAM4/delta0, protected inputs unchanged, workers off/owned Hermes scratch cleaned,
durable memory preserved. Test fixture uses original16 rather than mutable live ledger;
20 focused tests pass after fixture correction. No gameplay repair or policy change
introduced. Next Kent preflight/fallback recovery and remaining same closeout; no
automatic model substitution, allowance reopening, team reroll or endgame scope.

## D47 — Kent fallback accepted as frozen production resilience; final viewer gate first

User58e9f038 narrowly amends CAMPAIGN-EXPANSION-01: James qualifies current live Dots
Strategy; Kent's accurately diagnosed metadata timeout / deterministic fallback /
legal preparation are authoritative for this locked encounter. No regeneration,
PREP or System One preparation call; recovered provider applies to future legitimate
opportunities only. Kent still requires meaningful live Mercury, actual Hermes recap,
normal Mt. Moon travel, social/privacy, expanded native viewer and final offline restore.
Existing98 ledger only;36 consumed,62 aggregate remaining,53 battle/8 Hermes usable,
remaining Strategy1 closed without redistribution. First52 total rows immutable.

Zero-inference viewer repair first: source inspection found120s absolute snapshot
expiry, previous native browsing crossed it. One-owner bounded host snapshot uses600s
idle expiry renewed only on successful scoped queries. Branch/epoch/visibility/record
caps remain revalidated; no ROM or permanent RAM added. Idle expiration still requires
reopen, invalid requests do not renew. Current real8-post and explicit read-only9-post
native fixture must pass before live inference. Acceptance remains pending actual proof.
No new ticket, provider substitution, phase or endgame authorization.

### D47 actual closeout evidence and stop

Kent fallback/commitment preserved exactly;8 real Mercury executions,1 engine-forced
replacement,actual Hermes recap/follow4→5/district diffusion passed. Real8-post and
read-only9/12-row native viewer proofs passed before inference; no additional EWRAM.
Current world then suspended on offline replay of retained request9: engine fields
match but external enum was relabeled external_test versus prior mercury. Future
duplicate handling preserves immutable prior provenance and verifies engine fields;
focused tests pass, native fix proof unrun. No direct metadata unsuspend, rollback or
reroll used. Native ordinary counter18 victory save and DB backup retained UNPAIRED.
Final actual10-post viewer/pairing/fresh Continue unrun; ticket remains blocked.
46/98 calls/$0, workers stopped/default inference disabled;43 focused tests pass.
Next zero-inference validated recovery/pairing of retained victory, then final viewer
proof. No new ticket or later-phase implementation. [Evidence](campaign_expansion01_kent_closeout.md).

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

### Narrow retrospective pairing rule

User628f9c2f authorizes pairing metadata only when immutable native/host artifacts
prove identical build, campaign/branch/run lineage, canonical cutoffs, terminal
prerequisites and existing gameplay projections. The recovered manifest hashes all
inputs/cutoffs/jobs, uses the existing canonical checkpoint extension chain, labels
retrospective recovery explicitly, and is idempotent. No intent, battle, follow, post,
memory, progression, plan, tactical execution or exposure may be invented to match.
Otherwise remain unpaired. This does not weaken normal save-time pairing or authorize
recovery from timestamps, matching flags alone, arbitrary dumps or copied RAM.

Actual real-DB inspection found the lookup also needed to exclude lifecycle rows
when matching native terminal provenance. That pure lookup is shared with the live
managed receive path; the launch/branch guards remain. Actor grants stay revoked on
suspended originals; forensic row/hash inspection is host-owned only. All current
requests are historical terminal audit; no historical inference resumes. Original
metadata-timeout, fallback, provider recovery, actual decisions, suspension and
unpaired condition remain preserved alongside the new recovery record.


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


## D52 — RIVAL-01 scoped live authorization (2026-10-07)

User c5a5c563 authorizes real Save20→Cerulean Rival acceptance only. The lower readiness limits win: Strategy1/PREP0/battle32/Hermes4, maximum40 total but37 usable nonfungible slots. Explicit fresh route metadata checks pass; retain Dots/Mercury/Inkling, no substitutions. Work on a copy of protected normal Save20, preserve original seven projections and historical ledgers. Normal travel uses offline incidental recaps; adopt new Rival content only after actual arrival and deterministic public-only context audit. No permanent RAM growth, no later encounters/endgame. Acceptance not yet claimed.

### D52 continuation disposition — 2026-10-08

RIVAL-01 remains BLOCKED — TRAVEL TRANSPORT CONTINUITY, not accepted. Josh91 and Miriam120 native victories committed on the isolated branch; timed offline host shutdown preceded a wild event298 (ACK297/drops1/retries2). Restart HELLO did not recover the dequeued start. Its complete32-byte retained payload passes checksum and decodes as wild BATTLE_STARTED, but no recovery injection occurred and no recovery service is qualified. This is not a finding of irrecoverability. Working branch explicitly suspended at cursor669; actor grants revoked; forensic SQLite backup is unpaired. Last coherent accepted Save20 and original protected artifacts remain unchanged. Calls0, empty ledger closed, workers/emulator stopped, inference disabled, permanent EWRAM delta0/headroom4. Focused21 host tests pass/0 skipped, no live Rival acceptance. Evidence: `evidence/phase8/rival01/verification-blocked.json`; [report](rival01.md). Next exactly RIVAL-01 deterministic travel-continuity gate repair, zero hosted inference; later phases remain deferred.

### D52 travel-repair outcome — 2026-10-08

User dde48405 authorizes only zero-inference generic event/lifetime repair and safe disposition, not a fresh Rival attempt. A surviving native counterpart is mandatory in addition to checksum/identity/branch/order validation. Exact original event298 belongs to launch ee127f88-a163-4b48-a77a-f324ec51329b, nonce2493534040/generation1, suspended branch481b8552-6800-493e-b254-33baf7c77b41/cursor669; last durable sequence297. Offline writer --seconds3600 expired before emission. The volatile queue exhausted two60-frame retries, before host receipt/commit. Retained working battery is Save20; native state is absent. **RIVAL-01 TRAVEL RECOVERY BLOCKED — EXACT CONTINUATION UNPROVABLE**, stop conditionB. No original event injection or retrospective pair.

Generic opt-in managed correction: FULL/WAL exact-wire inbox, canonical ingest-before-ACK, separate recovery audit, trusted native/process witness and fail-closed whole-emulator lifetime guard. Explicit same-native restart waits for replacement writer readiness before SIGCONT; input lease cancels stale queued automation. Existing physical/logical build normalization remains. This does not grant arbitrary pending-message replay, durable native events before host capture, or recovery after native loss. Legacy launchers require managed configuration before relying on this correction.

39 focused host tests pass/0 skipped, including actual incident/read-only native-unavailable classification and existing source334/actor0326 constructor compatibility. Separate normal1x mGBA trial: real Zubat start; seq2 commit/ACK withheld; exact retransmission duplicate; subsequent contiguous events, ordinary Run outcome4, ACK5/drops0; normal paired Save21/cursor447; timed writer expiry freezes native frame14921; fresh offline field Continue preserves seven hashes/native identity/checkpoint. Failed early reconnect/environment/stale-command tests remain evidence. This test pair is not a replacement campaign.

Last accepted rollback: original Save20/cursor443; Josh/Miriam genuine victories remain suspended future history and are inactive after rollback. Offline rollback context retains22 public receipts, excludes47 private Rocket receipts, full7524/8192 bytes; no memo/job or model calls. All21 preserved artifacts unchanged, original0/40 ledger closed, workers stopped/inference disabled, ROM unchanged/native RAM delta0/headroom4. No RIVAL-01 acceptance or new milestone. Next single separately scoped task: rollback-based RIVAL-01 normal continuation from Save20 using managed lifetime and paired checkpoints. [Repair report](rival01_travel_continuity_repair.md), `evidence/phase8/rival01-travel-repair/verification.json`.


### D52 rollback continuation authorized — 2026-10-08

User e5440ab0 authorizes full RIVAL-01 continuation under two mandatory gates: zero-inference normal Save20-derived travel/checkpoint/fresh offline Continue/context first; only then fresh free route qualification and real source334/actor0326 live Strategy/Mercury/mandatory recap/HIGH_PROFILE/native viewer/final pairing. Lower role caps S1/P0/B32/H4 remain within original40 ceiling; original closed zero-use ledger is retained and carried to a new namespace, not reset or enlarged. Abandoned branch, Josh/Miriam outcomes and missing wild298 are not transplanted. All gameplay uses qualified1x supervised runtime/input lease, no native state edits or savestates. New report docs/rival01_rollback_continuation.md. This is authorization/progress, not acceptance; no subsequent ticket or endgame.

### D52 rollback continuation disposition — 2026-10-09

Gate A passes actual Save20-derived travel: player defeats Josh12/Miriam70/incidentally grunt35110/Miguel15,26 wild Run terminals, zero gaps/drops, normal Save22 and pre-Rival Save24 with fresh offline Continue/seven matching projection hashes. Current public context retains30 receipts, excludes92 private Rocket receipts and fits7524 bytes; no Rival memo/lock/battle commits. Fresh Dots free-text qualification fails: only listed AtlasCloud endpoint has status-2 (required0), despite zero prices and positive recent uptime. Mercury/Hermes routes qualify; hosted calls0/40, lower caps unchanged. Stop workers/default inference disabled and preserve branch6af32bb1-08de-44f1-b7f6-928ebd0f5921/checkpoint8f162291-19e8-489c-bbf5-62cc858d25b9/cursor880. No substitution, fallback reroll or ticket acceptance. Next is renewed configured-route qualification and continuation from Save24, or separately authorized explicit replacement; completed travel is not replayed. [Continuation report](rival01_rollback_continuation.md), `evidence/phase8/rival01-rollback/verification.json`.


### D52 Dots renewal / live Strategy disposition — 2026-10-09

User8a2fb2ff authorizes at most3 non-generation health checks and automatic Save24 continuation if Dots qualifies, original40 ceiling/S3/P0/B32/H5 ceilings. Check1 transport reset, check2 exact Dots/AtlasCloud status0/free qualifies; Mercury/Hermes routes qualify. One live public-scoped7524-byte memo commits and sole authored334→0326 preparation locks, no PREP inference. Preserve imperfect subjective prose and exact legal source party. Runtime retained stricter inherited S1/P0/B32/H4 caps;1/40 spent, no ledger reset/model replacement. Native continuity guard froze before Rival battle; explicit managed writer restart did not restore telemetry/input lease. Stop all owned workers/ledger/default inference, retain Save24 originals and separate committed host snapshot; no new pair or ticket acceptance. Writable-original verification mistake changed database bytes only; full-table/seven-hash equality and exact pre-renewal retained copy allowed byte-for-byte restoration, with sidecars archived. Next is zero-inference native resume qualification preserving live memo/lock, not travel replay or model replacement. [Full report](rival01_final_closeout.md), `evidence/phase8/rival01-dots-renewal/verification.json`. No downstream or endgame authorization.


### D52 native-resume contract disposition — 2026-10-10

User32d6b6b1 authorizes deterministic repair only,0 hosted generation, no Rival battle, and requires stop if the preserved post-Save24 Strategy/lock cannot reattach safely. Two disposable actual retained-data reproductions show normal authorize_launch→restore hides the memo/lock at saved derived cutoffs (Strategy16→14, PREP35→33), leaves immutable records intact, restores all seven parent hashes and marks pending fork. Accepted ordinary rollback contract explicitly excludes unsaved future Strategy; generic pre-battle descendant resume is absent. Do not rebind Save24, replay/copy receipts, regenerate Strategy or resurrect future memory. GateB blocked, GateA actual native progression unrun; required stop reached before emulator startup. Original18/older23 artifacts unchanged,0 new calls/ledger1/40 closed,21 focused host tests pass, no runtime/ROM implementation changes/headroom4. Retained native sample locates CPU audio-sync wait, but initiating cause remains unqualified. Next is generic descendant-resume contract qualification, then actual advancing-frame/host-reception/repeated Continue proof; no live Rival or later phase. [Report](rival01_native_resume_repair.md).


### D52 generic pre-battle continuation contract v1 — 2026-10-24

User explicitly authorizes generic restart-safe pre-battle continuation implementation/qualification inside RIVAL-01,0 hosted generation and no battle. Choose a versioned host-only descendant journal referencing immutable existing Strategy/PREP/decision receipts and exact native-equivalence evidence; do not rebind Save24 or create a retrospective pair. Explicit continuation launch validates the still-active descendant and fresh native grant without ordinary rollback. Ordinary restore abandons the journal; missing native closure, consumed opportunity, sibling/abandoned history and future schema fail closed. Shared APIs, no source334/model special cases. Current v1 native witness is managed pre-Continue menu/no gameplay; arbitrary field divergence requires durable native compatibility proof.

Actual retained live memo/lock admit; two real fresh mGBA Continues preserve all seven committed-world hashes, exact memo/lock and pending334→0326/Charmander state. Host records increasing native frames under new identities before input lease. Actual frame10732 freeze and writer reconnect successfully advance from10752; video-paced normal-speed launch removes dependence on sampled audio producer wait.75 unique focused host tests pass; no native memory/code growth (headroom4), no new calls/ledger1/40 closed, original parent/commitments/evidence unchanged, all owned workers stopped/default inference disabled. Repair accepted; full RIVAL-01 gameplay remains pending. Next separately authorized final live battle continuation reuses the sealed opportunity without Strategy/PREP generation. [Contract](prebattle_continuations.md), [report/readiness](rival01_prebattle_continuation.md), new phase8 continuation verification. No later phase or endgame.
