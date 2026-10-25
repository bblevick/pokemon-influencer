# BATTLE-END-01 — accepted, 2026-10-05

Completed this gate repair only, with **zero hosted inference**. VERTICAL-SLICE-01
remains blocked at its live closeout. The original closed 66-request ledger,
accepted pre-Brock database/save, exact StrategyMemo/commitment, providers,
prompts, legality, roster, virality policy and user dump are unchanged.

## Earliest failing boundary

**A: the previous harness abandoned native terminal presentation before the
finish hook ran.** The original three `gate-attempt*-ended` snapshots had matching
sequence/ACK 17/25/57, zero transport failures, and a still-allocated 1036-byte
battle Work pointer. The inspected screenshot says **AA paid prize money**, with
Onix alive; it is a player-loss presentation, not opponent exhaustion or victory.
The old runs were restored before cleanup. There is no evidence of B, C, D or E
in those three original attempts. Their absence of BATTLE_ENDED must not be
rewritten as a confirmed win, confirmed completed loss, or Mercury defect.
`original-boundary-investigation.json` retains the original samples. The 35
historically resolved choices and last aborted choice are explicitly annotated
in `prior-gate-dispositions.json`; this is retrospective audit, not a fabricated
native cancellation receipt or a rewrite of the original ledger/database.

Completing a real loss through its final dialogue produced the existing native
finish hook, canonical loss, automatic obligation and whiteout. A genuine win
required finishing Brock's long defeat speech. Even the *battle-screen* sentence
“received the BOULDERBADGE” precedes actual Gym flags: it is part of Brock's
Defeat text. Native script return, not that sentence, grants progression.

Two independent defects were repaired instead of relocating the correct hook:
terminal records could expire after three ordinary queue attempts, and interrupted
external choices lacked a durable terminal disposition. Lua also needed a safe
receipt after the tactical heap allocation was freed.

## Fix and inspected source

Pinned pret revision: `037335f4c725d7c9aecdac87066f2002b4bd7e14`, matching pinned
agbcc. The isolated build copies `.local/vertical-slice01-native`; source inspection
uses those actual build trees, not remembered upstream hooks.

- `src/battle_script_commands.c:3393`, `Cmd_checkteamslost`, totals both parties'
  remaining HP and sets native outcome. This covers final opposing exhaustion.
- `src/battle_main.c:3850`, `HandleEndTurn_FinishBattle`: only after its
  TRY_FINISH/FINISHED guard, existing `PiEvents_End` copies the result before
  `PiBattle_End`, quest logging, palette fade and `FreeResetData_ReturnToOvOrDoEvolutions`.
  Repeated finish calls cannot re-emit because PiEvents_End clears its active guard.
  This hook and its ordering were preserved.
- `src/pi_events.c`: stable transport-owned bytes, same-sequence terminal retries
  until ACK/reset; bounded queue reservation for terminal records, explicit drops.
- `src/pi_battle.c`: preserves controller disposition in the existing fixed block
  before freeing Work. Supported() already rejects terminal gBattleOutcome for
  both normal decisions and replacements. Selection/legality algorithms unchanged.
- `src/battle_setup.c:906`, `CB2_EndTrainerBattle`: ordinary defeat returns to
  WhiteOut; victory returns to the field script and sets fought status.
- `data/maps/PewterCity_Gym/scripts.inc:6`: real `TRAINER_LEADER_BROCK` battle;
  DefeatedBrock at line12 sets defeated/Boulder flags, scene and existing story
  gates, then gives TM39. The Gym script is byte-for-byte unchanged.

Contract and diagram: [battle_terminal_contract.md](battle_terminal_contract.md).
Changes: `native/battle_end01/{pi_events.c,pi_battle.c,transport.lua}`;
`battle/{transport.py,lifecycle.py}`, CampaignStore composition and host event
notification/recovery. Tools build/launch/capture/save/verify this isolated slice;
read-only probe and ordinary player-button automation are test-only. No model,
resource spending, native flags, party stats or outcomes are injected.

Lifecycle distinguishes requested, published, native controller emission and
canonical execution. Graceful stop cancels unfinished accepted choices; fresh
host recovery cancels unfinished prior-process work, never resends it. Terminal
tombstones and durable canonical end checks reject obsolete scheduling/publication.
Restored scopes cannot append future audit into the active branch. Lifecycle uses
existing append-only audit/checkpoint cutoffs, not new NPC knowledge or game facts.

## Actual native evidence

| Native session | Decision source | Actual result and evidence |
|---|---|---|
|3158766498|Deterministic first legal move|Completed Brock loss2, canonical end26, ACK26, heap0, whiteout; `external-progress2.json`|
|2796930416|Same deterministic provider|Completed loss2; end26 committed, socket disconnected, ACK withheld4 seconds, identical retransmissions deduped and retired after cleanup; `external-delay-loss.json`|
|3287450572|Vanilla AI, explicitly unarmed comparator ROM|Completed loss2, end66/ACK66, no tactical allocation/provider requests; `vanilla-result.json`|
|3029093765|Deterministic external, final revision2|**Real native Brock victory1**, 13 external choices resolved, one sole engine replacement; end55 committed once and retried after cleanup/4-second disconnect; real Gym script/TM39; `victory-paired-final.json`|
|1365259495|Deterministic external, intentional stop|Four choices resolved; request5 was published/emitted but unresolved, then **CANCELED_RUN_ABORT** on host shutdown; `abort-immediate-before.json`, `abort-after-stop.json`|

