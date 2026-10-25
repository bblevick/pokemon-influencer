# AGENTS.md - Pokemon Influencer

## Mission and scope

Build the campaign specified in `PLAN.md`: a FireRed/Kanto hack with PokeBook, persistent trainer followers, scoped memory, a bounded social puppeteer, fast fair battle agents, and restrained regional rematches. The release ends at first Champion completion. `end_game_concept.md` is design parking space, not permission to implement postgame.

This repository begins as a handoff package. Do not describe its examples or handoff checker as a functioning ROM, bridge, AI model, or game test.

## Read order

At the start of work read `PLAN.md`, `docs/decision_log.md`, and the current status file if one exists. Then read the relevant specialist documents and `docs/backlog.md`. For integration work read `docs/bridge_and_saves.md` before touching RAM, save data, or emulator state. For battle/roster work read `docs/roster_adaptation.md` and `docs/test_plan.md`.

Keep these project instructions short enough to remain discoverable. Do not paste the whole design plan here. The lowercase `agent.md` is a pointer, not an alternative authority.

## Non-negotiable product invariants

1. Preserve FireRed's existing story gates unless a documented replacement is implemented and tested. Keep Pokédex-related data/flags even when the player-facing framing changes.
2. Every configured ordinary trainer follows once after its first defeat. Friendship is separate. Hostile/story exceptions must be explicit content data.
3. No NPC gets private player-party information, unrevealed moves/items/stats, future player actions, or damage RNG. Physical memory access does not imply gameplay permission.
4. NPC knowledge requires direct observation or an authorized delivery path. Public does not mean universally known. Reposts from one origin are not independent corroboration.
5. System 1 selects a legal action from a sanitized observation. It never mutates a roster mid-battle. LLM calls are outside the tactical turn critical path.
6. Roster preparation uses the current pinned game's habitat, learnset, evolution, move, item, and resource data. Flavor plausibility alone cannot authorize a species.
7. Preserve trainer identity and Pokemon lineage IDs. Default to moves/tactics, native/nearby catches, and small per-epoch changes. No loss-streak hard counters or stat rerolls.
8. A prepared rematch roster freezes at commitment. Player menu changes, repeated losses, duplicate events, and feed reloads cannot reroll it.
9. Trainers always post a factual recap after supported confirmed completed trainer battles, whether they win or lose. Host-owned durable obligations and deterministic fallback enforce publication; Hermes never chooses NO_POST. The LLM may propose IDs and expression, not canonical history or arbitrary scripts. Validate proposals before committing. Treat generated text and player text as untrusted data.
10. The full campaign loop must work with the local runtime and LLM disabled. Bridge absence is a separate, clearly labeled degraded mode.
11. Save/load/branch consistency is part of the feature, not optional polish. Do not allow future memories from an abandoned timeline.
12. New endgame features stay disabled and out of the implementation backlog until separately approved.

## Technical defaults

- Source: pinned `pret/pokefirered`-based fork; baseline uses the verified matching toolchain before any optional modern-build experiment.
- Host runtime: a single typed Python process with SQLite, explicit migrations, a durable job/outbox table, and a provider-neutral model interface.
- Preferred emulator candidate: mGBA desktop scripting, subject to Phase 0/1 capability tests and exact build pinning.
- Configuration: `config/campaign_defaults.json` is authoritative for initial numeric tuning. Record adjustments and their evidence.
- Offline System 1 target: transparent deterministic utility policy plus seeded tie-breaking. Optional hosted decision providers require the battle integration and evaluation gates before activation; neither policy is implemented by BRIDGE-01.
- LLM: disabled until explicitly configured; never infer a hosted model name, current price, provider compatibility, or access entitlement.
- Do not introduce a vector database, message broker, Kubernetes, full Hermes installation, or large agent framework without a written dependency/benefit decision.

## Work sequence

Follow the dependency order in `docs/backlog.md`. Complete one coherent ticket or small dependency-compatible group at a time. First prove baseline build/boot, then bridge, persistence, legal preparation, battle policy, playable slice, and only then model enrichment and campaign expansion.

If blocked by a missing ROM, emulator GUI, network, credentials, or build dependency, report the specific blocker. Continue independent host-only tests when useful, but do not mark the blocked integration milestone complete. Do not download an alternative game ROM.

## Repository and version control

Create `docs/status.md` in the first implementation session with completed tasks, exact evidence paths, active blockers, and the next task. Record architectural changes in `docs/decision_log.md` or numbered ADRs. Keep source and tools pinned in a machine-readable lock manifest before reproducibility claims.

