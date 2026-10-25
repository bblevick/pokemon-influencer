# STRATEGY-MODEL-02 — blocked at provider qualification

**STRATEGY-MODEL-02 BLOCKED. No replacement activated.**
The primary Gemma free route qualifies from current metadata, but both allowed tiny
smoke attempts returned HTTP429 from Google AI Studio. The exact authorized Qwen
contingency is absent from the current catalog and its endpoint list is empty,
so no Qwen generation was attempted. No third model, random router or paid alias
was used. No campaign gameplay or James/Kent live Strategy job was started.

## Primary and secondary evidence

Exact primary `google/gemma-4-31b-it:free` exists; canonical slug
`google/gemma-4-31b-it-20260402`,262144 context, text input/output, prompt/completion
price0, max_tokens supported. Healthy accepting Google AI Studio endpoint reports
status0 with daily uptime99.32779754843811%. Five-minute/30-minute uptime are null.
The old generic adapter assumed a numeric short-window value and raised TypeError.
The source metadata snapshot identifies the cause; no request had been sent then.

The generic text-route predicate now requires status0, first published valid numeric
uptime among5m/30m/1d, known positive uptime<=100, zero prompt/completion prices and
bounded text output. A measured short-window zero cannot be overridden by a longer
positive value. Inactive status-2 still fails. If all metrics are unknown, fail closed.
Returned healthEvidence records the actual window used. This change is metadata
nullability handling, not a Gemma/trainer branch or strategy redesign. Tests retain
paid/inactive/unknown/zero rejection and no tools/JSON prerequisite.

Attempt1 `strategy-model02-smoke`: HTTP429, provider Google AI Studio, latency.301s.
Attempt2 `strategy-model02-smoke-retry`: HTTP429, same provider, about40s after attempt1,
latency.252s. Sanitized message `Provider returned error`; no provider raw body/request
ID or usage receipt is retained. Precise current classification **rate_limit**,
retryable=true. Neither request produced a usable completion. These are provider
smoke failures in this bounded window, not claims that Gemma is permanently unavailable
or that the configured OpenRouter account's quota was necessarily responsible.

After the authorized one transient retry failed, evaluated contingency
`qwen/qwen3.8-27b:free` via public metadata only. Exact model rows0, endpoint rows0:
`configured_model_unavailable`. Do not substitute another Qwen spelling/version or
infer a price/uptime from the user's earlier snapshot.

## Accounting and stop

Separate Strategy qualification ledger: max4 calls, actual2, both Gemma smoke;
Qwen0, production-shaped live fixture0, Mercury0, Hermes0, campaign jobs0.
Ledger closed;2 unused not spent automatically. Explicit free routing/max_price0
before both POSTs. Error responses supplied no usage/cost, so **reported cost unknown**;
no nonzero billed cost is asserted. No campaign98 allowance was consumed/reopened.

The production fixture was correctly withheld because no smoke passed. An early
fixture CLI attempt hit that guard before metadata/POST; its failed console is
retained and is not a generation request. Offline synthetic Avery fixture prepares
7738 bytes through the exact serializer and normal scouting prompt with own
persona/team/moves/resources, public scoped claims, provenance/relevance, uncertainty
and PREP bounds. No tools/tool_choice/response_format; no campaign job or executable
choice. Its live memo quality/storage gate remains **UNRUN**.

James/Kent local production contexts prepare against the Gemma candidate binding;
request hashes/bytes in candidate-local-readiness.json. These are candidate-only,
not new active campaign memos or an accepted model switch. Historical C1 normal
restore returns exact memo text/provider/model/context/prompt metadata and Greg lock
without reinference. Original databases, C1 battery, historical/continuation ledgers,
model_profiles.yaml and campaign content remain byte-identical.

## Configuration disposition

Do not silently return to or qualify Nemotron. It remains the unchanged, known-blocked
configured model; no new Strategy work may run under this failed qualification.
Gemma is recorded as the evaluated replacement candidate, not an active qualified
production model. The .env model selector was not changed because neither candidate
passed live transport. Hosted inference stays disabled.

The established selector `POKEINFLUENCER_STRATEGY_MODEL` is the appropriate eventual
explicit swap mechanism after qualification. `config/model_profiles.yaml` contributes
to historical Strategy configuration identity; changing its defaults blindly would
invalidate existing store opens. .env selection supplies per-job providerConfiguration
and preserves that domain identity. No model name is hardcoded into domain/trainer/
prompt logic; qualification candidate constants only restrict this authorized test.
Historical Nemotron/other-model memos must retain their original metadata forever.

The98-call campaign readiness calculation, C1 and Greg lock are unchanged. Final
CAMPAIGN-EXPANSION-01 remains blocked at required Strategy qualification. No campaign
continuation, acceptance or next-phase implementation is claimed.

## Validation, memory and evidence

49 relevant tests passed,0 skips: three new metadata tests plus retained Strategy
provider/memo/gate regressions; exact count/exit in tests.log. No skipped tests are claimed as executed. Native
ROM unchanged; all RAM tuples match preceding accepted ELF, permanent EWRAM before4/
after4/delta0. No ROM rebuild or permanent instrumentation; runtime stack/heap peaks
remain unqualified. No task worker/emulator was launched; one-shot CLI requests ended.

Evidence root `evidence/phase3/strategy_model02/`:
gemma-metadata.json, gemma-route.json, gemma-failure.json (initial adapter TypeError),
smoke-route.json, smoke.json, smoke-retry-route.json, smoke-retry.json, qwen-metadata.json,
qwen-failure.json, requests.json, synthetic-context.json, synthetic-request.json,
candidate-local-readiness.json, historical-preservation.json, protected.json,
verification.json, tests.log and console transcripts. Diagnostics retain category,
HTTPstatus, model/provider, logical job, stage, hashes, timing/retryability without
credentials or full sensitive packets. Fixture is fictional public-game data only.
No old artifact or historical error classification was rewritten.

## Exact commands

From `/Users/blevicki/Documents/poke/pokefirered`:

```sh
.venv/bin/python tools/strategy_model02.py smoke
.venv/bin/python tools/strategy_model02.py fixture
.venv/bin/python tools/strategy_model02.py smoke --retry
.venv/bin/python tools/strategy_model02.py close
.venv/bin/python -m unittest discover -s tests -p test_strategy_model02.py
.venv/bin/python -m py_compile strategy/provider.py tools/strategy_model02.py
```

The fixture command above failed its required successful-smoke guard; no POST.
Gemma/Qwen catalog/endpoints metadata used `public_get`, then `qualify_text_route`,
saving exact model-row/endpoint snapshots. Offline preparation used
`qualification_packet()`/`OpenRouterProvider.prepare_request` only. History proof
used an isolated SQLite backup, new candidate context binding, normal paired C1
restore, replay hashes and exact existing memo/lock comparisons. Original files
checked by SHA256; memory by source ELF `ram()` tuple comparison.

Relevant combined regression command:

```sh
.venv/bin/python - <<'PY'
import unittest
patterns=['test_strategy_model02.py','test_strategy01_provider.py','test_strategy_memo.py','test_campaign_gate_repair.py']
s=unittest.TestSuite(unittest.defaultTestLoader.discover('tests',pattern=p) for p in patterns)
r=unittest.TextTestRunner().run(s)
raise SystemExit(not r.wasSuccessful())
PY
```

Next remains Strategy replacement qualification under a separately explicit bounded
availability/model decision. No further calls under this closed window. Once a model
passes, update the selector and readiness, then return to the already authorized
Greg→James→Kent closeout. No third model or gameplay under this ticket; endgame deferred.
