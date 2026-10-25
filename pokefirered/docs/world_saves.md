# Managed normal-save pairing and recovery

Supported workflow: a known paired battery save in a **fresh mGBA OS process**, native Continue, ordinary in-game Save with a prior durable host intent, and the existing `savedataUpdated` lifecycle callback. No savestates are used by WORLD-01. Unmanaged controller reset, hot loads, rewind, copied RAM snapshots and same-process script reload are unsupported; the WORLD harness rejects its snapshot/reset test commands. An unexpected transport run suspends ingestion. Launching from an unknown fingerprint fails before replacing the current private battery. Import requires an explicit command into a new database and does not invent earlier canonical history.

Inspected source: `src/save.c:sSaveSlotLayout`, `WriteSaveSectorOrSlot`, `HandleWriteSector`, `GetSaveValidStatus`, `CalculateChecksum`; `include/save.h:SaveSector`; `src/load_save.c:SaveSerializedGame/LoadSerializedGame`. Two14-sector slots alternate by counter parity. Physical section order rotates modulo14. The primary campaign consists of SaveBlock2, SaveBlock1 and PC storage. FireRed's native flags/structures/flash code are unchanged.

Algorithm **fr-save-v1** in `world/saves.py`:

1. Accept exactly128KiB flash, optionally followed by the pinned mGBA16-byte RTC footer.
2. Read each14-sector slot. Require section IDs0–13 exactly once, signature0x08012025, one common32-bit save counter, and each source checksum over the actual ELF/ROM-derived section length.
3. Select the greatest complete slot counter, with the source special transition0xFFFFFFFF→0. Reject ambiguous equal-counter slots with different payloads. A torn newer slot is never published as a new pair.
4. Sort sections by logical ID; encode each as little-endian u16 ID,u16 actual length,payload bytes. SHA256 of that concatenation is the content digest.
5. Fingerprint is SHA256 of ASCII `fr-save-v1`, NUL, little-endian u32 counter and that same concatenation. Counter distinguishes later saves even if payload content is unchanged; content distinguishes saves with equal counters.

Physical slot/order, older slot contents, unused section/footer padding, auxiliary HoF/Tower sectors and the emulator RTC footer do not define the campaign fingerprint. They are intentionally excluded. HoF/Tower are not WORLD canonical facts; endgame stays deferred. Section sizes from final B3 ELF:3876,3968,3968,3968,3816, eight3968 entries and2000. No padding is claimed safe for storage. The fingerprint is not a hash of volatile RAM, filename, save slot, game trainer ID or timestamps.

`save-begin` commits an intent fixing campaign/branch/canonical cursor, authorized nonce/run, last durably ingested transport sequence and old save fingerprint/counter. It requires completed battles. Re-saving a restored cursor pairs that same historical view without creating a branch; the pending fork remains until a new canonical battle start. Start/menu cursor remains native state; the replay helper has an explicit `--menu-cursor` parameter. The player then performs **native Save**; no host writes game state. The existing lifecycle callback writes a local bounded receipt containing counter, nonce/run, ROM captured-event counter/ACK/queue state/drops. This is trusted emulator lifecycle evidence, not a new gameplay bridge event or NPC observation.

The host requires a new complete counter=old+1, exact captured/acknowledged transport sequence, empty queue, idle mailbox, zero drops and unchanged world cursor. It fsyncs the private battery and requires two stable fingerprint reads. Checkpoint, intent completion and notification outbox entry commit in one SQLite transaction. An unarmed save remains unpaired, even if a file change is observed; the host never guesses its canonical cutoff from file polling alone.

Pinned mGBA `src/gba/gba.c:GBAFrameEnded` invokes savedataUpdated after dirty state clears; `src/gba/savedata.c:GBASavedataClean` attempts file sync and writes RTC metadata. The callback itself does not prove sync success: the host fsync/read/checksum gate is therefore required. The Lua receipt flush is not a cross-process fsync or distributed transaction. ROM save and SQLite are separate persistence systems; no perfect atomicity is claimed.

| Failure | Safe result / recovery |
|---|---|
| Native save incomplete/unchanged or queue/gap mismatch | No new checkpoint; pending intent remains detectable. Restore known pair or abandon intent explicitly. |
| Native save succeeds; host absent/crashes before pairing | New fingerprint is unpaired. If a complete matching trusted receipt and pending intent survive, same-launch host restart can finish; otherwise restore last known pair or explicitly import into a new DB. |
| Checkpoint transaction fails | All checkpoint/outbox/intent completion writes roll back together. Retry the same intent/receipt; no partially published pair. |
| Published checkpoint; process exits | SQLite FULL commit and battery fsync precede publication. Restart from that known fingerprint. Hardware/filesystem durability failures remain possible. |
| File changes again before receipt processing | Counter/barrier mismatch fails closed; do not infer the missed pairing. |
| Database missing/newer/build or catalog mismatch | Refuse enhanced integration; recover matching database/backups or explicitly import a new lineage. Core FireRed remains playable. |
| Unmanaged reset, gaps, stale origin | Persistent incomplete status; recover through a fresh paired normal-save launch. |

