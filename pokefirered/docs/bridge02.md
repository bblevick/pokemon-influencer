# BRIDGE-02 — typed events and scoped observations

BRIDGE-02 is complete for the user-authorized facts/observations scope (2026-10-02). Final-build wild victory, ordinary trainer defeat, absent-host gameplay, reconnect, reset with a pending event, and savestate rollback were exercised. The prototype limits below remain explicit; no world-memory or AI implementation is included.

Source pin and toolchain remain those in `config/phase0.lock.json`. English FireRed rev0, MODERN=0. Build flags `PI_BRIDGE=1 PI_EVENTS=1` select transport2. `PI_EVENTS=0` retains protocol1 PING behavior; both flags default off. No battle AI, party construction, trainer flags, story gates, menus or saves are replaced.

## Facts and knowledge are separate

`schemas/bridge/event.schema.json` uses distinct closed payloads and `recordClass` values: `canonical_event` and `observation`. The append-only mock receipt stream includes both in capture order; convenience sinks separate them. This receipt stream is not an NPC memory store. Canonical event possession does **not** authorize NPC exposure. Future context builders must filter by witness/delivery provenance and NPC identity before retrieval. `observation_for_context` rejects canonical records. No Hermes/model adapter exists.

The NPC-side observation includes its own active species, exact HP/maxHP, major status, moves and PP; the player's visible active species, a coarse 0–48 HP bar, and moves previously announced in this encounter for that active party slot. The slot index and private party are not serialized. No names, unseen party, unrevealed moves, items, exact player HP/stats/PP, hidden selections, future RNG, status2 or raw structure copies leave the ROM. Public information is not broadcast permission for unrelated NPCs. Own bench/items, opponent statuses/stat stages and weather remain omitted pending audited exporters. `legalActionsComplete=false`: this **cannot** issue a tactical decision request.

Opponent status and weather in the future BattleDecisionRequest schema are optional, so unknown fields can be omitted rather than fabricated as `none`. Existing fictional packets remain valid. The projection is a compatibility preview, not an implemented BattleContextBuilder or action exporter.

## Protocol and taxonomy

Authoritative ABI: `bridge/events_protocol.json`, generated `include/pi_events.h`; wire codec `bridge/events_wire.py`, host mapping `bridge/events.py`. Little-endian only, no ROM JSON or strings. Mailbox196 bytes, payload96 max. Event header24 bytes `<HHIIHHIHH>`: schema1, type, sequence32, battle32, turn16, phase16, ROM frame32, payload length16, reserved flags16. Outer framed wire protocol2 has a36-byte header and u16 body length; total134 bytes maximum. Authenticated loopback HELLO checks launch token and full ROM checksum before mailbox writes; manifest verifies actual ELF/map/ROM and Lua/schema hashes.

| Type | Payload bytes | Meaning |
|---|---:|---|
| BATTLE_STARTED | 8 | Battle flags, wild/trainer kind, effective trainer ID and pre-battle undefeated flag snapshot |
| BATTLE_TURN_STARTED | 0 | Once at native selection entry per turn |
| BATTLE_ACTION_RESOLVED | 6 | Actor side, visible species, announced move or slot advance without announcement |
| TRAINER_DEFEATED | 4 | Trainer ID, prior undefeated flag and actual victory outcome |
| BATTLE_ENDED | 4 | Trainer ID, prior undefeated flag and native outcome, including loss/flee |
| BATTLE_OBSERVATION | 40 | Distinct scoped NPC-side record at selection; not canonical truth |

Action records mark the native action-slot advance. An announced move is what the game displayed, not a guarantee of damage or successful effect. Unannounced slot advance omits the chosen action category. It never reveals a pending choice. Gym badges and the full game event catalog are deferred. Supported modes are ordinary single wild/trainer only; A flags allowlist admits only ordinary master/single-trainer flags; every special flag (including Poke Dude, ghost, scripted and legendary encounters) stays native and is excluded.

## Identity and bounded failure

The identity is `(ROM build, launch nonce, Lua epoch/run, event sequence)`; battle/turn/phase correlate within that run. Launch nonce changes with a fresh launcher; Lua run starts1. Battle ID increments at supported battle start, turn starts1 at selection; phases0 start,1 selection,2 action advance,3 end. ROM counters reset on ROM initialization; they are transient, not durable trainer/Pokémon lineage. Effective VS Seeker trainer ID is captured; original/rematch content identity mapping remains future work.

