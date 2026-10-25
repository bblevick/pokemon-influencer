# Start the first Codex session here

Open Codex in the root containing `AGENTS.md`. Keep the whole handoff folder together. Put the user's local FireRed dump outside version control; its path can be configured locally when needed.

## Kickoff prompt

```text
You are implementing Pokemon Influencer from this repository's handoff.

Read AGENTS.md, PLAN.md, docs/decision_log.md, docs/bridge_and_saves.md,
and Phase 0 tickets in docs/backlog.md. This repository initially contains
specifications and reference fixtures, not a working game.

For this session, execute Phase 0 only. Establish docs/status.md, inspect
available tools and permissions, validate the handoff package, and identify
and pin a supported pret/pokefirered source and matching baseline toolchain.
Use my own locally supplied FireRed dump only for appropriate verification
and patch testing; do not download a game ROM or upload mine.

Attempt a clean baseline build and record its target revision/checksum.
When emulator access is available, boot it, complete one ordinary battle,
perform an in-game save, and reload. Record actual evidence and exact
commands. Probe the candidate emulator's scripting/memory/socket capabilities
without claiming that a bridge has already been implemented.

Create a short source-integration map identifying where trainer battle
selection, party construction, first-win events, VS Seeker rematches,
menu text, and save serialization would be integrated. Inspect the pinned
source before naming exact hooks. Do not add an LLM or modify battle AI yet.

If some environment capability is missing, report that precise blocker and
finish independently testable setup work. Do not mark mocked or unrun
emulator steps complete. End with completed ticket IDs, evidence paths,
open risks, and the next Phase 1 task. Keep endgame implementation deferred.
```

## Later sessions

Give Codex one milestone or small ticket group at a time. An example after Phase 0 genuinely passes:

```text
Read AGENTS.md and docs/status.md. Implement BRIDGE-01 and BRIDGE-02 only,
following docs/bridge_and_saves.md. Use the pinned baseline and add tests for
wrong-build rejection, bounded payloads, timeout, duplicate requests, and
session mismatch. Do not introduce cloud inference. Record which tests used
the actual emulator and which were host-only.
```

## Expected first-session outputs

- Updated `docs/status.md` with a capabilities table and transparent pass/block status.
- A lock manifest containing actual source/toolchain/emulator identifiers, or clearly marked unresolved entries.
- Verified baseline build logs and hashes when the build succeeds.
- Emulator screenshots/logs and save/reload evidence when those steps actually run.
- A pinned-source hook map, not unsupported assumptions about RAM or API names.
- A minimal reproducible development command entry point and a deliberate repository/source layout decision.

No first-session completion claim requires a new region, social UI, trained model, or playable full hack. Those are later acceptance gates.
