# RIVAL-01 planning / readiness — 2026-10-07

**Current disposition (D51): RIVAL-01 PREREQUISITES ACCEPTED; READY FOR LIVE IMPLEMENTATION.** See [prerequisite report](rival01_prerequisites.md) and [context policy v1](context_selection_policy.md). Real22-receipt full context is7524 bytes; native isolated Cerulean334 constructor/canonical0326/first turn are proven; fixed RAM delta0/headroom4. No hosted calls or active campaign changes. Live implementation remains separately authorized.

The following original planning assessment is retained as history. Its three blockers are resolved by D51. The proposed global virality-policy migration was superseded by a separate opportunity-context policy: old diffusion epochs and policy hash stay intact.

**BLOCKED BEFORE IMPLEMENTATION.** The next encounter and saved starter branch are proven; persistent identity already exists. Three host prerequisites remain: explicit versioned Cerulean progression/relevance-policy adoption that preserves historical diffusion epochs, qualification of a scripted no-intro story encounter with canonical constructor attribution, and a bounded public-facts projection that fits the existing prebattle contract. Neither was implemented. No provider/network request, emulator gameplay, save advancement, content adoption or campaign mutation occurred.

The smallest prerequisite is to specify and qualify **future-only, branch/save-aware virality policy adoption** before changing `config/virality_policy.json`. Current `ViralityMixin.__init__` deliberately rejects a different policy hash. This is a compatibility guard, not a provider problem. The story-content changes below can then be part of a separately authorized RIVAL-01 implementation. Do not disable the guard or rewrite old epochs/checkpoints to pass it.

## Accepted starting point and actual next encounter

Use retained normal Save20 `.local/rocket01/post-rocket-pair.sav` with protected `.local/rocket01/post-rocket-pair.sqlite3`; current working database is `.local/rocket01/world.sqlite3`. Checkpoint **fc2eb9f8-d613-4f48-aebf-b2ffa2c44824**, campaign **a8c24607-48a7-4e47-a204-4221a7367fcc**, branch **13a44cee-b272-40bb-9cfc-0815e1d386df**, cursor443, fingerprint **8d07886f33eea4d863209f9be626c191f4cf475262ceb5db5c3951f0f1c7d435**. Pairing is normal, not the earlier post-Kent retrospective checkpoint. [ROCKET disposition](rocket01_hermes_disposition.md) remains accepted; no recap reroll.

Pinned source **037335f4c725d7c9aecdac87066f2002b4bd7e14**. The accepted native save is Mt. Moon B2F (group1/map3), position18,31. Brock-defeated flag is set; fossil obtained and Fame Checker flags are unset. Read-only checksum-valid slot decoding gives `VAR_STARTER_MON=0` and `VAR_MAP_SCENE_CERULEAN_CITY_RIVAL=0`.

The next natural Rival is **Cerulean City's north exit toward Nugget Bridge**, not an earlier Route22 battle. `data/maps/CeruleanCity/map.json` has scene0 triggers at **22,6 / 23,6 / 24,6**, elevation3. `CeruleanCity_EventScript_RivalTriggerLeft/Mid/Right` select movement only; all enter `CeruleanCity_EventScript_Rival`. `scripts.inc:45–47` branches on the saved starter, then invokes the real `trainerbattle_no_intro` at lines69/73/77. No clone, developer trigger or early-rival tutorial mode.

Natural prerequisites: finish remaining cave/story route, reach Route4/Cerulean and cross that north-exit trigger with scene0. The accepted save has **not** cleared Miguel/fossil progression: `MtMoon_B2F_EventScript_BattleMiguel` launches native170 with no intro, then sets `VAR_MAP_SCENE_MT_MOON_B2F=1`; fossil selection sets `FLAG_GOT_FOSSIL_FROM_MT_MOON`. Preserve these scripts and normal travel/wild encounters. Do not assume today's public projection is the final pre-Rival projection: legitimate intervening recaps may add public history. Unqualified incidental trainers use ordinary native control and mandatory deterministic recap, with zero additional live roles; they must not become another expansion ticket.

