# Pokemon Influencer - end-to-end campaign implementation plan

**Status:** design specification, not implementation evidence.
**Target:** FireRed/Kanto, desktop emulator plus local companion runtime.
**Release boundary:** opening sequence through first Champion completion.
**Deferred:** all new post-Champion systems in `end_game_concept.md`.

## 1. The game we are making

You leave Pallet Town to document your Pokemon journey on **PokeBook**. Oak's species research survives as the platform's Field Journal rather than being deleted from the game. Badges and the League remain the main adventure. Becoming known changes who follows you, what people believe, and how familiar trainers prepare for your return.

The primary gameplay loop is:

```text
Explore and battle
    -> an event is recorded
    -> direct witnesses remember what they actually saw
    -> every completed trainer battle requires an evidence-backed NPC recap; player posting remains optional
    -> PokeBook delivers it to a limited, plausible audience
    -> exposed NPCs update beliefs and relationships
    -> a Gym checkpoint opens restrained training opportunities
    -> followers prepare and offer rematches
    -> the next encounter refers to shared history
```

**The emotional promise:** a route trainer you met early still feels like the same person later, but has learned something from you. The world notices your choices without secretly reading your party or manufacturing impossible counters.

## 2. Design pillars

### 2.1 Persistent people, not disposable encounters

Every *eligible ordinary trainer* defeated for the first time follows the player. This is not a random 20% selection. Friendship is a separate relationship that grows through interactions. Hostile organizations and story-critical rivals use explicit narrative policies rather than automatically becoming friendly.

Persistence does not mean one always-running LLM process per NPC. Trainers are records and event-driven actors. They wake for relevant events, conversations, preparation opportunities, and battles.

### 2.2 PokeBook explains information flow

The player can trace why an opponent knows something: they witnessed it, were told by an appropriate contact, or saw a post. A public post is not automatically known to everyone. Public visibility, actual delivery, and belief are different states.

### 2.3 Adaptation is recognizable and restrained

Campaign opponents improve decisions and legal movesets before acquiring new Pokemon. They keep their signature companions. New catches are usually native, sometimes nearby, and outside those areas only through an explicit, rare story permission. Four losses to Charmander do not create a Blastoise.

### 2.4 Rules protect the game; models provide bounded agency

The ROM resolves battles and story progression. The host runtime maintains the event ledger, knowledge permissions, reputation, and roster constraints. The puppeteer and NPC LLMs propose plans and expression inside those boundaries. A model cannot create money, awards, quest completions, Pokemon, or historical facts by writing prose.

### 2.5 The adventure works without a cloud model

Local rules, memory, roster preparation, and PokeBook templates remain functional with LLM calls disabled. This is the supported no-cloud mode. A missing *local bridge* is a separate degraded condition, with safe core gameplay but reduced social continuity; it is not advertised as equivalent to the full experience.

## 3. Scope contract

### Included in the campaign release

- FireRed's existing Kanto adventure, adapted opening, PokeBook device/menu, and Field Journal framing.
- First-win follows for configured ordinary trainers; separate friendship, respect, familiarity, and rivalry.
- Named trainer profiles with authored identity and generated-but-validated expression.
- An event-driven puppeteer controlling information delivery, memory retrieval, and bounded social opportunities.
- A local, fast System 1 battle policy for supported trainer battles, with fair observations and legal-action validation.
- LLM strategic planning between encounters and LLM social writing, with a deterministic fallback for every required operation.
- Rematch invitations after region-specific Gym predicates, with restrained, persistent preparation plans.
- Data-derived habitat and move/evolution legality, plus authored travel/resource permissions.
- Save-paired social history, branch-aware replay, model-output recording, and recovery tools.
- Build, patch, and compatibility documentation for one explicitly supported desktop emulator configuration.

### Excluded until separately approved

- Emerald migration, a new region, modern-generation battle expansion, a physical/special split, and new battle gimmicks.
- Real social-media accounts, multiplayer, live streaming, accounts for real followers, monetization, and public online services.
- A literal LLM on GBA hardware, physical-cartridge parity, mobile-emulator compatibility, or a promise that a `.gba` alone includes the AI world.
- Unrestricted free-text player chat, model-controlled scripts, autonomous web access, shell tools, or arbitrary plugins inside the game agents.
- Automatic difficulty rubber-banding based on the player's private party, perfect counter-teams, or infinite rematch growth.
- A complete simulator rewrite, self-training neural networks during play, or a required vector database.
- New endgame tournaments, traveling super-rivals, expanded catch pools, sponsors, or post-Champion social campaigns.

## 4. Player-facing campaign specification

### 4.1 Opening and identity

Oak introduces PokeBook as field observations plus a trainer community. The player selects a handle with a short, engine-safe character limit and a starter through the normal story path. Initial follower counts remain small. The rival is already active online, but exaggerated numbers are authored flavor, not a mandatory power scale.

Keep existing Pokédex-related story and reward checks intact until each dependency is audited. The early integration should add a PokeBook entry without replacing inventory, save, options, or key quest menus. Renaming the Pokédex interface does not justify removing its data or flags.

### 4.2 Posting

Meaningful events create optional post drafts: first catches, Gym wins, discoveries, help given to NPCs, and selected battles. The player chooses **Post**, **Keep private**, or **Later**, then a small authored tone selection. No keyboard chat is required.

