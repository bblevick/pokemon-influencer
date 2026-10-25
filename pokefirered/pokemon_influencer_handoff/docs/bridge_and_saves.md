# Emulator bridge, protocol, and save consistency

## 1. Feasibility before architecture claims

Preferred candidate: a supported desktop mGBA build with scripting enabled. Official documentation provides relevant memory, socket, and callback capabilities, but it does not prove our transport, patched ROM, or save pairing. Phase 0/1 must establish those experimentally.

Do not assume mobile emulators, original GBA hardware, or arbitrary emulator versions support this integration. The intended deliverable is a patched ROM plus a tested local companion/bridge, not a standalone AI ROM.

## 2. Capability spike

Record OS/architecture, emulator version/build/package, scripting availability, Lua behavior, callback support, memory reads/writes, socket event behavior, input/screenshot access for tests, and managed snapshot capabilities.

Prove a harmless ping and bounded response before exporting player state. Measure normal play and fast-forward. Test service absent, wrong build, malformed data, disconnected socket, and a delayed response. Confirm the actual snapshot behavior for battery saves versus emulator save states.

Do not invent APIs. In the inspected docs, `readRange` exists, writes use `write8/16/32`, and socket connect is documented as blocking. A generic `writeRange` or save-state-loaded callback was not established. Build helpers only on confirmed primitives.

## 3. ROM-side mailbox

Reserve a named, aligned buffer through the actual linker/source allocation system. The address and size come from that build's ELF/map and are emitted into a bridge manifest. Never find "unused RAM" by visual inspection and write into it.

Provisional resource target: keep transient mailbox/event/UI buffers within a small explicit budget, initially aim below 8 KiB combined. This is a planning target, not verified free space. Audit EWRAM/IWRAM usage, heap/stack margins, script/text buffers, and linker collisions before selecting a final layout.

Use fixed-width integer fields, little-endian encoding, explicit maximum lengths, and C static size/offset assertions. ROM payloads are bounded binary structures; host-domain JSON is not copied as arbitrary bytes into game memory. Generate shared protocol constants rather than maintaining unsynchronized C, Lua, and Python definitions.

## 4. Message identity

Every applicable message must carry or resolve through a handshake to:

| Field | Purpose |
|---|---|
| Protocol major/minor | Reject incompatible layouts |
| ROM/content/catalog identifiers | Prevent interpreting a different build's memory |
| Save-lineage ID | Separate playthroughs |
| Branch ID | Separate rewound/divergent histories |
| Host session nonce | Invalidate previous process responses |
| Game generation/boot token | Invalidate replies after reset/load |
| Request/event sequence | Order and correlate work |
| Battle/turn/phase identifiers | Reject a reply for another battle phase |
| Payload length and integrity check | Reject truncation/corruption |
| Observation hash / plan version | Bind an action to the state it evaluated |

A checksum detects accidental corruption, not malicious authorization. Local connection authentication and strict loopback binding are separate controls. Never put API keys in ROM memory or protocol logs.

## 5. Transport design

Preferred launch order: start the local service, verify readiness, load the tested bridge, establish a connection before advancing gameplay. Bind only to `127.0.0.1` or a confirmed local-only mechanism. Use a random local-session token exchanged through the launch configuration, not a hard-coded shared password.

Do not perform synchronous reconnect attempts in every emulator frame. A failed connection leaves the ROM in fallback mode; retry at an explicit safe lifecycle point. A listener-oriented bridge may be preferable if capability tests prove it more reliable; document the decision instead of assuming it works.

Use length-prefixed bounded binary transport envelopes. Lua can pass payload bytes without parsing domain JSON; Python translates into validated typed records. Handle partial reads, short writes, duplicate requests, backpressure, disconnects, and maximum queue sizes. No `eval`, pickle, executable expressions, or arbitrary filesystem paths in messages.

The local transport is not a remote multiplayer protocol. Supporting connections from another machine is out of scope.

## 6. Request lifecycle

```text
IDLE
 -> ROM writes payload + sequence
 -> ROM publishes REQUEST_READY last
 -> bridge validates and forwards
 -> host validates, computes, and returns bounded response
 -> bridge checks current identity and writes response bytes
 -> bridge publishes RESPONSE_READY last
 -> ROM validates identity/length/action before consuming
 -> ACK / IDLE
```

Use double-buffering or a versioned publication scheme so callbacks cannot see a half-written request. Only one battle decision request is in flight initially. Event delivery and social jobs are separately bounded; slow posts cannot block a tactical reply.

The ROM yields in a task/state machine while waiting. Do not spin-wait with interrupts disabled. On deadline it chooses a legal fallback and advances request generation. A late reply is ignored, not applied to the next action.

Frame counts and host wall-clock deadlines are both logged. A provisional ROM deadline is 18 normal-play frames; measure whether this feels acceptable and adjust based on real integration. Fast-forward can cause earlier fallbacks in wall-clock terms.

