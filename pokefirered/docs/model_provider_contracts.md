# Provider contracts — target v4

## Current System One preparation contract — D33 (2026-10-04)

SYSTEM1-01A is accepted for controlled opening Rick. Implemented provider-neutral `DecisionProvider.decide(state, question, choices)` returns a supplied choice ID, complete optional probabilities/confidence and normalized diagnostics. Preparation uses the exact frozen StrategyMemo in a separate subjective section and all current legal PREP candidates with source-derived neutral mechanics. Semantic approximation never expands the option set or turns prose into facts. A returned choice is recorded before fresh atomic commitment consumes an opportunity, updates finite stock/lineages and locks exact memo/envelope/candidate references. Stored choices replay without credentials or inference.

The native OpenRouter `/api/v1/systemone` adapter supports Jev/Mercury-style text state and one fixed-choice question; no chat/tools/prose parsing or vendor SDK in domain code. Configured Mercury Decide Free remains unchanged; the closed experiment used2 actual POSTs at zero recorded cost. Offline continuity fallback and sole-option selection are distinct sources; no resampling/confidence legality gate. Request/result/commitment schema1 artifacts are in schemas/system1/. Current <=32 choices,32768 request bytes,65536 response bytes and35-second request bounds are preparation-tested, not tactical latency acceptance.

Actual native constructors and paired Save19 reload are proved only for the controlled Rick installation path. Expanded BATTLE-01/D34 now qualifies the deterministic native legal-action/context/execution/fallback boundary for armed D33 Rick ordinary singles. SYSTEM1-01B/D35 actual shadow/enabled battle control and Save20 reload are accepted only for controlled Rick ordinary singles at normal speed. Broader BATTLE-02 campaign integration remains deferred. Historical battle v1/StrategicPosture fixtures are not silently migrated. Full rematch UX, nonzero items, later acquisitions, other trainers and unsupported battle formats require separate gates. See docs/system1_01a.md, docs/system1_01b_readiness.md and evidence/phase3/system1_01a/completion.json.

The D32 section below records the preceding Strategy-only scope. Its statements that commitment/installation were absent or System One unauthorized are historical; D33 supersedes them for this preparation gate only.


## Current Strategy output contract — D32 (2026-10-04)

Strategy emits a bounded, exact natural-language **StrategyMemo**, not required JSON, tools, enums, evidence IDs or numeric posture. One ordinary completion interprets the existing actor-filtered context and legal preparation constraints. Approximately100–250 words is a prompt target, not a semantic validation requirement. Host validation enforces nonempty strict UTF-8, at most4096 UTF-8 bytes, no unsafe control/format characters (paragraph LF allowed), and the current immutable actor/job/branch grant. The provider also enforces at most1800 output tokens,65536 response bytes,24576 request bytes/conservative input tokens,35 seconds/request and120 seconds/job. A failed completion produces explicitly labeled deterministic prose fallback; no repair loop.

Persist accepted text verbatim with host-generated strategy/job/actor IDs, campaign/branch/generation/cutoffs, context/material hashes, preparation-envelope reference, persona/configuration/prompt versions, timestamp/cursor and provider/model diagnostics. Reuse stored text on restart, UI refresh and repeated decisions. Fresh legitimate opportunities/material precommit evidence may yield different prose; replay does not regenerate it. Future commitment must atomically lock the exact memo reference/hash alongside the team. Commitment/installation is not implemented here.

A memo is subjective interpretation. Even an unsupported prediction remains text: it never becomes canonical truth, actor knowledge, acquisition permission, resources, preparation selection or a battle action. Future System One requests must separate **AUTHORIZED FACTS** from **STRATEGY MEMO — SUBJECTIVE**, pass the exact stored text, and allow only supplied current legal candidate/action IDs. No prose-to-facts or prose-to-numeric-posture conversion is required or implemented.

Historical posture schemas, prompt/config hashes, records and closed experiments remain unchanged. `strategy/memo.py` adds schema3/prompt2 MEMO receipts using the existing paired Strategy cutoff/hash. Historical internal projection key `postures` retains its name to preserve existing checkpoint hashes; `memo_records()` exposes only schema3 text. Explicit MemoStore adoption is limited to the new acceptance working copy; legacy StrategyStore refuses a memo-enabled database. Original databases are not migrated or rewritten. Normal inference remains disabled. No System One, party/resource/ROM change or endgame work is authorized.


