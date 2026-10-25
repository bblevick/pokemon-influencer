# Fresh Hermes execution and safe cleanup

Install from `config/hermes_runtime.lock.json` into `.local/hermes-source` and `.local/hermes-venv`, separate from `.runtime/hermes/jobs/<fresh UUID>`. The official source checkout must have no `.env`. Each launcher creates a new mode-0700 home/work directory and approved config, sets HERMES_HOME before importing Hermes, verifies the pinned home resolver, and starts a new AIAgent conversation. It never clones personal profiles or prior homes. HERMES_SAFE_MODE disables plugin discovery; context files, SOUL, memory/profile, compression, background review, skill auto-load, checkpoints, retries and automatic recovery are disabled. Built-in registry discovery is removed before tools are selected, with another removal after lazy imports; exact resolved and registered sets are verified before inference. A minimal prompt override prevents upstream's generic local-profile path hints entering model input. The conversation/inference/tool dispatch loop is the actual official Hermes runtime.

Recap jobs expose four bound RPC tools; read-only continuity inspection exposes only recall. Prompt v2 retrieves a bundle through get_battle_evidence containing battle evidence, actorContext and priorMemory from the same validated actor/timeline services, allowing serial retrieval → submission → finish within three requests. This path is actual-Hermes/mock tested but not live retested; v1 live artifacts are retained. SQLite and the real credential stay in the host guard. The worker receives an ephemeral local bearer token, cannot resolve/connect outside its exact loopback guard port, and never receives a cloud credential. Guard forwards only the configured Puppeteer model, current zero-pricing/tool/token-verified, with zero prompt/completion price ceilings and provider fallbacks disabled. Normal mode is offline. Shadow audits real proposals but commits fallback; enabled-test allows valid proposals in the managed test campaign. Per job: three requests, six game-tool calls, 1,200 output tokens/request, 48,000 input bytes/request, fifteen-second provider timeout, fifty-five-second process deadline. A locked persistent counter caps this ticket at ten live attempts including failures; a process lock permits only one active model worker. Auxiliary requests hit the same guard or are refused by child networking.

```sh
python3 scripts/install_hermes.py --verify-only
# Reproduce from the official source and lock when absent:
python3 scripts/install_hermes.py
python3 scripts/run_hermes_fresh.py --database .local/hermes01/world.sqlite3
# Explicit mocked actual-Hermes integration:
python3 scripts/run_hermes_fresh.py --database .local/hermes01/world.sqlite3 --mode mock
# Explicit bounded live test, only while this ticket's budget permits:
python3 scripts/run_hermes_fresh.py --database .local/hermes01/world.sqlite3 --mode enabled-test --live
# Read-only fresh-process recall; mock inference is the default:
python3 scripts/inspect_hermes_memory.py --database .local/hermes01/world.sqlite3 --actor trainer:fr:trainer:0102
python3 scripts/clean_hermes_runtime.py /absolute/project/.runtime/hermes/jobs/UUID
python3 scripts/clean_hermes_runtime.py /absolute/project/.runtime/hermes/jobs/UUID --delete
```

Cleanup defaults to dry-run exact candidates. It requires the fixed root, direct UUID child, marker identity, no symlinked ancestry/interior entries, inactive worker and settled/revoked SQL grant. Empty/root/home/repository/path-traversal/personal/unmarked targets are refused. `--recover` explicitly settles/revokes an abandoned grant before cleanup. `--stop` signals only the marked PID after checking its exact worker/config command; no blanket process kill. Active homes cannot be wiped accidentally. `--quarantine` moves an owned unsafe abandoned home without following interior symlinks; it is never reused. If a worker is not safely stopped/reaped, deletion remains refused. Runtime homes contain execution/cache files only. Game databases, saves, source, credentials, installation and required bounded request/result audits live outside them.

This is a reviewed tool/transport permission boundary, not an operating-system sandbox against arbitrary modified Python code. It does not claim to provide model-generated-code execution; no execution tool is exposed. Local files and operator commands remain trusted.

The HERMES-01 experiment exhausted all ten authorized live attempts. Live commands now fail closed at the persistent cap. See `docs/hermes01.md` and `evidence/phase2/hermes01/live-summary.json`; normal hosted inference remains disabled. A new budget requires separate explicit authorization, not clearing this counter.


HERMES-01 closeout D23 used the existing bundle and explicit `--experiment closeout` on the launcher/host/read-only inspection CLI. Its separate `.local/hermes01/closeout-live-budget.json` allows a four-request ceiling per job and10additional total; original input/output/tool/deadline limits remain. On a successful submission the child uses pinned official `AIAgent.interrupt(hard_cancel=True, tool_reason='game_recap_committed')` after receiving the domain commit to prevent a gratuitous finished model call. Actual native job used3requests including one invalid-extra-field rejection; fresh recall used2. Ledger is closed at5/10; further closeout live attempts fail closed. Original10/10 ledger stays unchanged. Current accepted evidence is in `evidence/phase2/hermes01/closeout/`; both homes were removed and durable memory/save/audit retained. Normal inference remains disabled.