Restore identifies the fingerprint's immutable checkpoint, verifies versions/build and replay hash, reconstructs that cursor and deactivates prior launches. It changes only the active view; later events remain append-only. If the restored cursor is below branch head, `pending_fork=1`. Merely restarting/reconnecting/querying does not fork. The next fresh canonical battle start creates a child branch with the checkpoint prefix. Restored queued records cannot serve as divergence; supported fresh battery boots contain no restored RAM queue. Observations and old replies do not create branches.

A campaign UUID represents one imported/new lineage, independent of launch. Branch UUID changes only on divergent continuation. Launch UUID/nonce changes on each managed fresh process; run remains1 in this workflow. The native battle counter is namespaced by launch/run. Canonical cursor excludes observations. There is one campaign per database in v1. Importing unrelated saves into an existing campaign is rejected; create a separate database. A save fingerprint already bound to a different history is rejected rather than merged.

Recovery commands (repository root):

```sh
.venv/bin/python tools/world01.py fingerprint --save path/to/local.sav
.venv/bin/python tools/world01.py --database .local/new-lineage/world.sqlite3 import --save path/to/local.sav
# Acceptance launcher uses .local/world01/world.sqlite3; seed it explicitly once:
.venv/bin/python tools/world01.py import --save .local/phase1-ui-emulator/bridge03-native-counter4.sav
.venv/bin/python tools/world01_launch.py --start --save .local/world01/S1.sav
# Native Tools > Scripting > File > Load .local/world01-run.lua once per process.
.venv/bin/python tools/world01_host.py --seconds 1800
.venv/bin/python tools/world01.py save-begin
# Perform native Save, or use the reviewed input helper:
.venv/bin/python tools/world01_scenario.py save --label next-save --menu-cursor 0
# The helper arms its own intent; do not run save-begin immediately before it.
.venv/bin/python tools/world01.py save-abandon --intent INTENT_UUID
.venv/bin/python tools/world01_replay.py --database .local/world01/world.sqlite3
.venv/bin/python tools/world01_replay.py --fixture evidence/phase2/world01/rick-canonical-fixture.json
```

Stop task-local mGBA before managed launch/restore. The launcher refuses a running task-local process; keep immutable copies of paired battery saves with the database. Copying a battery while mGBA runs is not a supported load. Native Save without an intent is degraded/unpaired, never silently attached. Host-only replay needs no mGBA, ROM files, network, model or .env. Commands intentionally do not download/upload ROMs or saves.

## MEMORY-01 subjective cutoff

Managed normal-save checkpoints now also bind an immutable subjective sequence through the additive memory extension. Restoring the checkpoint selects canonical cursor and memory cutoff; a later delivery at the same world cursor is excluded. Child branches inherit both cutoffs. Memory-only future evidence sets deferred divergence, while the native canonical fork still begins with a fresh BATTLE_STARTED. Fixture delivery is refused during unresolved fork or pending save. Existing fingerprint/native receipt/fsync/fresh-process restrictions remain unchanged. See `memory_schema.md` and new live S1/Rick/one Janice receipt/S2/restore/divergence evidence in `memory01.md`.

## SOCIAL-01 managed extension

See `social_schema.md` and `social01.md`. Native paired checkpoints now atomically bind canonical cursor, MEMORY cutoff, SOCIAL cutoff/replay hash and pending social jobs represented in that hash. Native save intent/receipt/fingerprint and fresh-process Continue requirements are unchanged. WORLD-only/MEMORY-only accepted databases remain separate evidence.

A host social mutation after restoring a checkpoint with inactive subjective/social future creates a child at the same canonical fork cursor, inheriting exactly the checkpoint's memory/social cutoffs before writing. This explicitly extends the earlier ROM-event-only deferred-fork rule for SOCIAL-01; it does not authorize unmanaged savestates/reset/rewind. Restoring performs no policy/job work and revokes social capabilities. An identical battery fingerprint cannot be paired to different subjective/social state; native re-save is required. Exposure and receipt cutoffs cannot be mixed. Pending save intents block social mutations. A known paired later checkpoint remains independently restorable.

## PREP-01 additive normal-save pairing

PREP schema1 adds a preparation log cutoff/hash to each existing managed checkpoint. Explicit activation initializes exact authored individuals and zero/no-restock resources. A validated normal-save completion reads only the two pinned native Brock/Boulder flags from SaveBlock1 and atomically appends their progression receipt and justified first forest opportunities before checkpoint publication. Native flag acquisition does not grant actor knowledge or modify the canonical event ABI. `prep/progression.py`, `config/prep_save_layout.json` and docs/prep01.md define the build/ABI/source/checksum bounds.

