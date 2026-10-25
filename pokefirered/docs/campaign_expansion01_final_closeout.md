> Historical report preserved. D48 now closes the persistence gate and accepts
> CAMPAIGN-EXPANSION-01: [final recovery](campaign_expansion01_final_recovery.md).

> Historical D46 closeout below. Current D47 Kent gameplay/social proof and new
> restart/pairing blocker supersede its Kent-unrun status: [current closeout](campaign_expansion01_kent_closeout.md).

# CAMPAIGN-EXPANSION-01 final live continuation — blocked at Kent

Current disposition, 2026-10-06 (D46): **not accepted**. Greg and James completed
real Route 3 encounters with live Mercury, actual Hermes recaps, follows and diffusion.
Kent's required new Dots Strategy failed at route-metadata preflight before generation.
The production fallback memo and preparation lock were committed. A subsequent
read-only Dots check passed; this is not evidence that Dots is dead or currently
unavailable. No model was changed, memo overwritten, opportunity fabricated or battle
replayed to bypass this gate. User attachment f93dfac2 §18 requires the nearest coherent
checkpoint and a precise blocker when a required new Strategy does not succeed live.

No ticket completed in this continuation. The next task is **Kent preflight/fallback
recovery, then the remaining same campaign closeout**, with an explicit disposition
for the frozen fallback opportunity before any generation. The remaining allowance
is recorded, not automatically reopened. No next-phase implementation or post-acceptance
EARLY-KANTO readiness recommendation was produced.

## Actual path and frozen state

Exact accepted C1 restored through normal Continue; Rick/Brock/Sally were not replayed.
Greg's memo `strategy-memo:eedb063f8ea3c0fae17ff233b2dd6c19d8f824dac2868ddc6563eb0a2c80ebb2`
and preparation `commitment:7a33ffd01727d65489da6a3c8cfc4b3f65658ae83e5136a6907af02e13fad6dc`
remained unchanged. Initial fresh non-generation Dots/Mercury/Inkling checks passed.

| Native encounter | Meaningful live Mercury choices | Native forced/sole bypass | Timeout fallback | Actual result |
| --- | ---: | ---: | ---: | --- |
| Greg 106 | 15 | 1 | 0 | Player victory, canonical terminal receipt |
| James 107 | 16 | 2 | 0 | Player victory, canonical terminal receipt |
| Kent 108 | Unrun | Unrun | Unrun | Strategy gate blocked before encounter |

Greg has 13 `EXECUTED` resolved-action lifecycle receipts. Two live forced replacements
have `CONTROLLER_EMITTED` and terminal `CANCELED_BATTLE_ENDED`, without resolved-action
receipts. Their actual application is independently confirmed by the next native
snapshot: request6→7 and12→13, activeSlot3 in NORMAL_TURN. Do not call these lifecycle
rows EXECUTED. James has 16 EXECUTED receipts. Selected legal moves/switches included
String Shot, Harden and switching; no optimal-action override or probability resampling.
The remaining engine-forced choices incurred no inference.

Greg and James each used two real Inkling/Hermes requests. Their persisted outcomes
have producer `hermes`, no fallbackReason, and durable episodes/public posts:

- Greg job `b3353e12-06a8-4048-a702-d1e4476dfe18`, episode
  `c01110601b0228d37ec441161ca5cca370865962368a9e268f00c12a938a011d`, post
  `897023c92908b646503a0c0581fb88d5b921bcd408c30d9ab3ebb3535471143d`.
- James job `d7da55a8-0896-48f9-94d0-6c830d0cb75d`, episode
  `84f1718c359d1b6608d390b96b7e12e97d10072dbc0541d36d749b525c995fe9`, post
  `f811207154be96b61ef0f88f62ee0b1135c17768e9d189486da8ead05248a8b2`.

Followers increased 2→3→4 exactly once per selected victory. Public recaps expose
only their published claims; detailed battle observations and director episodes remain
separate. Greg's public result/species claims do not expose his direct Vine Whip/Leech
Seed observations. Ordinary local diffusion has budget2/window1; explicitly configured
chronically-online delivery is separate. James's actual post-Greg context contained
Brock's two public claims, rather than every post or Greg's private history. All retained
reported claims were matched against their attributed public source posts.

