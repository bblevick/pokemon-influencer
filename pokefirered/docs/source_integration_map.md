# Phase 0 source integration map

Inspected commit: `037335f4c725d7c9aecdac87066f2002b4bd7e14` from pret/pokefirered. The table records Phase 0 candidate boundaries; implemented BRIDGE-02 hooks are listed separately below. Line numbers refer to this pin. Initial enhancement scope remains eligible single-trainer battles; preserve other modes.

| Surface | Inspected path and call flow | Integration constraint |
|---|---|---|
| Trainer selection | `src/scrcmd.c:1887` `ScrCmd_trainerbattle` → `src/battle_setup.c:787` `BattleSetup_ConfigureTrainerBattle`; approach path `ConfigureAndSetUpOneTrainerBattle` at 832; `StartTrainerBattle` at 896. Mode dispatch loads trainer/script arguments and remaps VS Seeker IDs. | Capture original and effective IDs/mode before rematch translation; no invented content bindings. |
| Party construction | `src/battle_main.c:707` calls static `CreateNPCTrainerParty` at 1539. It reads `gTrainers[trainerNum]` from `src/data/trainers.h` and typed party arrays in `src/data/trainer_parties.h`; calls `CreateMon`, then `SetMonData` for custom moves, PP and items. | Integrate a validated frozen plan before battle initialization through constructors. Preserve original identity and exclude Tower/e-Reader/special paths; never rewrite active party bytes. |
| Controller/action selection | `src/battle_controllers.c:65` `InitBattleControllers` separates link and single-player controllers; `InitSinglePlayerBtlControllers` selects tutorial/Safari/double paths. `src/battle_controller_opponent.c:1339` `OpponentHandleChooseAction` → `AI_TrySwitchOrUseItem`; 1350 `OpponentHandleChooseMove` → `BattleAI_SetupAIData` / `BattleAI_ChooseMoveOrAction`. `src/battle_ai_switch_items.c:358` and 428 own switch/item and replacement scoring; opponent `OpponentHandleChoosePokemon` at 1410 emits replacement selection. | Future observation/action adapter must cover action, move, voluntary switch/item and forced replacement separately. No AI modifications in Phase 0. |
| First-win event | `src/battle_setup.c:906` `CB2_EndTrainerBattle` branches on mode/outcome, returns to field and invokes `SetBattledTrainerFlag` / `QuestLogEvents_HandleEndTrainerBattle`. `HasTrainerBeenFought` at 881 queries `TRAINER_FLAGS_START + trainerId`. | Snapshot prior flag at setup, then explicitly require a victory and eligibility at completion. Early-rival loss also sets a trainer flag, so flag-setting alone is not victory evidence. Secret-base/special branches need exclusions. Host follow/reward idempotence comes later. |
| VS Seeker rematch | Configure dispatch at 813–826 maps rematch IDs through `src/vs_seeker.c:1075` `GetRematchTrainerId` → `GetNextAvailableRematchTrainer` / `TryGetRematchTrainerIdGivenGameState`; readiness at 1086. `src/battle_setup.c:954` `CB2_EndRematchBattle` clears last-talked rematch state on success; `StartRematchBattle` at 973 selects this completion callback. | Route native and social invitations through one future policy. Preserve first-battle flags and avoid duplicate reward paths. Audit full readiness predicates in CONTENT-01. |
| Menu and text | `src/start_menu.c:41` option enum/capacity, action table at 116, `SetUpStartMenu_NormalField` at 213 append gated Pokédex/Pokémon plus Bag/Player/Save/Option/Exit. `src/strings.c` contains menu labels; `charmap.txt` / preprocessor encode text; `src/text.c:1020` `GetStringWidth` measures engine glyph widths. | Extend enum/order/table/capacity together, preserve gates and existing actions. Encode bounded text and measure pixels; no arbitrary host bytes. |
| Save serialization | `src/start_menu.c:801` uses `TrySavingData(SAVE_NORMAL)` → `src/save.c:650` `HandleSavingData` → `src/load_save.c:196` `SaveSerializedGame` → `WriteSaveSectorOrSlot`. `src/save.c:803` `LoadGameSave` → `TryLoadSaveSlot` → `LoadSerializedGame` at load_save.c:202. `sSaveSlotLayout` at save.c:54 chunks SaveBlock2, SaveBlock1, PC storage; `UpdateSaveAddresses` at 630 resolves pointers. `include/save.h` defines two rotating 14-sector slots, 3968 data bytes/sector, footer signature/counter/checksum; `CalculateChecksum` at save.c:614 sums 32-bit words. | SAVE-01 must audit sizes, initialization, all save modes, checksums, rotation and migrations. No padding declared safe. `SetSaveBlocksPointers` at load_save.c:69 means addresses must not be assumed fixed. |