## 7. Operations to implement incrementally

1. `HELLO`, capability/build validation, `PING`, `ACK`.
2. `GAME_EVENT` with idempotent ingestion and durable acknowledgment.
3. `UI_PAGE_REQUEST` / bounded encoded feed page.
4. `PREPARED_PLAN_REQUEST` / validated immutable roster payload.
5. `BATTLE_OBSERVATION` / `BATTLE_ACTION`.
6. `CHECKPOINT_PREPARE`, marker synchronization, checkpoint finalization.

Exact opcodes, field offsets, and struct sizes are Phase 1 deliverables. `contracts/domain.schema.json` is a reference *domain* schema, not a promised implementation of this wire ABI.

## 8. ROM integration surfaces

Inspect the pinned source around battle controller selection, move AI, separate switch/item selection, forced replacements, trainer party creation, battle end/results, menus/text encoding, VS Seeker, and save serialization. Candidate source paths are registered in `docs/source_notes.md`.

Implement wrappers at stable semantic boundaries. Never overwrite active Pokemon structures mid-animation or grant a reward solely because an LLM message arrived. The ROM revalidates each plan/action payload before invoking its own safe constructors/commands.

Enhanced single-trainer battles are the initial target. Wild, Safari, double, link, scripted special, and other unsupported modes retain explicit original behavior until individually tested. Unsupported does not mean unreachable: the campaign must still complete them safely.

## 9. Persistence architecture

The ROM remains authoritative for game simulation. SQLite stores social history and prepared state. A save marker associates a game snapshot with a compatible host event cursor, branch, checkpoint, and content version.

The exact save-marker layout requires auditing the existing flash sections, size limits, checksums, redundant writes, and initialization. Do not assume padding is available. If no safe extension exists, choose a documented alternate pairing strategy before shipping; the marker design is a feasibility gate.

Canonical event ingestion, projection updates, and outbox creation occur in one SQLite transaction. Durable acknowledgment means the event can be recovered after a process crash. Model output is stored before dependent publication so replay uses the actual selected artifact rather than calling the model again.

## 10. Managed checkpoint procedure

Cross-process storage is not magically atomic. Use a recoverable manifest protocol:

1. Reach a safe snapshot boundary; settle/persist accepted game events and outstanding state-changing responses.
2. Allocate a checkpoint ID and write a pending host checkpoint for the exact committed cursor.
3. Synchronize the ROM's branch/cursor/checkpoint marker and capture the game state/save using the verified snapshot method.
4. Snapshot/checkpoint SQLite using its supported backup/checkpoint mechanism; never copy an active database file while ignoring its WAL.
5. Write game and host artifacts into a temporary checkpoint directory with hashes, schema/content/ROM/emulator versions, and pairing metadata.
6. Verify both sides reference the same checkpoint/cursor, then atomically publish the final manifest/directory where supported.
7. On startup, incomplete pending checkpoints are ignored or recovered by documented rules; they never replace the last valid pair.

For emulator save states, explicitly specify and test whether battery-save data is included/restored. Default flag behavior may differ between save and load calls. Do not assume RAM state and `.sav` already form a consistent pair.

## 11. Load, rewind, and branching rules

A standard in-game save marker identifies the appropriate host cursor. On load, restore/replay the host view at that cursor. If host history extends beyond the saved cursor, create a new branch from that point for future gameplay; abandoned future memories remain inaccessible.

A branch has a parent and fork cursor. Queries include inherited events only through the fork point and new events on the branch. Reusing an event sequence from a divergent future without a branch ID is invalid.

For v1, managed checkpoints and ordinary in-game saves with verified pairing are supported. Arbitrary emulator rewind and independently exchanged save states are not guaranteed. Disable rewind in the tested launcher configuration where possible, document unsupported hotkeys, and detect marker regression/mismatch. There may be no universal state-load callback; managed load wrappers plus marker checks are required.

Do not claim marker polling catches every possible divergent state immediately. If a state cannot be paired confidently, suspend enhanced social writes and offer restore of a valid pair or an explicit new social profile. Do not merge a newer world into an older game silently.

## 12. Failure cases

| Failure | Required behavior |
|---|---|
| Cloud unavailable | Local memory/rosters/social templates continue |
| Host slow on a battle action | ROM deadline selects fallback; late reply rejected |
| Bridge disconnected | Core game continues safely; show nonintrusive degraded status |
| Event buffer fills while disconnected | Record overflow/gap; do not fabricate a complete history on reconnect |
| Database behind an acknowledged ROM cursor | Attempt recovery from durable log/checkpoint; otherwise suspend enhanced writes |
| Database ahead after game reload | Restore cursor view and fork future history |
| Wrong ROM/content version | Refuse enhanced integration, not arbitrary memory writes |
| Corrupt save marker | Offer checkpoint recovery; do not auto-reset user data |
| Crash during checkpoint | Last published valid pair remains usable |
| Missing database but existing game save | Explicit restore/import/new-social-profile choice; never claim memory continuity |