The Rival can be postponed by avoiding the north exit; it gates this normal path toward Route24/Bill. Misty has no prerequisite in the Rival trigger, so Gym-first remains possible. Recommend Rival first for this slice; do not implement Misty. The intro sets Route22 scene2 before battle, including on a later loss. Victory sets the selected native trainer-defeated flag, returns to the continuing cutscene, marks Cerulean Rival scene1, gives Fame Checker/sets its flag, then removes the Rival. The script does not award a badge or SS Ticket.

Loss uses the ordinary no-intro trainer path: `StartTrainerBattle` sets normal trainer flags; `CB2_EndTrainerBattle` whiteouts a defeated player without setting the trainer-defeated flag or executing post-victory continuation. Cerulean is **not** `TRAINER_BATTLE_EARLY_RIVAL` with healing/continued-loss behavior. Preserve the native retryable scene. Canonical terminal loss still creates a mandatory factual recap under existing policy; test both outcomes deterministically before live calls. Acceptance's smallest progression target is one normal player victory. If an actual loss occurs, retain it and its recap; do not restore R1 merely to erase it, regenerate the locked strategy, or start an unbudgeted retry.

## Persistent identity and exact party branches

`tools/world_registry.py` explicitly constructs a `story_rival` family from trusted `TRAINER_RIVAL_*` and `TRAINER_CHAMPION_*` constants; `config/trainer_registry.json` already maps **27 source definitions** to world **fr:trainer:0326**, actor **trainer:fr:trainer:0326**:

`326–334, 426–440, 739–741`.

This includes starter variants and later Champion records as source identity evidence, not permission for later encounters/postgame. Giovanni348/349/350 is a different family. Display name `TERRY`, player-assigned name, roster hash, native ID, or model text never determines identity. Keep native334 on encounter/action/install receipts and actor0326 on social/memory/Strategy/resource ownership. Do not create actor0334 or merge unrelated trainers.

| Player starter / saved variable | Rival starter | Native ID / party symbol |
|---|---|---|
| Bulbasaur /0 **accepted save** | Charmander | **334**, `sParty_RivalCeruleanCharmander` |
| Squirtle /1 | Bulbasaur |333, `sParty_RivalCeruleanBulbasaur`|
| Charmander /2 | Squirtle |332, `sParty_RivalCeruleanSquirtle`|

No extra branch changes party based on trigger lane, badge count, player team or social evidence. All three are singles, four partners, authored custom moves (`NO_ITEM_CUSTOM_MOVES`, flag1), no held items and battle inventory `[0,0,0,0]`. AI mask **7** = CHECK_BAD_MOVE | TRY_TO_FAINT | CHECK_VIABILITY; this remains native fallback behavior.

| Slots shared by all variants | Level | Exact authored moves | Source IV → fixed IV |
|---|---:|---|---|
| Pidgeotto17 |17|Tackle33, Sand Attack28, Gust16, Quick Attack98|50→6|
| Abra63 |16|Teleport100, None0, None0, None0|50→6|
| Rattata19 |15|Tackle33, Tail Whip39, Quick Attack98, None0|50→6|
| Charmander4, selected334 |18|Metal Claw232, Ember52, Growl45, Scratch10|100→12|
| Bulbasaur1, variant333 |18|Sleep Powder79, Poison Powder77, Vine Whip22, Leech Seed73|100→12|
| Squirtle7, variant332 |18|Tackle33, Tail Whip39, Withdraw110, Water Gun55|100→12|

Source: `src/data/trainer_parties.h:3789–3869`, `src/data/trainers.h:3315–3343`, compiled pinned catalog `config/roster_catalog.json`. No default-move reconstruction or learnset correction: retain the explicitly authored starter and Abra moves. Abra's Teleport is selectable but fails in trainer battles (`data/battle_scripts_1.s:1921`, trainer-type jump to ButItFailed). That is legal engine behavior, not permission to repair its roster or mark the move unavailable. Verify PP use/failure/native terminal behavior in the deterministic test path.

Protect the current four companions; starter is the signature individual. Initial source baselines have native-specific lineage IDs; future continuity must retain individual identity through evolution and source party changes, rather than reinitialize a new person for each variant. No later roster/lineage transitions implemented here. Existing early Rival observations absent from the supported ledger must not be fabricated from story completion.

## Public scouting: actual retained data and relevance gap

