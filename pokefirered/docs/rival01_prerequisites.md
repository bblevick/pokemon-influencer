# RIVAL-01 prerequisite gate repair — D51

**RIVAL-01 PREREQUISITES ACCEPTED. RIVAL-01 READY FOR LIVE IMPLEMENTATION.** This ticket used zero hosted inference and did not advance or adopt content into the accepted campaign. The actual live Rival battle, recap, diffusion and save acceptance are next-ticket work.

## Evidence and repaired behavior

The versioned [context policy](context_selection_policy.md) resolves Cerulean relevance at a new opportunity without changing `config/virality_policy.json` or old diffusion epochs. `ScriptedContent` adds source-bound `trainerbattle_no_intro` singles independently of ordinary object-sight qualification. The generic constructor observer now resolves native IDs through the persistent trainer registry. All27 Rival/Champion definitions remain actor0326; no new actor0334 is invented.

The real accepted world retains11 public posts/22 public actor receipts, including the grunt's two published claims. Full legacy public projection was18,844 bytes. A measurement-only unselected full-context assembly with current own state is32,835 bytes. The qualified **full production StrategyContext is7,524 bytes**, including scope, metadata, own companions, resources, envelope summary and selected social claims; model input5,977 bytes. The chat serialization dry run is8,102 bytes with a clearly labeled route fixture, not a live provider-health check.

The deterministic selection contains three normalized claims with three full references from two immediate authors: Bulbasaur seen (eight independent battle origins retained in memory/audit; selected Brock reference), Brock's public defeat outcome, and Ivysaur seen (three independent origins; selected grunt public reference). Current opposing lead/party stays UNKNOWN. All22 receipts are present before/after; selection does not forget, deliver or publish anything. Audit lists every eligible receipt, feature, priority, normalized group, selection/omission reason and full source IDs. Forty-seven private Rocket delivery receipt IDs are excluded. The prompt's “45 private observations” cannot be derived by subtracting two public semantic claims from47 delivery receipts; these have different granularity. No private claim was inferred from that subtraction.

Files under `evidence/phase8/rival01-prerequisites/`:

- `host-verification.json`, `strategy-context.json`, `selection-audit.json`, `authorized-public-receipts.json`: real memory, exact context/hash/bytes, unchanged historical jobs/projections, isolated adoption/fallback/sole commitment and restore checks.
- `manifest-native.json`, `native-build.log`, `native-memory.json`: source-derived isolated ROM, unchanged save/combat ABI, identical permanent RAM symbols/end, zero fixed RAM delta,4 bytes EWRAM remaining.
- `native-fixture.json`, `native-trace.jsonl`, `native-first-state.json`, `native-inputs.jsonl`, `native-emulator.jsonl`: actual mGBA0.10.5 source-script trace, constructor and sanitized first turn.
- `tests.log`, `rocket-regression.log`, `strategy-regression.log`, `campaign-regression.log`: separately labeled host tests.
- `verification.json`, `verification-console.log`, `shutdown.json`: combined disposition and cleanup checks.

Host checks passed:18 new prerequisite tests,12 Rocket regressions,14 StrategyMemo regressions and13 campaign-content regressions (57 total, zero skips). Full native battle completion was not tested. `git diff --check` still reports pre-existing whitespace in `src/new_menu_helpers.c:670`; unrelated code was left alone.

Context file SHA256 (including its final LF): `2d44ce34962f0b1d82d248e83072e6acac2bf4a76d25fec3ff6de3b020b5b199`. Byte bound counts the canonical packet without LF. Exact material/context hashes are in `host-verification.json`.

## Native qualification, with its limits

The native run used an **explicitly edited isolated battery fixture**, not normal campaign travel and not a recovered accepted save pair. It copies Save20; only location/continue-warp fields, map-layout ID and internal Continue-warp bit are authored for test placement, with valid sector checksums. Player party, story flags, starter and Rival scene remain unchanged. A fresh separate WorldStore explicitly imports this fixture. The final native Continue uses the game's normal warp path to reconstruct Cerulean geometry/objects; earlier incomplete relocation attempts are retained in the logs and do not count as acceptance.

Ordinary buttons walk from22,7 to the source trigger22,6 at elevation3. The unchanged script selects saved starter0 → native334/Charmander, enters the normal no-intro trainer battle, and constructs Pidgeotto17/Abra16/Rattata15/Charmander18 with exact authored custom moves, held items0 and battle items0. Abra keeps Teleport; it is not “fixed.” Native counter increments exactly once. Real `BATTLE_STARTED` enters the canonical reducer as native334 / persistent `fr:trainer:0326`. The existing bridge exports seven legal first-turn actions and the exact sanitized party.