A bridge-disconnected session may lose social observations once its bounded queue fills. Document that limitation. The supported offline mode is local runtime active with cloud inference disabled, not unlimited gameplay with no persistence service.

## 13. Required evidence

Keep a protocol version/spec, generated layout assertions, ELF-derived manifest, capability report, real ping trace, action timeout trace, reconnect trace, wrong-build rejection, paired save/load test, rewind-future-memory rejection, and crash-recovery results. These are release artifacts for engineering review, not assumptions inferred from upstream documentation.

## BRIDGE-02 implementation boundary

The event/observation ABI, actual source hooks, transient identity limits, bounded recorder, emulator socket findings and current evidence are documented in `../../docs/bridge02.md` (authoritative repository path: `docs/bridge02.md`). `schemas/bridge/event.schema.json` distinguishes canonical events from NPC-side observations; canonical possession grants no exposure permission. The current observation is explicitly incomplete for legal actions. No paired save, durable branch or canonical world database is implemented by this transport. Track live verification status in `docs/status.md`; build/host/native fixtures are not emulator acceptance evidence.


## BRIDGE-03 implemented presentation contract

The final bounded UI protocol, native lifecycle, safe text mapping and managed transient-run cancellation are specified in repository-root `docs/bridge03.md`, with shared `bridge/ui_protocol.json` and generated `include/pi_ui.h`. UI_NOTICE and native two-choice UI_CHOICE are presentation requests. Their correlated responses never enter canonical game facts or NPC observations. No PokeBook/domain action, AI decision or durable save marker is implemented. Managed reset/load can cancel volatile UI; arbitrary unmanaged rollback and durable canonical/save pairing remain WORLD-01 work. Actual evidence belongs under `evidence/phase1/bridge03/`; architecture text alone is not acceptance.

## MEMORY-01 implemented subjective pairing

Repository-root `docs/memory_schema.md` specifies the additive actor evidence layer and independent subjective checkpoint cutoff. WORLD-01's normal battery fingerprint/receipt protocol remains unchanged; deliveries do not advance the canonical cursor, so MemoryStore binds both cutoffs to save/checkpoint and parent branch. New real MEMORY Rick/Janice/restart/native restore/divergence acceptance is in repository-root `docs/memory01.md`. No bridge ABI, ROM save structure, hot-load/rewind capability or inference path is added.

### SOCIAL-01 checkpoint extension

SOCIAL1 reuses the accepted normal-save intent/drained callback/fingerprint/fresh-process workflow and adds a social log cutoff/replay hash alongside canonical and MEMORY cutoffs. Pending social work is represented, never executed by restore. Explicit host social mutation can create a same-canonical-cursor child with bounded parent subjective/social cutoffs. See repository-root `docs/world_saves.md`, `docs/social_schema.md` and D20. This is not general savestate/reset/rewind support and consumes no additional ROM RAM or payload capacity.

## POKEBOOK-01 native player presentation

Viewer schema2/kind3 is a bounded24byte query/96byte maximum reply within the existing presentation mailbox, not a new gameplay/event channel. Host authority binds campaign/branch/social restore epoch/player; ROM owns native modal rendering and validates view/snapshot/request/post/page, glyphs and pixel bounds. Old schema1 notices/choices and field gates remain unchanged. No read markers or new save sectors exist. Supported restores still require fresh OS processes and known paired normal batteries; old view sessions/payloads are invalidated. New ROM uses an explicitly imported separate campaign lineage, without migrating/whitelisting B3 history. Actual reader payload replay from the abandoned launch is rejected before presentation by nonce/envelope validation. See docs/pokebook01.md, bridge/pokebook_protocol.json and schemas/bridge/pokebook-player-view.schema.json.

## PREP-01 host progression evidence

PREP reads the two source-pinned native Brock/Boulder flags from the checksum-valid battery selected by the accepted WORLD normal-save protocol. The new preparation receipt/checkpoint layer is host-only; no mailbox/event ABI, native flag, ROM save field or RAM allocation was added. Flags are canonical progression authority and confer no NPC observation. Exact agbcc/APCS offsets, atomic PREP checkpoint cutoffs and fresh-process restore restrictions are in docs/prep01.md and world_saves.md. Read-only field-position diagnostics in bridge/prep_acceptance_probe.lua support native acceptance walking only; they are not a gameplay bridge or legal-action exporter.


## D33 preparation pairing extension