James generated one actual Dots/AtlasCloud memo, attempt34 (new attempt18), HTTP200,
8.255s provider latency, 273 completion tokens, cost0. Exact memo
`strategy-memo:4ee0a692ce44505c75b9bb62e632213727dfe1c59a759ab7add207937400d7b1`
was retained through later evidence and player changes. It favors cautious endurance,
String Shot/Harden and conserving resources, treats Bulbasaur reports as uncertain,
and preserves Caterpie/Metapod. Its subjective move-change discussion did not grant
illegal edits. Sole authored PREP candidate selected deterministically, no preparation
call. Full text/model/provider/prompt/context provenance is in C3 and requests.json.

An ordinary travel route accidentally crossed Ben89's sightline. The player fought
and won his legitimate native encounter with vanilla opponent control and zero hosted
calls. Its canonical history and deterministic fallback recap remain retained. Ben did
not follow under current policy. This produces eight total posts rather than seven;
no rollback erased the encounter. The collision-only route helper does not account
for trainer sightlines. The corrected James approach is retained in route/input logs.
No losses occurred in these attempts. Normal learning/evolution produced Ivysaur16;
there were no HP/PP/level/RNG writes or state manipulation.

## Exact blocker and coherent saves

Kent job `strategy-job:9c4671bd7de63b67e375b97b63a43227997d4a2b5a8e3d8dec2702c0359a0805`
at cutoff340: `TimeoutError`, category timeout, stage route_metadata,
model `dots-studio/dots-3-note-preview:free`, code unspecified, retryable true.
HTTP status, serving provider, request ID and elapsed latency were not captured for
this failed metadata GET. No Kent completion POST/cost receipt exists. The metadata
GET has a configured15s timeout; that is not a measured elapsed duration.

Fallback memo `strategy-memo:cbe1919cf88ecd2c31c5c28f101fefa0d15283bb60deb22e340015653ae68606`
and its normal PREP lock consumed this logical opportunity. Follow-up metadata passed
in0.402s, recorded separately in post-block-route-check.json. A healthy later route
cannot silently authorize replacing a durable fallback or rerolling the locked team.
This current timeout does not reclassify the old historical Greg ProviderError, whose
specific cause remains UNKNOWN due insufficient retained telemetry.

| Save | Checkpoint | Cursor / native counter | Verified recovery |
| --- | --- | --- | --- |
| C2 Greg | c495d82e-f6e6-41df-bed1-fc734531ee1b | 259 /16 | Fresh-process normal Continue, seven hashes match |
| C3 James, Kent blocked | 88582f26-ee1e-4a05-8862-b46b9057b010 | 340 /17 | Offline fresh-process normal Continue, seven hashes match |

Nearest coherent save: `.local/campaign_expansion01_final/C3-james-blocked.sav`.
Native fingerprint `f3a84bf75154d2c8ce80b87269f4a560558cf4b22a1491c126075c58c04c0a25`,
serialized content SHA256 `7d545e4fec9a971a223674a87debff2ad544da0b0140efc7408ed5ec0ce9016c`.
C3 explicitly includes Kent's fallback/lock. Actual in-game Save and native save
callbacks established pairing; no domain/checkpoint injection. Native trainer flags
confirm Greg/James defeated, Kent not defeated. Rick/Brock/Sally battle counts remain1.

Offline C3 native Home showed four followers; Rick and Brock posts were opened.
Later pagination returned “PokeBook unavailable,” so full eight-post browsing and
followers-list pagination are **not proven**. Before/after seven hashes and ledger
were unchanged, including NPC knowledge. A screenshot initially named c3-greg-post
actually shows Brock; it is not Greg proof. One input socket reset occurred; an
incorrect no-space key command was rejected and corrected. These retained errors
were not mistaken for successful UI actions. No additional UI repair implemented.
Kent battle/recap, Mt. Moon transition, final Kent save/feed/reload are **unrun**.

## Accounting, cleanup and memory

Additional ceiling98: Strategy2/preparation0/battle84/Hermes12. Actual new36 calls:
Strategy1/preparation0/battle31/Hermes4. All36 retained usage receipts report costUSD0.
Ledger closed, unused62 (Strategy1/battle53/Hermes8), with original16-row prefix
immutable. MODEL03 qualification3 remains a separate historical ledger.
All task host/emulator processes stopped. Both owned settled Hermes runtime homes
were cleaned with the ownership-checked cleanup API; durable episodes and all seven
state hashes remained intact. Default hosted inference remains disabled.