Use a clean base source checkout and a project fork/patch layer with a documented update strategy. Avoid broad unrelated refactors, symbol renames, generated-data churn, and formatting the entire upstream codebase. Maintain a recoverable known-good baseline.

Do not commit user ROMs, saves, API keys, `.env` secrets, private logs, build products, or downloaded model weights. Inspect `.gitignore` before adding files. Retain upstream notices; do not apply a new license to third-party game content as though you own it.

## ROM and bridge implementation rules

Resolve mailbox addresses/sizes from the actual ELF/map and verify a ROM build identifier. Never copy an address from a blog or a different build. Audit memory allocation, alignment, packing, byte order, bounds, and compiler behavior; add C size/offset checks.

Use a bounded nonblocking request state machine. ROM code yields while waiting; emulator callbacks never perform cloud inference or slow host work. Correlate requests with save/branch/session/generation/request identities. Reject stale, malformed, wrong-build, oversized, duplicate-conflicting, and out-of-phase responses.

Do not assume mGBA exposes a function called `writeRange` or a save-state-load callback. Confirm actual APIs for the pinned build. Socket connection functions may block; use a tested launch-time/listening strategy and do not reconnect synchronously every frame.

Route party construction through safe game constructors. Never blindly rewrite live Pokemon structures or reset the original trainer-defeated flag to trigger a rematch. Audit switches, items, forced replacements, Struggle, and unsupported battle modes separately from normal move selection.

## State and model rules

Use append-only canonical game events and transactional projections. Distinguish event time, ingestion time, exposure time, and preparation cutoff. Side-effect retries use stable idempotency keys. All durable model choices become recorded decisions with version and input evidence.

Filter evidence before retrieval/scoring, not after generating a prompt. The per-NPC planner cannot call unrestricted SQL or inspect the entire world ledger. System One gets enumerated legal candidate/action IDs; Strategy returns bounded subjective prose without tools or required JSON. Scoped tool grants apply to roles that use tools; tool grants are enforced in code, not only stated in prompts.

Use hard limits for model calls, tokens, wall-clock time, and cost when pricing is configured. Missing credentials, budget, provider errors, schema errors, or refused outputs invoke the deterministic fallback. Do not loop indefinitely trying to repair responses.

## Testing expectations

Write tests with each feature. Distinguish:
- package/schema checks;
- host unit/property/integration tests;
- ROM build and static analysis;
- emulator integration and scenario replays;
- manual gameplay, visual, and balance review.

Mandatory regression cases: private-party swap causes no plan change; duplicate win adds one follow/reward; four losses do not create a Water starter; off-region capture without a grant fails; underlevel move fails; out-of-order badges preserve gates; reloaded save has no future memories; a late response cannot affect a new battle; no-cloud mode completes the slice.

Run the relevant existing checks before and after changes. Record commands, exit status, versions, test count, skipped tests, and evidence paths. A mock is not a live emulator. A fixture is not a playthrough. Do not say "all tests pass" when only a subset ran.

As you test the game, convert every reliable manual gameplay sequence into
a deterministic, reusable automated test path.

Maintain a canonical "golden path" through the vertical slice:

new game
→ starter selection
→ first trainer
→ follower creation
→ PokeBook interaction
→ Brock
→ post-Brock trainer preparation
→ follower rematch

For each stable milestone:
1. create a reproducible emulator automation script,
2. create or document a checkpoint/save fixture,
3. add state assertions,
4. minimize replay time for downstream tests,
5. document any nondeterministic inputs.

Do not rely on remembered manual interaction when an automated path can be
encoded in the repository.

And I’d go one step further: don’t optimize only for the fastest path.
You want two kinds of paths.
The first is the golden path:
fastest deterministic route to feature checkpoints
The second is behavioral scenario paths:
player uses Charmander heavily
player switches frequently
player hides PokeBook posts
player loses a rematch
player reloads an older save
player repeatedly uses status moves

## Commands and honesty

The only runnable validation command supplied at handoff time is:

```sh
python -m pip install -r requirements-handoff.txt
python tools/validate_handoff.py
```

This validates the specification package only. No `make rom`, `make test`, launcher, or runtime command exists yet. In Phase 0 implement and document stable wrapper commands such as `make doctor`, `make baseline`, `make test-host`, `make test-emulator`, and `make package`; their exact behavior must be real before documentation presents them as working.