The isolated accepted-world copy proves **11 public posts, 22 actor-authorized claims**, all with recorded `chronically_online` feed exposure to actor0326. Publication order: Rick102, Sammy104, Brock414, Colton105, Sally117, Greg106, Ben89, James107, Robin118, Kent108, grunt352. Each currently publishes an outcome and seen-species claim. These are actual active posts, not a proposed future feed. Full IDs, bodies, claims, original attribution and scope are in `evidence/phase8/rival01-readiness/inspection.json`.

Reuse `policy.plan`'s trusted Rival scout override → separate FEED → recorded EXPOSURE in `ViralityMixin._process/_expose_public` → `for_actor(actor).records` → `evidence_context` → `strategy.social_context.build_social_evidence`. The scout override bypasses follow-path gating, **not exposure or disclosure authorization**. Never query all canonical battles for a Strategy prompt. At eventual prebattle opportunity, finish legitimate pending public exposure ticks, then freeze context. Opening the player's feed does not expose anything to NPCs or generate Strategy.

Evidence descriptors include direct/reported mode, source/original-source actor, channel, quality, campaign distance, social path, publication order/lag and independent origins. Current sort is relevance CURRENT/RECENT/OLDER, descending publication order, stable memory ID; quality/corroboration are descriptors, not additional undocumented sort keys. Durable older facts are retained; repeated receipts from one origin are not independent corroboration. Bounds64 facts,24576-byte Strategy social packet; prebattle frozen facts also face8192-byte bound. Today's full social packet fits the Strategy component bound at19,186 bytes, but its18,844-byte frozen model view **fails the8,192-byte prebattle bound** in `ScoutingContextMixin.prebattle_facts`. No complete StrategyContext with companions/envelope was generated, so its combined24,576-byte limit remains unproven. Future implementation needs the same attributable ranked projection bounded for both consumers, using compact approved descriptors or explicit ranked-tail truncation, and preserving durable receipts. A pure existing-order tail-trim preview is archived as planning evidence only; it is not a repaired production context. Do not raise limits or claim all22 claims fit the tactical freeze. Recheck after stage correction/travel.

**Gap:** profile0326 uses first source occurrence `pallet`, order0; native332–334 encounterStage is unknown, and progression ends at Route4 order7. All today's Rival facts are consequently OLDER, including grunt/Kent distance6. Do not claim current ranking already models Cerulean relevance correctly. Future adoption should bind native332–334 to Cerulean order8 and an explicit encounter-scoped recipient position for Rival scouting; keep identity separate from encounter location. Retain old epoch configuration/content hashes and recompute old epochs under their original policy. Do not globally change the persistent actor's past location or redistribute the existing11 posts. This needs a tested version/cutoff-aware compatibility path, not SQL editing of `virality_version`.

Private denial is already measurable: Rival has exactly **two grunt public claims** and no ROCKET_INTEL receipt/channel, while Giovanni has47 private receipts/seven distinct semantic claims. No leadership context may be passed to Rival, and Hermes director memory cannot silently broaden Rival's knowledge. The prompt's “other45 observations” is not a literal semantic subtraction:47 is receipt count,2 is distinct public claims. Multiple private receipts support those same public claims. Acceptance must compare published claim sets, source/channel grants and forbidden receipt IDs, not subtract unlike counts.

## Persona, Strategy and preparation plan

No Rival production Strategy persona exists: it currently uses neutral defaults. Proposed concise authored persona: confident, strongly competitive and aggressive, dismissive of the player, modest caution, moderate adaptability/patience/flexibility, strong signature attachment/resource conservation. Scouting may be discounted or overinterpreted subjectively; persona never hardcodes actions. Cerulean dialogue supports boasting, rivalry and condescension. “Chronically online” is explicit project content, not a FireRed fact—the native dialogue even claims not to care about others. Document this adaptation rather than pretending the source implements scouting.

Plan one NEW opportunity at a safe **Cerulean pre-trigger position**, after legitimate travel/post processing, before crossing22–24,6. Context: actor0326 + encounter334 + proposed persona + four exact owned partners/empty resources + trusted campaign stage + ranked exposed public facts + legal unchanged preparation envelope. Known opposing current lead stays UNKNOWN. Exclude other actors' private observations/episodes, canonical hidden party, unrevealed moves/items/stats/RNG and Rocket leadership data. Proven packet above is a **public-context component**, not a completed production StrategyContext or PREP grant: no Rival profile/envelope/job exists yet.