No native/ROM change. All permanent RAM symbols identical to the accepted build;
EWRAM headroom4 bytes before/after, delta0. ROM SHA256
`3807c79fc7554c45e275b3e4d2db2b3c5b01d3b262683b27e803e6f69cf979d4`, pret revision
`037335f4c725d7c9aecdac87066f2002b4bd7e14`. All protected original saves/databases,
old ledger, content/model-profile identities and user ROM hashes remain unchanged.
352 actual heap samples: maximum sampled allocated95888 bytes, minimum sampled free
and largest block17968. These are sampled screens, not worst-case peak qualification;
stack high-water remains unmeasured. RSS snapshots retained, not a leak-free claim.

## Changes, exact commands and evidence

Changes this continuation: ordinary-input player helper with source-derived own-menu
cursor/ownPP handling and bounded safety/evolution review; zero-inference final evidence
closeout utility; temporary budget-test fixture now uses the original16 rows rather
than all subsequent gameplay receipts; authoritative reports/status/roadmap updates.
No game AI, legality, content, providers, acquisition or preparation policy was changed.

Working directory `/Users/blevicki/Documents/poke/pokefirered`:

```sh
.venv/bin/python tools/campaign_expansion01_final.py launch --restore .local/campaign_expansion01_final/C1-sally-recovered.sav
.venv/bin/python tools/campaign_expansion01_final.py host --seconds 3600 --live --continue-authorized-run
.local/mGBA.app/Contents/MacOS/mGBA -C hwaccelVideo=0 -C savegamePath=/Users/blevicki/Documents/poke/pokefirered/.local/campaign_expansion01_final /Users/blevicki/Documents/poke/pokefirered/.local/campaign-expansion01-native/pokefirered.gba
# Through mGBA Tools > Scripting: dofile generated run.lua and source-bound player helper.
.venv/bin/python tools/campaign_expansion01_final.py save --label c2-greg --menu-cursor 7
.venv/bin/python tools/campaign_expansion01_final.py launch --restore .local/campaign_expansion01_final/C2-greg.sav
.venv/bin/python tools/campaign_expansion01_final.py save --label c3-james --menu-cursor 7
.venv/bin/python tools/campaign_expansion01_final.py launch --restore .local/campaign_expansion01_final/C3-james-blocked.sav
.venv/bin/python tools/campaign_expansion01_final.py host --seconds 1200
POKEINFLUENCER_CAMPAIGN_FINAL=1 .venv/bin/python tools/campaign_expansion01_capture.py C3-after-viewer
.venv/bin/python tools/campaign_expansion01_final_evidence.py
.venv/bin/python -m unittest discover -s tests -p test_campaign_expansion_final_budget.py
.venv/bin/python -m unittest discover -s tests -p test_final_closeout_budget.py
.venv/bin/python -m unittest discover -s tests -p test_campaign_expansion01.py
```

Full ordinary buttons/ACKs/screenshots, exact waypoint traces, source symbols, save
receipts and restart commands reside in `evidence/phase6/campaign_expansion01_final/`.
Key evidence: `partial-golden-trace.json`, `causal-trace.jsonl`, `accounting.json`,
`requests.json`, `verification.json`, `C2-{greg,fresh-continue}.json`,
`C3-{james-blocked,offline-restored,after-viewer}.json`, `native-memory-current.json`,
`turn-*.json`, `input-commands.jsonl`, `pairings.jsonl`, `save-receipts.jsonl`.
Private actual screenshots: `evidence/private/campaign_expansion01/c3-*.png` and
Greg/James/Ben review screenshots. Secrets/ROM/save bytes were not uploaded.

Scoped regressions:3 budget,4 prior final-budget,13 content/pack tests passed,0 skips.
Initial budget rerun failed1/3 because its fixture consumed live rows; original failure
log retained, fixture-only correction and passing rerun retained. Prior start checks
also passed. Evidence utility asserts accounting, source flags, actor claim provenance,
cleanup durability, protection hashes and seven-way restore. No mocked Kent step
counts as acceptance. No endgame implementation.

Historical initial Nemotron pre-dispatch report is superseded by D45 and this actual
run; its original verification remains `initial-verification.json`, route/readiness
records retained. Earlier readiness documents are historical, not current acceptance.