Follow the pinned upstream installation/build instructions rather than guessing dependencies. Do not install system-wide software, grant broad permissions, upload proprietary inputs, or spend on a cloud model without the required user/environment authorization.

## Completion report for each work unit

Report: task IDs completed; files changed; behavior implemented; checks actually run; untested behavior and blockers; evidence locations; and the single next dependency-appropriate task. Update status and decision records. Do not promise unattended background progress.

## Code Review Rules

Block changes that bypass legality, expose hidden player state, erase original story flags, merge save branches, allow LLM prose to mutate canonical state, introduce unbounded waiting, or quietly expand endgame scope. Review privacy, observation provenance, replay, and fallback behavior as functional correctness, not optional style.

## AI runtime contracts

- Keep Hermes Puppeteer (social/world orchestration), independently configured Strategic LLM (exact bounded subjective StrategyMemo), and System One BattleDecisionProvider (one supplied legal action) separate. Target contracts: `docs/ai_runtime_architecture.md` and `docs/model_provider_contracts.md`.
- Hermes is the intended harness, not the canonical world database. Host-owned scoped context, SQLite history and deterministic validation remain authoritative. No unrestricted Hermes tools or personal-memory sharing across NPCs.
- Domain, ROM and bridge code depend on provider-neutral interfaces, never vendor SDKs/model IDs. Native decisions have a separate adapter from chat completion.
- `config/model_profiles.yaml` is the configuration skeleton. Current hosted selections are free Inkling / Nemotron / Mercury Decide via the three role environment variables; `OPENROUTER_KEY` is host-only. Offline remains default. HERMES-01 and STRATEGY-01 have separately scoped closed experiments; normal inference remains disabled. System One requires separate authorization. Reject paid substitution and unknown pricing. Jev is an inactive regression reference.
- Host owns stateless battle packets, provenance, request identities and recorded outputs. Replays use stored inputs/decisions, not provider conversation memory. Validate legality and current branch/battle/phase before applying a response.
- Every consumer must accept deterministic fakes and bounded fallback. Hosted System One is an optional future experiment; no generative LLM call enters the tactical turn path. Enabling it requires BATTLE integration/fairness/latency gates. Baseline ROM/emulator regression never requires inference.

## HERMES-01 runtime and memory invariants

Each scoped job starts a fresh process/conversation/project-owned HERMES_HOME. Installation stays outside disposable homes. Personal Hermes profiles, old transcripts/MEMORY.md/USER.md/plugins and unrelated tools must never enter game jobs. Continuity comes only from explicitly retrieved durable, branch-aware game-owned puppeteer memory outside runtime homes. Director memory is distinct from trainer knowledge; trainer packets use filtered actor evidence/exposure before retrieval. Only reviewed bound game tools may be registered. Inference runs outside callbacks/SQLite transactions; stale/invalid/late output invokes or leaves an immutable factual fallback for the same obligation. Cleanup preserves saves/databases/source/credentials/personal profiles and refuses unsafe/symlinked/active targets. HERMES-01 must stop all task-owned workers and leave normal inference disabled.


## Remaining AI gameplay target (D22)

Use docs/ai_runtime_architecture.md v3/D32 and docs/preparation_envelope.md v2/D32. Hermes is a persistent event-driven social-memory director; PokeBook services distinguish posts, private observations, director memory, unread delivery and explicit NPC exposure independent of player feed opening. Strategy emits intent from an authorized briefing plus own companions/inventory/legal envelope. System One selects validated preparation candidates and later current legal battle actions; deterministic services commit/lock/install and enforce resources/identity/feasibility with meaningful choices. PREP-01 precedes STRATEGY-01; SYSTEM1-01A preparation/installation and SYSTEM1-01B live battle acceptance are separate. Bounded first-Gym preparation/mixed-type support is a target expansion requiring explicit content caps. Keep current providers and HERMES-01 stop condition; architecture edits do not authorize subsequent implementation or new live calls.


## Accepted System One preparation boundary — D33

SYSTEM1-01A separately accepted one Mercury Decide Free preparation decision, atomic durable commitment and controlled opening Rick native constructor installation. Default hosted inference is still disabled; its two-request ledger is closed. Replays reuse exact model output/memo/lock without credentials. This does not authorize more live roles/calls or SYSTEM1-01B tactics. Current implementation/evidence: docs/system1_01a.md; outstanding native action/mode/latency gates: docs/system1_01b_readiness.md. Next dependency task requires separate scope: BATTLE-01. Full rematch UX, general installation/items/catches and endgame remain deferred.