Phase 0 introduced none of those features. BRIDGE-01 now adds only the mailbox/debug PING described below; save markers, gameplay event export, LLM, endgame and battle policy remain absent. ELF symbol evidence for diagnostic same-value memory stores is in `evidence/phase0/elf-probe-symbols.txt`; these addresses are not bridge addresses.

## Implemented BRIDGE-01 surface

`ld_script.ld` adds a dedicated NOLOAD mailbox section after the complete upstream EWRAM section, without changing original RAM symbols. `src/pi_bridge.c` defines the initialized/section-attributed `gPiMailbox`, `PiBridge_Init`, `PiBridge_Tick`, compiled build tag and layout descriptor. `src/main.c` calls Init before its main loop and Tick after ReadKeys only under PI_BRIDGE. The isolated builder generates build identity and derives every mailbox address/offset from ELF/compiler output. Default PI_BRIDGE=0 produces the exact baseline ROM. At BRIDGE-01 completion no battle, trainer, menu, rematch or save hook above had been modified. BRIDGE-02 now adds the separately listed event-only hooks.

See `docs/bridge01.md`, `bridge/protocol.json`, generated `include/pi_protocol.h`, `evidence/phase1/manifest-enabled.json`. The debug-only trigger writes a request flag, then ROM code constructs PING; Lua never constructs a gameplay event.

## Implemented BRIDGE-02 event hooks

The isolated overlay compiles the following hooks against the same source pin. They export facts/observations and preserve native decisions:

| Actual hook | Meaning / limitation |
|---|---|
| `BattleStartClearSetData`, after native turn/special-status reset (`src/battle_main.c`) | `PiEvents_BattleStart`: supported single encounters only; captures effective `gTrainerBattleOpponent_A` and `HasTrainerBeenFought` snapshot. |
| `HandleTurnActionSelectionState`, entry | `PiEvents_Turn`: once per native turn; typed turn event and distinct NPC-side observation. |
| `BattleTurnPassed`, entry | `PiEvents_NextTurn`: allows next selection observation. |
| `RunTurnActionsFunctions`, after native action returns and action index advances | `PiEvents_Action`: completed slot/announced move, no selected category. This is not proof a move damaged the target. |
| `Cmd_attackstring`, only in actual `STRINGID_USEDMOVE` branch (`src/battle_script_commands.c`) | `PiEvents_Reveal`: captures displayed move; tracks player revelation per internal party slot, never exports that slot/private party. |
| `HandleEndTurn_FinishBattle`, before `TrySetQuestLogBattleEvent` | `PiEvents_End`: actual outcome; victory emits trainer defeat then battle end. Native flag/field completion remains unchanged. |

Source truth exporter: `src/pi_events.c`; generated bounded ABI: `include/pi_events.h`. Same reserved linker section holds the196-byte mailbox and472-byte control/queue state. See `docs/bridge02.md` and `evidence/phase1/bridge02/manifest-enabled.json`. No party construction, controller/AI selection, follow/reward, original VS Seeker readiness, menu or save serializer implementation was added. First-defeat eligibility/content exclusions and original/effective rematch identity normalization remain future domain work.

