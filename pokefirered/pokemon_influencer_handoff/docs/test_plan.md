# Testing, evaluation, and release gates

**These are required future tests, not tests already performed.** `evidence/handoff_validation.json` reports only the reference package checks.

## 1. Test layers and evidence labels

| Layer | What it establishes | What it does not establish |
|---|---|---|
| Handoff validation | Files, reference schema/examples, selected config consistency | Working game code |
| Host unit/property tests | Pure rules and state transitions on controlled inputs | Correct ROM hooks |
| Host integration tests | Database, protocol parser, jobs, model fallbacks | Actual emulator behavior |
| Build checks | Source compiles, layout fits, baseline matches when appropriate | Gameplay progression |
| Emulator tests | Actual patched ROM/bridge works in specified scenarios | Complete campaign quality |
| Manual QA/playtests | Visual legibility, narrative continuity, usability, fun | Exhaustive formal correctness |

Evidence records include commit/build IDs, configuration, versions, command, timestamp, seed, expected/actual result, artifact paths, duration, and pass/fail/blocked status. Never turn a skipped capability test into a pass.

## 2. Baseline and build tests

**BUILD-01:** clean baseline build matches its documented target checksum; modified builds have separately recorded hashes.

**BUILD-02:** reproducible build from locked inputs on the supported environment. Record any nondeterministic metadata and eliminate it from release outputs where appropriate.

**BUILD-03:** mailbox structures have checked size/offsets; linker output and runtime canaries show no collision with existing data, heap, or stack.

**BUILD-04:** safe text rendering, save extension, trainer bindings, feature flags, and generated catalogs are included in the actual ROM and match the host manifest.

**BUILD-05:** enhanced features disabled still permit normal baseline boot, battle, and story progression for excluded battle types.

## 3. Unit and property tests

### Events, memory, and social delivery

**MEM-01:** duplicate first-win events yield one follow edge and one original-win effect.

**MEM-02:** unrelated NPC receives no private battle or catch information; filtering happens before model context assembly.

**MEM-03:** a public post without delivery/access does not update a named NPC's beliefs.

**MEM-04:** ten reposts from the same origin do not count as ten independent observations.

**MEM-05:** old predictive beliefs can weaken while their historical supporting events remain unchanged.

**MEM-06:** contradictory evidence updates uncertainty without rewriting a true earlier event.

**MEM-07:** hostile/story-exception trainers use their explicit follow/relationship policy.

**MEM-08:** a commenter cannot reply to an invisible parent; a private event cannot be published through an unauthorized template.

**MEM-09:** attempted prompt injection in a handle/post is data and cannot invoke an extra tool or alter rules.

### Roster legality and restraint

**ROSTER-01:** underlevel moves fail; include Butterfree Sleep Powder below level 15 for the pinned inspected rules, then derive the final fixture from the locked catalog.

**ROSTER-02:** an off-region species with no acquisition grant fails even when its type is an excellent counter.

**ROSTER-03:** four repeated losses with no new milestone create no extra growth epoch, capture opportunity, or IV/nature reroll.

**ROSTER-04:** at most two changed move slots across existing partners; automatic level-up moves cannot bypass the budget.

**ROSTER-05:** signature/original lineage constraints survive evolution and repeated preparation; new IDs cannot disguise replacing an existing partner.

**ROSTER-06:** a valid evolution is allowed without requiring the evolved species to be a wild local encounter; invalid method/resources fail.

**ROSTER-07:** TM compatibility without a permitted source/resource does not authorize a move.

**ROSTER-08:** changing a private player party with identical authorized evidence produces the same candidate list and committed plan for the same seed.

**ROSTER-09:** plan/reward/opportunity IDs are idempotent; replay and repeated feed openings cannot reroll a capture or team.

**ROSTER-10:** missed epochs permit bounded level catch-up but never stacked captures, move budgets, invitations, or payout tokens.

**ROSTER-11:** no legal new candidate produces a retained legal plan, not an exception that skips validation.

