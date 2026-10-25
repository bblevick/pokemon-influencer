# BRIDGE-03: bounded native presentation

Implementation scope is generic presentation only. UI content and responses are not canonical facts, NPC observations, social actions, follows, rewards or AI decisions. No credentials or hosted inference are used. Native FireRed resolves player input. WORLD-01 is the next milestone and is not implemented here.

## Build and allocation

Pinned pret source and matching agbcc remain the Phase0 pins. `PI_UI=0` and `PI_UI_TEST=0` are defaults. The acceptance build uses `PI_BRIDGE=1 PI_EVENTS=1 PI_UI=1 PI_UI_TEST=1 PI_BRIDGE_TEST=0 MODERN=0` on English FireRed revision0. `PI_UI` requires `PI_EVENTS`. `PI_UI_TEST=0` compiles out the mailbox diagnostic trigger. No story NPC/script or campaign flag was repurposed.

A dedicated NOLOAD allocation follows all original EWRAM. The196-byte BRIDGE-02 mailbox and472-byte event state remain unchanged; `gPiUi` adds148bytes and its private control state64bytes. Combined allocation880bytes leaves224bytes of EWRAM. All947 original RAM records, heap and IWRAM boundary remain unchanged. Existing stack/global gap2496bytes is preserved; worst stack depth remains unmeasured. UI allocation uses no new heap allocator. Native windows use the existing window subsystem. Generated C offset/size assertions and the actual ARM-compiled offset descriptor are checked against the JSON specification and ELF. Launcher and host independently verify the UI symbol/address/size, every offset, compiled descriptor and codec/harness hashes before use; five actual-manifest positive/forged-input tests cover that gate. Addresses must come from the manifest, never this document.

Final hash and actual checks are recorded in `evidence/phase1/bridge03/manifest-enabled.json`; disabled ROM must equal Phase0/user dump. Exploratory build records are retained under `attempt1/` and `attempt2/` and are not final acceptance.

## Separate versioned envelopes

Shared ABI: `bridge/ui_protocol.json`; generated C header: `include/pi_ui.h`. Host domain schemas: `schemas/bridge/ui-{command,response}.schema.json`. Binary codec: `bridge/ui.py`. The existing PI02/protocol2 outer envelope remains unchanged (36-byte header,u16 length prefix,96-byte payload limit,FNV corruption check,build tag,launch nonce,run,sequence,type,result/error). Authentication still checks the random local token and full ROM SHA256. A checksum is not an authorization mechanism.

Additional types5 UI_REQUEST,6 UI_COMMAND,7 UI_RESPONSE,8 UI_RECEIPT occupy their own presentation lane. Wire kinds1 request,4 command,5 response,6 receipt are distinct from canonical-event kind1/type3 and its kind2/type4 ACK. Incoming host content never enters `bridge.events.Consumer`. Accepted player responses go only to `ui-responses.jsonl`; no world projections or exposure permissions are changed.

- Diagnostic request: `<HHI>` schema1,command kind,requestID; outer sequence=requestID.
- Command: `<HHIIHHHH>` schema1,kind,requestID,TTL ticks,count,YES stable ID,NO stable ID,text length, then encoded text. Outer sequence=commandID. Maximum68bytes (20-byte header+48text). UI_NOTICE=1 has no choices and zero IDs. UI_CHOICE=2 requires count2 and distinct positive u16 IDs. YES/NO labels are fixed native ROM text. Host API rejects other labels/counts; no host label bytes enter a printer. A new version/command variant may introduce a generic menu later.
- Response: `<HHIIHH>` schema1,kind,commandID,requestID,result,choiceID; outer sequence=commandID. IDs plus full build/nonce/run correlate it. OK=0;MALFORMED=2;SCHEMA=3;TEXT=4;BUSY=5;TIMEOUT=6;CANCELLED=7. A notice acknowledgement has choice0. Choice OK must contain one of the supplied IDs; B cancels with choice0. Failure results are terminal transport outcomes, not gameplay facts.
- Receipt: empty payload,kind6/type8,matching command/run. Late, wrong-run, wrong-request, unsolicited, zero-ID and duplicate commands cannot start another UI. Command IDs are strictly increasing per authenticated run in the launch-bounded adapter.

Host response dedupe is bounded256 and rejects conflicting duplicates and capacity exhaustion. The fixture host has at most256 requests/commands per launch. It is test scaffolding, not a durable runtime.

## Text contract

Pipeline: host UTF8 strict decode → CRLF-to-LF normalization → ASCII allowlist → bounded word wrapping → explicit FireRed encoding → checksummed command → independent ROM validation → ROM-owned EOS → native field printer.

