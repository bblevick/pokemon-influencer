# STRATEGY-MODEL-03 — accepted live-catalog replacement

**STRATEGY-MODEL-03 ACCEPTED. Active new-job Strategy model:
`dots-studio/dots-3-note-preview:free`.** Existing `.env` selector now resolves this
exact model through the unchanged provider-neutral ordinary-text adapter. No tools,
JSON, response_format, candidate selection, retrieval or campaign mutation introduced.
Hosted inference remains disabled outside separately authorized runs.

## Live catalog and selection

Queried current `/api/v1/models` first, then endpoint metadata. Mandatory filter:
explicit :free, text input/output, max_tokens, >=24576 context, zero prompt/completion
prices, healthy accepting endpoint with known positive uptime, sufficient output
bounds, usage compatible with one-shot prose, no expiration before near-term closeout.
Published metadata and endpoints retained, including absent preferred routes.

Neither preferred `inclusionai/ling-3.0-flash:free` nor
`inclusionai/ling-3.0-flash-fin:free` exists as a free entry. Current corresponding
non-free IDs cannot be substituted. Finance/medicine/safety/coding-specialized entries
were not favored over suitable general ones. Inkling excluded pending removal of
incompatible agent-harness restrictions; no change to Strategy architecture. Google
AI Studio Gemma excluded after prior two429 failures without a different provider.
Historical unhealthy Nemotron Lightning remains excluded.

Eligible general shortlist was ranked deterministically by general task fit, provider
diversity from failed routes, current measured uptime, healthy provider count, daily
uptime and sufficient context. No benchmark/prestige score. Metadata showed:

| Catalog shortlist | Provider |5m uptime |1d uptime | Context | Disposition |
|---|---|---:|---:|---:|---|
| Liquid LFM2.5-2.6B free | Liquid |100% |99.9602% |65536 | general secondary preferred over absent finance route; smoke400 |
| Dots3-Note Preview free | AtlasCloud |100% |99.6627% |512000 | next ranked diverse general route; third contingency passed |
| Nemotron3 Super free | Nvidia |100% |99.9339% |262144 | lower provider diversity; not generation-tested |
| Nemotron3 Ultra free | Nvidia |99.0235% |96.2319% |1000000 | lower provider diversity/health; not generation-tested |
| Apodex1.1 Mini free | Novita |100% |99.9823% |262144 | research/forecasting-specific fit below general candidates; not generation-tested |

Section6 authorizes a healthy general-purpose secondary over the finance-tuned model;
Liquid was that secondary. Its one smoke returned **HTTP400**, sanitized message
`Reasoning is mandatory for this endpoint and cannot be disabled.` The existing
adapter disables optional reasoning; Liquid catalog marks mandatory=true. Retain this
as a request/adapter compatibility rejection, not an endpoint outage or vague provider
error. No retry, paid route, model-specific adapter branch or reasoning contract change.

Section7's single additional catalog-selected contingency was Dots: next eligible
ranked general route with provider diversity. Current catalog marks reasoning optional,
so the exact production request fits. No fourth candidate or further generation
comparison. Metadata inspection of the shortlist is not a model benchmark or generation.
`ranking-initial.json` preserves the original ranking; `ranking.json` records the
secondary failure and contingency disposition before its request.

## Terms, expiry and actual proof