The winning player used ordinary Growl/Leech Seed/Tackle inputs. Native Geodude
XP raised Bulbasaur from9 to11 and taught Vine Whip from the pinned learnset;
Vine Whip22 is present in actual canonical turn13 resolution against Onix. No
move/level/HP/RNG write made this possible. The player reached12 after victory.
Earlier failed attempts and a test-driver slot3 navigation mistake remain retained;
the corrected driver sends both Right and Down. These are test harness issues,
not reasons to alter Brock or claim wins in failed artifacts.

`lifecycle-trace.json` correlates native outcome/function/callback/heap/request,
actual wire identity, durable commit/duplicate results, sequence and eventual ACK.
Native symbols come from each actual ELF. The terminal event was copied before
heap0; the game returned to the field while ACK was still withheld. Repeated
callbacks, frame polling, four-second reconnect and duplicates produce one active
canonical end. `fresh-host-terminal-dedupe.json` reopens the actual DB in a new
Python process and replays the real wire: same event ID, no second obligation.
Distinct later battle identities are separately accepted by focused tests.

## Save and downstream proof

Normal native Save produced checkpoint `51f1b3f4-8cf1-4c7b-91e0-dacfa1dfc10d`,
counter13, fingerprint `cac7d75838fca04715c7b6814a1fea64d8d6bbec726da6cca151a936da9488d0`.
Both native flags are true in validated battery data. Fresh OS Continue restored
all seven hashes, lifecycle and the same automatic **RECAP_REQUIRED** obligation.
It remains unpublished; no Hermes/fallback publication or diffusion was run.

The production ingest created obligation
`731af83d2fb4f6f2bb8f7c5331a91dd8c80159154809d17ae4d1d52b982acfc7`
from actual canonical end
`d4ff44113a69798cf542ce758ae865060393c0906d9a30263c85656ba31041cf`.
Trusted trainer414 maps to the source registry's TRAINER_CLASS_LEADER and `gym`
prominence, supplying the existing HIGH_PROFILE policy independently of prose/UI.
`restore-stale-work-and-prominence.json` proves that input without diffusion.

Restoring the original paired pre-Brock checkpoint excludes the future Brock
battle, obligation and all tactical lifecycle rows; attempting to start its
abandoned obligation is rejected without changing any of seven hashes. The abort
branch is likewise excluded. Winning paired battery retained privately at
`.local/battle_end01/victory-paired.sav`; original production checkpoint/database
remain untouched. See `victory-reload-proof.json`, `pre-brock-rollback-proof.json`,
`abort-restored.json` and the scoped host race/restore tests.

## Build, footprint and checks

Final external revision2 SHA256:
`a7568526e6042b38b82bb82962218440bf519998d6601be954a574d4a1b2ed98`.
Final vanilla revision2 SHA256:
`43bba24bbd0a06ccbff02a4ccc02cdc0673c733ac68f1b7e77adc414132c98fd`.
Both clean matching-toolchain builds exit0. Vanilla emulator comparison ran
revision1 (`c6dc1e97171c600ff3baac802ba0858619dfb5be136b824f1260d99ac895248b`);
vanilla revision2 was rebuilt/static checked, not boot-tested. Revision2 corrects
sole-engine versus invalid-fallback disposition reasons; earlier artifacts retained.

Actual ELF: mailbox196 at0x0203FBB0; event state472; UI148+64; viewer pointer4;
preparation168; tactical control48 at0x0203FFCC. Allocation ends0x0203FFFC:
**4 bytes fixed EWRAM headroom**, unchanged. Work1036 (+existing allocator header16)
and snapshot708 remain unchanged; teardown frees Work. No additional fixed RAM or
save-layout change. The inherited top-level manifest's stale220-byte headroom
field was corrected from ELF symbols; it was metadata, not available space.
Worst-case stack/high-water behavior is not newly measured or broadly qualified.

Actual checks:

- 23 focused host tests,0 skips, pass (`final-host-tests.log`).
- 28 retained vertical-slice/closeout tests passed; an additional requested module
  failed import due to its tests-path dependency. Corrected invocation separately
  passed all30 virality tests (`campaign-regression.log`, `virality-regression.log`).
  Total passing focused host tests81; not a full-suite claim.
- 27 actual-C terminal/retained transport/observation cases plus pinned-source
  legality/controller/lifecycle matrix pass (`native-tests-final.log`). Game globals
  and controller stubs are fixtures, not emulator gameplay.
- 69 actual artifact checks pass (`verification.json`), including all protected
  hashes and unchanged closed66 ledger. Py_compile passes for edited host/tools.
- Exact commands/failures: [battle_end01_commands.md](battle_end01_commands.md).

Limits: saturated/previously incomplete streams still suspend canonical ingestion;
terminal retention cannot manufacture missing preceding events. Four-record RAM
queues do not support arbitrary numbers of offline battles or power loss. Soft
reset/hot savestates, broader modes/actions/items and fast-forward remain earlier
qualification risks. Retained screenshots are private/ignored. No ROM was fetched
or uploaded. No gameplay content or subsequent AI phase was implemented.

Stop reached: BATTLE-END-01 accepted. Owned workers/listeners stopped, inference
disabled. Next task is separately authorized **VERTICAL-SLICE-01 final live closeout**;
see [vertical_slice01_final_readiness.md](vertical_slice01_final_readiness.md).