Repeated ordinary battles can be summarized at safe moments rather than interrupting every fight. Every supported confirmed completed trainer battle creates a mandatory recap from that trainer, on wins, losses and completed rematches. Hermes processes authorized evidence and durable puppeteer memory; provider failure uses factual fallback and never suppresses publication. Optional player drafts remain separate. Hiding your own post does not erase a witness's memory, but it does not grant unlimited permission for witnesses to publish secrets either; that is controlled by event visibility.

### 4.3 Feed, profile, and people

PokeBook has Feed, Profile, Following/Followers, Challenges, and Field Journal views. A compact in-ROM version is required for the playable vertical slice. A browser/debug feed may accelerate engineering but is not the final player experience.

Posts display an author, region/topic, short text, and limited engagement. Notifications queue until safe overworld moments. No notification pauses a battle animation or steals input from another menu. All text goes through a game-character-map encoder and pixel-width layout checks.

Named trainer followers are real persistent graph nodes. Large audience counts are aggregate simulations, not thousands of hidden LLM actors. Followers measure visibility; they do not directly increase Pokemon stats or gate the next Gym.

### 4.4 Friends, rivals, and hostiles

A first victory creates a directed follow edge once. A follow is not automatically a mutual friendship. Choosing supportive responses, returning for rematches, and shared events can increase trust and friendship. A competitive follower can respect you and remain irritated at losing. Rocket members retain hostility unless an authored story explicitly changes that relationship.

### 4.5 Rematches

Each trainer maps to a named region and an explicit unlock predicate, such as the Boulder Badge for the Viridian Forest cluster. Later badges create additional qualifying opportunities, but there is at most one pending invitation per trainer and no queue of farmable missed tokens.

A challenge is fought at a reachable, authored location. Do not teleport trainers or players through story barriers. A ready challenge can wait while the player continues the main quest. Declining or ignoring it has no mandatory-story penalty.

The original first-battle defeated flag stays set. A separate rematch state machine owns invitations and rewards. Existing rematch paths, including VS Seeker integration, must route through the same policy or be excluded explicitly to avoid duplicate battles and payouts.

### 4.6 First battles versus rematches

Ordinary first-battle rosters stay authored in the first release. These trainers may use the System 1 policy, but their initial team is not secretly rebuilt for the current player. Dynamic roster generation applies to the recurring campaign rematches.

Architecture realignment D22 explicitly expands the first-roster default for opted-in Gym Leaders: bounded first-encounter preparation may select legal movesets, finite item allocation and limited mixed-type support while preserving signature companions and primary-theme identity. An authored profile must specify stage/resource/change/support caps before implementation; missing profiles and other bosses retain authored baselines. This is not last-moment player-party scouting. Commit and lock before the encounter; see docs/preparation_envelope.md.

## 5. Architecture decision

Use a FireRed source fork based on `pret/pokefirered`, not an Emerald-based reconstruction of Kanto. The source repository and build instructions provide the starting point; the exact revision must be pinned and built in Phase 0. See sources S1-S2 in `docs/source_notes.md`.

```text
FireRed ROM / game authority
  - canonical battles, flags, items, map state
  - safe event and observation export
  - bounded request mailbox and text UI
                 |
                 v
Desktop emulator bridge
  - version/capability handshake
  - framed messages and session identity
  - managed save snapshots
                 |
                 v
Local companion runtime
  - event ledger + projections in SQLite
  - puppeteer / social delivery / memory
  - roster legality + constrained preparation
  - fast System 1 policy
  - optional provider-neutral LLM adapter
```

mGBA is the preferred *candidate* bridge host because its official scripting API documents memory access and socket callbacks. Its exact packaged build, response latency, and state-loading behavior must be tested; documentation is not proof that our bridge works. See S3.

HERMES-01 authorizes actual pinned Hermes integration over the separate canonical host world-memory layer and additive durable puppeteer summaries. Its personal memory is not shared canonical NPC storage. Three independent inference roles and native decision adapters are specified in repository-root `docs/ai_runtime_architecture.md`; Historical foundation reports remain evidence of their original scopes. Fresh Hermes execution homes retrieve branch-aware durable game memory explicitly; director memory is never copied into NPC context. NPC knowledge isolation and replay remain custom requirements. See S4.

## 6. Authority and evidence contract

| Component | May decide | Must not decide |
|---|---|---|
| ROM rules | Battle outcome, actual HP, badges, inventory, legal battle execution | Model-generated narrative facts |
| Trusted host rules | Knowledge permissions, event effects, legal rosters, exposure scheduling limits | Unobserved gameplay events |
| Hermes director | Process mandatory recaps, retain provenance-backed memory, prepare lawful scoped briefings/notes | Decide whether required posting occurs, grant omniscient NPC knowledge, unrestricted world edits |
| NPC strategy LLM | Interpret authorized briefing/personality, companions/inventory and legal preparation envelope into strategic intent | Unrestricted party edits, new legality/resources, hidden-player scouting |
| System One | Select validated preparation candidates; select current legal battle actions using locked preparation/intent and permitted evolving context | Unvalidated edits, future actions/RNG, hidden-player inspection, mid-battle roster mutation |
| Social writer | Wording of an approved event/claim | Awards, roster commitments, true history, quest scripts |

The puppeteer is genuinely agentic: it has goals, durable state, scoped read tools, a small action menu, and validation feedback. Its job is to create believable continuity, not maximize engagement or guarantee the player's defeat. Most routine events still use deterministic rules rather than paying for a model call.

## 7. Restrained adaptation defaults

