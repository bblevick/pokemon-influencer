# POKEBOOK-01 native player viewer — accepted

Final-build acceptance passed after the cursor/readback correction below. This ticket implements only presentation over accepted WORLD/MEMORY/SOCIAL/HERMES services. No new inference, posting/memory/distribution service, strategy, preparation, battle AI, resource rules or endgame implementation. The current result is recorded in `evidence/phase2/pokebook01/completion.json` with the accepted result.

## Native interface

Normal-field Start adds **PokeBook after Exit**, preserving Save, Bag, Pokemon, Options, Pokedex, story gates and the original nine-byte order array. At most eight normal rows use14pixel spacing and a14tile window above the help panel; other menus retain original behavior. Native home has Feed, Followers and Refresh. Native ListMenu lists three rows/page; A opens a complete post, Left/Right changes pages, B returns or immediately cancels pending work. The reader retains author identity. Exit uses `CB2_ReturnToFieldWithOpenMenu` and restores ordinary game controls.

Inspection of pinned FireRed's implementation established that its misleadingly named `cursorPos` is the scroll offset, while `itemsAbove` controls the visible row. The original viewer read the first output of `ListMenuGetScrollAndRow` as the row, causing wrong author/return selection for rows2/3. The first correction mistakenly changed initialization instead; the native three-row proof rejected it. Final code retains `ListMenuInit(template,0,row)` and reads `ListMenuGetScrollAndRow(task,NULL,&row)`. Actual-C regression checks initialization and row3→post-reference3/author-row3; live proof selects row3, reads five pages and returns to row3. Both candidate ROMs/databases/saves/logs/PNGs are preserved in `*-cursor-candidate` and `*-selection-candidate` directories and are superseded, not final acceptance.

## Authorization and information boundaries

`pokebook/viewer.py` is trusted host code bound to campaign, active branch, social restore epoch and player identity. Requests contain no actor selector, SQL, canonical-event query or director tool. Narrow discovery policy: validated **public completed-battle recaps involving this campaign's player**, plus already-authorized public deliveries to the player. Participation/author is determined from canonical completion records, never model prose. A trainer follow does not create reciprocal following or friendship. Actual incoming edges followed==player are deduplicated/count/listed with the same scope as rows.

The serializer allowlists only published postID/author/body. Private evidence IDs/observations, prompts, director episodes, grants and diagnostics never enter native payloads or previews. Visibility/participation/follower membership is revalidated every query. IDs are references, not permissions. One120second ephemeral snapshot retains stable IDs while new posts arrive; Refresh creates a new snapshot. Navigation has no persistent read markers. Browsing never calls Hermes, posts, follows, advances epochs, delivers claims or exposes another NPC. Publication, unread delivery, actual exposure and retained actor knowledge remain distinct; no autonomous exposure scheduler is added.

Hermes prompts/private evidence/retrieval/episode code is unchanged. Detailed private input still includes revealed player moves and the NPC's own announced actions, with canonical and bounded-observation records retained independently of UI pages. The accepted bundle deduplicates factual claims/caps64references: it is **not a complete chronological turn transcript**. `recap-detail-preserved.json` records this limitation. Public text is displayed in full without inference, summarization or truncation; it does not replace private model input.

## Paging, text and lifecycle

`bridge/pokebook_protocol.json` defines schema2/kind3 inside the existing transport2 presentation mailbox. Schema1 notices/choices retain their validation and safe field gates. Lua forwards exactly24query bytes and checks96byte reply/correlation; Python owns blocking connection establishment, never an emulator frame callback. Native modal ownership does not relax unrelated menu/battle/save safety.

Header24bytes: version/op, request/view/snapshot/post-reference u32s, page and reserved/page-count u16s. Limits:192posts/followers,64pages,3rows/page; each row is u32reference +19byte label (18safecharacters,FFdelimiter/zero padding). Reader pages have at most3×23characters +2native FEline breaks (71bytes). At most4096single-paragraph ASCII characters/post; unsupported Unicode/newlines/controls/placeholders and over-capacity history fail closed. No material text is silently dropped. Wrapping preserves original characters/spaces, with inserted presentation line breaks only. Pinned safe glyph widths are<=8px; conservative184pixel lines fit208pixel reader, with native `GetStringWidth(FONT_NORMAL)` checks. Labels check184pixels.

Actual-C validator rejects malformed lengths/schema/status, request/view/snapshot/post/page, FC/FD/FF content, misplaced FE and delimiter/padding errors. Existing FNV envelope binds nonce/run/command/payload. Cancel clears mailbox before freeing; stale replies fail transport/run/phase/request and native view checks. Host close operation exists; native exit leaves only one bounded ephemeral host view to expire. Timeout180frames yields an unavailable screen with immediate exit. Empty content and unreachable host are distinct; no fabricated cache/content appears on failure.

