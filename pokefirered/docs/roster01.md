# ROSTER-01 — source catalog and pure prerequisite services

Implemented ROSTER-01 only. No team selection, optimization, captures, growth, inventory debits, commitment, installation, rematches, strategy, System One or new inference. No ROM/gameplay source, save format, bridge or permanent RAM change. The host library is internal tooling, not an unrestricted NPC data tool. POKEBOOK/HERMES acceptance and stop conditions remain intact.

## Reproduce and verify

From the repository root, with the existing pinned tools available:

```sh
.venv/bin/python tools/roster01.py --write
.venv/bin/python tools/roster01.py
.venv/bin/python tools/roster01_examples.py
.venv/bin/python -m unittest discover -s tests -v
```

The first command generates **and verifies** the catalog. The second independently regenerates it and rejects stale output. Both compile effective C initializers, validate the schema, regenerate the item/wild headers in temporary storage with the existing jsonproc tool, compare them with the working/generated and accepted build headers, inspect actual ARM ROM tables, and run the actual native default-move functions through a host C accessor harness. Missing source/tools/accepted artifacts fail visibly. No network or credential is used. This is not a new ROM build or emulator run.

Pinned pret source: `037335f4c725d7c9aecdac87066f2002b4bd7e14`. Effective target: FIRERED, English, revision0, MODERN0. Existing bridge/events/UI feature flags are unrelated to Pokémon table extraction. Matching agbcc pin remains `da598c1d918402c42c0c0d7128ba14567f3175e9`. Current ROM association remains `bec6245f354e0846a9e606ba0665d9dabc2e4f9825ba278342755143de56e829`.

`config/roster_catalog.json` and `evidence/phase3/roster01/extraction-manifest.json` record source-file digests, pinned-file digests, effective dirty inputs, target, extractor/schema versions, generated headers, compiler/extractor hashes, content identity and qualified coverage. Policy has a separate hash. The accepted event hooks in battle_main are recorded dirty; they are not concealed by reporting only a Git commit. Registry provenance remains a separate generated host identity authority.

Content serialization/order is deterministic and timestamp-free. Content-addressed catalog/policy copies preserve accepted identities. UI files such as pi_pokebook/start_menu are excluded from mechanics; tests prove a UI-only edit has no effect and a learnset edit invalidates the catalog. Whole audited behavior-file fingerprints are conservative: an edit within pokemon/battle_main/party_menu can require review even if it ultimately proves harmless. Unsupported generator/config/layout changes and unfamiliar table conditionals fail closed pending an adapter audit. A new mechanics catalog does not migrate or weaken WORLD's exact ROM/save compatibility guards.

## What is extracted

412 species table slots,355 move records,743 trainer records,375 item slots and2,176 selected FireRed encounter slots. These counts include sentinel, unused, old Unown and dummy trainer records; lookup rejects non-playable species/unused items. Broad extraction does not authorize campaign content or endgame. Actual stable identity mapping/families reuse `config/trainer_registry.json`; display names do not join people.

C compilation resolves constants, aliases, preprocessor branches, default-zero fields, party flags, TM/HM masks and learnset termination. Learnset pointer aliases are retained, including NONE's Bulbasaur pointer without making NONE playable. JSON wild selection follows the audited generator's version branches; LeafGreen records are excluded. Map/method/slot/rarity/level/equipment references survive. Non-map specialty groups do not become regular acquisition routes.

Species metadata includes base stats/types/abilities/catch/growth, ordered level learnsets, compatibility and all evolution method/parameter/target slots. Move metadata includes type/power/accuracy/PP/effect/target/priority/flags. Items retain source use callbacks, battle usage, held effects, price and pocket; unused slots have an index distinct from their declared ITEM_NONE. Teaching mappings come from the actual `party_menu.h:sTMHMMoves` array and are checked against item JSON and ROM. Trainer records retain variant identity, flags/class/AI flags/battle items, authored party slots/levels/IV source/fixed-IV conversion/held items and custom-vs-default moves.