D22 preserves actual HERMES-01 integration and its stop condition. The interfaces below are future provider-neutral contracts, not implemented strategy/System One classes. Actual Hermes uses its pinned conversation/tool runtime with guarded transport; a direct language-provider wrapper does not replace that requirement. `config/model_profiles.yaml` and its current providers are unchanged. No System One or additional live role is authorized; current bounded Strategy scope is recorded in D32.

These are domain interfaces, not implemented Python classes or SDK dependencies.

```python
LanguageModelProvider.complete(packet, limits) -> TextProposal
LanguageModelProvider.structured(packet, output_schema, limits) -> StructuredProposal
PreparationDecisionProvider.select(request: PreparationSelectionRequest, limits) -> PreparationSelectionResult
BattleDecisionProvider.decide(request: BattleDecisionRequest, limits) -> BattleDecisionResult
```

Strategy packets contain actor-authorized context without candidate IDs. System One packets additionally contain enumerated legal candidates/actions. Limits include hard request/input/output byte and token bounds, absolute deadline, maximum calls and zero cost policy. Callers inject adapters/fakes; no gameplay/domain/ROM/Lua code imports a vendor SDK or knows a model name. Hermes uses its actual scoped harness and guarded model transport; strategy has its own provider instance/configuration. System One uses two typed adapters under the existing slot: preparation candidate selection and battle legal-action selection. Neither adapter may reinterpret an output as unrestricted edits.

| Adapter target | Provider surface | Mapping |
|---|---|---|
| OpenRouter language | Chat completions | Inkling puppeteer / Nemotron strategy; Strategy: exact prose storage bounds; Hermes: guarded typed proposals |
| OpenRouter Mercury | Native System One | Battle state plus supplied legal action IDs → BattleDecisionResult; preparation envelope/candidate IDs → PreparationSelectionResult requires separate capability/mapping validation |
| OpenRouter Jev reference | Decisions API | State/questions → typed choice/probabilities, inactive under free-only policy |
| Future local Kev/MLP | Native local inference contract | Same typed preparation and battle choice boundaries; implementation/model capability unselected |
| Fake/template/heuristic | In-process deterministic fixture/policy | Same contract, no network |