The recorded native constructor bytes are additionally replayed through the actual generic CampaignHandler and observer under a **synthetic locked host scope**, including duplicate suppression. This is an adapter qualification, not a production installation receipt or fabricated save pairing. The emulator was stopped with its isolated battle unfinished. No battle outcome or normal campaign result was committed. Terminal compatibility is proven by typed host fixtures/duplicate handling and the unchanged BATTLE-END-01 native path; a complete live Rival terminal remains unrun and belongs to the next ticket. Starter1→333/Bulbasaur and starter2→332/Squirtle are source/content fixture tests; only starter0 executed natively.

Trusted native subtype332/333/334=`rival` and registry actor0326 produce existing HIGH_PROFILE policy64/7 in a pure preview. No name matching or LLM classification is involved. No actual Rival post/diffusion was generated here. This context policy does not retroactively move old epochs or migrate the distribution policy's historical home-stage fields.

## Exact commands

Run from `pokefirered`:

```sh
.venv/bin/python tools/scripted_prereq_build.py
.venv/bin/python tools/scripted_prereq_build.py --incremental
.venv/bin/python tools/rival01_prerequisites.py
.venv/bin/python -m unittest discover -s tests -p test_rival01_prerequisites.py -v
.venv/bin/python -m unittest discover -s tests -p test_rocket01.py -v
.venv/bin/python -m unittest discover -s tests -p test_strategy_memo.py -v
.venv/bin/python -m unittest discover -s tests -p test_campaign_expansion01.py -v
.venv/bin/python tools/rival01_native.py prepare
.venv/bin/python tools/rival01_native.py record 300
.local/mGBA.app/Contents/MacOS/mGBA -C hwaccelVideo=0 -C savegamePath=/Users/blevicki/Documents/poke/pokefirered/.local/rival01-native-fixture /Users/blevicki/Documents/poke/pokefirered/.local/scripted-prereq-native/pokefirered.gba
```

GUI: Tools → Scripting → File → load `.local/rival01-native-fixture/run.lua`. Logged native inputs:

```sh
.venv/bin/python tools/rival01_native_input.py 'key 0 180 600' 'key 0 8 360' 'key 1 8 120' 'shot warp-fixture-field'
.venv/bin/python tools/rival01_native_input.py 'arm' 'key 6 9 120' 'shot cerulean-native-trigger' 'a 20' 'shot cerulean-native-battle'
.venv/bin/python tools/rival01_native_input.py 'a 12' 'key 9 0 240' 'shot cerulean-native-first-turn'
.venv/bin/python tools/verify_rival01_prerequisites.py
```

`arm` uses the existing bounded control interface. No hosted worker/provider runs; absence of an external response exercises native timeout/fallback. Recorded inputs use ordinary buttons. Shutdown uses native Quit and stops the recorder; no normal in-game save is performed in this synthetic unfinished battle. Screenshots remain private under `evidence/private/rival01-prerequisites/`.

## Accepted starting point and next ticket

Retain normal Save20 pair `.local/rocket01/post-rocket-pair.sav` + `post-rocket-pair.sqlite3`, checkpoint `fc2eb9f8-d613-4f48-aebf-b2ffa2c44824`, campaign `a8c24607-48a7-4e47-a204-4221a7367fcc`, branch `13a44cee-b272-40bb-9cfc-0815e1d386df`, cursor443, fingerprint `8d07886f33eea4d863209f9be626c191f4cf475262ceb5db5c3951f0f1c7d435`. Protected active/pair files and closed20/50 Rocket call ledger match their original hashes. Old Sally/Greg/James/Kent/Rocket Strategy jobs remain byte-for-byte intact. Isolated adoption can fork bookkeeping scope, changing its memory projection hash without altering any of the22 receipts; restoring Save20 recovers all seven original projection hashes.

**Next: RIVAL-01 live implementation, requiring separate authorization.** Normal cave/Miguel/fossil/Route4 travel is still required. Bind starter from the trusted save, explicitly adopt qualified content in the new working branch, and select context at the actual opportunity; intervening legitimate public posts may change selection. Keep native and host checkpoints causal. Expected configured Strategy model is `dots-studio/dots-3-note-preview:free`; verify its fresh free route then. No current route-health claim is made.

Budget recommendation only: Strategy1 / PREP0 / Mercury battle50 / Hermes4 =55 for one planned challenge. Sole unchanged source preparation needs no model. Use R0 accepted post-Rocket pair, R1 paired pre-Rival memo/party lock, R2 real terminal+recap+diffusion normal save, then fresh offline Continue and private rollback checks. Do not treat a real loss as an abandoned branch to hide it; no implicit second challenge or budget exists.

Remaining live gates: real public-context Strategy memo; sole locked party through normal constructor; live System One choices/execution/fallback audit; authoritative native completion; direct Rival memory; mandatory Hermes recap; trusted HIGH_PROFILE diffusion/public-only downstream exposure; normal paired save and fresh offline retrieval. No Rival production result, Misty/Gym, acquisition or endgame work starts under this ticket. Default inference stays disabled and workers stopped.
