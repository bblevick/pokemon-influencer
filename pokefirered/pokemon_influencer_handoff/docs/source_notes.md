# Primary sources and evidence boundaries

**Checked:** 2026-09-29. Repository default branches can change; implementation must pin commits. These sources verify starting capabilities and data locations, not the successful execution of this project's integration.

## Source register

### S0 - Codex project instructions

Official OpenAI documentation, accessed through `https://developers.openai.com/codex/guides/agents-md/` (redirected to `https://learn.chatgpt.com/docs/agent-configuration/agents-md`).

Confirms project discovery of `AGENTS.md`, override precedence, configurable fallback names, and a combined instruction-size limit. The handoff therefore uses `AGENTS.md` as the canonical file and keeps the detailed plan separate.

### S1 - FireRed source baseline

`https://github.com/pret/pokefirered`

The README identifies the English FireRed/LeafGreen decompilation and matching targets. At inspection, the documented FireRed SHA-1 values included:

```text
FireRed default: 41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc
FireRed rev1:    dd5945db9b930750cb39d00c84da8571feebf417
```

These identify baseline targets, not the modified hack. Verify the user's actual dump; do not rename or patch an unknown file on the assumption that it matches. Record SHA-256 as well for the local release workflow.

### S2 - Build instructions

`https://raw.githubusercontent.com/pret/pokefirered/master/INSTALL.md`

Documents platform setup, agbcc installation, `make`, revision-specific targets, and comparison commands. Follow the pinned revision. Some platform sections contain legacy environment assumptions; a successful local build is the acceptance criterion, not copying an old installation recipe blindly.

### S3 - Emulator scripting

`https://mgba.io/docs/scripting.html`

Documents memory reads/writes, frame and save-data callbacks, save-state methods, screenshots/input control, and TCP socket callbacks. It explicitly warns that socket connect calls block. A `writeRange` helper and generic save-state-load event were not established from this documentation. Probe exact runtime capabilities and do not invent API calls.

### S4 - Hermes memory analogy

`https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/memory.md`

Documents bounded curated memory, session retrieval, and a session-start snapshot pattern. It warns against multiple agents sharing one Hermes home. This project borrows the separation of durable storage, scoped retrieval, and agent context; it does not assume Hermes provides a ready-made game memory/visibility/synchronization system.

### S5 - Battle AI integration candidates

```text
https://raw.githubusercontent.com/pret/pokefirered/master/src/battle_ai_script_commands.c
https://raw.githubusercontent.com/pret/pokefirered/master/src/battle_ai_switch_items.c
https://raw.githubusercontent.com/pret/pokefirered/master/src/battle_controller_opponent.c
```

The inspected source includes move-scoring/selection and separate switch/item paths. Replacing only the normal move selector is not a complete battle-agent integration. Exact controller hooks and forced replacement behavior must be traced in the pinned source.

### S6 - Trainer, battle setup, and rematches

```text
https://raw.githubusercontent.com/pret/pokefirered/master/src/data/trainer_parties.h
https://raw.githubusercontent.com/pret/pokefirered/master/src/battle_setup.c
https://raw.githubusercontent.com/pret/pokefirered/master/src/vs_seeker.c
```

Use these as inspection entry points for trainer-party construction and existing rematch behavior. The reference NPC in `examples/` is intentionally illustrative and unbound; it is not asserted to match a vanilla trainer record.

### S7 - Habitat data

`https://raw.githubusercontent.com/pret/pokefirered/master/src/data/wild_encounters.json`

The file contains version-specific encounter data. The inspected FireRed Viridian Forest entries include Caterpie, Weedle, Metapod, Kakuna, and Pikachu. This does not make every species suitable for every trainer archetype, and does not establish Scyther or Pinsir as ordinary early-forest catches.

### S8 - Learnsets and evolution

```text
https://raw.githubusercontent.com/pret/pokefirered/master/src/data/pokemon/level_up_learnsets.h
https://raw.githubusercontent.com/pret/pokefirered/master/src/data/pokemon/tmhm_learnsets.h
https://raw.githubusercontent.com/pret/pokefirered/master/src/data/pokemon/evolution.h
```

These are sources for a generated legality catalog, supplemented by actual acquisition/evolution/resource rules. For example, the inspected FireRed Butterfree learnset places Stun Spore at level 14 and Sleep Powder at level 15. Earlier casual examples with underlevel Sleep Powder should not enter the implementation.

### S9 - Save serialization

`https://raw.githubusercontent.com/pret/pokefirered/master/src/save.c`

An inspection entry point for save sections, checksums, and write/load behavior. The existence of this file does not establish that spare save space is safe to use. The save marker and migrations require a real audit and tests.

## What is not yet verified

No source commit was built for this handoff. No RAM mailbox address, save extension, ROM patch, mGBA bridge, emulator package compatibility, trained policy, token price, latency claim, or balanced campaign roster has been established experimentally.

All architectural algorithms, budgets, prompts, suggested thresholds, and milestone gates in this package are project design proposals unless explicitly marked as a source fact. The handoff validation report only covers the included files.