`CB2_OpenPokeBook` checks state/window allocation, owns BG0/tilemap/palette/window/ListMenu task, and releases its resources before native field return. Source hooks are in `docs/source_integration_map.md`. No trainer selection/party constructor/flag/VS Seeker/save serializer/AI hook changes.

## Build and resources

Pinned pret037335f4c725d7c9aecdac87066f2002b4bd7e14/toolchain remain unchanged. Final ROM SHA256 **bec6245f354e0846a9e606ba0665d9dabc2e4f9825ba278342755143de56e829**; manifest-enabled.json audits947unchanged original RAM symbols and original heap/stack boundaries. Only a4byte owner pointer is permanent, leaving220static EWRAM bytes. Disabled overlay byte-matches Phase0.

Temporary screen payload2260 + window13312 =15572bytes; added heap headers bring ownership cost to15604. Actual viewer readings:99068free/largest contiguous bytes,1task/1window/0sprites. Five closures must return identically to103072free/largest,11520allocated,6blocks,3tasks/1window/6field sprites and owner0. `emulator.jsonl.resources` is a read-only heap/task/window/sprite audit; static headroom is distinct from runtime heap. Actual-C ASan/UBSan separately tests allocation/partial-window failure,30pending cancellations, generation exit and selected-row restoration with hardware substitutes. No native allocation-failure or worst-case stack qualification is claimed.

## Managed saves and fixtures

Acceptance uses a new explicit final-build campaign lineage seeded from the user's local pre-Rick native battery, with **no old database/history migration or arbitrary build whitelist**. Native save structures are unchanged, but that fact alone does not certify cross-build history compatibility. Earlier HERMES/foundation evidence is preserved. Launcher selects the import checkpoint before initial activation; normal paired restores never auto-activate new history.

Normal Save requires an armed intent, drained transport, actual savedataUpdated receipt, validated flash checksums/counter, fsync/stable rereads and atomic four-cutoff pairing. Only fresh OS-process Continue with known paired batteries is supported. S1 predates battle: no future recap/follow/episode/claims. S2 restores exact four history hashes and actor facts while grant epochs advance. An old actual reader payload from the abandoned launch is rejected by nonce/envelope validation before presentation. Unmanaged savestates/reset/hot-load/rewind and distributed power-loss recovery remain unqualified.

Production host is offline-only and uses existing mandatory deterministic recap fallback. Rick's actual native battle creates the persisted recap and one follow, then normal menu browsing displays them. No fake production post is inserted. Old accepted Hermes public text is rendered only through explicit **Stored RICK** fixture mode sourced read-only from its accepted database; no new inference or migration is claimed. **Layout fixture** repeats that public body to form five pages/three synthetic rows solely for layout/selection tests. Fixtures create no history/follows/exposures. Neither mode is default production behavior.

## Commands and evidence

Run from this repository using `.venv/bin/python`:

```sh
.venv/bin/python tools/pokebook01_build.py --rebuild
.venv/bin/python tools/pokebook01_build.py --disabled --rebuild
.venv/bin/python tools/pokebook01_test.py
.venv/bin/python tools/pokebook01_retained_c.py
.venv/bin/python tools/pokebook01_launch.py --start
# Load .local/pokebook01-run.lua through native Tools > Scripting > File.
.venv/bin/python tools/pokebook01_host.py --seconds 1800
.venv/bin/python tools/pokebook01_viewer_scenario.py empty --label accepted-empty --menu-cursor 0
.venv/bin/python tools/pokebook01_input.py --label accepted-rick-start 'key 6 16 300' 'a 3' 'key 9 0 300'
.venv/bin/python tools/pokebook01_scenario.py battle --label accepted-rick --steps 60
.venv/bin/python tools/pokebook01_post_scenario.py
# Stop normal host before presentation-only fixture/fault peers.
.venv/bin/python tools/pokebook01_host.py --stored-output-fixture evidence/phase2/pokebook01/stored-hermes-public-fixture.json
.venv/bin/python tools/pokebook01_host.py --stored-output-fixture evidence/phase2/pokebook01/layout-public-fixture.json
.venv/bin/python tools/pokebook01_fault_scenario.py absent silent disconnect late schema malformed control stale-view stale-nonce missing oversized
# Stop task-local emulator/host before each paired restore.
.venv/bin/python tools/pokebook01_launch.py --start --save .local/pokebook01/S1.sav
.venv/bin/python tools/pokebook01_fault_host.py abandoned --seconds 30
.venv/bin/python tools/pokebook01_launch.py --start --save .local/pokebook01/S2.sav
.venv/bin/python tools/verify_pokebook01.py
```