Final-build integration evidence: SHA256 `eb8ce46de923e3d85216754ec880d50e8fdc2c95efa31a1dff73d4cbd6df6214`, retained53 live assertions in `evidence/phase1/bridge02/emulator-integration.json`. Rick's inspected binding is `data/maps/ViridianForest/scripts.inc` → `TRAINER_BUG_CATCHER_RICK`, numeric102 in `include/constants/opponents.h`; `src/data/trainers.h` selects `sParty_BugCatcherRick`, whose source party is Weedle6/Caterpie6 in `src/data/trainer_parties.h`. His map object is47,45, facing left, sight5; the private pre-battle checkpoint is42,46. Actual native victory emits trainer102 defeat before end. Source-map/test diagnostics and private saves never enter the NPC observation builder.

## BRIDGE-03 inspected native UI hooks

`src/overworld.c`: feature-gated `PiUi_IsField` compares native CB1_Overworld/CB2_Overworld; `DoCB1_Overworld` calls `PiUi_Field` before ordinary player input. `src/main.c` adds initialization/deadline ticking after the existing bridge hooks. `src/pi_ui.c` validates commands and owns control locks/object freezes, field message, printer completion, notice keys and native yes/no results. Existing `ShowFieldMessage`/`HideFieldMessageBox` live in `src/field_message_box.c`; `DisplayYesNoMenuDefaultYes` is in `src/new_menu_helpers.c`; `Menu_ProcessInputNoWrapClearOnChoose` and native menu destruction are in `src/menu.c`. `src/text_printer.c` adds a feature-gated printer0 cancellation function accessing its actual static `sTextPrinters` array. No new global printer struct or guessed pointer is used. `charmap.txt` provides the audited ASCII encoding subset. The shared generated ABI and ARM manifest allocate a separate presentation mailbox; canonical-event and bounded-observation structures are unchanged. Save serialization, AI, party construction, trainer flags and rematch scripts receive no BRIDGE-03 hooks.

## WORLD-01 implemented host integration

The historical Phase1 statements above describe what was absent at those milestones. WORLD-01 now implements host-side canonical persistence and **managed normal battery** pairing, not arbitrary RAM/savestate origin recovery.

- Existing `PiEvents_BattleStart/Turn/Action/End` records are decoded by `bridge/events.py` and transactionally ingested by `world/store.py`; no additional trainer, battle or ROM hooks were added. The final B3 ROM and every recorded overlay source hash are unchanged.
- `tools/world_registry.py` reads pinned `include/constants/opponents.h`, `src/data/trainers.h`, all `data/maps/*/scripts.inc` references and `src/vs_seeker.c:sRematches`. The explicit registry normalizes effective VS Seeker and story-person variants. Rick102 resolves to `fr:trainer:0102`; there is no Rick VS Seeker entry.
- `world/saves.py:layout_from_build/fingerprint` reads actual compiled `sSaveSlotLayout` through the B3 ELF symbol and validates the serialized sectors defined by `include/save.h`. `src/save.c:GetSaveValidStatus` supplies slot/counter selection semantics; `HandleWriteSector` supplies rotation and checksum semantics. No save serializer or struct is modified.
- `tools/world01_launch.py` derives a local diagnostic lifecycle receipt from the existing pinned mGBA `savedataUpdated` callback. Pinned native implementations are `GBAFrameEnded` (`src/gba/gba.c`) and `GBASavedataClean/GBASavedataRTCWrite` (`src/gba/savedata.c`). Lua still listens; it never calls a blocking socket connection. Host fsync, validated content and a durable save intent establish the checkpoint barrier.
- Future memory consumers must use separate provenance/scoped grants. Canonical truth APIs do not provide NPC knowledge authorization. No party constructor, battle controller/AI, menu text, follower, social or endgame integration was added.

Authoritative contracts and evidence: `docs/world01.md`, `docs/world_schema.md`, `docs/trainer_identities.md`, `docs/world_saves.md`, `evidence/phase2/world01/`.

## MEMORY-01 implemented host knowledge boundary