Recommend **one unchanged legal candidate**, all four authored partners/moves/levels, fixed IVs, no item/level/move/acquisition/resource changes. Deterministically commit and lock that candidate; **no System One preparation inference**. The existing content contract has no Rival adaptation policy; don't invent alternatives. Host can generate its declarative baseline envelope from `Catalog.own_baseline(actor0326,334)` once new content is qualified. Normal `CreateNPCTrainerParty` builds it; installation receipt must match exact native source variant and party. No live structures or `gTrainers` edits.

One free-form Strategy completion (or bounded deterministic fallback), stored verbatim with host-generated job/context/provider/cutoff/identity hashes, freezes for the encounter. Current `.env` Strategy slot is **dots-studio/dots-3-note-preview:free**; defaults still contain older model references. Future implementation must resolve the actual slot and freshly qualify its free route before calls. No route checked in planning. Preserve configured Mercury and Inkling slots. Provider recovery, feed refresh or restart cannot reroll a committed memo. Subjective guesses never become facts or legal options.

## Native integration and minimal implementation diff

Cerulean no-intro is ordinary singles, zero items, normal replacements/switching; not doubles, tutorial, scripted healing or special battle flags. Existing generic legal exporter/controller, bounded transport, deterministic timeout behavior and BATTLE-END terminal receipt apply. No new combat engine. Abra Teleport failure and four-member replacements/voluntary switching remain **MUST VERIFY** through the actual source path before live inference.

Expected minimal changes under future authorization:

1. Versioned future-only progression/relevance-policy adoption and historical replay compatibility (host-only prerequisite above).
2. Additive Rival story-content/persona row for actor0326 and qualified native334, trusted starter/scene trigger binding, no-follow exception, signature/current companion retention and sole unchanged candidate. Generic content validation must accept reviewed `trainerbattle_no_intro`/coord-script chains; existing `CampaignContent.validate` assumes a single object with `trainerbattle_single`, empty signatures and ordinary-stage rules, so this is **not merely another ordinary row**. Do not weaken ordinary validation.
3. Fix the generic native-constructor observer's identity lookup: `ExpansionStore.observe_native_preparation` formats native ID into an actor, while `battle.domain.request_for` already uses the registry. Native334 must resolve to0326 consistently, preserving334 on receipts. This is a shared-family attribution correction, not a Rival-specific tactical branch.
4. Qualify a shared bounded public-context projection for Strategy and prebattle facts. The present full Rival view deterministically exceeds8192 bytes; preserve trusted provenance and ranked relevance, mark truncation explicitly and leave durable memory unchanged. Verify the combined Strategy and battle request bounds before inference.
5. Add selected334 to ROM qualification macro `PI_CAMPAIGN_TRAINERS(X)` and manifest; current accepted list contains106/107/108/117/352/414 plus special Rick. This is ROM/static data, **not permanent RAM**. Use normal build compatibility/same-save-layout adoption on new working copies; keep R0 original ROM/pair. No new native hook, transport field or mailbox.
6. Scope existing ordered scheduler/orchestration to the one new story opportunity, record golden trace/checkpoints/native viewer path. Do not schedule it immediately in Mt. Moon or create another free-text action provider.

Predicted permanent EWRAM change **0**, final headroom **4 bytes**. Rebuild must prove identical defined RAM symbols/linker end/save layout and measure existing temporary allocations for four partners. Stop if this needs a new permanent field; do not spend the last four bytes. No build was run in this planning pass.

## Trusted high-profile recap and downstream distribution

Classification already exists: source trainer class RIVAL_EARLY maps332/333/334 to `eventKinds='rival'`, author0326 in `sourceActors`. `policy.plan` selects `highProfile` whenever prominence is non-ordinary. Thus HIGH_PROFILE is the conceptual category; serialized trusted subtype remains **rival**, not a new enum invented from a name or model text.

Native canonical completion → Rival legitimate direct evidence → mandatory recap obligation → repaired generic Hermes content adapter → strict validation → live-or-fallback public post plus separate actor-owned private episode → public distribution/exposure. Posting is mandatory even for a terminal loss; authored no-follow exception keeps existing five followers unless actual legitimate intervening events change them. Do not propagate private Rival/director memory except selected published evidence. Later encounter Strategies may use the same actor's retained direct observations, prior public history and new public exposures, with a new opportunity—not rewritten old memos.

