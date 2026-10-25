# Campaign roster adaptation and rematches

## 1. The campaign promise

**A familiar trainer becomes more prepared, not a different trainer designed around your hidden weaknesses.**

The normal order of adaptation is tactical preferences, legal moveset refinement, ordinary level/evolution growth, then an occasional plausible local catch. No improvement is mandatory; keeping a coherent team is better than forcing a mutation.

## 2. Three independent state tracks

- **Learning:** observations and tentative beliefs can update after battles or delivered posts.
- **Growth opportunities:** explicit Gym/milestone epochs authorize bounded training resources and levels.
- **Committed challenge:** a specific prepared roster with a fixed evidence cutoff, version, and resource spend.

Repeated losses affect the first track, not the second. While an invitation is pending, new observations can inform a later opportunity but cannot rewrite that challenge.

## 3. Region and progression model

Define region clusters in content rather than deriving everything from geographic distance. Each cluster specifies home maps, nearby reachable maps, travel predicates, encounter methods, original trainer bindings, first-rematch unlock predicate, later qualifying milestones, and stage targets.

Suggested early clusters: Viridian/Forest/Pewter, Route 3/Mt. Moon/Cerulean approaches, and Vermilion approaches. These are design groupings to verify against actual routes and script access, not automatic permission to catch everything in a similarly named area.

Use predicates such as `badge.boulder == true` and explicitly authored story flags. Do not assume badges must occur in a fixed numeric order. Later-stage cap selection uses the approved earned milestone table; access uses named predicates independently.

A trainer's world access is not the player's access. NPC travel/resources are separately authored. The player obtaining Surf does not grant every Bug Catcher a fishing trip or a Water starter.

## 4. Habitat catalog

Export version-specific encounters from the pinned source. Preserve source path/commit, map, method, min/max encounter level, species, encounter rarity, and required access/tool predicates. Exclude encounters for other game versions from the selected catalog.

Intersect candidates with:

```text
ROM-supported species
 AND reachable map/method at trainer's permission level
 AND archetype identity
 AND capture/resource budget
 AND allowed campaign acquisition tier
 AND level/evolution legality
 AND active/reserve roster limits
```

### Tiers

| Tier | Meaning | Campaign default |
|---|---|---|
| Native | Home-cluster encounter under permitted method/access | Preferred |
| Nearby | Explicit reachable adjacent-cluster permission | Secondary |
| Accessible | Farther location/trade/gift with a validated acquisition grant | Disabled without a grant; rare authored exception |
| Exceptional | Unusual special acquisition with dedicated story authorization | Disabled without a grant; not procedural |

An existing partner can evolve through its own legal lineage even when the evolved species is not a wild local encounter. Evolution is not a new capture. Stone/trade/friendship/other methods need their own resources or conditions, not just the target species ID.

Do not invent "local" Scyther, Pinsir, Lapras, or starter access from narrative vibes. If the content team wants a new habitat, that is a separate explicit game-data change with its own review and player availability implications.

## 5. Stable Pokemon identity

Each NPC-owned Pokemon receives a stable individual/lineage ID. Evolution preserves it. Keep provenance, acquisition epoch, current species/level, nature, IVs, EVs, ability identity where relevant, moves and how each was learned, and permitted held item.

Do not recreate the entire party with new random IVs/natures on each fight. Party construction should faithfully instantiate the prepared records using the game's safe APIs. The first implementation may retain fixed authored IV/EV values; it must not quietly "improve" them after losses.

A prepared challenge defines the encounter-start condition, including full healing/PP according to normal trainer-battle behavior. This does not imply that cross-battle damage must persist indefinitely. The lineage is persistent; encounter healing is a separate rule.

## 6. Initial restrained change budget

All values below are initial tuning defaults in `config/campaign_defaults.json`.