Supported: A–Z,a–z,0–9,space,`! ? . - ' , /`,newline. Mapping comes from the pinned `charmap.txt`: space00,digitsA1–AA,punctuationAB/AC/AD/AE/B4/B8/BA,uppercaseBB–D4,lowercaseD5–EE,newlineFE. FF is appended only by ROM; FC,FD,FA,FB,unknown bytes and all embedded terminators are rejected. Host raw UTF8 cannot be passed directly to the printer. Placeholder braces, tabs, NUL, lone CR, malformed UTF8 and Unicode outside the subset are rejected. No arbitrary pointers, native function names or script bytes exist in the command.

Maximum48encodedbytes including the optional single newline; two nonempty lines, at most24characters each. One-line input longer than24 wraps once at the last space at/before column24. No silent truncation or paging. If either resulting line is too long or the encoded total exceeds48, reject. CRLF is the only control normalization. Maximum24 glyphs at native normal font's8-pixel maximum width fits the dialogue text area. ROM separately enforces line/count/length/character bounds before constructing its49-byte EOS buffer. Because every allowed byte excludes placeholders/control syntax, the reused `ShowFieldMessage` placeholder expansion has no host-controlled expansion token.

## Native scheduling and ownership

`src/pi_ui.c` owns its small lifecycle. `src/main.c` initializes it and ticks deadlines after the existing event bridge tick. `PiUi_IsField` compares the actual native callbacks to CB1_Overworld/CB2_Overworld. `DoCB1_Overworld` calls `PiUi_Field` before player field input; only this ordinary overworld path can acquire the UI.

Accept only a solicited response in WAIT_COMMAND. Validate schema,identity,checksum,kind,choices,text and TTL first. Then require ordinary field callbacks, unlocked controls, disabled script context, no palette fade, hidden field message, no quest-log playback (including the last scene/running playback state), and stationary player. Unsafe commands receive BUSY immediately; no deferred queue. This excludes battle callbacks, save/start-menu locks, transitions, scripts and existing modals. UI already in flight rejects additional commands in Lua without touching native UI.

Acquire field controls and freeze field objects only after those checks. `ShowFieldMessage`/its existing draw task prints the text. Once printing completes, notice waits for a new A/B press; choice uses `DisplayYesNoMenuDefaultYes` and `Menu_ProcessInputNoWrapClearOnChoose`. Stable IDs are separate from labels. Release closes only the owned yes/no window, cancels only printer0 through the feature-gated `PiUi_StopPrinter`, hides its field message, unfreezes objects and unlocks controls. Native yes/no input destroys its window itself; the release path avoids a second removal. No battle AI/controller, party, first-win flag or flash serialization changes exist.

Request wait180ROMticks, presentation TTL60–900ticks, response delivery180ticks. The ROM never locks controls while waiting for a host. Even displayed UI cancels at its deadline. Responses retry every60emulatorframes within the ROM delivery bound and dedupe at the host. Failure to receive a receipt clears the lane after the delivery deadline. Extra debug triggers while busy are consumed without replacing the request. No unbounded queue or wait exists.

## Reset, rollback and reconnect

Keep the BRIDGE-02 tested localhost listener, bounded RX/TX512,128-byte receives,two parses/frame, one client, no synchronous Lua connect or inference. A new UI adapter is derived from that retained listener; BRIDGE-02 Lua itself is unchanged. The SIGPIPE-ignore launcher, EOF detection and bounded closed-native-object retention remain necessary for the pinned mGBA.128 retired gameplay sockets require a fresh process at exhaustion. Same-process script reload/unlimited reconnect remain unsupported.

A command's captured nonce/run must match the separate current authority fields. Lua publishes those independently of HELLO so absence/reconnect cannot reauthorize an abandoned command. Reconnect in the same run preserves identity. Reset callback/heartbeat regression creates a new run; C initialization clears pending UI on ROM reset. Managed test `reload` calls `PI_UI.boundary` immediately after explicit-ALL load, before advancing another ROM frame: invalidate authentication, advance run, publish current authority. An owned restored modal is closed by the first ordinary-field hook; restored pending commands/responses are discarded. Old host responses cannot be accepted for the new run. Native framebuffer contents belonging to the loaded snapshot are not a newly accepted command.

This is **transient UI cancellation**, not durable game/host save pairing. Arbitrary unmanaged loads/rewind with equal or higher heartbeats are not detected reliably and are outside the supported contract. Managed loads must go through the retained boundary; use a fresh process for unsupported lifecycle operations. Restored BRIDGE-02 queued gameplay records still lack durable origin identity. WORLD-01 must resolve canonical save/branch pairing before NPC memory consumes them.

## Reproduction