`branch=transient:{nonce}:{run}` is only a transport lifetime tag. Explicit emulator reset callback increments run. ROM heartbeat regression detects common soft reset/state rollback and disconnects old authentication. Reconnect preserves run. Save callbacks log battery writes without pairing host state. Arbitrary savestate rollback at equal/higher heartbeat, rewind and controller-only reset are unresolved; no durable branch marker, world projections or future-memory rollback guarantee is claimed. Counter exhaustion refuses new IDs rather than reusing them. At turn65535 the next selection disables export for that encounter and increments drops; event/battle32-bit exhaustion also refuses capture. Ordinary gameplay continues, and that extreme encounter has no complete external lifecycle.

The mailbox generation is assigned on authenticated HELLO. Before that handshake, an offline restored mailbox may still contain the saved generation; it is not the current Lua run. Queued records restored from a savestate can receive the new transport run on delivery. This is not durable event-origin identity or cross-branch exactly-once handling. Future save pairing must reconcile that boundary before implementing NPC memories or canonical projections. The recorder retains old accepted histories and changes its per-run consumer; it does not erase an abandoned timeline or present old history as current NPC knowledge.

Four queued records, one in flight;60 ROM-tick deadline, two retries after the initial attempt. Exact bytes/sequence persist across retries. Overflow drops newest and increments captured sequence, exposing a gap. Exhausted retry drops head. Gameplay never waits for the host. Lua binds/listens/accepts locally; only Python connects, with timeouts. Lua RX/TX512 bytes,128-byte reads and at most2 parses per frame. ACK checks launch/run/sequence/build and type/empty payload/checksum. Malformed/stale responses fail closed. Host validates closed schemas and lifecycle, tracks256 recent duplicate receipts/32 battles, diagnoses gaps, rejects conflicting duplicates, regressions and events after end. Exact duplicates receive an ACK without a second accepted record. Host JSONL recovery replays accepted bytes before reconnect. Fsync precedes ACK; this is a test recorder, not transactional canonical world storage.

## Allocation and commands

Final enabled ROM SHA256: `eb8ce46de923e3d85216754ec880d50e8fdc2c95efa31a1dff73d4cbd6df6214`. Mailbox address is derived from this ELF:0x0203FBB0. Dedicated mailbox/control section668 bytes;436 EWRAM bytes remain. All947 original RAM symbols retain address/size; original heap/IWRAM/stack margin unchanged. Worst-depth stack usage remains unmeasured.

```sh
.venv/bin/python tools/phase1_events_build.py
.venv/bin/python tools/phase1_events_build.py --disabled
.venv/bin/python tools/phase1_events_test.py
.venv/bin/python tools/phase1_events_launch.py --start
# Native Tools > Scripting > File > Load script: .local/events-bridge-run.lua
.venv/bin/python tools/phase1_events_host.py --seconds 3600
.venv/bin/python tools/phase1_events_input.py sample
.venv/bin/python tools/phase1_events_scenario.py LABEL 'key KEY HOLD REST'
.venv/bin/python tools/phase1_events_replay.py --log evidence/phase1/bridge02/events.jsonl --report evidence/phase1/bridge02/replay.json
```

Input harness is separate test tooling on loopback18773. Gameplay listener18772. Only bounded buttons/screenshots/read-only samples and explicit test reset/checkpoint/reload commands are accepted; no arbitrary RPC/eval or game RAM mutation. Checkpoint/reset/reload execute immediately, so finish queued input before invoking them. `.local` ROM/save/savestate copies and `evidence/private/bridge02` screenshots stay ignored. Original dump is never overwritten or uploaded.

## Experimental emulator findings

Initial disconnect testing exposed SIGPIPE termination in the native socket send. Task launcher now preserves Python's ignored SIGPIPE (`restore_signals=False`); this applies to this launcher, not every way of opening mGBA. Initial failure trace is retained as `launch-attempt1-sigpipe.log`. The pinned receive wrapper may report stale AGAIN at EOF; Lua polls native socket readiness on nil receive to distinguish EOF from idle. General same-process script reload and arbitrary socket/lifecycle behavior remain outside the proven contract.

Actual commands are retained in `input-commands.jsonl`, segment/route logs; callback trace in `emulator.jsonl`; accepted bytes in `events.jsonl`, separated sinks and host mode traces. Static and native checks are in `host-static-tests.json`, compiled manifests and corresponding logs. `pre-final-live/` holds preliminary failures/unfinished attempts and is not counted as final-build acceptance evidence.

The pinned native socket close does not invalidate its descriptor and its destructor invokes the same close again. `socket-lifetime-audit.json` records the inspected implementation and distinguishes source-backed inference from observed disconnects. The bounded guard retains128 closed native objects for the gameplay listener (512 in separate test input), so their destructor cannot close a reused descriptor during this launch. Acceptance stops before its budget is exhausted; a fresh process is then required. This is an explicit limited-lifetime prototype contract, not unlimited reconnect support. Same-process script reload remains unsupported; scripts must be loaded once per fresh process. The emulator binary is unchanged.