| Dimension | Default |
|---|---|
| Changed move slots | At most 2 across existing partners per prepared opportunity |
| Level growth | At most 4 levels per earned training epoch, bounded by stage target/cap |
| New captures on first epoch | None |
| Later capture attempt | 25% once per eligible opportunity, before legality filtering |
| Successful acquisitions | At most 1 per opportunity, 2 in the campaign total |
| Acquisition spacing | At least 2 earned epochs between successful catches |
| Capture-tier weights | 80% native / 20% nearby after filtering; no automatic off-region tier |
| Roster replacement | Disabled in initial campaign policy |
| Signature partner | Always retained |
| Original lineage floor | All by default; general floor at least ceil(0.75 * original count) |
| Nature/IV rerolls or loss buffs | None |

Party size is bounded by the original size plus permitted additions, a data-driven stage cap, and the engine maximum. Stage caps must never delete an original authored Pokemon; either grandfather the base roster or explicitly exclude/review that trainer. Early ordinary trainers should not suddenly acquire a full team of six.

Move changes count added moves, replacements, and any automatically proposed level-up moves. Do not let auto-generated movesets bypass the two-slot budget. Retained moves are legal only if their learning history permits retention; do not assume a species can relearn every earlier move for free.

A newly caught Pokemon's initial legal moves are checked as part of acquisition; otherwise a normal four-move catch could consume more than the whole move-edit budget. That exception must apply only to the single approved new acquisition, not to recreating existing Pokemon under new IDs. Existing Pokemon's edits remain limited to two slots.

## 7. Training epochs and catch-up

Each qualifying new milestone creates one unique epoch. For level growth, missed epochs can be accounted for once each to bring a long-unvisited trainer toward its authored stage target. This is independent of player loss count and current party level.

Structural budgets do not stack: revisiting after four missed badges does not authorize four new catches, eight move edits, four pending invitations, or four rewards. Use one current preparation opportunity with the normal structural budget. Track the number of eligible level-growth epochs applied, separately from successful rematches and acquisitions.

Suggested level rule:

```text
new_level = max(old_level,
                min(authored_target_for_trainer_and_earned_stage,
                    earned_stage_cap,
                    old_level + 4 * unapplied_growth_epochs))
```

If the target/cap is below the original level, do not delevel an authored trainer silently; flag the content profile for review. Exact late-return targets should be tuned so a return encounter is neither trivial nor compulsory grinding.

## 8. Candidate generation and selection

1. Load the existing owned team, trainer identity, current committed plan state, and permitted epoch.
2. Snapshot authorized evidence at `evidence_cutoff_seq`; never inspect the player's current hidden party.
3. Apply deterministic level/evolution candidates within resources and limits.
4. Generate move edits from legal learning sources and training availability.
5. Optionally attempt one native/nearby acquisition using a seeded, recorded attempt; no repeated rerolls on UI open.
6. Produce a bounded list of complete candidate plans, including a no-change option.
7. Reject illegal candidates before ranking.
8. Rank with identity, general competence, small evidence-based adaptation, and disruption/resource penalties.
9. An optional NPC LLM selects among legal candidate IDs and explains strategy intent; it cannot add candidates with arbitrary species or moves.
10. Atomically commit plan, resource spending, epoch use, and optional challenge post. Freeze the roster.

Recommended initial normalized objective:

```text
0.50 * general_team_coherence
+ 0.25 * identity_continuity
+ 0.15 * observed_opponent_fit
+ 0.10 * personality_fit
- disruption_cost
```

These weights are a design starting point. The adaptation term is deliberately smaller than general competence and identity. The planner cannot overfit a perfectly known current player lineup because it does not receive one.

## 9. Legal moves and resources

A move is eligible only if the selected ROM rules support the species/move combination at the current level/history and the NPC has a permitted learning source. Include level-up, evolution history, TM/HM compatibility, available tutor/trade/gift sources, and any deliberate content changes.

TM compatibility alone is insufficient: the trainer also needs access and budget. The initial campaign can disable optional TM/tutor optimization until acquisition/resource catalogs are implemented. Rare expensive coverage must not appear for every low-resource trainer.

Item legality includes possession, stage availability, archetype budget, and consumption rules. More losses do not generate free healing items. Initial ordinary rematches can keep baseline battle items unchanged.