At current followers5, recent ordinary grunt post uses **budget12/window3/district**; Rival HIGH_PROFILE uses **budget64/window7/qualified-region**. This stronger treatment is already configured and proved by pure planning preview; eligible audiences may differ, so raw counts need not exceed the ordinary post's count. Direct followers and chronically-online recipients are handled separately. Existing highProfile is a fixed floor matching the top ordinary band; **additional high-profile follower amplification beyond64 is not implemented**. Do not promise a new algorithm or extend it here.

Example legitimate later public recipients already recognized as scouts: Misty415, Gym Picnicker Diana150 and Swimmer Luis234. Their future Strategy/battles remain unimplemented. Route24/25 ordinary actors may receive discovery only after their actual positions are qualified and selected by normal budgets; an unknown location is not automatic reach. Compare a recent ordinary post and Rival post with the same frozen follower/eligibility settings, then separately show actual deliveries/exposures contain only Rival-published claims. No fake Rival post was committed by the pure preview.

## Checkpoints, acceptance and golden trace

- **R0:** immutable accepted Save20/post-Rocket pair. No future Rival state.
- **R1:** normal paired save at safe Cerulean pre-trigger after travel and one frozen memo + unchanged preparation commitment; new compatible ROM/policy receipt. Preserve any real intermediate story/public history. All jobs settled.
- **R2:** native Rival victory, full canonical terminal/action resolution, direct observations, mandatory recap, high-profile epochs/deliveries/exposures settled, normal in-game paired save.
- **R3:** fresh offline process/Continue from R2; exact hashes/context/lock/post/direct/private scopes/epoch receipts, no recreated Strategy/Hermes/tactics or pending save.

Eventual causal trace:

`R0 → natural cave/fossil/travel → legitimate public ticks → Rival exposed/public-scoped context → one StrategyMemo/fallback → sole baseline commitment → R1 → native334 cutscene/battle → generic live System One/native revalidation/actions → canonical terminal → actor0326 direct receipts → mandatory Hermes/live-or-fallback recap → rival HIGH_PROFILE epoch → downstream public exposures → R2 paired save → R3 offline Continue`.

Generic services already implement most nodes. New work is source/story content qualification, canonical constructor binding, explicit stage/version adoption and experiment tooling; never restart the foundations. The source cutscene remains responsible for scene/Fame Checker/trainer flags.

Required implementation acceptance gates:

1. Actual starter branch334 and native trigger/continuation; canonical actor0326 remains shared across all27 definitions. Cross-family rejection and native receipt ID preservation.
2. Exact four-member authored party/zero items, one legal baseline lock, signature/current partners protected; installed native party matches. Strategy frozen verbatim/fallback, no preparation model call.
3. Best bounded **exposed public** context at actual opportunity; quality/relevance/cutoffs attributable; no private Rocket/director/other-trainer evidence or hidden player facts. Independently assert two published grunt claims versus forbidden47 private receipt IDs/channels.
4. Deterministic no-intro victory/loss, Teleport failure, switches/replacements/sole paths, timeout/late/duplicate/reset/terminal checks before hosted generation. Actual victory uses live Mercury participation with exact legal/execution receipts; failures remain honest fallback/canceled audit, not claimed live execution.
5. One canonical completion and mandatory recap, public trusted subtype rival, high-profile64/7 vs ordinary12/3 treatment, downstream claim-only exposure and private Rival memory retained. No follow granted by enemy name/class.
6. Native expanded feed ordering/pagination/post details/follower count; viewer read-only, no inference or NPC learning on browse.
7. R1 rollback excludes future battle/post/diffusion/direct memory (prebattle public evidence/memo legitimately remains). R0 additionally excludes memo/lock/adoption. R2 restore recovers once; old policies replay their original epochs. Fresh offline Continue requires no history inference.
8. Static/native RAM delta0/headroom≥4, normal source/save gates, explicit authorized verified-free budgets, workers stopped/default inference disabled at finish. No Misty/acquisition/rematch/leader/doubles/items/endgame work.

## Recommended future call ceiling — recommendation, not authorization