Gameplay scenario/route/battle drivers acquire an exclusive host file lock for their complete run. Do not invoke raw input commands to issue competing buttons while a driver is active; read-only diagnostics and deliberately requested lifecycle fault commands are separate. Static source routing has no live object/script/battle knowledge and stops on no progress. Battle helper uses ordinary default Fight/Tackle buttons only, with a finite input bound; it is test-player automation, not the NPC battle AI. Random encounters, misses, movement NPCs, animation and idle time remain nondeterministic; failure logs and screenshots must be inspected rather than assuming a route completed.

## Final-build live evidence and results

`emulator-integration.json` has53 assertions over retained real traces and screenshot retention, not a simulated or freshly generated playthrough. Session2886554291 used the final ROM above. Its67 accepted records are included in `events.jsonl`; `replay.json` independently reconstructs153 accepted records across5 identities, including explicitly labeled earlier-build attempts, and validates7 fictional fixtures without mGBA.

| Scenario | Actual result |
|---|---|
| B: Rick | Run1/battle1, trainer102 from the pinned forest script/constants, Weedle6 then Caterpie6.47 records,11 turns, native victory. Seq46 `TRAINER_DEFEATED` (previously undefeated true) immediately precedes seq47 `BATTLE_ENDED` outcome1. Initial observation has no revealed player moves; Leech Seed73 and Tackle33 appear only after native announcements. |
| A: ordinary wild | Run2/battle1, trainer0, Caterpie4.18 records,4 turns, outcome1. Field movement resumes; `final-wild-field.png` is private. |
| C: absent host | Run3/battle1 advances through multiple turns with no accepted receipts, changing HP and continuing normally. After reconnect, final action33 and end34 arrive with an explicit32-record gap and `streamIncomplete=true`; actual outcome1 and field return are observed. Diagnostic totals32 drops,65 retries,97 failures include the subsequent stale-ACK fault. No complete history is invented for the missing portion. |
| D: reload/reset | `C.SAVESTATE.ALL` restores the pre-trainer field checkpoint (seq0/battle0/turn0, save counter3, Bulbasaur7/HP24). Heartbeat regression changes Lua run1→2; battle/sequence1 is reused under a distinct identity. Additional reloads and two pending-event resets were exercised. The repeated automated pending reset changes Lua run6→7, with native pending seq1/queue1 cleared to0. A normal Continue reaches the original forest position; authenticated HELLO reports run7. |

Native in-game Save after Rick wrote counter4, level8/HP15 at42,46; both save callbacks were observed. `trainer-battery-save.json` binds a retained private battery copy and checksum. The explicit ALL savestate restores counter3 and save-related state; this is an unmanaged experimental rollback, not host-paired save semantics. `pre-rick-save.json` and `checkpoint-final.json` document normal-input provenance and final-ROM snapshot identity. Only task-local saves were used; the supplied dump and original Phase0 fixture were preserved.

Missed ACK at run1/seq1 retransmits exactly once into the host duplicate path. Intentional disconnect at run2/seq1 reconnects with the same run and duplicate ACK. Stale seq32 ACK for run3/seq33 is rejected and the exact event is retransmitted. Sixteen authenticated reconnects retain run2; explicit forced Lua GC was followed by subsequent successful transport and resets. No gameplay-listener unknown-error disconnect occurred in this final launch. These observations establish the bounded tested contract, not universal socket robustness.

The separate input listener reset once during `final-absent-turns`; `test-input-disconnect.json` retains the failure and reviewed recovery. Reset invoked from the input callback twice performed the reset but lost its socket reply. `phase1_events_pending_reset.py` never repeats that command automatically; it verifies a pending event before reset and cleared native IDs through a fresh read-only connection afterward. `pending-reset.json` records the timed-out reply. Neither symptom froze FireRed; neither is silently called a flawless harness run. General same-process script reload, reconnect-budget exhaustion, high/unbounded fast-forward, crash-tail recovery and disk failure remain untested.

## Reusable scenario commands

These commands were actually run. The retained input trace provides every accepted bounded button command; screenshots and state samples verify segments. They are checkpoint-based scenario helpers, not an unattended campaign golden path. Source routing can encounter NPCs/trees/warps; inspect a failure and issue a reviewed intermediate route instead of bypassing story flags.

