# Pokemon Influencer - Codex handoff

**Version:** 0.1 design handoff | **Prepared:** 2026-09-29

A FireRed/Kanto campaign where your journey becomes a PokeBook story, defeated trainers become followers, and recurring opponents learn from believable information while keeping recognizable teams.

**This package is a specification, not a built game.** No ROM was supplied or modified for this handoff. No emulator bridge, battle policy, or gameplay test has been executed. The included checker validates this package's reference records, links, and selected design invariants only.

## Begin here

1. Put this folder at the root of the new project and open that root in Codex.
2. Read `AGENTS.md`, `PLAN.md`, and `CODEX_START_HERE.md`.
3. Give Codex the kickoff prompt in `CODEX_START_HERE.md`. Its first assignment is the Phase 0 feasibility gate, not the entire game.
4. Supply your own FireRed dump locally when requested by the build/patch verification workflow. Keep it outside version control. Emerald is not needed for this design.

`AGENTS.md` is the authoritative Codex instruction file. `agent.md` is a small compatibility pointer supplied to match the requested filename; do not maintain two competing instruction sets.

## Document map

| File | Purpose |
|---|---|
| `PLAN.md` | Product definition, campaign scope, ownership boundaries, milestones, release definition |
| `AGENTS.md` | Engineering instructions and non-negotiable guardrails for Codex |
| `CODEX_START_HERE.md` | First-session prompt and execution/reporting expectations |
| `docs/architecture.md` | Runtime components, battle policy, interfaces, tooling, failure modes |
| `docs/memory_and_pokebook.md` | Puppeteer, scoped memory, social propagation, reputation, in-game experience |
| `docs/roster_adaptation.md` | Restrained growth, geography, legality, rematch state machine, worked example |
| `docs/bridge_and_saves.md` | Emulator integration, wire protocol requirements, save/rewind consistency |
| `docs/test_plan.md` | Unit, integration, emulator, adversarial, balance, and release tests |
| `docs/backlog.md` | Dependency-ordered implementation tickets and acceptance criteria |
| `docs/decision_log.md` | Locked choices, reversible defaults, and unresolved feasibility decisions |
| `docs/source_notes.md` | Primary sources, verified facts, and assumptions that still require experiments |
| `end_game_concept.md` | Explicitly deferred post-Champion design space |
| `config/campaign_defaults.json` | Initial tuning values; proposals, not playtest findings |
| `contracts/domain.schema.json` | Reference JSON Schema for seven domain record types, not the C mailbox ABI |
| `examples/` | Illustrative records validated by the included handoff checker |
| `prompts/` | Bounded puppeteer, trainer-planner, and social-writing instructions |
| `tools/validate_handoff.py` | Package validation; does not test the future game |
| `evidence/handoff_validation.json` | Results from running the handoff checker |

## Product in one sentence

**Battle, post, get followed, become known, and meet the same trainers again after they have trained intelligently within their own part of Kanto.**

The campaign ends at the first Champion completion for this release. Existing postgame access is audited for compatibility, but new endgame content is not an implementation task yet.

## How to use the specifications

The source of truth for ordinary campaign behavior is `PLAN.md` plus the specialist documents. Numeric tuning lives in the config. If these disagree, log the conflict and reconcile it before implementing; never silently prefer the larger or more powerful interpretation. Example records are explicitly unbound until matched to the pinned game data.

Game source, reference ROMs, local saves, credentials, generated player logs, and copyrighted release artifacts must not be accidentally bundled with this handoff. The future release workflow is patch-oriented and separate from this documentation package.