`config/campaign_defaults.json` contains initial values to test, not claims about final balance.

- Maximum two changed move slots across existing partners per preparation opportunity, including added moves and replacements. A single approved new catch receives its own legal initial moves under the acquisition budget.
- At most four levels of advancement per earned epoch, also limited by an authored regional stage target and a campaign cap. Missed epochs may advance level growth once each; they do not multiply captures, moveset changes, invitations, or rewards.
- No catches on the first preparation epoch. Later eligible epochs have a 25% capture-attempt probability before all legality checks, with at least two epochs between successful acquisitions.
- At most one new Pokemon per preparation opportunity and two campaign acquisitions in total for a trainer. No automatic non-signature replacements in the initial campaign policy.
- Native versus nearby proposal weights are 80/20 after eligibility filtering; accessible and exceptional are disabled without an explicit acquisition grant.
- Preserve all original companions by default; the general validator also enforces a 75% original-lineage floor for any future approved replacement policy. Signature partners are never dropped.
- No loss-streak stat buffs, perfect-IV rewrites, automatic competitive EV spreads, hidden nature changes, or item resources created on demand.
- Preparation freezes when committed for an encounter, including opted-in first Gym encounters; later posts, opening menus, changing party, reloading a feed, or losses do not reroll it. Resource changes follow actual explicit game rules only.

An unchanged team is a valid result. A trainer can get smarter without every preparation producing a new species or a new move.

## 8. Implementation phases and stop gates

### Phase 0 - prove the foundation

Inventory the user's environment and local dump revision without uploading it. Pin source/toolchain candidates. Build a clean supported FireRed target, compare its expected baseline hash, boot it, battle, save, and reload. Establish the development repository and record capabilities.

**Exit:** real build and emulator evidence, or an explicit blocker report. Without these, host-only work may continue, but there is no claim of ROM integration.

### Phase 1 - prove the narrow bridge

Add a dedicated symbol-resolved mailbox and a feature flag. Complete handshake, ping, one harmless ROM event, and a short bounded text response. Prove correct build rejection, timeout, reconnect, and absence-of-bridge behavior before adding an LLM.

**Exit:** frame-safe communication and an integration report with measured timings; no unverified hard-coded memory addresses.

### Phase 2 - prove persistence and the social rules

Implement ledger, migrations, outbox, scoped memories, named follows, basic exposure, and the rematch state machine using templates and fake game events. Build managed save checkpoints early, before accumulating a persistent social world.

**Exit:** deterministic replay, duplicate-event safety, save branch isolation, and no private-knowledge leaks in fixtures.

### Phase 3 - prove legal restrained preparation and fast battles

Export pinned game data; build habitat/legality validation; implement constrained roster plans and a transparent System 1 baseline. Integrate battle observations and legal actions through the ROM adapter. Record decisions for replay.

**Exit:** no illegal action execution, no hidden-party influence, no impossible team generation, stable locked rematches, and working fallback.

### Phase 4 - prove the complete playable loop

Ship the first small slice: Pallet onboarding, Viridian/Forest, Pewter/Brock, and a return to a follower for a rematch. Use roughly 6-10 persistent trainer/social profiles, at least three eligible ordinary trainers, Oak/rival social roles, and a controllable negative-visibility case.

**Exit:** player can win, see a follow, choose a post, observe limited social spread, win Boulder Badge, receive a challenge, fight the legal adapted roster, then save/reload consistently. All this works with LLM disabled.

### Phase 5 - add bounded LLM agency

Connect one configurable LLM provider and retain template mode. Add candidate-ranking and social-opportunity proposals; use role-appropriate boundaries: guarded structured social proposals, exact subjective StrategyMemo prose, and supplied legal IDs for System One. Cache and record outputs. Test malformed responses, semantic invention, refusals, latency, and budget exhaustion.

A compact learned System 1 model is an optional subphase after the baseline and simulator tests are stable. It must beat defined evaluation criteria under identical information restrictions. It is not a prerequisite for calling the first version a fast System 1 policy, and no learned model should be represented as trained before it exists.

**Exit:** models visibly enrich continuity without becoming a gameplay dependency or changing canonical facts through prose.

### Phase 6 - expand the campaign in verified batches

Roll profiles, region permissions, and social content from Pewter through Cerulean, Vermilion, Celadon, the branching midgame, the final Gyms, and the League. Use explicit story predicates instead of assuming one fixed badge order. Test each map/quest batch before moving on.

**Exit:** complete first-Champion playthrough, all configured trainer bindings covered, no new mandatory backtracking, no story softlocks, and a stable follower/rematch economy.

### Phase 7 - harden and package

Complete fault injection, migration tests, text QA, performance measurement, blind playtesting, patch reproducibility, and installation on a clean supported desktop environment. Document incompatibilities and reset/recovery procedures.

**Exit:** release checklist in `docs/test_plan.md` passes. Deliver source changes, a patch tied to the supported local base checksum, the runtime/bridge, configuration, and tested installation instructions. Do not ship a full Nintendo ROM in the project release bundle.

## 9. Vertical-slice acceptance story

A tester begins a new game, chooses Charmander, and meets a configured forest trainer. After the trainer loses, a single follow appears. The trainer remembers only the Pokemon and moves actually revealed.

The player shares a battle post. One relevant local contact receives it, while an unrelated contact does not; the debug explanation can show the delivery path. The player beats Brock. The forest trainer becomes eligible, prepares a team with the same original lineages, and announces a challenge.