Restore selects precisely the stored preparation cutoff, restores companion/resource/opportunity/reservation projections, increments the capability epoch and leaves future receipts inactive. New branches inherit only the paired prefix. Querying/enumerating does not consume stock or create an epoch. A future committed plan requires a separately implemented atomic resource/opportunity writer; no native team is installed by PREP. Foundation stores refuse writing preparation-enabled databases. No hot-load, reset, rewind, new ROM save sector or arbitrary old-build database migration is authorized.

STRATEGY-01 adds another derived append-only cutoff/hash to normal paired checkpoints. Existing checkpoints explicitly migrate with empty Strategy history. Normal saves atomically pair new opportunity/grant/posture history; identical fingerprints cannot be rebound. Restore advances Strategy epoch, excludes future decisions, revokes active grants and preserves durable retry counts. A result must present its original immutable context grant, so a later regrant under the same semantic job cannot accept an old response. Recorded replay performs no inference. This session's actual fresh Save14/16 proof is **fallback-only**; no live-model acceptance or native team commitment is claimed. Historical decisions/envelope IDs stay immutable; a fresh current material-context/envelope binding is returned separately for future System One revalidation. See strategy01.md/native-restores.json.


## Current Strategy output contract — D32 (2026-10-04)

Strategy emits a bounded, exact natural-language **StrategyMemo**, not required JSON, tools, enums, evidence IDs or numeric posture. One ordinary completion interprets the existing actor-filtered context and legal preparation constraints. Approximately100–250 words is a prompt target, not a semantic validation requirement. Host validation enforces nonempty strict UTF-8, at most4096 UTF-8 bytes, no unsafe control/format characters (paragraph LF allowed), and the current immutable actor/job/branch grant. The provider also enforces at most1800 output tokens,65536 response bytes,24576 request bytes/conservative input tokens,35 seconds/request and120 seconds/job. A failed completion produces explicitly labeled deterministic prose fallback; no repair loop.

Persist accepted text verbatim with host-generated strategy/job/actor IDs, campaign/branch/generation/cutoffs, context/material hashes, preparation-envelope reference, persona/configuration/prompt versions, timestamp/cursor and provider/model diagnostics. Reuse stored text on restart, UI refresh and repeated decisions. Fresh legitimate opportunities/material precommit evidence may yield different prose; replay does not regenerate it. Future commitment must atomically lock the exact memo reference/hash alongside the team. Commitment/installation is not implemented here.

A memo is subjective interpretation. Even an unsupported prediction remains text: it never becomes canonical truth, actor knowledge, acquisition permission, resources, preparation selection or a battle action. Future System One requests must separate **AUTHORIZED FACTS** from **STRATEGY MEMO — SUBJECTIVE**, pass the exact stored text, and allow only supplied current legal candidate/action IDs. No prose-to-facts or prose-to-numeric-posture conversion is required or implemented.

Historical posture schemas, prompt/config hashes, records and closed experiments remain unchanged. `strategy/memo.py` adds schema3/prompt2 MEMO receipts using the existing paired Strategy cutoff/hash. Historical internal projection key `postures` retains its name to preserve existing checkpoint hashes; `memo_records()` exposes only schema3 text. Explicit MemoStore adoption is limited to the new acceptance working copy; legacy StrategyStore refuses a memo-enabled database. Original databases are not migrated or rewritten. Normal inference remains disabled. No System One, party/resource/ROM change or endgame work is authorized.



D32 acceptance (2026-10-04): corrected StrategyMemo host runtime and actual free Nemotron smoke/Rick result accepted. Exact model text survives fresh host/native Save17 Continue, paired Save16 rewind excludes it/late grant, and paired Save17 return retrieves it without inference.67 unique focused tests/0 skips and actual-artifact audit passed;16 full Rick option plans, knowledge/history/companions/resources and ROM unchanged. Budget closed2/2; historical records/inputs/evidence preserved and all task processes stopped. See docs/strategy01.md and evidence/phase3/strategy01/memo/completion.json. Next separately authorized SYSTEM1-01A; no selection/commit/install/action or endgame implemented.

## D48 exceptional retained-evidence recovery

Normal prior-intent + native callback/barrier + stable checksummed battery pairing
remains preferred. User628f9c2f authorized one retrospective post-Kent recovery from
retained durable evidence. `campaign/recovery.py` verifies contiguous checksummed
stream/callback/run/previous-pair lineage, source-native save identity/flag deltas,
exact canonical and every subjective/social/plan/audit cutoff, terminal required
jobs and unchanged domain rows. Its canonical checkpoint extension chain binds
all existing tables; immutable `retrospective_pairs` stores manifest/hash/time/tool
version and checkpoint kind `retrospective_recovery`. It never synthesizes an intent
or edits game/domain truth. Ordinary known-pair restore resumes capabilities.
Missing/conflicting evidence remains unpaired. This narrow audited exception is not
a file-polling shortcut or routine replacement for managed saves. See
[actual recovery and fresh native proof](campaign_expansion01_final_recovery.md).