**ROSTER-12:** original large parties are not silently truncated by an early stage cap.

Run seeded randomized candidate tests across every implemented archetype, region predicate, stage, species/evolution family, and resource class. Suggested starting suite: 250 generated cases; release target: at least 10,000 diverse candidate cases, plus all known regression fixtures. Count diversity/coverage, not only repeated easy passes.

### Rematches and progression

**REMATCH-01:** first defeat before region gate follows but does not unlock an early rematch.

**REMATCH-02:** first defeat after the gate creates one current opportunity, not historical tokens.

**REMATCH-03:** out-of-order badges preserve explicit region predicates and stage caps.

**REMATCH-04:** player loss returns to the same ready plan; player victory closes and pays once.

**REMATCH-05:** VS Seeker/direct interaction/PokeBook do not independently create duplicate enhanced rematches.

**REMATCH-06:** ignoring a challenge never blocks a required story path or key item.

## 4. Battle-policy tests

**AI-01:** every returned candidate exists in the current legal set; stale candidates cannot execute.

**AI-02:** zero PP, forced moves, recharge, trapping, fainting, no available switch, and Struggle are handled correctly.

**AI-03:** mutate hidden opponent moves, items, exact stats, boxed party, and selected player command while keeping the sanitized observation fixed. Policy output with the same seed must remain identical.

**AI-04:** an observed move updates knowledge only after its reveal. Shared historical move knowledge requires a valid exposure record.

**AI-05:** the policy does not consume the game's damage RNG; replay remains consistent with recorded decisions.

**AI-06:** utility rankings behave sensibly on authored tactical fixtures without requiring an unmeasured claim of optimal play.

**AI-07:** switching does not loop pathologically; survival tactics still work when switching is the only valid option.

**AI-08:** items and forced replacements are tested independently of ordinary move choice.

**AI-09:** unsupported special/double/wild/link/Safari modes take their explicit safe original path, and do not send malformed enhanced requests.

Compare policies under identical roster, observations, rules, and seeded scenario sets. Report win rate with sample size/uncertainty, illegal proposal rate, timeouts, decision latency, repetitive behavior, and resource use. A higher win rate alone does not justify unfair or frustrating behavior.

## 5. Protocol and failure-injection tests

Test wrong protocol/build/catalog, truncated header, oversized body, bad integrity check, invalid action, duplicate payload, conflicting duplicate identity, stale observation, stale plan, old session nonce, reset mid-request, partial socket read/write, disconnect, backpressure, and event queue overflow.

Run a real emulator test where the host reply is intentionally delayed beyond the ROM deadline. Confirm the ROM advances legally, and the late action cannot affect the next turn. Repeat during fainting/replacement and at battle end.

Test 1x play and available fast-forward modes. Report added latency and fallback rates by speed rather than claiming a single latency number covers all configurations. No inference work may run synchronously inside an emulator frame callback.

## 6. Save and timeline tests

**SAVE-01:** normal in-game save/load restores corresponding followers, feed, beliefs, and committed roster versions.

**SAVE-02:** loading an older paired checkpoint excludes future posts, captures, friendships, awards, and memories.

**SAVE-03:** two divergent branches cannot see each other's future evidence even if event counters overlap.

**SAVE-04:** crash after event commit but before acknowledgment does not duplicate effects on retry.

**SAVE-05:** crash at each step of checkpoint preparation/publishing preserves the previous valid pair.

**SAVE-06:** a host database ahead of the ROM marker branches correctly; a database behind the ROM marker does not fabricate missing events.

**SAVE-07:** missing/corrupt database, incompatible schema/content, wrong ROM, and invalid marker produce a recoverable warning without destroying game data.

**SAVE-08:** managed emulator state load includes the intended battery-save behavior; independent raw states are either detected/rejected or explicitly unsupported.

**SAVE-09:** two playthroughs with identical player names remain isolated by save IDs.

**SAVE-10:** migration copies/backs up data before transformation, validates results, and preserves a rollback path.