At the rematch, the trainer uses a legal improved moveset or better tactics rather than an unexplained Water starter. Changing the player's team after the invitation does not alter the prepared opponent. A loss and retry use the same roster version. A win awards the rematch reward once. Reloading a paired save restores the correct prior knowledge and feed.

Disconnecting the cloud model still allows the entire story. Breaking the local bridge triggers documented degraded behavior rather than a freeze or invented history.

## 10. Evaluation and release standards

Evaluate four different things separately:

1. **Correctness:** builds, legal actions/rosters, data bindings, story flags, replay, persistence.
2. **Fairness:** no hidden inputs, no magical acquisitions, bounded growth, no correlated-rumor inflation.
3. **Experience:** understandable social consequences, recognizable NPCs, limited interruptions, optional backtracking, enjoyable rematches.
4. **Operations:** bounded latency/cost, safe failure, deterministic offline tests, clean installs, patch compatibility.

A successful compile is not a playable game. A host test is not an emulator test. An emulator boot is not a complete story playthrough. Reports must label exactly what was run.

## 11. Risks with explicit mitigations

| Risk | Mitigation and release consequence |
|---|---|
| Emulator scripting differs by build | Capability spike; pin supported package; narrow transport fallback only after measurement |
| Memory or save layout has insufficient safe space | Linker/save-layout audit before integration; explicit expansion/migration design rather than overwriting padding |
| Persistent history outlives a rewound game | Paired checkpoints, branch IDs, replay cursors, fail-closed social recovery |
| LLM invents events or illegal teams | Typed evidence/candidate IDs, rule validation, safe templates, no prose-to-state pathway |
| AI secretly sees selected player action | Sanitize at source; snapshot before opponent selection; hidden-state mutation tests |
| Dynamic rosters become tedious or unfair | Small mutation budgets, fixed regional targets, identity preservation, no loss rubber-band |
| PokeBook feels like a debug overlay | In-ROM menu, brief text, safe notifications, authored opening, optional posting |
| Campaign scope overwhelms implementation | One completed playable loop first; batch content expansion; defer endgame |
| Model calls become mandatory or expensive | No-cloud mode, quotas, cached outputs, provider-neutral adapter, no turn-by-turn LLM |
| Unverified licensing/distribution assumptions | Separate local development inputs from release artifacts; retain notices; independent review before public distribution |

## 12. What the user will hand to Codex

Hand over this entire package, not only one mega-prompt. Keep `AGENTS.md` at the project root. Start with the Phase 0 prompt. Codex should produce small reviewable changes, a current status record, exact commands and outcomes, and the next task with its dependencies.

The objective is not to ask an agent to invent everything at once. It is to give it an executable sequence of decisions and acceptance gates while preserving the game's defining constraint: **NPCs grow like people in Kanto, not like an omniscient difficulty controller.**

## HERMES-01 authorized milestone override (2026-10-02)

Implement only actual pinned Hermes runtime, mandatory single-trainer recap obligations/fallback, persistent provenance-backed puppeteer memory, actor-scoped knowledge packets and safe fresh-home launcher/cleanup. This separately authorized milestone precedes the other original model-phase features; it does not authorize strategy, System One, rosters, rematches, reputation, full UI or endgame. Normal inference stays offline by default. Live Puppeteer experiment uses only the configured verified-free model,<=10 attempts total,<=3 requests/<=6 game tools per job, one active job and bounded tokens/deadlines; auxiliary calls are disabled/accounted. See D21 and docs/hermes01.md for implementation status/evidence rather than implying the historical phases already implemented this.


## AI gameplay architecture realignment (2026-10-02, D22)

Authoritative future target: docs/ai_runtime_architecture.md v2 and docs/preparation_envelope.md v1. Hermes is the persistent event-driven social-memory director, not only a formatter. PokeBook is the social-memory system and in-world interface; public posts, private observations and director memory remain separately authorized views. NPC exposure is scheduled through bounded game services independently of player feed opening, and still requires recorded actor-specific exposure/delivery before knowledge. Current explicit exposure proves the boundary, not an implemented autonomous scheduler.

Define and implement PREP-01 envelope/feasible candidate services before STRATEGY-01. Strategy interprets authorized briefings/personality with own companions/inventory/envelope into intent. System One has separate SYSTEM1-01A preparation selection/commitment/installation and SYSTEM1-01B live legal-action control gates. Deterministic services define stage/earned-epoch growth, acquisition/resources/identity/theme feasibility and offer meaningful choices; models never widen those rules. Always-on availability means durable event-driven jobs/fresh workers, not continuous inference or wall-clock growth.

Model slots/providers stay replaceable and currently configured selections stay unchanged. Architecture approval does not activate any additional live role or gameplay phase. Preserve HERMES-01 implementation and its partial acceptance/10-attempt exhausted-budget stop condition. Foundation reports/evidence remain intact; docs/architecture_realignment.md records schema/content/action-coverage gaps. Stop at the current authorization; endgame remains deferred.

## HERMES-01 acceptance closeout (D23)

The separately authorized bounded closeout accepted HERMES-01: actual game-triggered model selection committed, survived cleanup/native paired reload and was retrieved by a fresh actual Hermes worker with correct actor disclosure. The original10attempts remain recorded;5additional requests were used and the new ledger is closed. No new inference role or subsequent gameplay feature was started. Preserve D22 architecture; next separately authorized milestone is POKEBOOK-01, then STRATEGY-01 and SYSTEM1-01A/B with executable PREP contracts before consumption. See docs/hermes01.md and docs/pokebook01_readiness.md.

