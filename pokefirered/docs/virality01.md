# VIRALITY-01 — deterministic public diffusion and faction intelligence

Scope: host social-distribution/evidence quality only. No model calls, emulator
launch, ROM edits, Strategy regeneration, team selection or resource spending.
The accepted WORLD/MEMORY/SOCIAL/HERMES/POKEBOOK/preparation/battle layers are
retained. New versioned history is additive; historical SOCIAL1 reducers,
configuration hashes, paired checkpoints, model profiles and memo/lock identities
are unchanged.

## Distribution contract

`config/virality_policy.json` is authored opening balance version
`opening-virality-1`, source-bound to pret revision
`037335f4c725d7c9aecdac87066f2002b4bd7e14` and the accepted trainer registry.
It binds actual native source IDs, stable map IDs and map group/number pairs.
Policy validation verifies those bindings against pinned local source/registry.
Native encounter IDs determine prominence, including Rival/Champion and
Giovanni story families sharing a persistent actor. Prose and names cannot
classify events. Scouts have explicit source-bound role memberships; Rocket
member/leader assignments are separate privileges.

Qualified campaign order is Pallet (0), Route1 (1), Viridian/Route2 (2),
Viridian Forest (3), Pewter/Gym (4), Route3 (5), MtMoon floors (6), Route4 (7).
These are authored progression positions, not spatial coordinates, adjacency,
or observations of the player's location. Native-ID origin bindings distinguish
encounters in a shared identity family. An unqualified origin remains unknown;
no remote map is invented. Later campaign order/content qualification remains
work for a future pack.

| Player active incoming followers | Ordinary discovery budget | Stage window | Breadth |
|---|---:|---:|---|
| 0–4 | 2 | 1 | local |
| 5–19 | 12 | 3 | district |
| 20+ | 64 | 7 | qualified region |

Counts use unique registered incoming edges on the active social timeline;
inactive, duplicate, unknown and abandoned-future edges do not count. This is
player fame, not a second arbitrary fame meter. Budgets are maxima, not required
recipient counts. Candidate ranking uses campaign distance, graph distance and
stable actor ID. No randomness, matchup information or strategic conclusions
participate. Graph paths describe known relationships, not fabricated reposts.
Direct author-follow relationships are honored separately.

Trusted Gym/Rival/E4/Champion/Rocket-leader posts have a 64-recipient discovery
budget/window7 independent of follower count. For an unqualified high-profile
origin, discovery may reach actors with qualified encounter positions; its
origin/distance stays unknown in quality descriptors. No unqualified ordinary
actor is invented to fill the budget.

Gym trainers, Gym Leaders, Rivals/Champion, E4 and Rocket leadership monitor all
supported public player trainer recaps, independently of follow edges and
ordinary discovery. Scouting delivery is access. Knowledge still requires an
explicit exposure receipt. Scouts see Rick's original public claim as a report,
never as a direct personal observation or omniscient canonical fact.

## Lifecycle and storage

`virality/store.py` adds append-only ACTIVATED/EPOCH/FEED/EXPOSURE/INTEL/TICK
history with its own branch parent cutoffs, save cutoffs, snapshot hashes and
restore epochs. Existing paired saves adopt empty virality state, without
retroactive rewriting. `activate_virality()` is explicit. Existing publications
are adopted only at the first explicit domain distribution tick. Subsequent
new publication and confirmed battle-completion transactions trigger the scheduler
automatically, including Rocket intelligence before any public recap exists. Explicit
publication, battle-completion, progression and exposure ticks can advance
remaining bounded work. Reading the player viewer or an actor context is pure.
No background polling loop, wall-clock timer, socket callback inference, or
viewer-open trigger was added.

Each post freezes follower count, branch/social/memory/virality scope, graph,
reach policy and publication order at its **first distribution epoch**. New
followers do not redistribute it. High-profile posts also have one epoch; no
trending/resurfacing lifecycle is implemented. Delivery and exposure are
separate log records and can be advanced separately (`expose=False`). Default
publication scheduling records exposure after delivery without player input.
Maximum work per tick: four new posts, 128 public exposures, 128 internal
intelligence receipts. Remaining exposure/intelligence work waits for a later
meaningful domain tick. Empty/repeated ticks produce no duplicate effects.

Public exposures deliver only exact published evidence IDs through the existing
`post_exposure/pokebook` primitive. Public provenance stops at the published
report. The old actor API and new scheduler reuse each other's receipts in both
orders. `ViralitySocialActor` provides compatible metadata/body retrieval while
maintaining the unread/body boundary. Trusted host factories have actor
parameters; consumer methods do not gain arbitrary SQL or other actors' grants.

New and already-open legacy writers are rejected for a virality-enabled database
so they cannot bypass its save pairing. `ViralityStore`,
`ViralityPuppeteerStore`, and optional `ViralityBattleStore` compose the matching
accepted foundation writer. Native battle manifest checks remain unchanged.
Restore performs no propagation. It restores all cutoffs, revokes prior grants,
and branches host-only work from the correct parent prefix. A queued call must
present its captured `expected_scope`; an abandoned/old restore epoch cannot
commit. All receipts and epoch creation are transactional; interruption rolls
back both memory and virality history.

Balance hashes are pinned at database adoption. A changed file is rejected with
an explicit migration requirement rather than rerolling old epochs. Future
balance/content versions require an explicit reviewed migration/new-policy
adoption; this ticket does not silently update existing campaigns.

## Evidence quality and Rocket contract