The catalog does not simulate damage, compute new individual nature/IVs, or create a campaign-wide authorization database. Native personality construction uses encoded trainer/species name hashes; no stats or identity are rerolled here.

## Three authorities

1. Extracted mechanics say what the selected source supports.
2. `config/roster_policy.json` binds authored territory/restraint and identifies missing content.
3. A trusted host supplies immutable `Context` ownership/history/inventory/earned named milestones/epochs and active scope. It is not a model request or a new world writer.

The actual handoff defaults live at `pokemon_influencer_handoff/config/campaign_defaults.json`, rather than AGENTS' older root path. The policy references its digest and copies existing adaptation limits without new tuning. The specialist handoff documents likewise live beneath `pokemon_influencer_handoff/docs/`. D22 supersedes their older model-selection flow; no candidate ranking is implemented.

Rick102 resolves to world ID `fr:trainer:0102` and existing actor ID `trainer:fr:trainer:0102` (using `memory.store.actor_id`), home Viridian Forest. The minimal authored early binding identifies Forest land encounters as native and Route2 as nearby, requiring a separately issued `permission.rick.route2`. This is a classification, not an automatic travel grant. No connection-chain traversal grants access. Pewter's Brock414 resolves to world ID `fr:trainer:0414` / actor `trainer:fr:trainer:0414`; Rock is represented as his baseline/target theme. Onix slot1 is a source-backed **signature candidate**, pending explicit CONTENT-01 binding. Other areas and actors remain unqualified/off-region, never freely accessible.

Production policy deliberately has no per-trainer stage targets, initial inventory, earned opportunity issuer, exceptional acquisition issuer or Gym mixed-support caps. Named badge caps alone are insufficient. Growth returns `missing_trainer_stage_target`; Gym identity returns `missing_gym_support_bounds`. Capture additionally requires known campaign/opportunity counts/spacing, earned epochs, capture permission and finite balls. Unknown history is not zero/unlimited. The first epoch cannot capture. Capture eligibility is permission to attempt, not capture success or whole-team legality.

Fixture-only profiles demonstrate before/after Boulder/Cascade/Rainbow levels using the existing proposed stage caps and existing four-level epoch limit. Fixture targets, inventory and permissions are explicitly hypothetical; a fixture policy cannot bind a non-fixture context. No fixture was installed into the campaign or source. CONTENT-01 must own actual reviewed profiles and named predicate issuers before PREP uses them.

## Individual histories and narrow baselines

Rick's Weedle6 defaults to Poison Sting/String Shot; Caterpie6 defaults to Tackle/String Shot. Default construction uses the **ordered** source table, stops at the first higher learning level, skips already-known moves and removes the oldest when full. It is not an evolution-family union or free relearn. Brock's Geodude12 and Onix14 use custom authored moves; Onix's Rock Tomb is preserved as an authored slot, not inferred from its level learnset.

A baseline origin binds exact source trainer variant, slot and source property. Actor mismatch, forged move snapshot or a different slot's origin fails. All authored custom moves are scoped retention facts, including281 properties not present in that species' at-level learnset. That diagnostic is not a claim they are illegal: a TM/tutor/authored source can explain them. They never grant general teaching resources or exceptions to other individuals.

A supplied trusted companion history is replayed from exact baseline or a version-specific wild route. Supported recorded history is bounded level growth, direct level evolution and a move learned at the exact species/level. Unsupported recorded acquisition methods fail rather than accepting model prose. Future teaching receipts and a persisted companion-state issuer remain PREP/ROSTER-02 work. The library is not that issuer.

Retained pre-evolution Tackle/String Shot survive Caterpie→Metapod→Butterfree without becoming free relearn options for every Butterfree. A move from another family member is blocked without its actual path. Wild Metapod below the Caterpie evolution threshold is valid owned provenance; thresholds govern a **new evolution**, not every existing evolved individual.

Pinned Butterfree boundaries are Stun Spore14, Sleep Powder15 and Gust28. Tests check each just below/at its learning level under clearly labeled lawful-source stage fixtures. Future moves need an earned growth path and learning permission; missed old moves are not freely available. Four slots, duplicate moves and edit budgets are checked by the element validator, while PREP must aggregate the two-slot budget across all companions.

