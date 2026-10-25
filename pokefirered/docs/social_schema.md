# SOCIAL-01 schema and distribution contract

SOCIAL schema1/reducer1/policy1/template1 is additive to WORLD1/MEMORY1 in the same SQLite database. `social/migrations/001.sql` creates `social_version` (exact config/catalog/registry hash), append-only `social_log`, `social_branches` (parent social cutoff), `social_checkpoints` (cutoff plus replay hash), and mutable `social_view` (selected branch/cutoff/revocation epoch). Actors and knowledge receipts remain MEMORY-owned; no parallel identity or memory tables exist. The campaign player is a reserved social target `player:<campaignUUID>`, not an NPC memory actor.

The pure reducer applies committed ACTIVATED/FOLLOW/PROPOSAL/OUTCOME/POST/JOB/JOB_DONE/TICK/FEED/EXPOSURE records. Follows, posts, deliveries, exposures and pending work are projections of this log. Canonical event time, source observation cursor, publication cutoff, distribution tick and exposure cursor are distinct. Wall-clock timestamps from the retained WORLD audit do not schedule social effects.

Installation creates empty social cutoffs for existing branches/checkpoints. Explicit activation records a canonical boundary and authored seed edges. Only completed eligible victories after that boundary qualify. No historical backfill, policy upgrade repost, retrospective subscription, automatic exposure or reputation calculation occurs. Old World/Memory writers refuse a social-enabled database, including writers opened before migration.

A first confirmed eligible defeat adds one directed trainer→player edge. Rick102 alone is eligible in versioned `config/social_slice.json`; Janice116→Rick102 is authored slice configuration. Unclassified actors and story/hostile actors are not eligible implicitly. Doug103 is outside this audience. Counts derive from actual active edges. A follow conveys neither reciprocal following nor friendship nor access to private memory.

`social/policy.py` selects one direct result and optionally one directly seen species from this battle. Service validation independently requires author ownership, current campaign/branch/cutoffs, a qualifying battle, 1–2 distinct supported claim types and public/private visibility. Proposal keys are exactly battleID/evidenceIDs/visibility/policyVersion. No arbitrary body, inference, move claim, hidden party or stat is accepted. The renderer yields at most160 UTF8 bytes, interpolates only source-backed species names, and records policy/template/config versions. At most one recap per battle. A private committed recap is author-readable and never distributed; unpublished proposals stay outside feeds. Future expression changes require a separately versioned bounded contract.

Publication enqueues a stable job and grants nobody knowledge. Explicit `tick(n)` must be the current tick (retry) or next tick. It processes at most4 jobs and8 recipients per job, ordered by post ID and follower actor ID. Public posts reach direct followers of their author only; FEED records bind tick and qualifying edge. Job completion is committed with delivery. Newly created follows enqueue no historical posts. Replays apply stored recipient decisions, never invoke a newer policy. Limits are per tick/job, not claimed total database limits.

Feed metadata returns at most32 entries with postID/author/seen/channel, without body or claims. `read_post` permits the author or a recipient with an existing exposure. Explicit `expose` requires a selected feed entry, branches if necessary, invokes MEMORY's common authorized one-claim delivery primitive for each selected source, then commits receipts and exposure in one transaction. A failure rolls back both. Receipts are delivered/reported, never firsthand observations. Internal lineage retains parent author evidence, post and exposure; recipient-readable provenance stops at the published receipt and exposes author/post/channel/attribution, not private source IDs, turn IDs or parent traversal. Querying the author's private memory ID remains denied.

Stable semantic keys cover follow edge, battle recap, recipient/post feed and exposure. Receipt IDs include campaign/branch/post/recipient/source. Repeated transport, same tick, host reopen and repeated exposure preserve IDs and counts. Append-only triggers reject history mutation. Compatibility mismatches require explicit future migration; they are not silently reinterpreted.

Trusted application code issues `SocialActor` capabilities bound to actor, campaign, branch, canonical cursor, memory cutoff, social cutoff and revocation epoch. Restores and branch changes revoke cached handles, including restoration back to the same checkpoint. Models must receive only selected bound methods; neither actor IDs in model JSON, the factory, store object, admin CLI, administrative fixture nor raw SQL constitutes authority. This is an application boundary, not a Python sandbox.

Replay fixtures are versioned, bounded administrative JSON with exact table/column allowlists and parameterized inserts into isolated SQLite. They contain full internal history and must never become model contexts. Canonical and memory reducers audit source histories; social verification audits rendered claims, author scope, graph delivery and atomic receipt lineage. Replay needs no emulator, ROM, credentials or provider.

A scoped author submission records its actual selected references and published outcome atomically alongside the recap, separately from the trigger's earlier deterministic candidate. Retries preserve those records. This is the future choice boundary; no model runtime is involved.

## Additive VIRALITY-01 contract (D36)

SOCIAL1 snapshots/reducers remain authoritative for their historical one-hop
records. Versioned `virality_log/view/branches/checkpoints` extend distribution
with frozen follower reach, native encounter prominence and explicit scouting
access/exposure. Public memory still uses exact published IDs and reported-post
provenance. Both exposure APIs reuse identical receipts; player viewer reads
stay pure. Private Rocket intelligence is a different guarded channel.
Campaign order/source-quality/typed Strategy projection, bounds and migration
rules are defined in docs/virality01.md and config/virality_policy.json.
