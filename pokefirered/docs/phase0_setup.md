# Phase 0 setup and reproduction

Run from `/Users/blevicki/Documents/poke/pokefirered`. Specifications remain under `pokemon_influencer_handoff/`, with root PLAN and the requested docs paths linked to those canonical files; repository-root `AGENTS.md` is canonical. Implementation status lives at `docs/status.md`. No game feature implementation exists yet.

## Local safety and provenance

The user explicitly identified `pokefirered.gba` as their locally supplied dump. It was read only, never uploaded, renamed, or overwritten. The 16 MiB header reports `POKEMON FIRE`, `BPRE`, revision 0 and a valid complement checksum. SHA-1 is `41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc`; SHA-256 is `3d0c79f1627022e18765766f6cb5ea067f6b5bf7dca115552189ad65a5c3a8ac`. `cmp` also found the clean generated baseline byte-identical. This establishes the patch base; no campaign patch was produced or tested. A verified private copy is preserved at `.local/inputs/user-firered-rev0.gba` because upstream root `make` uses the same output filename as the user input. Use the isolated wrapper for baseline work; do not build into that input path.

`.local/`, `.venv/`, user ROMs/saves, private screenshots, databases and environment secrets are ignored. Existing tracked upstream `data/mb_*.gba` reference assets were retained. No files were staged, committed or pushed. No system-wide software was installed and no paid/cloud calls were made.

## Verified commands

```sh
/opt/homebrew/bin/python3.13 -m venv .venv
.venv/bin/python -m pip install -r pokemon_influencer_handoff/requirements-handoff.txt
make -f Makefile.phase0 doctor
make -f Makefile.phase0 test-host
make -f Makefile.phase0 baseline
make -f Makefile.phase0 inspect-dump DUMP=pokefirered.gba
cmp pokefirered.gba .local/baseline-1jl4v4c6/pokefirered.gba
```

The system Python 3.9.6 could not install the supplied `jsonschema==4.26.0`; existing Homebrew Python 3.13 resolved it. The original checker crashed because the handoff's AGENTS file was relocated. Its required-file and navigation checks now explicitly resolve the repository-root file. Before editing, 32/33 handoff manifest paths matched, and the relocated root AGENTS matched the missing file's digest. The original checksum manifest is preserved as a delivery receipt, not a hash claim about subsequent edits.

`test-host` runs only the specification/schema checker: 60 checks, nine illustrative JSON fixtures, zero failures. There is no host runtime, bridge, legality engine or gameplay assertion in this checker. `doctor` checks actual pinned build prerequisites. `baseline` exports the pinned Git commit into a fresh ignored directory each run, installs verified pre-existing agbcc binaries/headers/libraries according to upstream's install operations, runs upstream `make -j8 compare GAME_VERSION=FIRERED GAME_REVISION=0 GAME_LANGUAGE=ENGLISH MODERN=0`, checks SHA-1/SHA-256/size and records ELF/map hashes. It never writes the root dump.

The source pin is `037335f4c725d7c9aecdac87066f2002b4bd7e14`; agbcc pin is `da598c1d918402c42c0c0d7128ba14567f3175e9`. This matching build uses agbcc for C, ARM GCC 16.2.0 only for preprocessing, GNU ARM binutils 2.47.20260726, Apple clang 17.0.0 for host tools, Make 3.81 and libpng 1.6.58. Compiler binaries/libraries/headers are hashed in `config/phase0.lock.json`; agbcc itself was already built locally and was not rebuilt this session. Support is demonstrated for this local configuration, not a clean-machine provisioning claim.

The first install attempt was invoked from the wrong working directory, so it could not copy agbcc; the resulting baseline attempt failed. Those logs are retained. Installing from the agbcc directory corrected it; both the retry and the fresh wrapper build passed. No modern target was substituted.

## Source strategy

The local project branch is `pokemon-influencer/phase0` (no commits or push this session). Keep a project fork/patch layer on the pinned upstream history and preserve a fresh unmodified export for comparison. Do not automatically follow upstream master. Updating the pin requires a reviewed source diff, lock changes, baseline comparison and emulator smoke tests. Retain upstream notices. The machine-readable lock records this session's exact tool/package identity and local paths; it does not install dependencies.