Commands are stage-specific, not a blind restart sequence. Normal fresh Continue includes title/Continue input and dismissal of FireRed's quest replay before menu navigation. Exact native commands, completion markers, response hex, launches, receipts, save identities and resources are logged. Do not retry ambiguous Save blindly. Snapshots/PNGs/saves/SQLite stay local/ignored; screenshot hashes/index and shareable records live in evidence/phase2/pokebook01. Hardware-substituted tests and explicit fixtures remain distinct from real gameplay.

Checks:211baseline host tests anew,226final combined host tests (15new viewer tests), actual-C wire/lifecycle ASan/UBSan,48retained actual-C UI/event/observation cases, enabled/disabled ARM audits,60handoffchecks/9fixtures and43architecture checks. Final native proof covers entry/home/feed/full reader/followers/empty/unavailable, actual offline battle pipeline, no private leakage or browsing mutations, unread vs exposed Janice/Doug knowledge, five cleanup cycles, pending cancel/late reply, fault outcomes, movement, native Save/Continue, host restart and paired early/late restore. `verification.json` asserts evidence; it is not a replacement for inspected native screenshots.

Limitations: authored slice and explicit NPC exposure; ASCII/paragraph/record caps; manual script load and launch-bounded sockets; unsupported unmanaged rollback/reset; pending power-loss/worst-stack/full-campaign qualification; existing Hermes fact-deduplicated private packet. Next dependency task is separately authorized ROSTER-01, supplying the legality catalog for PREP-01 (also requiring CONTENT-01) before STRATEGY-01 consumes executable envelopes. `docs/strategy01_readiness.md` is planning only. System One preparation/installation/live control and endgame stay deferred. All task-owned processes must stop, inference remain offline/false and prior Hermes10/10 + closed5/10 ledgers remain unchanged at completion.

The post-scenario helper initially treated the bounded evidence packet as its evidence list and stopped while writing a diagnostic report, after successful read-only/exposure assertions and before arming a save. The helper now uses the packet's `evidence` field. The diagnostic was regenerated from unchanged authoritative data; the separate exact-intent Save command completed the native S2 proof. Its nonzero initial log is retained, not counted as a successful wrapper run.

## Accepted final run

Final campaign c203a489-7600-4153-806f-9e1fa64e09b6, branch 20c0a4b9-6fbc-4e5f-bff8-c4159e3a6e56. Ordinary native Rick victory:8turns/27canonical records/8observations, ACK35/drops0. Production mandatory offline outcome committed post `95e019a767b64c278129236bfceb6b5d048875aff8361442719660c3e0ba0bd3` and one Rick→player follow; native home/feed/reader/followers match the persisted author/body/count. Browsing and host restart preserve all four histories/trainer packets. Later controlled unread delivery gives Janice no knowledge; explicit exposure gives exactly public loss+Bulbasaur, Tackle remains private, Doug empty.

Final S1counter10/checkpoint faf650b6-08ef-417f-badf-aaf075ee0c1c restores empty feed/followers/future episodes/Janice claims. Replayed actual old production reader payload is rejected by old nonce before presentation. Final S2counter11/checkpoint 6da73242-64be-49f2-89e6-1e0bfc366e10 restores exact four history hashes/actor facts and the same native recap/follower, while restore epochs advance. Normal Save/Continue, movement after errors and native three-row selection are actual final-build evidence.

`verification.json` passed23assertions over actual logs/resources/fixtures/restores;148local screenshots are indexed in screenshots.json. Native pixels/author/row/count were separately inspected. All ten final fault outcomes pixel-match the native unavailable screen; delayed cancellation rejects phase, and actual abandoned timeline rejects nonce. Earlier candidate conclusions are explicitly superseded. Final restore helper's uppercase screenshot label was rejected before any input; the corrected lowercase rerun is the proof, with prevalidation failure retained. A transient CUA capture failure on the superseded selection candidate was recovered by stopping that task process and using a fresh managed launch. Launcher process matching now anchors the executable to avoid a test shell's literal path falsely appearing to be a running emulator.

**POKEBOOK-01 accepted; stop reached.** Task hosts/peers/emulator/listeners stopped, no pending save/job, accepted database backed up via SQLite backup. Hosted inference remains false/offline; original10/10 and closed5/10ledgers unchanged. User dump preserved/unuploaded. No next-phase or endgame execution. See cleanup.json/completion.json and docs/strategy01_readiness.md.

## D47 snapshot lifetime correction

Host-only single-owner snapshots use600-second idle expiry renewed by valid successful
scoped queries rather than absolute120-second age. Invalid queries do not renew;
branch/epoch/visibility/ownership/caps remain checked and idle expiration requires
reopen. Real C3 eight-post native browsing plus labeled9/12-row read-only fixtures
prove traversal without knowledge mutation. Final actual Kent feed remains unrun
because of the separate restart suspension; see [closeout](campaign_expansion01_kent_closeout.md).
ROM unchanged; permanent EWRAM delta0/headroom4.