All paths are relative to repository root. The supplied dump is neither modified nor uploaded. Native saves/checkpoints/screenshots remain ignored local inputs/artifacts.

```sh
.venv/bin/python tools/phase1_ui_build.py
.venv/bin/python tools/phase1_ui_build.py --disabled
.venv/bin/python tools/phase1_ui_test.py
.venv/bin/python tools/phase1_events_build.py --output-prefix phase1-ui-events --evidence-dir evidence/phase1/bridge03/events-regression
.venv/bin/python tools/phase1_events_build.py --disabled --output-prefix phase1-ui-events --evidence-dir evidence/phase1/bridge03/events-regression
.venv/bin/python tools/phase1_events_test.py --build-prefix phase1-ui-events --evidence-dir evidence/phase1/bridge03/events-regression
.venv/bin/python tools/phase1_build.py --output-prefix phase1-ui-ping --evidence-dir evidence/phase1/bridge03/ping-regression
.venv/bin/python tools/phase1_build.py --disabled --output-prefix phase1-ui-ping --evidence-dir evidence/phase1/bridge03/ping-regression
.venv/bin/python tools/phase1_test.py --build-prefix phase1-ui-ping --evidence-dir evidence/phase1/bridge03/ping-regression
.venv/bin/python tools/phase1_ui_launch.py --start
```

Existing output directories are intentionally refused; use `--verify-existing` for audits, or move prior outputs aside before a fresh build. Fresh mGBA process: Tools→Scripting→File→Load `.local/ui-bridge-run.lua` exactly once; minimize the Scripting window. Native file loading is the one unavoidable manual launch step; CLI autoload is not claimed. The launcher ignores inherited SIGPIPE using `restore_signals=False`.

```sh
.venv/bin/python tools/phase1_ui_host.py --seconds 1800
.venv/bin/python tools/phase1_ui_input.py 'a 2' 'key 0 10 400' 'shot final-continue'
.venv/bin/python tools/phase1_ui_input.py 'key 0 10 150' 'ui 1' 'key 9 0 60' 'shot questlog-busy-final' 'key 1 10 500' 'shot field-final'
.venv/bin/python tools/phase1_ui_input.py 'checkpoint'
.venv/bin/python tools/phase1_ui_scenario.py acceptance
.venv/bin/python tools/phase1_ui_scenario.py faults
```

Use only the private normal campaign battery copy seeded by the launcher. Final-build checkpoints are created afresh; do not load BRIDGE-02 savestates into this ROM. Queued test input expresses native key presses, screenshots and a feature-gated diagnostic request, with no NPC/gameplay-memory mutations. The test socket is separate from production transport. Exact command/reply trace is in `input-commands.jsonl`. Reset can unwind its input callback before replying: do not repeat an ambiguous reset; verify independently over a new read-only sample.

## Final actual results — 2026-10-02

BRIDGE-03 passes for the pinned mGBA0.10.5 process, normal playback and **managed** snapshot workflow. This closes Phase1's supported bounded prototype. General emulator support, arbitrary rewind, production-duration socket robustness and durable world/save consistency are not claimed.

Final enabled SHA256: `739bd3eebb91aaa5210f8f8cd1f357a8272dc98db7060356c649b4c38a0dbc2d`. It changed from BRIDGE-02 `eb8ce46de923e3d85216754ec880d50e8fdc2c95efa31a1dff73d4cbd6df6214`. Disabled SHA256 remains `3d0c79f1627022e18765766f6cb5ea067f6b5bf7dca115552189ad65a5c3a8ac`. The user's dump and retained dump copy are unchanged.

Actual checks:75host unit tests (49 retained+26UI),28actual-C UI validation/lifecycle cases with ASAN/UBSAN (native printer/menu excluded),13actual-C event transport cases,7actual-C observation cases,15actual-C PING cases; fresh BRIDGE-01/02 enabled and exact-disabled builds; actual ARM layout/allocation checks;43architecture checks;60handoff checks/9reference fixtures. Retained Phase0/BRIDGE-01/02 evidence assertions12/27/53 passed; those assertions are not new playthroughs. The final UI evidence verifier passes144assertions bound to21accepted UI outcomes and18real gameplay/observation records. Native UI rendering was visually inspected separately from those machine assertions.

Final session2870791104: notice command2 acknowledged; choice command3 returnedNO/choice22. Malformed schema/control/terminator/length/count/ID/oversized text/short commands were rejected without rendering; UI timeout cancelled an owned message; duplicate/stale commands were rejected; an intentionally missed player-result receipt produced a duplicate deduped by the host. Quest-log, native Start menu and active wild battle returnedBUSY. Silent/disconnect/oversized-wire/fully absent-host scenarios each recovered an idle lane and native coordinates42,46→43,46→42,46. The initial8-frame direction inputs only turned the player; their failed movement audit is retained, and the final replay uses an explicit facing tap plus16-frame movement.