No new ROM hooks or bridge ABI changes. `memory/store.py:MemoryStore._derive` consumes the persisted launch/run/domain battle correlation and a field allowlist: participant start/end, BATTLE_OBSERVATION's opponentActive revealed species/moves, and explicitly visible player announcements already produced by `Cmd_attackstring`/`PiEvents_Reveal` and the completed action exporter. Own HP/PP/moves, previous-win flags and unannounced action slots never enter actor claims. Rick102 and Janice116/507/508 bind through the existing pinned WORLD registry; the actual constants were inspected at pret037335f4c725d7c9aecdac87066f2002b4bd7e14. No duplicated rematch identity logic.

MemoryStore's transaction extension derives evidence before the existing host ACK and pairs subjective cutoffs with normal-save checkpoints. `ActorView` is the future retrieval boundary; the trusted host issues a fixed actor/campaign/branch/two-cutoff grant. `deliver_fixture` is a development-only one-claim receipt, never a broadcast/UI/canonical event. Legacy WorldStore is rejected as a writer on an extended database. See `memory_schema.md`, `memory01.md`, `evidence/phase2/memory01/`. Native battle selection/party construction/first-win flags/VS Seeker/text/save serializer/AI remain unchanged.

## SOCIAL-01 host integration

No new pinned-source ROM hooks are required. The accepted canonical completed-battle event and MEMORY direct evidence feed `SocialStore._after_memory_transaction` before commit/ACK. `social/policy.py` proposes only supported author references; service validation/persistence owns follows/posts, explicit ticks own one-hop feed distribution, explicit scoped exposure uses MEMORY's authorized delivery primitive. Native checkpoint hooks are reused with a third host cutoff. Species render names are independently reproduced from pinned `include/constants/species.h` and `src/data/text/species_names.h` via `tools/social_species_catalog.py`. Trainer selection/party/menu/save serializer/AI source remains unchanged in this ticket.

## POKEBOOK-01 inspected and implemented native hooks

Pinned source remains037335f4c725d7c9aecdac87066f2002b4bd7e14. `src/start_menu.c` adds the feature-gated action/table/help and normal-field entry only; its callback performs the existing fade/menu cleanup before `CB2_OpenPokeBook`. The unchanged9byte order array holds8normal items; eight-row spacing14pixels and `CreateStartMenuWindow` in `src/new_menu_helpers.c` use14tiles to fit the existing help panel. Save/Bag/Pokemon/Options/Pokedex flags/actions retain their original meanings. Disabled overlay byte-matches baseline.

`src/pi_pokebook.c` owns checked temporary native BG0/window/tilemap/ListMenu state, post pagination and the normal return callback `CB2_ReturnToFieldWithOpenMenu`; it follows inspected native screen/window/list lifecycle rather than invoking the Fame Checker itself. `src/pi_ui.c` checks the existing envelope checksum and reserves kind3 for this modal owner; old field notices/choices retain their safe-state rules. `bridge/ui_mgba.lua` forwards bounded schema2 viewer requests through the existing presentation mailbox; no additional gameplay facts or observation hooks were added. `pokebook/viewer.py` supplies a campaign/branch/restore/player-bound allowlisted projection over accepted domain records. No battle selection/party constructor/AI/first-win flag/VS Seeker/save serializer hook is changed by POKEBOOK-01.

Actual final hash,947original-symbol audit, runtime resource measurements, native battle/viewer/fault/save evidence and explicit fixture distinction: docs/pokebook01.md and evidence/phase2/pokebook01/. Preparation and legal-action integration remain future work under D22.

## ROSTER-01 host-only source readers

`roster/extract.py` compiles `src/data/pokemon/{species_info,level_up_learnsets,level_up_learnset_pointers,tmhm_learnsets,evolution}.h`, battle_moves/trainers/trainer_parties headers with effective FireRed constants. `src/data/wild_encounters.json(.txt)` selects FireRed maps/methods; items.json(.txt) describes item categories, with actual `src/data/party_menu.h:sTMHMMoves` mapping. The unchanged `src/pokemon.c:GiveBoxMonInitialMoveset/GiveMoveToBoxMon/DeleteFirstMoveAndGiveMoveToBoxMon` functions provide default-move semantics; `GetEvolutionTargetSpecies`, evolution_scene's National Dex gate and party_menu TM/HM consumption/IsMoveHm rules bound the supported primitives. Existing stable registry families and memory.store.actor_id bind identities. No new hooks/constructor/save/AI edits were made. Independent verification reads the existing accepted ELF/ROM; host-native accessor substitution is not installation proof. See docs/roster01.md.


