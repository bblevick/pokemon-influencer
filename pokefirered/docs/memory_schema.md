# MEMORY-01 domain contract v1

Canonical WORLD schema/reducer remain v1. `memory/migrations/001.sql` installs a separately versioned, transactional additive schema (`memory_version`: schema1/reducer1). Newer or incompatible memory versions fail closed. Existing canonical history, transport deliveries, raw bounded observations and checkpoints are unchanged. The two pre-existing tables named `observations` and `deliveries` remain raw transport/source stores; they are **not** knowledge grants.

| Structure | Authority |
|---|---|
| memory_actors | Immutable `trainer:<worldTrainerID>` → existing source-backed WORLD identity |
| memory_sources | Immutable processed-source identities, including sources producing no actor evidence |
| memory_evidence | Immutable actor-owned direct evidence or one-claim targeted delivery receipt |
| memory_branches | Immutable parent subjective cutoff captured at canonical branch creation |
| memory_checkpoints | Immutable subjective cutoff paired with each native-save checkpoint |
| memory_view | Reconstructible active branch/cutoff selection; trusted host only |

MemoryStore subclasses WorldStore's transaction boundary: canonical ingestion, derived direct evidence, processed-source marking and active memory view commit together **before transport ACK**. A derivation failure rolls everything back. Canonical-only WorldStore refuses memory-enabled databases, preventing an older writer from bypassing the extension. Old WORLD databases still open unchanged; migration runs only when explicitly opened with MemoryStore. Backfill derives only justified participant evidence from retained sources and binds legacy checkpoints to evidence whose source ingestion predates checkpoint publication. No missing pre-import history is invented. The accepted WORLD database is preserved; migration acceptance uses a SQLite backup in a separate private path.

Actor IDs reuse the 580 WORLD trainer families. Rick102=`trainer:fr:trainer:0102`; Janice116/507/508=`trainer:fr:trainer:0116`. Names/party/session/branch never redefine identity. Actors are stable registry identities; evidence authorization additionally requires campaign, branch and cutoffs. Reserved future namespaces `player:<campaignID>` and `faction:<authoredID>` can be introduced by a new explicit migration; no non-trainer actor is instantiated now. Composite source trainers remain composite identities until a separately audited participant exporter exists.

## Minimal claim allowlist

Each claim contains a domain battle ID and stable participating world trainer ID.

| Claim | Additional values | Authorized producer |
|---|---|---|
| BATTLE_PARTICIPATION | None | The participant's supported trainer BATTLE_STARTED |
| TRAINER_BATTLE_RESULT | nativeOutcome | The participant's BATTLE_ENDED; native1 means player victory/trainer loss |
| POKEMON_SEEN | speciesID | NPC-side BATTLE_OBSERVATION.opponentActive.revealedSpeciesID |
| MOVE_REVEALED | speciesID, moveID | That observation's revealedMoveIDs; or explicitly announced player move/species from the audited native used-move text producer |

The source launch/run/native battle identity must correlate to the persisted canonical start and trainer. Wild encounters grant no trainer knowledge. The canonical turn/defeat record is not generically promoted. NPC action slots and player actions without an actual move announcement produce no evidence. No status/switch claims are implemented because the present exporter lacks an audited producer for them. No unseen party, unrevealed move, private player HP/PP/stat, own exact HP/moves/PP, RAM sample, internal flag, RNG, future action, personality, confidence, salience, belief or preference enters the claim/context allowlist.

Every direct record includes schema, owning actor, campaign/branch, world availability cursor, monotonic memory sequence, source kind/ID (canonical event or bounded observation), domain battle and native turn. Its deterministic ID hashes version/actor/source identity/typed claim. Sources remain resolvable in the host ledger; the actor API does not expose raw payloads. Repeated source delivery is idempotent. Repeated witnessed moves retain distinct immutable evidence; context groups identical claims/mode/sender, with bounded evidence IDs and an occurrence count **within the returned window**, without inferring favored strategy.

## Explicit delivery and provenance

`MemoryStore.deliver_fixture(...)` is a trusted development-only writer, not a model tool. It accepts one source memory ID, sender actor, recipient actor, bounded idempotency key, and exact active campaign/branch/world cursor. The sender must currently have access to that source record. It copies only that record's typed claim and references its parent provenance. No arbitrary text/claims/broadcasts/public posts/channels are accepted. Channel is fixed `development_fixture`, status `recorded`. Unsupported recipient, missing/foreign source, conflicting duplicate, stale branch/campaign, future/past cursor, suspended state, pending save or unresolved restore fork is rejected. A restored historical view must first diverge through fresh canonical gameplay before new delivery. No social delivery eligibility is invented.