### POKEBOOK-01 accepted native slice

The player's native Start-menu viewer now presents existing authorized public recaps and incoming followers through bounded, read-only pages. Actual offline Rick pipeline, stored Hermes-output rendering (explicit fixture), privacy/NPC-exposure independence, temporary resources, faults and fresh paired early/late restore passed. No player browsing triggers models, history or NPC knowledge. New build uses a separate explicit campaign lineage; no B3 save/history migration is claimed. See docs/pokebook01.md. D22 remains authoritative; ROSTER-01 is the next dependency task; PREP-01/CONTENT-01 executable feasibility is required before STRATEGY-01. No later phase or endgame implementation is authorized.

ROSTER-01 implementation update (D25): the pinned effective FireRed host catalog and side-effect-free element prerequisites are accepted within docs/roster01.md's coverage. They do not construct/select/commit/install teams. Missing real trainer/stage/resource/travel/signature/Gym profiles fail closed; next dependency is CONTENT-01 before executable PREP-01. D22's agency/first-Gym expansion and later Strategy/System One A/B gates remain authoritative. Endgame stays deferred.

CONTENT-01/D26 update: the opening-kanto v1 production pack concretely binds Rick/Doug/Janice/Brock first encounters and one post-Boulder forest opportunity, retaining source identities and explicit zero starting supplies/acquisitions. Opening Brock keeps Onix/Geodude with zero support; future bounded mixed-type support remains D22's architecture. No roster was selected/installed and no live progression hook was added. PREP-01 is now the next dependency, using this pack plus trusted live state before Strategy/System One. See docs/content01.md.

CONTENT-01 clarification/D27: preserve configurable campaign adaptation while opening remains zero-catch. Later trainer/stage allowances1/2 supersede older final1/opportunity,2/campaign assumptions; probability/spacing/campaign cap await qualification. Filtered eligible-origin80/20 draws precede System One species/no-change selection; accessible/exceptional origins require distinct explicit grants. No reserves or rotation; six/stage active capacity applies. Changes affect future uncommitted opportunities only. Shared pure rules and scenario tests do not activate later content. PREP-01 remains next.

PREP-01/D28 update: executable schema1/generator1 host feasibility and durable preparation receipts are accepted for the opening pack. Actual native Brock/Boulder normal Save and fresh paired before/after Continue proved Rick eligibility once, durable retrieval and rewind isolation. No model selected or native trainer team changed. Source-fixed first encounters preserve authored order; later acquisition sampler/packages and live commitment/installation remain separate gates. STRATEGY-01 is the next dependency task, requiring separate authorization; SYSTEM1-01A/B and endgame remain deferred. See docs/prep01.md and docs/prep01_readiness.md.

STRATEGY-01/D29 update: host StrategyContextPacket schema1 and StrategicPosture schema2 implement scoped intent, authored behavior, capability summaries, deterministic fallback and derived save-paired history without any candidate selection/team/resource/tactical mutation. The separately authorized10-request free Strategy experiment produced no accepted live posture; final diagnosed NVIDIA upstream502 responses leave the actual Rick gate open. Default inference stays offline and its budget is closed. **Next: STRATEGY-01 acceptance closeout under separate live authorization; SYSTEM1-01A follows only after acceptance.** See docs/strategy01.md. Preparation selection/commitment/native installation and all legal-action coverage/endgame remain deferred.

STRATEGY-01/D30 renewed acceptance closeout: exact configured free Nemotron remains live-blocked after3 additional NVIDIA upstream502 responses, one bounded/backed-off job. Original10 attempts preserved; renewed ledger closed3/10, backup model inactive.40 focused offline tests/18 transport retests/27 artifact assertions passed; no actual live posture or after-live native paired proof. Next is separately authorized Strategy provider/model change or later bounded retry; SYSTEM1-01A/B and endgame remain deferred. See docs/strategy01.md and evidence/phase3/strategy01/closeout/completion.json.

STRATEGY-01/D31 explicit backup qualification: Inkling-small lacks forced tool_choice (0 calls); latest user-named Qwen contingency qualifies metadata but actual3/5 calls return400/429/429, no live intent. openrouter/free lacks endpoint records for current exact-model/tool/free gate (0 calls). Primary13 attempts/evidence preserved, new ledger closed, preferred model/profile unchanged, no automatic chain/other role. Scoped host/metadata/non-mutation/replay checks pass, live and after-live paired gates remain blocked. Next requires separately authorized small model-selection/HTTP400–429 diagnostics; SYSTEM1-01A/B/endgame remain deferred. See docs/strategy01.md/backup evidence.


## Current Strategy output contract — D32 (2026-10-04)

Strategy emits a bounded, exact natural-language **StrategyMemo**, not required JSON, tools, enums, evidence IDs or numeric posture. One ordinary completion interprets the existing actor-filtered context and legal preparation constraints. Approximately100–250 words is a prompt target, not a semantic validation requirement. Host validation enforces nonempty strict UTF-8, at most4096 UTF-8 bytes, no unsafe control/format characters (paragraph LF allowed), and the current immutable actor/job/branch grant. The provider also enforces at most1800 output tokens,65536 response bytes,24576 request bytes/conservative input tokens,35 seconds/request and120 seconds/job. A failed completion produces explicitly labeled deterministic prose fallback; no repair loop.