## Emulator setup and probes

Official package: [mGBA 0.10.5 macOS](https://github.com/mgba-emu/mgba/releases/download/0.10.5/mGBA-0.10.5-macos.dmg), SHA-256 `443b490ec728293dfcde1cb9db160f73d94c457cb1864f3ce0407e60e174b09c`. Candidate executable reports source commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`; the matching official source tag was checked out for API inspection. The app is copied under ignored `.local/`, not `/Applications`.

```sh
curl --fail --location --max-time 60 https://github.com/mgba-emu/mgba/releases/download/0.10.5/mGBA-0.10.5-macos.dmg -o .local/mGBA-0.10.5-macos.dmg
# Initial download timed out; actual successful continuation:
curl --fail --location --continue-at - --max-time 60 https://github.com/mgba-emu/mgba/releases/download/0.10.5/mGBA-0.10.5-macos.dmg -o .local/mGBA-0.10.5-macos.dmg
hdiutil attach -readonly -nobrowse .local/mGBA-0.10.5-macos.dmg -mountpoint .local/mgba-volume
cp -R .local/mgba-volume/mGBA.app .local/mGBA.app
.local/mGBA.app/Contents/MacOS/mGBA --version
.local/mGBA.app/Contents/MacOS/mGBA --help
mkdir -p .local/emulator-test evidence/private
.local/mGBA.app/Contents/MacOS/mGBA -C savegamePath=/Users/blevicki/Documents/poke/pokefirered/.local/emulator-test .local/baseline-1jl4v4c6/pokefirered.gba
```

The initial active GUI instance was launched with the same command plus `-d` (Qt debugger option); a redundant instance was stopped. In Tools → Scripting, the actual console command loaded `tools/phase0_probe.lua`, then `tools/phase0_inputs.lua`. The bounded input driver in `tools/phase0_driver.lua` was pasted directly into the console after a `dofile` read failed with `Bad file descriptor`. `tools/phase0_input.py` sends only bounded key sequences and sanitized screenshot names to loopback port 18766. This is an emulator diagnostic/test harness, not a ROM mailbox or companion bridge. Exact accepted gameplay commands are recorded in `evidence/phase0/input-commands.jsonl`; frame/input/probe evidence is in `emulator-runtime.log` and private screenshots.

Live probes confirmed Lua 5.4; read8/16/32/readRange, same-value write8/16/32 at ELF-derived `gBattleTypeFlags`; frame callbacks; screenshots; setKeys; an explicit ALL state-buffer round trip; and a loopback socket listener/receive/send callback. No arbitrary free RAM was written and no mailbox address was selected. `writeRange` was nil. `runFrame()` exists but failed in this desktop console context; asynchronous normal-frame inputs work. Initial socket disconnect handling repeatedly logged errors; closing the diagnostic client corrected it, with the original trace retained. These failures demonstrate why upstream API existence is not sufficient.

Tagged source shows saveStateBuffer defaults to ALL, but loadStateBuffer defaults to ALL without SAVEDATA. The explicit-ALL round trip does not independently establish battery-save rollback semantics. No generic state-load callback, reconnect behavior, bridge timeout/wrong-build rejection, fast-forward performance or paired host save was tested. Those are Phase 1/SAVE deliverables, not completed Phase 0 bridge work.

Renderer retry (actual command):

```sh
.local/mGBA.app/Contents/MacOS/mGBA -C hwaccelVideo=0 -C savegamePath=/Users/blevicki/Documents/poke/pokefirered/.local/emulator-test -t .local/emulator-test/transition.ss0 .local/baseline-1jl4v4c6/pokefirered.gba
```

`transition.ss0` is a private emulator diagnostic snapshot saved with explicit ALL flags, not an in-game save or a managed host checkpoint. The initial run's framebuffer sometimes became black while frame counts advanced; renderer causality is not proven. On the retry, loading the diagnostic listener via `dofile` logged success but the port was not listening; direct console execution restored a verified loopback listener. Script loading/lifetime requires investigation before promoting this package to a supported bridge configuration.

## Completed live smoke and retained assertions

The new game used player AA, rival AAAA and Bulbasaur. The initial special rival tutorial ended in a loss (`battleflags=28`, outcome 2); it is explicitly excluded from the ordinary-battle requirement. A normal Route 1 level-4 Rattata encounter (`battleflags=4`, outcome 0) was defeated using the original Tackle policy/menus. The return-to-field capture has outcome 1. No battle AI or party memory was modified.

The successful local sequence from the observed Route 1 road checkpoint (x13,y32,map3/19) was:

```sh
.venv/bin/python tools/phase0_input.py 'KEY 4 80 20' 'KEY 7 64 150' 'SHOT ordinary-battle-start'
.venv/bin/python tools/phase0_input.py 'A 30' 'SHOT ordinary-battle-result-01'
.venv/bin/python tools/phase0_input.py 'A 30' 'SHOT ordinary-battle-result-02'
.venv/bin/python tools/phase0_input.py 'A 30' 'A 30' 'SHOT ordinary-battle-result-03'
.venv/bin/python tools/phase0_input.py 'KEY 3 20 80' 'SHOT save-menu'
.venv/bin/python tools/phase0_input.py 'KEY 7 1 20' 'KEY 7 1 20' 'KEY 7 1 20' 'KEY 0 20 80' 'SHOT save-confirm'
.venv/bin/python tools/phase0_input.py 'KEY 0 20 300' 'SHOT in-game-saved'
.venv/bin/python tools/phase0_input.py 'KEY 1 1 600' 'SHOT in-game-saved-finished'
.venv/bin/python tools/verify_phase0_save.py
kill -TERM 26342
.local/mGBA.app/Contents/MacOS/mGBA -C hwaccelVideo=0 -C savegamePath=/Users/blevicki/Documents/poke/pokefirered/.local/emulator-test .local/baseline-1jl4v4c6/pokefirered.gba
```

Commands enqueue asynchronous frame inputs; wait for the named capture before advancing. The full earlier new-game route and failed approaches are preserved in `input-commands.jsonl`; they are not yet a timing-independent golden path. Encounter timing/species, damage RNG and inter-command idle frames are nondeterministic. The current baseline battery save is a private checkpoint at `.local/emulator-test/pokefirered.sav`; downstream tests can use a private copy rather than repeat new game. It contains one valid 14-section rotating save slot, counter 1. All checksums were recomputed from the actual ELF-resolved `sSaveSlotLayout`. SHA-256: `142d1518a27f65f3646d327459bb7407d63d2e4069e92a1b13655509acf05ff0`.

In the fresh process's Tools → Scripting console, these exact commands resumed the battery save without loading any emulator snapshot:

```lua
dofile('/Users/blevicki/Documents/poke/pokefirered/tools/phase0_reload.lua'); p0tap(3,20,150); p0shot('reload-continue-menu')
p0tap(0,20,180); p0shot('battery-reload-field')
p0tap(1,20,600); p0shot('battery-reload-field')
p0persist('persist-after')
```

The first field capture was the expected quest recap; the final capture shows the saved Route 1 field. Source/ELF-derived observations agree before/after: x18,y32,mapgroup3,mapnum19, save counter1, partycount1, level5, HP5. The save callback fired once. This is battery persistence, not host history pairing or rollback testing. Final screenshot hashes and 12 assertions are recorded in `emulator-smoke.json`. Read-only revalidation is:

```sh
make -f Makefile.phase0 verify-emulator-evidence
```

This command validates retained live evidence and the local save; it does not launch a fresh playthrough. The Lua input helpers and recorded commands are reusable Phase 0 milestone paths with state assertions, but the later trainer/follower/PokeBook/Brock golden path remains unimplemented. No `make test-emulator` full-replay or `make package` release command is advertised.

No active environment blocker remains for Phase 0. The conditional emulator decision and remaining bridge/save risks are in D12 and `emulator-capabilities.json`. Final package checks: 60 specification checks with 9 fixtures; 15 pinned build-prerequisite checks; one fresh matching build; one normal wild win; one in-game save and fresh-process reload; 12 retained smoke assertions. Screenshots and saves remain ignored/private. The source integration map is based on inspected pinned files, not implemented hooks.
