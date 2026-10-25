# Runtime architecture and battle agents

## 1. Runtime components

Keep one local companion process initially. An internal module boundary is not a requirement for another service or framework.

| Module | Responsibility | Inputs | Outputs |
|---|---|---|---|
| ROM adapter | Emit trusted game events, sanitized observations, UI requests; execute validated actions | Actual game state | Bounded mailbox records |
| Emulator bridge | Move records, verify build/session, coordinate managed checkpoints | ROM mailbox + local transport | Correlated requests/replies |
| Event service | Append events once, sequence them, update projections | Authenticated game/host events | Ledger rows, outbox jobs |
| Visibility service | Determine who may access evidence | Event permissions, social edges, delivery log | Scoped evidence sets |
| Memory service | Maintain episodes, beliefs, relationship context | Authorized evidence | NPC context packets |
| Social puppeteer | Prioritize allowed social actions and continuity | Scoped jobs, actor goals, candidate actions | Validated proposal or rule fallback |
| PokeBook service | Drafts, publication, delivery, feed pagination | Approved claims and social decisions | Encoded feed pages/notifications |
| Roster planner | Generate/rank small legal changes | Identity, budgets, evidence cutoff, catalog | Immutable prepared plan |
| Battle policy | Choose a fast legal action | Sanitized turn observation, strategy profile | Action ID and debug reason code |
| Model adapter | Bounded provider calls and output validation | Scoped structured request | Recorded model decision or fallback |
| Save coordinator | Pair game snapshots with host history | Game marker and committed event cursor | Recoverable checkpoint manifest |

The runtime owns one serialized world-state writer. Concurrent model jobs return proposals; they do not mutate SQLite directly. Transaction boundaries protect event application, plan commitments, rewards, and exposure deliveries from races.

## 2. Implementation stack

Proposed baseline: Python 3.12+ with a pinned supported minor version, SQLite, `asyncio`, typed records, a JSON-schema validation library, tests, and a small CLI. Use the version actually available and supported by selected dependencies; record it in the lock manifest. Do not assume a pre-existing user's Python environment is compatible.

Use Python's built-in socket/async primitives for local transport before adding a web server. A local read-only debug view is useful but must not become a dependency of the in-game feed. No cloud database, hosted backend, vector database, queue server, or continuously running general-purpose agent platform is required.

Content/configuration stays in reviewed JSON initially. A build step validates it and generates compact ROM tables and a host catalog from a single versioned source. Avoid independently handwritten enums on both sides of the bridge.

## 3. Proposed future repository layout

This is a target layout, not a claim these implementation directories already exist:

```text
AGENTS.md / PLAN.md / docs/ / config/ / contracts/
game/                   pinned source fork or reviewed patch workspace
bridge/mgba/            Lua adapter, capability probe, transport code
runtime/influencer/
  events/               ledger, migrations, idempotency
  memory/               scoped retrieval, beliefs, consolidation
  social/               graph, delivery, feed, puppeteer
  trainers/             profiles, legality, preparation, rematches
  battle/               observations, utility policy, fallback parity
  models/               provider adapters, budgets, recorded responses
  saves/                checkpointing, replay, migration
  cli/                  launch, verify, export, debug
content/                trainer bindings, regions, permissions, templates
generated/              catalog, protocol definitions, ROM content tables
tests/                  unit, property, integration, emulator scenarios
tools/                  build, data export, packing, patching
local/                  ignored secrets, user's local paths, runtime state
artifacts/              ignored build/test outputs unless deliberately curated
```

Decide fork versus pinned upstream plus patch queue in SETUP-02. Keep upstream provenance and a clean baseline. Do not treat a mutable default branch as a release dependency.

## 4. Fast System 1 battle policy

### 4.1 Meaning of System 1

Here it means a fast policy that does not perform an LLM reasoning call per turn. Start with an inspectable utility evaluator. Its interface permits a compact learned policy later; neither the plan nor the label asserts that such a model has already been trained.

The behavior can still be adaptive because its strategy weights and opponent beliefs come from legitimate past observations. Intelligence is not synonymous with a remote model invocation.

### 4.2 Information boundary

Create the observation inside the trusted ROM adapter or an equivalently audited boundary. The policy receives its own team, known resources, current public battle state, revealed opponent facts, and scoped historical beliefs. It must not receive a dump of player memory.

Allowed: opponent species currently revealed, displayed level, public status/weather, visible stat-stage changes, observed move outcomes, and moves actually revealed in this battle or through delivered prior information. Exact own-team HP/stats/PP are available; opponent HP should be no more precise than the chosen fair visibility model, initially coarse displayed HP buckets.

Not allowed: unshown party/boxes, unrevealed held items/abilities/moves, exact private opponent stats, selected player commands, future RNG, unpublished catches, or a list of all possible legal opponent actions derived from their hidden moveset.

Battle results can update observations only after they become visible. Commit the opponent's action before the adapter exposes any result of the player's current choice. If FireRed's controller ordering stores the player's command earlier, do not read that field; prove the sanitization using mutation tests rather than assuming controller order protects it.

### 4.3 Action interface

Input has an observation ID, battle ID, turn/phase ID, plan version, battle-state generation, knowledge cutoff, legal action IDs, own known data, visible opposing data, and a strategy profile. Output identifies exactly one candidate action ID; it does not invent a move, species, or arbitrary memory write.