PreparationDecisionStore adds append-only model DECISION, locked COMMITMENT, INSTALLATION and actual NATIVE_PROVENANCE receipts with branch-inherited cutoffs/checkpoint hashes. Restore selects this prefix before inherited PREP projection validation; future grants are revoked and cannot recommit. Original accepted databases/saves are preserved. The new isolated native build changes no SaveBlock/flag/section serializer and is admitted only by the explicit hash-verified NativePreparationStore compatibility adapter, not generic cross-ROM import. First unsaved host commitment continuation is a narrowly audited explicit `--continue-preparation` mode; ordinary authorize_launch/restore always selects the paired prefix. Actual Save17 excludes future lock, Save18 restores commitment only, Save19 restores installation too. See docs/system1_01a.md, tools/system1_01a_audit.py and evidence/phase3/system1_01a/paired-restore-audit.json. Generic savestate restore remains outside this normal-battery proof.


## BATTLE-01 audit pairing (D34)

The explicit BattleStore overlay retains logical catalog/save identity after checksum/source/RAM/serialization verification of the new actual ROM. Tactical audit is separate append-only data, never canonical knowledge. Normal checkpoints pair its branch-visible row cutoff/hash; branch forks retain only the parent prefix at the fork. Save20/fresh runtime preserves five completed decisions, Save19 restore excludes the later audit/post. Ephemeral fragments/provider jobs/request state are never normal-save contents. Cancel on disconnect or invalid scope; resetting/rewinding requires a fresh known paired battery launch. Arbitrary savestates remain unsupported. Native snapshot memory is freed at battle end and pointer initialized on fresh boot. Exact protocol/deadlines and evidence are docs/battle01.md and evidence/phase4/battle01/verification.json. Do not open the working battle database with a legacy writer that cannot maintain its audit cutoff; no generic migration is claimed.

## D36 host-only virality pairing

Virality adds its own immutable branch parent bounds/checkpoint cutoff+state hash
and restore epoch alongside existing world/memory/social/puppeteer layers.
Historical checkpoints adopt empty virality state; no ROM save layout/mailbox/
bridge protocol changes occur. Only virality-aware writers can mutate an upgraded
database; queued jobs bind the complete active scope. Restoring never runs the
scheduler. Host fixture battery pair/reload tests and private-copy native-history
restore proofs are recorded separately from emulator acceptance. The next
continuous native campaign must use the composed writer and pair new exposures
with ordinary native saves; this ticket did not create a new native save.

## BATTLE-END-01 terminal retention

See [battle_terminal_contract.md](battle_terminal_contract.md) for unchanged
canonical wire semantics, stable terminal copies/retries, tactical dispositions
and branch-cutoff recovery. This narrow repair does not qualify arbitrary hot
savestates, power-loss persistence or unlimited bridge-absent battles.

D48 records an explicitly authorized exceptional retrospective pair from retained
post-Kent native callback/contiguous stream and exact projection evidence, without
changing native storage or gameplay truth. Normal managed save intent workflow is
still preferred. See [recovery policy/proof](campaign_expansion01_final_recovery.md)
and `world_saves.md`; absent causal evidence remains unpaired.

## D52 managed continuity correction (2026-10-08)

Opt-in continuity configurations retain exact physical wire in a separate durable
inbox before existing canonical ingestion. ACK follows canonical commit and a
published durable high-water mark. Replay requires campaign/branch/causal identity
and the same surviving native process, not merely a checksum or battery file.
The accepted native adapter still distinguishes physical ROM provenance from the
logical campaign build. Recovery audit is separate from gameplay events.

The local supervisor freezes the whole owned emulator on host loss/expiry or
event gaps; input leases cancel queued PI_TEST inputs. Explicit reconnect waits
for replacement writer readiness while native remains frozen, then revalidates
authenticated transport/high-water state before enabling input. It is qualified
for pinned macOS/mGBA at normal speed; legacy unmanaged launchers, fast-forward,
other input helpers and simultaneous guard/writer failure are not covered by that
claim. No permanent native buffer was added. An event not yet captured by the
host still depends on surviving native RAM; absent native counterparts require a
verified rollback pair. Historical RIVAL travel298 is such a blocked case.

Actual isolated lost-ACK/reconnect/wild travel/normal save/fresh offline Continue,
failure matrix, limitations and safe original Save20 rollback:
[RIVAL travel repair](rival01_travel_continuity_repair.md).


## Versioned pre-battle descendant journals — 2026-10-24

The ordinary paired-save rollback contract remains unchanged. An explicit host-only pre-battle continuation can preserve a validated current post-parent Strategy/preparation descendant through a fresh native session, under the separate [v1 continuation contract](prebattle_continuations.md). This is not same-fingerprint rebinding or a fully paired checkpoint. Normal restore abandons journal authority; missing native settlement or divergent/superseded history fails closed. Actual two-process qualification: [RIVAL-01 report](rival01_prebattle_continuation.md).