Recipient provenance is a bounded same-claim chain: receipt → sender's evidence → canonical/observation source ID. It identifies each actual owner and distinguishes delivered/direct evidence. It never expands a source actor's other records or returns raw source payloads. A recipient cannot query a sender's memory ID independently. Chain depth is bounded16; future propagation must apply its own stricter scheduling/eligibility rules and common-origin handling. Provenance does not certify a delivered claim as a recipient's firsthand observation or an inferred belief.

## Saves, branches and retrieval

World cursor counts canonical facts only. A delivery can occur at the same cursor as a save, so filtering only by world cursor would leak later information. Native-save checkpoints atomically bind **both** canonical cursor and subjective cutoff. Restore selects both; later evidence stays immutable/inactive. A future subjective receipt alone sets deferred divergence even when canonical head equals the checkpoint cursor. The existing canonical rule remains: fork only on a new BATTLE_STARTED. The new branch inherits parent evidence through both canonical fork cursor and captured subjective cutoff. Unrelated branch futures cannot leak through stable actor IDs. Native re-saving a restored view does not itself fork. Arbitrary savestates/reset/rewind/hot loads remain unsupported.

The trusted host issues `store.for_actor(actorID)`; future adapters receive only the returned ActorView's `context`, `records`, and `provenance` callables. Retrieval methods have **no actor/campaign/branch selector**, no SQL and no source-payload dereference. Grants are pinned to campaign/branch/world cursor/memory cutoff; later ingestion does not broaden them. Restore/branch/suspension invalidates incompatible grants. `as_of_cursor` can only narrow an existing grant; same-cursor timing remains bounded by its subjective cutoff. Registry identity retrieval contains no canonical trainer facts.

Records paginate by memory sequence, maximum256/page. Context uses the earliest256 authorized records at the grant cutoff, stable grouping/order, up to8 evidence IDs per group, and an explicit truncated flag. This conservative v1 window retains history in storage; it is not psychological forgetting or relevance ranking. Future consumers needing another page use the same actor-bound records API. Runtime injection has no Python/process sandbox: trusted embedding must register only these callables, not expose MemoryStore, factory, private attributes, database, shell or filesystem. No Hermes code is implemented.

`verify_memory_replay` rederives all direct claims from source history in an isolated in-memory database, compares immutable fields/identities, validates delivery parent claim/owner/campaign/branch/ordering and hashes active actor contexts. Stored memory sequence is the authoritative exposure order; source timestamps are provenance, not an NPC recency score. SQLite ownership remains trusted, as for WORLD-01. A future Hermes `prefetch` may call actor-bound context; `sync_turn` must validate approved typed domain outputs through separate writer rules. Hermes MEMORY.md/USER.md must never replace this store. LLM interpretation, beliefs, social relationships and propagation remain deferred.

## SOCIAL-01 publication receipt boundary

`post_exposure`/`pokebook` receipts use the same protected authorized delivery primitive as development receipts, with SocialStore-only authority. Full internal parent lineage is retained for audit. Public actor records/context/provenance represent an attributed published report and terminate at that receipt; private parent memory IDs and original turn/source IDs are omitted. Development-only fixture delivery retains its earlier audit semantics. Only explicit exposure delivers the validated post subset; feed/publication alone add no evidence. See `social_schema.md` for grants and `world_saves.md` for the third checkpoint cutoff.

## VIRALITY-01 authorized organizational delivery (D36)

The guarded trusted delivery primitive additionally permits
`rocket_intel/ROCKET_INTEL` only through a virality-capable writer. It verifies
explicit source member/recipient leader permissions, active source evidence,
direct mode and the member's own battle before delivering the exact same claim.
No other private NPC/director memory or unseen state is authorized. Public-post
provenance remains truncated at the reported post; organizational provenance
retains its legitimately observed parent. Branch/memory/virality save cutoffs
and restore epochs jointly authorize delivery. Native item-observation export
is not yet qualified; the four-claim Potion example is a host domain fixture.
Typed deterministic quality descriptors do not change claims or erase old rows.