| Retained comparable encounter | Live Mercury requests | Context |
|---|---:|---|
| Brock final winning gate |20|2 partners; all meaningful selections live, one sole native replacement|
| Sally |12|2 partners; additional3 meaningful fallbacks, one sole replacement|
| Greg |15|4 partners; two replacement lifecycle rows canceled at terminal, application independently proved|
| James |16|3 partners; two sole/forced bypasses|
| Kent |8|2 partners; one sole replacement|
| Rocket352 |11|3 partners; all selected actions canonically resolved|

Use the conservative upper comparable density: Brock20 /2 partners × Rival4 = **40 battle requests**, plus **10 (25%) contingency** for longer native play/provider attempts. The budget bounds requests, not victories or turns; it does not authorize resampling a decision. Recommend **Strategy1 + PREP0 + battle50 + Hermes4 =55 maximum hosted attempts** for one planned Rival challenge. Hermes four includes up to three retrieval requests plus submission as measured by the repaired qualification; compared with historical two-call recaps, two are pipeline contingency. Strategy is one normal completion, no repair retry. This is not automatically a two-battle allowance or a route-health/model-substitution budget. If real loss or external exhaustion leaves acceptance incomplete, retain state and report the exact remaining gate before requesting another scope. Incidental travel recaps are deterministic/offline; no live Miguel expansion.

All roles need fresh non-generation free-route qualification during implementation. No model/provider requests were made now; the closed Rocket20/50 ledger is untouched and cannot fund Rival. No endpoint uptime claim or guaranteed latency is inferred from old receipts.

## Ranked risks and planning validation

| Rank | Finding / disposition |
|---|---|
| **BLOCKER** | Current hash-locked virality policy has no Cerulean stage and Rival relevance uses Pallet. Specify/test future-only policy history/adoption before activating stage8; preserve old saves/epochs/config receipts. |
| **BLOCKER** | Existing ordinary content validator rejects no-intro trigger chains/signatures; constructor observer would look for actor0334. Qualify the new story row and generic canonical lookup before live use. |
| **BLOCKER** | Rival public model view18,844 bytes exceeds the8192-byte frozen-facts contract. Qualify compact/bounded ranked projection before calling Strategy or System One; leave durable public evidence intact. |
| **MUST VERIFY** | Source-bound334 macro/build compatibility, four-partner temporary resources, unchanged RAM/save layout, and no-intro terminal/cutscene victory/loss/Teleport behavior. Singles mode fits existing engine scope; no unrelated mode expansion. |
| **MUST VERIFY** | Safe travel/fossil route, final public evidence freshness, locked context byte bounds, public-only downgrade/grants, versioned actor encounter location, hostile non-follow policy. |
| **ACCEPTED EXISTING BEHAVIOR** | Persistent Rival registry family, source-backed authored parties, public scout exposures, high-profile subtype/rules, bounded Strategy/System One/Hermes/fallbacks, paired save/rollback and native viewer. New encounter acceptance is still required. |
| **RESIDUAL RISK** | Free endpoint availability, native lawful quirky choices/Abra useless move, longer battle, future party/lineage continuity and player-loss rechallenge strategy policy. Do not silently solve these by roster edits/rerolls. |

Executed `.venv/bin/python tools/rival01_readiness.py`: checksum-valid save decoding, all27 identity joins, three catalog party branches, isolated real-world public projection, private-receipt denial, pure high-profile treatment comparison, seven replay-hash equality, twelve inspected-source hashes matching pinned Git, and before/after hashes of all config files plus active/protected databases/saves/ledger. It opens only a disposable `.local/rival01-readiness/planning.sqlite3` copy through the existing store; constructors may run idempotent copy setup but no domain tick/adoption/exposure/Strategy is issued. The active database is never opened as a writer. Machine artifact: `evidence/phase8/rival01-readiness/inspection.json`; execution log: `console.log`. These are **planning checks, not native or live RIVAL acceptance**. No full StrategyContext/envelope generated; projection serializes within the existing social contract. Workers remain stopped; hosted inference disabled.

Files added: this report, read-only inspection helper and evidence. `docs/status.md` records planning status only; authoritative architecture/content/providers and active campaign are unchanged. No implementation prerequisite was auto-fixed. Next task is the explicit versioned progression/relevance-adoption prerequisite under separate authorization; endgame remains deferred.