Level evolutions require an actual subsequent leveling trigger, owned lineage and earned stage/growth permission. Item evolution requires the actual finite stone and permission. Everstone and the native National Dex cross-generation gate are enforced. Friendship, trade, stat/personality/beauty/special evolutions and disabled day/night methods are cataloged but not qualified transition solvers. Tutors/relearners/breeding/gifts/trades/fossils/static encounters and water/fishing/Rock Smash acquisitions remain unsupported. An existing authored Pokémon never disappears because its region lacks a new-capture route.

## Resources, API and privacy

`Catalog.lookup` is internal mechanics inspection; `View.baseline` is actor-bound. `acquisition_routes/acquisition`, `growth`, `evolution_paths/evolution`, `move_paths/move`, `allocations`, `identity` and `validate_moveset` are pure query interfaces. They return allowed/blocked/unqualified, IDs, prerequisites/resource deficits, source references, catalog/policy/validator identity, scope and context digest. **fully_legal is always false**: an element proof is not whole-package approval. Unknown IDs/malformed trusted snapshots fail before lookup. A witness string or supplied reference cannot create permission; move proofs are checked against trusted current lookup/state.

Separate finite allocation categories are held, battle bag, teaching, evolution and capture. Duplicate consumable reservations fail. TMs consume one; HMs are reusable teaching equipment. Native IsMoveHm excludes Dive from the seven protected HM moves; Dive teaching is deliberately unqualified rather than generalized from another game's behavior. Held-effect permission is separate from bag usage. NPC bag-item execution is unqualified even when an item is cataloged and owned. No shops/restocking are inferred; actual consumption/healing/PP/restocking remain downstream gates.

Original lineages cannot be removed. A new lineage or species transition requires its own acquisition/evolution proof and complete PREP validation. Gym mixed-type support is permitted by D22's target architecture, but production caps are absent; a one-support **fixture** demonstrates theme feasibility and rejects two off-theme additions while retaining the separate whole-package gate. No strict-monotype rule or unrestricted counter-team is introduced.

No global mutable current roster, cache, world connection, events, memory, social input, player-party data or RNG is present. Earlier and later contexts produce distinct scoped results without future-cache reuse. Reading a PokeBook claim cannot expand resources or feasibility. Complete extracted trainer parties stay internal; future NPC adapters must expose only the bound actor's own records/options.

## Verification and remaining gates

Evidence records exact final test counts/commands in `completion.json` and `commands.json`. Source agreement checks every compiled species/learnset/TM mask/evolution/move/trainer/party record, every selected encounter, item categories and teaching mappings against the unchanged accepted ARM ROM;7,184 checks. Host compilation of the three actual default-move functions checks41,200 species/level cases, substituting Box accessors/level/PP only. This does not prove encrypted construction, installation or in-game development.

No new emulator battle or ROM rebuild was required or performed. Accepted PokeBook RAM/memory evidence remains prior evidence: no new permanent EWRAM allocation. Protected source-overlay/build/dump/save/database/inference-budget checks are in `preservation.json`. Source agreement and all final host tests passed; development failures were corrected and are not counted as acceptance.

`docs/roster01_prep_readiness.md` maps outputs to the shared envelope and names missing gates. The next dependency-appropriate ticket is **CONTENT-01**: bind the qualified trainer/region/stage/resource/signature/Gym profiles needed by PREP-01. Do not start it under this authorization. PREP still owns complete envelope schemas, aggregate budgets, meaningful bounded candidates, branch-aware grants/receipts and eventual resource commit/lock; selection/installation/live legal actions belong to later tickets.

Carry forward the context limit: Hermes facts are deduplicated, not a turn transcript. Do not infer action frequency, switch sequences or timing from them. A later separately scoped exporter/context ticket would need authorized chronological actor-visible actions with battle/turn/sequence/outcome provenance; ROSTER does not reconstruct missing history. Endgame remains deferred.