Pending owned notice snapshot: old command17/run1 was acknowledged, then reloaded; managed authority moved to run2 and the restored modal cleared before further ROM interaction. No old command17 response was accepted in run2. Fresh command18 completed there. Pending choice19/run2 was reset; native IDs cleared and HELLO/run3 established; choice19 produced no accepted response in the new run. Reset lost its reply and the first read-only reconnect reset its socket. Neither reset nor ambiguous mutations were retried; independent read-only checks succeeded. Fresh command20/request1 completed in run3. A stopped/restarted fixture host restored launch-scoped correlation/dedupe from validated log bytes and command21 completed; this is not a durable world runtime.

Final-ROM ordinary wild Weedle4 victory exported18records over4turns, with separate canonical and observation sinks; no UI content entered either. A managed pre-battle reload for availability retakes created run4; this explicitly retained the abandoned run3 records without pretending to pair canonical history to the native save. Native in-game Save then wrote counter4; its14-section slot checksums and retained local copy hash passed. Save polling initially saw the prior valid slot while native flash writing was still in progress; completion was asserted only after the actual savedataUpdated callback, return to field and valid counter4. No fresh OS-process reload of this new save is claimed; Phase0/earlier retained fresh-save reload evidence remains separate.

Additional exact commands:

```sh
.venv/bin/python tools/phase1_ui_boundaries.py rollback
.venv/bin/python tools/phase1_ui_boundaries.py reset
# After the independently verified input-socket failure, without repeating reset:
.venv/bin/python tools/phase1_ui_boundaries.py reset --resume-reset
.venv/bin/python tools/phase1_ui_unavailable.py disconnect
.venv/bin/python tools/phase1_ui_unavailable.py timeout
.venv/bin/python tools/phase1_ui_unavailable.py oversized-wire
# Stop the fixture host, then run the real absent case:
.venv/bin/python tools/phase1_ui_unavailable.py absent
.venv/bin/python tools/phase1_ui_host.py --seconds 1200
# Reviewed native wild opening followed by bounded ordinary Fight/Tackle input:
.venv/bin/python tools/phase1_ui_battle.py
.venv/bin/python tools/verify_phase0_save.py --manifest evidence/phase1/bridge03/manifest-enabled.json --save .local/phase1-ui-emulator/bridge03-native-counter4.sav --report evidence/phase1/bridge03/native-battery-save.json
.venv/bin/python tools/verify_phase1_ui_emulator.py
.venv/bin/python pokemon_influencer_handoff/tools/validate_handoff.py
.venv/bin/python tools/validate_ai_contracts.py
.venv/bin/python tools/verify_phase0_emulator.py
.venv/bin/python tools/verify_phase1_emulator.py
.venv/bin/python tools/verify_phase1_events_emulator.py
```

The exact native save/direction/Continue/wild inputs and reply outcomes are retained in `input-commands.jsonl`. Build logs begin with exact make argv/cwd/feature flags; test JSON reports include argv/exit status/log path. Reset/rollback provenance is in `*-boundary.json` and `input-reset-recovery.json`; native save in `native-battery-save.json`; independent host/source/ABI checks in `host-static-tests.json` and the two regression directories; final live evidence in `emulator-integration.json`, `scenarios.jsonl`, separate UI/event/observation sinks and host/emulator traces. `changed-files.json` lists the source/tool/document inventory. `screenshot-recovery.json` documents a reused-label capture bug: original bytes were restored from SHA256-identical retained native images; new host-restart captures were preserved separately; the driver now uses unique replay names and actual queued completion markers. Failure/attempt artifacts are retained and excluded from final acceptance.

When no command was assigned (absent/silent/disconnected host or a rejected transport frame), the ROM emits a bounded diagnostic terminal with command0 and the requestID; the fixture host does not accept it as a player response or canonical fact. Delivery expires rather than keeping the game waiting. Both implemented command variants require a player reply; fire-and-forget presentation is not supported.

Remaining risks:224-byte EWRAM headroom and unmeasured worst stack depth; native mGBA socket defects guarded only for bounded fresh-process launches; no same-process script reload or high/unbounded playback qualification; no reliable arbitrary unmanaged rewind detection; no durable origin/branch/save pairing or world projection; fixture log crash-tail/disk recovery is not production storage; fixed YES/NO labels and limited ASCII/48bytes. All task-launched processes/listeners were stopped. No mocked or unrun emulator scenario counts as acceptance. Stop after BRIDGE-03; next WORLD-01 covers canonical world state, persistent trainer identities, event ingestion and save/branch pairing without an LLM.