`schemas/social/evidence_quality.schema.json` defines host-owned DIRECT/HIGH/
MODERATE/LOW source quality and CURRENT/RECENT/OLDER relevance. Descriptors carry
source and original-source actor, direct/reported attribution, channel, original
campaign stage, campaign distance, graph degree/path, publication lag/order and
independent-origin count. Direct observations are DIRECT. Original scouting/
follower public sources and Rocket internal sources are HIGH. Longer social
paths may reduce quality. Unknown/far/older origins reduce relevance without
reducing original-source scouting fidelity. These labels are deterministic,
not calibrated probabilities or claims that old observations became false.

Corroboration traces exact same-claim lineage to its original actor/battle.
Forwarding one source does not create a second independent origin. Retrieval
filters to the actor's authorized receipts before ranking. Newer nearer reports
surface first; older records remain in immutable memory and paginated retrieval.
The 64-record/24,576-byte Strategy projection explicitly reports truncation.

Rocket intelligence requires an explicit member source, explicit leadership
recipient, active legitimate direct battle observation and active branch scope.
Completed member battles produce exact same-claim receipts through the private
`ROCKET_INTEL` channel, independent of public publication. Members' unrelated
private episodes, director memory, unseen party/moves/items/stats, future input
and RNG are excluded. Non-Rocket recipients cannot request this privilege.
Private receipt provenance retains the original observed claim, with full
organizational fidelity and no ordinary social-distance penalty.

The four-claim domain fixture simulates observed Bulbasaur, Tackle, Pidgeotto
and Potion; its public subset is only Bulbasaur. Leadership receives all four
through the typed authorization adapter, and hidden-field/nonmember/nonleader/
wrong-campaign/wrong-branch inputs are rejected. This is **not a live Rocket
battle**. Existing native MEMORY fixtures additionally prove durable internal
receipt, restore, replay and non-Rocket isolation. Native player-item observation
export remains unqualified: Potion in the domain fixture is not evidence that
FireRed currently exports player item announcements.

## Strategy integration

`strategy/social_context.py:build_social_evidence` constructs an additive
StrategyContext v3 social section with typed, validated quality descriptors,
authorized claim references/attribution, unknowns and no strategic conclusion.
It retrieves actor evidence before scoring. Existing StrategyContext v2 schema,
prompt/config hashes, frozen StrategyMemo and preparation commitments remain
unchanged. Future inference must explicitly adopt a new context/prompt version;
no model adapter consumes this extension automatically and no memo is
regenerated here. SUBJECTIVE strategy remains separate from AUTHORIZED FACTS.

## Proof and reproduction

`tools/virality01.py` copies the closed, WAL-free accepted HERMES-01 closeout
snapshot into a fresh ignored `.local` database. It verifies an actual completed
Rick native battle/public recap, Rick's private Tackle observation, and no prior
Brock encounter. No new playthrough is claimed. Brock first gets unread scouting
metadata and no knowledge; explicit exposure yields exactly the published result
and Bulbasaur claims with HIGH quality, Forest→Pewter relevance and reported
original-post provenance. Tackle and hidden party never enter his context. No
follow is invented. Canonical history, legacy social state, director episodes
and source database bytes remain unchanged. A fresh host retrieves the identical
packet; restoring the old native pairing excludes later virality adoption and
rejects the old job grant.

`evidence/phase4/virality01/` holds production source/post/epoch/packet and 21
assertions, labeled follower and Rocket fixtures, regression logs, protected
input verification and completion. Baseline39 social, earlier295 subset, full466
host tests and final30 focused tests passed with no skips; the full run collected
26 virality cases before final refinements, all rerun by the final focused suite.
21 production and26 artifact checks passed, and2,423 protected inputs match.
The accepted native ROM checksum is unchanged. The native writer composition
opens/replays an isolated copy, including copied closed WAL/SHM sidecars; original
files stay byte-identical. The retained handoff reference package checker also
passes independently; it does not validate the new engine. Constructed battery/native-message fixtures
prove post-exposure pairing, prepost rollback, child-branch divergence, Rocket
cutoffs, reach rollback, stale jobs and replay; these are host save tests, not
new native saves or emulator reloads.

Exact successful commands (repository root):

```sh
python3 -m unittest discover -s tests -p 'test_social01.py' -q
python3 -m unittest discover -s tests -p 'test_virality01.py' -q
python3 tools/virality01.py --destination .local/virality01/accepted-final-v5.sqlite3
python3 tools/verify_virality01.py
python3 pokemon_influencer_handoff/tools/validate_handoff.py
python3 -m unittest discover -s tests -p 'test_*01.py' -q
python3 -m unittest discover -s tests -v > evidence/phase4/virality01/host-tests.log 2>&1
```

The production command requires the original accepted private snapshot and a
fresh destination. It deliberately refuses existing destinations/live WAL
sources. Initial setup had a config-generator KeyError on a non-VS-Seeker
family, Rival/Champion classification test failures, a corrected indentation
error, a recency-ranking failure corrected by battle-origin publication order,
and an audit command using nonexistent `checkpoints.save` instead of
`save_identity`. The optional composition probe first rejected existing WAL sidecars, then used
byte-verified copies of the closed source/base/WAL/SHM set. The old handoff-checker
path was missing; its retained reference-package path was used instead.
These failed attempts are not acceptance proofs; final commands
above supersede them. Private exploratory copies remain ignored.

Remaining limits: future geography/profile/content qualification and balance
migration; integration of the composed writer with the continuous managed
campaign launcher; native player-item observation qualification; broader battle
mode/item/latency coverage; cross-process/power-loss and future real Rocket/Gym
playthrough qualification. Host-side application grants are not isolation from
arbitrary Python code. Whole-tree `git diff --check` reports pre-existing trailing whitespace at
`src/new_menu_helpers.c:670`; that unrelated native source was left untouched.
No hosted/model configuration changed. Endgame remains
deferred. See the revised readiness note; do not implement it under this ticket.
