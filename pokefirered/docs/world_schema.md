# Canonical world schema v1

`world/migrations/001.sql` creates schema1. `PRAGMA user_version`, metadata schema1/reducer1/protocol2, full ROM SHA256/build tag and registry SHA256 are all checked. Newer/unknown versions and mismatched builds/catalogs fail closed; there is no destructive migration or implicit rebinding. SQLite WAL, FULL synchronous commits, foreign keys and one bounded-time writer transaction protect ingestion. The runtime takes a process lock. Canonical event ACK follows commit; the secondary evidence JSONL is not authority. A disk/commit failure withholds ACK. A retry after an uncertain commit finds the durable delivery.

| Table | Meaning |
|---|---|
| campaigns | Durable lineage UUID, active branch/cursor, paired/imported/incomplete status, deferred fork |
| branches | Immutable lineage relation to parent and fork cursor; advancing local head |
| events | Append-only canonical ID, origin, branch-local cursor, domain battle ID, typed fact and ingestion time |
| deliveries | Append-only transport identity and exact bytes → canonical event or observation |
| launches / streams | Host-authorized fresh battery launch UUID/nonce and persisted run/sequence/lifecycle tracking |
| observations | Separate append-only bounded observation, source origin, branch and canonical cutoff; no knowledge grants |
| projection | Transactional materialized canonical state; reconstructible from the ledger |
| checkpoints | Append-only fingerprint → campaign/branch/cursor, save identity, replay hash and compatibility metadata |
| save_intents | Durable pending/paired/incomplete cross-process save operation |
| outbox | Durable checkpoint/suspension notifications; no social effects or worker implemented |

SQLite triggers reject updates/deletions of facts, deliveries, observations and published checkpoints. Database ownership is a trusted local host boundary, not protection against deliberate external database edits. Schema migration is explicit source data; triggers are installed during migration1. No ROM save fields or RAM allocation are added.

`world/reducer.py` is a pure reducer. Replay requires identical ordered canonical events and registry/reducer versions. Branch cursors count canonical facts only; observations advance the transport sequence but never the world cursor or trainer state. The projection tracks encounter count, completed battles, defeat count, first/latest encounter event, associated battles and outcomes. It derives no memory, witness authorization, relationship, reputation, progression absent an exported fact, follow, AI belief or interpretation.

Transport identity is `(ROM hash, launch nonce, run, ROM sequence)`. Canonical origin is `(host-persisted launch UUID, run, ROM sequence)`; canonical event ID is SHA256 of that origin. A host restart reuses the launch identity; reconnect is not a new campaign or battle. Domain battle IDs hash the launch/run/native battle ID, so a fresh native battle1 cannot collide with earlier battle1. Source origin and exact delivery bytes remain inspectable. Duplicate delivery is a no-op; conflicting bytes, duplicate defeat under a new sequence, stale/gapped order, malformed/versioned records and inconsistent battle lifecycle are rejected. A repeated source origin cannot attach an inactive future. This is not semantic matching of identical-looking battles across independently launched timelines.

The existing typed BRIDGE-02 decoder/Consumer validates the full stream, including separate observations. Its lifecycle state and sequence persist in `streams`; historical dedupe uses SQLite, not its bounded recent cache. Unknown trainer records and unsupported battle flags fail. Genuine gaps or unmanaged run changes suspend enhanced ingestion; ordinary ROM play remains available. Recovery is a fresh known paired battery launch or explicit new-database import, never fabrication of missing facts.

`WorldStore` exposes campaign/active branch/cursor, trainer identity+facts, encounters, battles, canonical events, checkpoints, replay/integrity verification, managed import/launch and save operations. Default canonical queries use the active cursor, including a restored historical view; explicit branch queries inspect inactive history. These are host-domain truth APIs, not NPC-scoped retrieval tools. `observations` has no NPC-memory consumer or implicit promotion path. MEMORY-01 must implement grants/provenance before any NPC/model consumes evidence.

## MEMORY-01 additive extension

The description above records WORLD-01's boundary. MEMORY-01 now adds a separately versioned subjective schema without changing canonical schema1/reducer1, raw observations/transport deliveries or their semantics. Canonical-only WorldStore refuses writes to memory-enabled databases; MemoryStore derives actor evidence within the same transaction before ACK. Only host-issued actor views grant retrieval. See `memory_schema.md`; `memory01.md` records the new live Rick/Janice acceptance and explicit migration backup.