## 7. Model behavior and cost tests

Use a fake provider in ordinary CI. Cases: valid proposal, invalid JSON, unknown candidate ID, unsupported fact, instruction injection, refusal, empty answer, oversized answer, timeout, rate limit, authentication error, malformed tool call, and budget exhaustion.

Every case must return a safe deterministic result or no-op without blocking the campaign. Test token/call/spend limits, zero-cost mode, missing price configuration, limited repair attempts, and caching keyed by branch/context/prompt/policy versions.

Recorded model outputs are replayed, not regenerated, during deterministic scenario tests. A provider claiming deterministic seed behavior is not a substitute for storing the selected output.

Human review samples dialogue for factual consistency, character identity, repetitive wording, tone, unsupported species/items, and whether social consequences are intelligible. Essential facts use typed slots/templates. Track rejected/rewritten generated text; do not treat every accepted schema as semantically correct.

## 8. Playable vertical-slice acceptance

Run the complete story in `PLAN.md` on the actual patched ROM and the supported emulator:

New game -> starter -> configured ordinary battle -> first follow -> optional post -> limited delivery -> Boulder Badge -> committed rematch -> actual adapted battle -> win/reward -> save/reload.

Repeat with all three starter choices and with posting declined. Include a player-party change after the invitation. Repeat with LLM disabled. Kill/restart the local runtime at safe and unsafe moments to verify documented behavior.

Evidence includes screenshots or video at key states, event/plan traces, exact builds, save-pair hashes, and a report distinguishing automation from manual actions.

## 9. Campaign compatibility and visual QA

Audit all enhanced trainer IDs against original script bindings. Special/story battles have explicit exclusions or tested integration. Inspect Pokédex-dependent rewards, key items, Cut/Surf access, rival battles, Rocket sequences, Gym flags, League entry, defeat/whiteout, and first Champion completion.

Use an exhaustive manifest of story milestones and region predicates. The release test plan includes at least one full playthrough per starter path plus targeted alternate Gym-order and optional-content tests. Automated route checks can supplement, not replace, manual exploration of dialogue and softlocks.

Check UI with maximum-length allowed handles, punctuation, Pokemon names, empty feeds, many followers, full challenge lists, unsupported characters, text-control bytes, and long translated/generated strings. Verify pixel width and page count in the actual game font. A screenshot that shows readable text is required; valid Unicode alone is not enough.

## 10. Balance and player experience

Keep the main adventure optional with respect to PokeBook posting and rematches. Review time spent in menus, notification interruptions, required backtracking, clarity of why an NPC knows something, trainer identity continuity, and perceived fairness.

Compare the same original and prepared trainer under a fixed set of reasonable player teams. Report level changes separately from strategic improvements. Do not optimize merely for causing player losses. A desirable rematch may be more interesting while remaining winnable.

Ask testers to explain an NPC's knowledge and preparation without seeing debug tools. If they conclude the trainer read their hidden party, investigate either actual leakage or insufficiently visible causality.

## 11. Release checklist

- Locked source/toolchain/emulator/runtime/content versions and reproducible build instructions.
- Local base revision/hash verified; wrong-base patch application rejected clearly.
- Patch reconstructs the expected target hash from a user-supplied supported base.
- No copyrighted full ROM, user saves, API keys, private logs, or unreviewed downloaded assets in the release archive.
- Every enhanced trainer has a binding/profile/predicate; every excluded special mode has a safe path.
- All critical legality, privacy, timeline, reward, and timeout regressions pass.
- Real complete campaign tests and screenshot reviews recorded; remaining limitations disclosed.
- No-cloud mode completes the campaign; model provider configuration is optional and documented.
- Install, launch, save backup, restore, reset-social-profile, and upgrade tested on a clean supported environment.
- Endgame flag remains off; reaching Champion does not invoke unimplemented content.

Passing means the documented supported configuration met the recorded tests. It is not a guarantee of zero undiscovered bugs or universal emulator compatibility.