## SYSTEM1-01A controlled constructor overlay — D33

Inspected source at the same pin: `CreateNPCTrainerParty` in src/battle_main.c is invoked before enemy battle initialization. The isolated builder tools/system1_01a_build.py inserts `PiPreparation_CreateParty` before its vanilla party dispatch; this function in native/system1_01a/pi_preparation.c uses `CreateMon`, explicit four moves/PP and held-item `SetMonData`, preserving original fixed IVs and stable original-lineage personality. It returns only for the committed ordinary Rick route; other modes/trainers retain vanilla construction. No live Pokemon memory replacement or battle-AI hook was added.

The isolated src/main.c initializes a separately allocated gPiPreparation; isolated src/overworld.c polls `PiPreparation_Field` at safe field state. This validates the authenticated plan and calls inspected `BattleSetup_ConfigureTrainerBattle`/`StartTrainerBattle` with a durable releaseall/end return script. Existing trainer defeat flags and source trainer bag data remain intact. This is a typed controlled acceptance entry, not authored VS Seeker/invitation/reward UX. SaveBlock serialization is unchanged; actual new-build compatibility checks41 catalog sources plus native layout/ELF/RAM, and the host appends actual build provenance while retaining baseline logical catalog identity. Normal Save19 paired restores include immutable host decision/commitment/installation cutoffs. See docs/system1_01a.md and manifest-native.json; actual constructor count1 and party comparison are emulator evidence, while all16 compiled validator cases are separate host evidence.


## BATTLE-01 actual isolated hooks (D34)

Pinned source remains037335f4c725d7c9aecdac87066f2002b4bd7e14. Isolated build .local/battle01-native-v3, manifest evidence/phase4/battle01/manifest-native.json. OpponentHandleChooseAction -> PiBattle_Select(PB_NORMAL); OpponentHandleChoosePokemon -> PiBattle_Select(PB_REPLACE), bypassing already-pending voluntary targets; OpponentHandleChooseMove -> PiBattle_Move emits the frozen slot/target once. Original controller fallback remains intact. battle_main PiEvents_BattleStart/End neighbors allocate/free work; RunTurnActionsFunctions records resolved chronology; battle_script_commands announced-attack callback retains revealed moves. CheckMoveLimitations and AreAllMovesUnusable remain original engine authority. Item wrapper stages normal AI itemType/flags/chosenItem and consumes trainerItems slot; normal scripts implement effects. No mutation of gTrainers, defeated flags, battle stats or RNG. See native/battle01 and tools/battle01_build.py for exact unambiguous patches. Native save serialization is unchanged; host BattleStore pairs a separate audit prefix/hash with normal checkpoints. Scope/fixtures/unsupported modes: docs/battle01.md.


## BATTLE-END-01 inspected terminal lifecycle (D38)

Actual pinned build `.local/battle-end01-external-v2`, pret037335f4c725d7c9aecdac87066f2002b4bd7e14:
Cmd_checkteamslost in battle_script_commands.c totals remaining party HP and sets
outcome. HandleEndTurn_FinishBattle in battle_main.c copies PiEvents_End exactly
once after TRY_FINISH/FINISHED, before PiBattle_End/free/fade/callback return.
CB2_EndTrainerBattle in battle_setup.c chooses ordinary WhiteOut or field-script
return; PewterCity_Gym/scripts.inc launches real trainer414 and grants flags only
in its DefeatedBrock continuation. Original hook/script unchanged. Test ELF-resolved
addresses and actual transitions are evidence/phase4/battle_end01/native-hooks-*.json
and lifecycle-trace.json; contract diagram is docs/battle_terminal_contract.md.