Persist accepted text verbatim with host-generated strategy/job/actor IDs, campaign/branch/generation/cutoffs, context/material hashes, preparation-envelope reference, persona/configuration/prompt versions, timestamp/cursor and provider/model diagnostics. Reuse stored text on restart, UI refresh and repeated decisions. Fresh legitimate opportunities/material precommit evidence may yield different prose; replay does not regenerate it. Future commitment must atomically lock the exact memo reference/hash alongside the team. Commitment/installation is not implemented here.

A memo is subjective interpretation. Even an unsupported prediction remains text: it never becomes canonical truth, actor knowledge, acquisition permission, resources, preparation selection or a battle action. Future System One requests must separate **AUTHORIZED FACTS** from **STRATEGY MEMO — SUBJECTIVE**, pass the exact stored text, and allow only supplied current legal candidate/action IDs. No prose-to-facts or prose-to-numeric-posture conversion is required or implemented.

Historical posture schemas, prompt/config hashes, records and closed experiments remain unchanged. `strategy/memo.py` adds schema3/prompt2 MEMO receipts using the existing paired Strategy cutoff/hash. Historical internal projection key `postures` retains its name to preserve existing checkpoint hashes; `memo_records()` exposes only schema3 text. Explicit MemoStore adoption is limited to the new acceptance working copy; legacy StrategyStore refuses a memo-enabled database. Original databases are not migrated or rewritten. Normal inference remains disabled. No System One, party/resource/ROM change or endgame work is authorized.



D32 acceptance (2026-10-04): corrected StrategyMemo host runtime and actual free Nemotron smoke/Rick result accepted. Exact model text survives fresh host/native Save17 Continue, paired Save16 rewind excludes it/late grant, and paired Save17 return retrieves it without inference.67 unique focused tests/0 skips and actual-artifact audit passed;16 full Rick option plans, knowledge/history/companions/resources and ROM unchanged. Budget closed2/2; historical records/inputs/evidence preserved and all task processes stopped. See docs/strategy01.md and evidence/phase3/strategy01/memo/completion.json. Next separately authorized SYSTEM1-01A; no selection/commit/install/action or endgame implemented.


## SYSTEM1-01A / D33 — accepted (2026-10-04)

Native Mercury Decide Free chose one of Rick's16 legal PREP candidates from his exact subjective StrategyMemo, with facts kept separate. The actual choice retained the unchanged roster; it was revalidated, committed once, constructed in native FireRed, battled under vanilla AI and paired/reloaded in normal Save19 without reinference. Save17/18/19 restore isolation and stale-result rejection passed.57 unique focused tests/0 skips,37 artifact checks and3 schema checks passed;2 zero-cost calls, closed budget, offline default, workers stopped. Controlled opening Rick installation is not general trainer/item/acquisition support or full campaign rematch UX. SYSTEM1-01B and endgame remain deferred. Next separately authorized dependency task: BATTLE-01, then BATTLE-02/ROSTER-03 before live battle control. See docs/system1_01a.md, docs/system1_01b_readiness.md and evidence/phase3/system1_01a/completion.json. Earlier dated acceptance sections remain historical.


## BATTLE-01 / D34 acceptance —2026-10-04

Expanded BATTLE-01 is accepted only for armed D33 Rick ordinary singles: source-authoritative legal moves/switches/finite-item/replacement/Struggle boundary, fair snapshot/exact subjective memo/chronological history, asynchronous deterministic fixed choices, native execution/revalidation and vanilla fallback. Actual external switch and five Poison Sting resolutions passed; sole replacement skipped the provider. Delayed deterministic output fell back without stopping frames/events. Full normal battle ended with player loss (outcome2), mandatory offline recap recovered/settled, and unchanged lock. Actual-C fixtures cover finite item command/decrement/disappearance and multiple replacements; item animation/HP effects are not claimed as emulator proof.28 focused unittest cases/0 skips,8 actual-Lua mock-control assertions,23 artifact checks passed.452 protected inputs unchanged;0 model calls. Exact evidence/failures/exclusions: docs/battle01.md and evidence/phase4/battle01/completion.json.

Save20 checkpoint f1633a24-d4ae-42c0-b586-a8a35eb47452/cursor179 was normally saved and reloaded. Five completed battle audits/post survive the pair; isolated Save19 restore excludes future audit/post. ROM SHA2566582e03a8a2daff55e47d153fc5eee9838c8ea55803ed446f99b8b6a01b0d570.48-byte fixed control plus1036-byte heap payload (freed),4 reserved bytes remain; save layout/prior RAM unchanged. Host publication latency6.4–211.2ms; hosted/fast-forward latency unqualified. Workers/listeners stopped, default hosted inference offline.

Completed ticket: BATTLE-01 only. Next separately authorized task: SYSTEM1-01B live native-provider acceptance for this qualified path; docs/system1_01b_readiness.md records remaining gates. No general rematch UX, new strategy/roster/resource behavior or endgame. Broader BATTLE-02 remains separate. This supersedes the earlier utility-only BATTLE-01 and broad BATTLE-02 prerequisite for controlled Rick model acceptance; foundations are not restarted.


## SYSTEM1-01B / D35 blocked closeout —2026-10-04