Handle these phases separately:

- Voluntary move/switch/item choice.
- Move target choice when applicable.
- Forced replacement after fainting.
- Forced move states, recharge, no PP/Struggle, trapping, and battle-end transitions.

The rules validator can use privileged internal mechanics to reject execution that is genuinely illegal. It must not expose hidden immunity information as a scoring hint; an ineffective attack may still be legal. Unrevealed opponent abilities are not a reason to delete a candidate unless the game actually prevents that action and the fair-observation policy accounts for that feedback.

### 4.4 Initial evaluator

For each legal candidate compute bounded features: approximate damage value, KO/survival value, status/setup value, matchup after switching, resource cost, and repeated-switch penalty. Blend these with personality and a weak evidence-based opponent-style prior.

```text
utility(action) =
    tactical_value(action, visible_state, own_team)
  + personality_bias(action)
  + bounded_strategy_bias(action, scoped_history)
  - resource_and_loop_penalties(action)
```

Unknown opponent properties use fixed public priors or explicit distributions, never the hidden actual values. Use a dedicated seeded policy PRNG, not the game's damage RNG. Seeded choice among near-equal scores produces variety without turning every trainer into the same perfect optimizer.

Start with a small, approximate evaluator rather than porting an entire later-generation simulator. If damage estimation is approximate, label it and test its ranking on canonical fixtures. A more complex simulator must match the pinned Gen III rules, not assume later-generation mechanics.

### 4.5 Personality and difficulty

Profiles control aggression, risk tolerance, patience, switching cost, resource conservation, and adaptation strength. Personality changes preferences among reasonable choices; it is not a license to cheat.

Ordinary trainers should remain imperfect and readable. Skilled trainers can use more reliable evaluation or less exploratory choice, within the same information boundary. Difficulty is authored; it does not secretly increase because the player wins repeatedly.

### 4.6 Fallback

For enhanced trainers, implement a small fair ROM-native fallback operating on the same permitted observation fields, even if it initially makes only simple legal move choices and conservative replacements. Do not call upstream vanilla AI an audited no-peeking policy without checking it.

Unsupported or excluded special battle types retain their original behavior explicitly. Track them in the coverage manifest. Vanilla fallbacks used temporarily during development must be labeled, and fairness claims must be limited accordingly.

## 5. LLM responsibilities

NPC planner: summarize an authorized experience, propose a strategy intent, and choose among validated roster candidates. Puppeteer: prioritize bounded social opportunities and retrieve/condense relevant evidence. Writer: express an approved claim in character.

Each invocation is a short-lived job with input evidence IDs, allowed actions, quotas, expiry, and a deterministic fallback. Maximum initial planning loop: two model steps and three scoped read-tool calls; no indefinite self-reflection or retry loop.

The model may select `adjust_strategy`, `choose_candidate`, `draft_post`, `reply`, `invite_rematch`, `summarize_memory`, or `no_op` only when that action is included in the current grant. A validated proposal is committed by a rules service. The model receives acceptance/rejection feedback for debugging, but cannot change the rules to make a rejected action succeed.

No model gets shell access, arbitrary SQL, general filesystem access, remote browsing, game scripting, or real social-media credentials. Player handles/posts are data, not instructions.

## 6. Latency and workload budgets

Initial goals, to measure on a named reference machine:

| Path | Proposed goal | Required fallback |
|---|---|---|
| System 1 host evaluation | p95 under 100 ms | ROM fallback at request deadline |
| Battle request end-to-end | Normal-play hard wait budget around 300 ms / bounded ROM frame count | Valid deterministic action |
| Feed open | Cached first page, no live model wait | Stored/template feed |
| Roster generation | Prepared at milestone/opportunity, not when entering battle | Last legal plan or legal rule plan |
| LLM job | 8 s host timeout; bounded queue | Template or rule decision |
| Inactive NPCs | No polling inference | Wake only on relevant events |

Frame deadlines and wall-clock time are different. Emulator fast-forward shortens the real time available per frame; tests must measure this and may accept more fallbacks. No code may assume an LLM finishes within a few emulated frames.

Cap model input/output tokens, calls per session, and spend when provider prices are configured. The USD amount in configuration is a user budget setting, not a prediction of actual cost. Unknown prices or missing authorization disable paid inference rather than bypass the budget.

## 7. Optional learned policy path

Only after the initial game loop is stable: collect sanitized observation/action/outcome records from reproducible permitted simulations; split by scenario, trainer, and seed to prevent leakage; train a compact policy or value model; compare under identical information restrictions and latency limits.

Promotion requires legal-action masking, offline reproducibility, robustness on unseen teams/status states, no regression in fairness, and meaningful improvement over the utility baseline. Store training data provenance, model/license details, feature schema, checksum, evaluation, and fallback behavior. Do not train on the player's evolving private data without an explicit separate decision.

## 8. Runtime observability

Logs should explain a decision without exposing secrets to the player-facing UI. Record observation hash, allowed evidence IDs, selected action/candidate, rejected constraints, policy/model/prompt versions, latency, fallback reason, and branch/save identity. The debug inspector should answer: "Why does this NPC know that?" and "Why was this team legal?"

Keep local logs out of version control and cloud requests by default. Publish aggregate evaluation results or synthetic fixtures, not raw user saves or credentials.