```sh
# Normal in-game preparation reached ViridianForest42,46, HP24/level7,
# following Oak parcel/Pokedex, mother heal and the catching tutorial.
# On the final ROM, Continue and capture the field checkpoint:
.venv/bin/python tools/phase1_events_scenario.py final-continue 'key 0 360 60' 'key 0 90 600' 'key 1 90 600'
.venv/bin/python tools/phase1_events_input.py sample checkpoint
.venv/bin/python tools/phase1_events_host.py --mode drop-ack-once --seconds 3600
.venv/bin/python tools/phase1_events_scenario.py final-rick-trigger 'key 6 16 600' 'key 0 90 600' 'key 0 90 600'
.venv/bin/python tools/phase1_events_scenario.py final-rick-selection 'key 0 90 600' 'key 0 90 600'
.venv/bin/python tools/phase1_events_scenario.py final-rick-seed 'key 7 1 60' 'key 0 90 600' 'key 0 90 600'
# Reviewed intermediate A segments are in input-commands.jsonl.
# At the observed Fight menu, open moves and select Tackle:
.venv/bin/python tools/phase1_events_scenario.py final-rick-tackle 'key 0 1 60' 'key 6 1 60' 'key 0 90 600'
.venv/bin/python tools/phase1_events_battle.py --label final-rick-finish --steps 40
# Stop the previous host before changing its fault mode.
.venv/bin/python tools/phase1_events_input.py reload sample
.venv/bin/python tools/phase1_events_host.py --mode disconnect-once --seconds 3600
.venv/bin/python tools/phase1_events_scenario.py final-wild-search 'key 5 64 180' 'key 6 64 180' 'key 7 64 180' 'key 6 64 180'
.venv/bin/python tools/phase1_events_battle.py --label final-wild-finish --steps 30
# With host stopped and no gameplay driver active:
.venv/bin/python tools/phase1_events_reconnect_probe.py --count 16
.venv/bin/python tools/phase1_events_input.py reload sample
# Offline battle inputs/reviewed recovery are retained in input-commands.jsonl.
.venv/bin/python tools/phase1_events_host.py --mode stale-ack-once --seconds 3600
# With host stopped, restore pre-Rick again and approach by ordinary input:
.venv/bin/python tools/phase1_events_input.py reload sample
.venv/bin/python tools/phase1_events_scenario.py final-pending-rick-retest 'key 6 16 180'
.venv/bin/python tools/phase1_events_pending_reset.py
.venv/bin/python tools/phase1_events_host.py --seconds 3600
.venv/bin/python tools/phase1_events_scenario.py final-reset-continue 'key 0 360 60' 'key 0 90 600' 'key 1 90 600'
.venv/bin/python tools/verify_phase1_events_emulator.py
```

Forced GC was executed once in the existing native scripting console: `collectgarbage('collect'); PI.log('socket-guard-GC','retired='..#PI.retired..' inputs='..#PI_INPUT.retired)`. The script was not reloaded. Native Emulation menu enabled2× fast-forward (actual AX title120.1fps); that bounded speed was used for final scenarios. Fast-forward was restored off, the prior Unbounded preference restored, and60fps observed before quitting. `emulator-settings.json` records that cleanup and closed loopback ports; no task host/emulator remains running. No claim is made for unbounded playback.

## Validation and deferred work

`phase1_events_test.py`:49 host tests,13 actual-C transport cases and7 actual-C observation cases with ASAN/UBSAN, enabled/disabled compiled ARM layout checks,43 architecture checks. Disabled ROM matches the supplied baseline SHA256 exactly. `bridge01-current-regression.json` records fresh independent BRIDGE-01 enabled/disabled builds and15 actual-C cases, retaining protocol1. Handoff60 checks/9 fixtures and retained Phase0/BRIDGE-01 live evidence12/27 assertions pass; those retained checks are not a new full baseline playthrough. `host-static-tests.json`, build manifests/logs, `replay.json` and `emulator-integration.json` distinguish each verification level.

Changed implementation groups: guarded source/linker/main hooks, `src/pi_events.c`/generated header; protocol/wire/mapping/Lua bridge; separate bounded test harness and build/host/scenario/replay/verifier tools; closed event schema and7 fixtures; actual-C and host tests; the two optional AI observation fields and documentation. No other AI schema redesign was necessary.

Next ticket: **BRIDGE-03 — bounded UI exchange**, with its event subrequirement already demonstrated here. Scope its small text/page protocol and tests separately. Before any NPC memory/model work, implement witness/delivery authorization and durable save/branch pairing. Follow/rewards, strategic posture, action legality/export, rematch identity normalization, party construction, battle policy, inference and endgame remain deferred.