Host live/shadow provider implementation and independent setup are complete, but SYSTEM1-01B is not accepted. Configured free Mercury native smoke passed; one actual Rick shadow proposal was valid (String Shot,1.687s), two complete-shadow HTTP attempts exceeded1.9/2.05s and one earlier trial hit the2.25s worker deadline.5 total charged requests including smoke; ledger closed, no retry/substitution/other roles. Two returned responses report zero cost; interrupted request usage is unknown. Full shadow715026728 completed normally under vanilla fallback, with sole forced replacement bypassing inference and an offline mandatory recap. Enabled battle was not run because latency qualification failed.

Actual normal Save20/checkpoint5575c709-d8c9-42ef-aee1-6c9fa80906a1/cursor177 was reloaded in a fresh native Continue and host: five audits, exact memo, D33 lock, recap and replay hashes survive; no further requests. Save19 excludes the future shadow history.25 artifact checks,28 retained +10 final focused tests (34 unique/0 skips),524 protected inputs unchanged. Unchanged BATTLE-01 ROM SHA2566582e03a8a2daff55e47d153fc5eee9838c8ea55803ed446f99b8b6a01b0d570. Exact attempts, latch reopenings, failed trials, commands and blocker: docs/system1_01b.md; evidence/phase4/system1_01b/verification.json. Workers stopped; normal hosted default remains disabled.

Completed new ticket IDs: none. Next task: SYSTEM1-01B latency qualification/acceptance closeout, then continuous VERTICAL-SLICE integration under separate authorization. No phase expansion, roster/memo/resource edits or endgame. Shadow save/reload is not enabled acceptance.


## SYSTEM1-01B / D35 acceptance —2026-10-04 (supersedes interim latency-blocked closeout)

SYSTEM1-01B is accepted for locked D33 Rick ordinary singles at normal speed. Full shadow1660475733 passed with4 real unexecuted Mercury proposals; full enabled3468328694 applied all4 meaningful Mercury choices (String Shot/switch/String Shot/String Shot) through unchanged native guards/controllers. The switch and first String Shot resolved; later move selections were interrupted by fainting, correctly recorded separately. Sole replacements bypassed inference. Both battles ended normally with player wins; no predetermined result or optimality override.

13 total charged requests including smoke/errors;10 returned responses reported cost0,3 interrupted responses lack usage. Same configured free Mercury, no other live roles, reroll/resampling/model substitution. Early deadline/startup/trigger/config-label failures and explicit same-ledger reopenings remain recorded. Final HTTP2.35/worker2.55/host2.75s lie within unchanged native180 frames; retained host default2.5s stays unchanged.8 passing shadow/enabled responses: HTTP median0.621s/max0.904s; host median0.820s/max1.017s. No small-sample p90/p95 claim or fast-forward qualification.

Actual normal Save20/checkpoint5cbfae80-800f-419f-9b45-1d42f4afee1b/cursor177 was freshly Continued with no reinference: exact lock/memo,5 enabled audits, offline mandatory recap and replay hashes survive; abandoned shadows/Save19 future exclusion pass.33 artifact checks,35 unique focused tests/0 skips,524 protected inputs unchanged. Native ROM SHA2566582e03a8a2daff55e47d153fc5eee9838c8ea55803ed446f99b8b6a01b0d570 unchanged. Source implementation/evidence/commands: docs/system1_01b.md; evidence/phase4/system1_01b/verification.json and completion.json. Workers/listener stopped,13-request ledger closed, configured providers/default offline unchanged.

Completed ticket: SYSTEM1-01B only. Next separately authorized task: VERTICAL-SLICE continuous managed campaign integration; docs/system1_01b_readiness.md records gaps. No live nonzero items/multiple replacements, general trainer/mode/rematch/Gym/acquisition expansion or endgame is claimed. Earlier blocked report is historical timing qualification, not current status.

### D36 / VIRALITY-01 social-distribution refinement

Ordinary public reach derives from actual branch-scoped incoming player followers
at a frozen distribution epoch. Trusted high-profile native encounters are broad
independently of that count. Explicit chronically-online scouts monitor public
sources without fake follows; delivery still differs from recorded exposure.
Rocket leadership has a separate complete-observed-claim faction channel.
Deterministic campaign-order relevance and original-source/path quality replace
random forgetting; no historical evidence is erased. Versioned configuration
and save-paired additive history preserve earlier memos/roster commitments.
See docs/virality01.md and D36. Next continuous slice centers Rick's first recap
and Brock scouting/first Gym; later Rick rematch is a longitudinal follow-up.
This refinement does not authorize its gameplay/model integration or endgame.


## D38 / BATTLE-END-01 gate repair accepted — 2026-10-05

Before additional live VERTICAL-SLICE closeout, repair/prove native canonical
trainer completion and explicit tactical execution/cancellation. Completed with
zero hosted requests: real Brock deterministic win/loss, vanilla loss, stable
terminal ACK/retry after cleanup, ordinary Gym/Boulder save and paired rollback.
No strategy/preparation/AI/content foundation restarted. VERTICAL-SLICE-01 remains
blocked at its separately authorized fully live closeout; readiness is a proposal,
not new inference permission. See docs/battle_end01.md,
docs/battle_terminal_contract.md and docs/vertical_slice01_final_readiness.md.


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

## CAMPAIGN-EXPANSION-01 / D40 — live blocked, not accepted (2026-10-06)