## 10. Worked example: illustrative forest specialist

The reference character "Reed" is an authored example, not an assertion about a vanilla trainer ID. Bind it to a verified trainer or explicitly add it during content work.

Initial team:

```text
reed.partner.1: Caterpie, level 7, Tackle / String Shot
reed.partner.2: Weedle, level 7, Poison Sting / String Shot
```

After one defeat, Reed knows the player used a revealed Fire move in that encounter. This is weak evidence for a long-term pattern, not knowledge of every Pokemon the player owns.

After Boulder Badge, an illustrative legal-growth candidate is:

```text
reed.partner.1: Butterfree, level 11,
                Tackle / String Shot / Confusion
reed.partner.2: Beedrill, level 11,
                Poison Sting / String Shot / Fury Attack
```

The individual IDs remain the same. Evolution paths and optional move retention must be simulated/validated under the pinned rules. Two added move slots consume the whole move-edit budget. No new catch is attempted on the first epoch. No Blastoise appears.

A later eligible epoch might permit a status move or a catch consistent with the trainer's actual permitted maps and archetype. In the inspected FireRed learnset Butterfree learns Stun Spore at level 14 and Sleep Powder at 15 (source S8). Underlevel Sleep Powder must fail validation; do not copy a move list from another generation.

A possible approved post: "Been training with my two partners. Ready for another round?" The post follows the committed training event; it does not create the evolution itself.

## 11. Rematch state machine

```text
UNMET
 -> FIRST_BATTLE_COMPLETE
 -> FOLLOWING_LOCKED          (region gate not yet met)
 -> TRAINING_ELIGIBLE         (gate true, epoch available)
 -> PREPARING
 -> READY                    (plan immutable; invitation created)
 -> IN_BATTLE
 -> WON_BY_PLAYER -> COOLDOWN
 -> LOST_BY_PLAYER -> READY  (same plan; no new reward opportunity)
```

Friendship is orthogonal. A trainer can follow without being a friend. `DECLINED` or `DEFERRED` is a UI disposition on the ready challenge, not a deletion of the plan.

First eligibility requires an original player victory plus the region gate. If the first victory happens after the gate is already met, create only the current opportunity. Later qualifying milestones can open a new challenge after the previous one is resolved. While a challenge is pending, do not stack future tokens; after resolution, coalesce to at most one current opportunity when policy permits.

Use stable IDs for trainer, opportunity, plan, battle instance, and reward claim. Original story-win flags are never cleared. Preserve scripted trainer follow-up dialogue and safe re-entry locations.

## 12. Rewards and anti-farming

One paid rematch victory per trainer/opportunity. Grant rewards through an idempotent transaction plus the appropriate ROM-side acknowledged operation. A repeated message must not award twice.

Keep normal battle experience behavior during the fight initially; do not promise complete elimination of experience grinding after repeated losses without adding a tested separate EXP policy. The anti-farming guarantee here concerns duplicate opportunities, repeated payouts, and roster rerolls, not every possible vanilla grinding technique.

VS Seeker, direct interaction, and PokeBook challenge acceptance must consult the same opportunity state for enhanced trainers. Unsupported legacy rematch paths require an explicit compatibility decision; do not leave two independent reward systems active.

## 13. Mandatory adversarial examples

- Four consecutive losses to Charmander with no new milestone: no new level epoch, catch, or stat reroll.
- Player swaps all boxed Pokemon after challenge commitment: prepared roster is byte-for-byte unchanged.
- Rare species is thematically appropriate but absent from permitted encounters: reject without a grant.
- Pokemon evolves in its known lineage: allowed if actual level/method/resources permit; not counted as a capture.
- Stale high-confidence rumor arrives after evidence cutoff: does not alter the committed plan.
- Every candidate violates constraints: retain the last legal plan or use a validated baseline, never bypass the validator.
- Same milestone delivered twice: one epoch.
- Skipped badges or different Gym order: predicates remain correct, with no access to an unearned region.