[Jev official documentation](https://openrouter.ai/docs/guides/community/jev) distinguishes `POST /api/alpha/decisions` from `POST /api/v1/systemone`. [Mercury's model page](https://openrouter.ai/inception/mercury-decide:free) specifically documents the System One schema. Do not assume Mercury accepts the alpha Decisions endpoint or treat a native decision as chat prose. Exact Mercury wire mapping is deferred to versioned adapter fixtures/live contract testing; no adapter exists yet. Naming `openrouter_systemone` in configuration is a project adapter identifier, not an installed SDK.

Public catalog snapshots do not advertise `response_format`/`structured_outputs` for the selected Inkling/Nemotron models. `structured` therefore means the adapter must parse and validate bounded output, not assume provider-enforced JSON schema. Unparseable/rejected output invokes templates; no indefinite repair or switch to a paid model.

Normalization records provider, requested/resolved model, adapter version, latency, error code and fallback status. Missing credentials, unavailable/rate-limited provider, timeout, malformed output, refusal, model mismatch, unknown price or illegal/stale action all yield bounded deterministic fallback. Never mask failed output as provider success. Native probabilities are optional, untrusted diagnostics, not proof of legality or correctness. If adapter cannot confirm requested model policy, reject the response.

Credential boundary: only the trusted host adapter/guard reads `OPENROUTER_KEY`. Redact authorization headers; never log `.env`, keys or full process environment. No secrets in config, prompts, manifests, fixtures, ROM, Lua, save or evidence. Default/static tests inject dummy providers and never read `.env`. Historical HERMES-01 and STRATEGY-01 windows remain closed. D32 separately permits one plain-text Strategy smoke and one legitimate Strategy memo; System One is not authorized.

Aliases are experimental serving selectors. The versioned Jev reference and floating `~typesafe/jev-latest` are retained disabled; input pricing for Jev was nonzero in public endpoint metadata. Stored inputs/outputs support replay; a model ID alone does not ensure deterministic future inference.


## Preparation/intent and battle correlation

`PreparationEnvelope` v2 target correlation is defined before STRATEGY-01 in `preparation_envelope.md`. Strategy receives authorized briefing/personality and own companions/inventory plus this envelope; it emits strategic intent, not species/move/item edits. Selection returns exactly a supplied current candidate ID. Trusted services check actor/branch/epochs/opportunity, envelope/candidate-set/intent hashes, catalog/resource proofs and current quantities before committing/locking/installing. No provider may create acquisition permissions or spend twice.

Target battle request v2 binds the installed preparation commitment and accepted intent, along with current legal-action set/observation/phase hashes. Later social messages do not change locked preparation. Actual native item/resource consumption updates game state only through explicit rules. Preserve v1 fixtures; add versioned schemas/adapter fixtures at PREP/STRATEGY/SYSTEM1 gates before runtime use.

Current Mercury configuration identifies a candidate provider, not proof of roster/moveset/item candidate choice support or complete battle control. Do not assume chat, alpha Decisions and native System One surfaces are interchangeable. Per-role transport/live capability, price/entitlement and budgets need independent authorization/verification. This architecture adds no requests, paid routing or model substitutions.

## Historical STRATEGY-01 structured mapping (D29, superseded by D32)

`strategy.provider.LanguageModelProvider.structured` now implements the Strategy-only interface with deterministic fixtures and a guarded OpenRouter adapter. Schemas/context/posture, one typed submit_strategic_posture tool, local semantic validation, bounded fallback and derived save pairing are documented in strategy01.md. Actual model remains configured free Nemotron; config/model_profiles.yaml is preserved byte-for-byte, including its historical implementation-status wording. Ten explicitly authorized POST attempts are exhausted/closed with no validated live result; final diagnosed provider failures are NVIDIA upstream502. This updates the earlier "no Strategy authorization" historical statements only for this completed experiment. No normal host inference, new Hermes role, System One provider or extra authorization follows. All language/battle/preparation interfaces beyond this Strategy adapter retain their prior gates.

D30 renewed Strategy closeout supersedes v4 single-provider routing for v5 only: same-model failover is allowed within the preflighted zero-price/function-tool provider allowlist, with require_parameters/max_price0 and no alternate model list. Bounded5/10-second upstream backoff; <=3/job and separate renewed ledger closed3/10. Exact Nemotron model remains configured, backup variable unused. Current only eligible route NVIDIA again returned3 error502 envelopes; no accepted live posture. No additional role, normal-host activation or model change. See strategy01.md/closeout evidence.

D31: explicit Strategy test model-role selection resolves primary, configured backup, user-named backup_backup and emergency without automatic cross-model fallback. Default primary/offline/config is preserved; standard OPENROUTER_API_KEY credential alias is host-only. Persisted experiment limit5 is honored after adapter restart, <=3/job. Inkling-small lacks forced tool_choice, Qwen qualified metadata but actual3 v5 calls400/429/429 produced only fallback, free router has no qualifying endpoint records. Post-run v6 retains bounded redacted HTTP error-body diagnostics and stops400/429 unchanged retries; it made0 live calls. No schema change or accepted live posture/quality comparison. Explicit or ordered production fallback needs separate approval/route qualification/actual serving-model audit; neither is enabled. See strategy01.md/D31.


D32 acceptance (2026-10-04): corrected StrategyMemo host runtime and actual free Nemotron smoke/Rick result accepted. Exact model text survives fresh host/native Save17 Continue, paired Save16 rewind excludes it/late grant, and paired Save17 return retrieves it without inference.67 unique focused tests/0 skips and actual-artifact audit passed;16 full Rick option plans, knowledge/history/companions/resources and ROM unchanged. Budget closed2/2; historical records/inputs/evidence preserved and all task processes stopped. See docs/strategy01.md and evidence/phase3/strategy01/memo/completion.json. Next separately authorized SYSTEM1-01A; no selection/commit/install/action or endgame implemented.


## BATTLE-01 tactical boundary (D34)

Current battle request/result/state schemas are schemas/battle/*.schema.json (request2), separate from historical battle v1 fixtures. Pure provider decide(state,question,choices) work runs outside the single SQLite/event writer, with one outstanding worker and no accumulating queue. Host owns correlation/campaign/branch and native mapping; an invalid choice is rejected, never approximated. Native revalidates current legal snapshot hash/session/battle/turn/phase/battler/deadline and uses ordinary controller emissions; vanilla handles unavailable decisions. BATTLE-01 made0 calls; configured hosted slots and closed phase3 budgets are unchanged. Exact fixture, measured local timing and future bounded native-provider requirements: docs/system1_01b_readiness.md. No model latency/availability claim follows from deterministic acceptance.


Current accepted tactical experiment: docs/system1_01b.md (D35), with separately scoped HTTP2.35/worker2.55/host2.75-second bounds and unchanged native180 frames. Preparation35-second and retained BATTLE host2.5-second defaults are unchanged. Actual enabled native control and paired persistence are proved; early shadow/fallback timing failures remain excluded and recorded. Ledger closed/default hosted disabled.