First shared ordinary-trainer content pack: Sally117/Greg106/James107/Kent108.
Additive branch-paired content and generic qualification add zero permanent RAM;
4-byte EWRAM headroom unchanged. Actual Sally native victory has12 executed Mercury
choices/3 meaningful fallbacks, then real Hermes recap/follow/ordinary diffusion.
Greg Strategy fallback; later encounters/MtMoon remain unrun. Recovered normal C1,
fresh offline PokeBook and paired-prefix fixture pass; automatic pending-save restart
recovery and new encounter provider recovery remain gates. Full pack not accepted.
No next campaign phase or later acquisitions authorized. See current status/D40/report.

## D41 / CAMPAIGN-EXPANSION-01 gate repair — zero inference, evidence gap

Production ordinary-text preflight, deterministic native timeout matrix and managed
pending-save restart paths are repaired/verified with zero generation and zero new
permanent RAM. Source C1/accepted history/closed ledger preserved. Gate repair is
not declared accepted because the original Greg ProviderError lacks its specific
preflight code/failed metadata. Current healthy-route qualification does not supply
that historical proof. See docs/campaign_expansion01_gate_repair.md/current status.
No next phase/live role or model substitution. Greg's immutable first memo/lock and
Kent's identity as the selected MtMoon actor constrain eventual closeout readiness.

## D42 / gate-repair historical evidence closeout — accepted (2026-10-06)

Accept the missing historical telemetry gate through explicit retained-artifact
irrecoverability, not an inferred provider code. Greg original failure UNKNOWN;
current path and six-category durable diagnostics pass. This narrowly amends D41
criterion1 only, retaining functional/privacy/save/deadline/RAM requirements.156 host
tests/0 skips, native checks, retained real emulator/restart proofs, EWRAM4/delta0,
zero generation and unchanged accepted artifacts. GATE REPAIR accepted; full campaign
expansion remains unaccepted. Final readiness preserves Greg locked memo and identifies
Kent108 as MtMoon; actual remaining path Greg→James→Kent. Proposed98-call ceiling
is not authorization. Next separately authorized live continuation only; no new phase,
fourth actor, same-opportunity reroll, acquisitions or endgame. See D42/readiness.

## D43 / final campaign closeout — configured provider blocked before dispatch

Exact new98 authorized (Strategy2/preparation0/battle84/Hermes12); preserved original
16/C1/Greg lock in generic isolated continuation. No generation or gameplay began:
required configured Nemotron endpoint status-2 does not meet accepted healthy-status0
free route. Mercury/Hermes qualify. No substitution/relaxed policy/new repair ticket.
Ledger closed98 unused; permanent headroom4/delta0, original protected hashes intact.
Gate repair accepted; full pack still unaccepted. Next same final live closeout on
route qualification or separately explicit model decision. No new phase/endgame.

## D44 / Strategy replacement qualification — blocked

Explicit bounded Gemma→conditionalQwen evaluation (not automatic production fallback).
Primary two HTTP429 smoke errors; secondary exact model/endpoint absent.2/4 generation,
closed unused2, no replacement activated, no gameplay/campaign inference. Generic
nullable-uptime handling retains accepting status/knownpositivehealth/free text gates.
Prior C1/memos/Greg lock/ledgers unchanged, RAM4/delta0, default inference disabled.
No full pack acceptance/new phase; model qualification remains next, then original
98-call Greg→James→Kent closeout. Endgame deferred. See D44/strategy_model02 report.

## D45 / STRATEGY-MODEL-03 — accepted explicit new-job Strategy model

Current live catalog qualified **dots-studio/dots-3-note-preview:free** /AtlasCloud.
Ling preferredfree absent; general secondary Liquid400 request incompatibility, single
ranked contingency Dots smoke+fictional memo pass.3/6 separate calls; no fourth model.
`.env` explicit selector updates future jobs without altering model-profile domain
identity or prior memos.49 relevant tests/0 skips, historical C1/Greg lock/replay,
local James/Kent and RAM4/delta0 pass. No automatic chain/JSON/tools/gameplay/new
campaign history. Both campaign ledgers and98 ceiling unchanged. Next same final
campaign continuation only; fresh route qualification/Dec31 preview expiry risk.
Normal inference disabled, no new phase or endgame. See D45/strategy_model03 report.

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
and paired Continue. No new phase/endgame. Details: [Kent closeout](docs/campaign_expansion01_kent_closeout.md).

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
See [final recovery](docs/campaign_expansion01_final_recovery.md) and
[next-step readiness](docs/early_kanto_next_step_readiness.md).


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

Evidence: [disposition](docs/rocket01_hermes_disposition.md), `evidence/phase7/rocket01/hermes-disposition/disposition.json`, `qualification.json`, fresh `disposition-verified-restored.json`, and protected original observation matrix/golden trace. Original BLOCKED verification remains historical; amended acceptance is separate. Next recommendation exactly RIVAL-01, planning only and requiring separate authorization: [readiness](docs/post_rocket_early_kanto_readiness.md). No subsequent phase or endgame implementation.


### D51 — Context selection before the Cerulean Rival opportunity

Keep durable actor memory distinct from bounded model context. The explicitly adopted `campaign-public-context-1` policy selects complete, attributable public claim groups relative to the actual encounter stage; omission is not forgetting. Old diffusion epochs, delivery receipts, memos and locked preparations remain unchanged. New jobs freeze policy/hash/selected references/full inputs; later publication or recovery cannot rebuild an encounter. See [context policy](docs/context_selection_policy.md) and [RIVAL prerequisites](docs/rival01_prerequisites.md). Deterministic prerequisites accepted; actual RIVAL live gameplay/social/save work awaits separate authorization.