Reviewed [OpenRouter Dots model page](https://openrouter.ai/dots-studio/dots-3-note-preview%3Afree)
and the publisher [model card](https://huggingface.co/dots-studio/dots3-note-prev/blob/main/README.md).
No incompatible one-shot/agent-harness use requirement identified; Apache2.0 weights/
code license does not replace hosted-service terms. Ordinary text generation was
actually exercised. No credentials, ROM, saves or confidential personal context were
sent; only a tiny fictional prompt and scoped fictional/public game fixture.

Published expiry is **2026-12-31**, after the intended next near-term closeout. Record
this residual maintenance limit and require fresh route metadata before actual future
jobs. This is an explicit free alias, not a promise of permanent availability or a
pinned immutable serving weight revision. No substitute may silently own a job.

Dots smoke: successful plain sentence, resolved exact free model, AtlasCloud,
HTTP200,3.437s, usage cost0. Synthetic Avery memo: HTTP200,7.604s, same exact model/
provider,2457 prompt+300 completion tokens, usage cost0. Existing scouting prompt,
fictional persona/team/moves/resources, attributed delivered Brock public facts,
uncertainty and PREP bounds; exact production serializer/extractor/storage text
validator. UTF8/hash/provenance fields are host-generated. No active campaign memo.

The memo substantially follows persona/evidence/resource limits and predicts a
possible Grass opponent while acknowledging unknown current party/lead. It invents
`Effect Nightmare` and overstates minor move-change permission/signature status.
Those remain subjective prose, not facts/owned moves/permissions. Do not repair or
rerun the memo: downstream PREP/System One must approximate intent using supplied
legal options. This meets the intended quality floor without asserting Pokémon
factual accuracy. Exact prose remains in contingency-fixture.json.

## Activation, historical replay and campaign readiness

First model passing metadata+smoke+fixture was explicitly activated by changing only
`POKEINFLUENCER_STRATEGY_MODEL` in `.env`. Other dotenv lines/credentials unchanged;
no dotenv content copied to public evidence. Selector proof in active-selection.json.
No cross-model live fallback chain. Backup environment values remain inactive.

`config/model_profiles.yaml` is unchanged because it contributes to historical
Strategy configuration identity. The established environment selector changes only
future per-job bindings. Legacy default Nemotron is no longer selected while the
explicit active selector is present; it is not treated as healthy fallback. Provider/
model identities already stored on Rick/Brock/Sally/Greg remain exact.

Offline isolated C1 restore/reopen proves existing Nemotron memo metadata/text intact
while the new active binding differs, all seven replay hashes unchanged, Greg lock
unchanged, no reinference. James/Kent local current context builders serialize with
active Dots binding (hashes/bytes in active-local-readiness.json). No real James/Kent
Strategy requests or new campaign records were committed. Actual later contexts must
reflect then-current authorized social knowledge. Original databases/C1/content/
model-profile identity and both old16/final98 ledgers remain byte-identical.

Next remains already-scoped CAMPAIGN-EXPANSION-01 final continuation, Greg→James→Kent.
Greg uses existing locked memo/preparation; Dots only for new James/Kent Strategy jobs,
Mercury for tactics, Hermes for recaps. **No gameplay started under this ticket.**
98 ceiling/sub-budgets unchanged and unused; no qualification calls transferred to it.

## Accounting and checks

Separate model03 ledger ceiling6; actual3: Liquid1 rejection, Dots2 successes.
Exactly two generation-tested models; preferred Ling metadata failed without a POST.
Dots at most2 calls; no further candidate tested after its success. Ledger closed,
unused3. Successful responses report total cost0; Liquid400 has no usage/cost receipt,
so whole-window reported cost is not falsely asserted fully known. All requests had
verified zero routes and max_price0. Mercury/Hermes/campaign calls0.

Verification compares protected file hashes, active configuration, exact historical
memo/lock and normal C1 restore/reopen, local James/Kent request hashes, production
text validator and source ELF RAM. 49 relevant tests passed,0 skips; regression log records count/exit. No
native code/rebuild/allocation: EWRAM before4/after4/delta0, all RAM tuples unchanged.
No task-owned workers remain; normal hosted defaults disabled. Stack/heap peaks remain
unqualified, as this host/config ticket does not run native battles.

Evidence `evidence/phase3/strategy_model03/`: catalog.json, catalog-text-free.json,
endpoint-qualification.json, ranking-initial.json, ranking.json, secondary-smoke.json,
contingency-{smoke,fixture}.json and route snapshots, requests.json, synthetic context/
request, active-selection.json, active-local-readiness.json, historical-preservation.json,
protected.json, verification.json and tests.log. All old failure records remain intact.

## Exact commands

Working directory `/Users/blevicki/Documents/poke/pokefirered`:

```sh
.venv/bin/python tools/strategy_model03.py smoke
.venv/bin/python tools/strategy_model03.py fixture
.venv/bin/python tools/strategy_model03.py smoke
.venv/bin/python tools/strategy_model03.py fixture
.venv/bin/python tools/strategy_model03.py close
.venv/bin/python tools/strategy_model03_verify.py
.venv/bin/python -m py_compile tools/strategy_model03.py tools/strategy_model03_verify.py
```

First smoke was Liquid400; the first fixture invocation failed successful-smoke
precondition before any POST. Ranking disposition then selected Dots under the same
ledger; subsequent smoke/fixture succeeded. Commands are not safe to rerun for new
inference: stable job identities and closed ledger reject duplicate attempts.

Metadata acquisition used `public_get` catalog once, endpoint calls in a four-thread
read-only pool, then `qualify_text_route`. Candidate filters/rank described above and
saved before dispatch. Activation used regex replacement of exactly one allowlisted
.env selector assignment, verifying all other lines equal in memory; never logged
keys. `strategy_model03_verify.py` is repeatable/offline, performs no network/calls.
Fixture storage validator is the same `strategy.memo.validate_text` used by
MemoStore.finish_memo; synthetic output is qualification evidence, not campaign state.

Relevant regression command:

```sh
.venv/bin/python - <<'PY'
import unittest
patterns=['test_strategy_model02.py','test_strategy01_provider.py','test_strategy_memo.py','test_campaign_gate_repair.py']
s=unittest.TestSuite(unittest.defaultTestLoader.discover('tests',pattern=p) for p in patterns)
r=unittest.TextTestRunner().run(s)
raise SystemExit(not r.wasSuccessful())
PY
```

Completed ticket STRATEGY-MODEL-03 only. Stop after verification/readiness update.
No automatic campaign continuation, new role, acquisition, next phase or endgame.
