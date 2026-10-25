# Trainer battle completion and tactical disposition — BATTLE-END-01

Canonical truth remains native. The existing BRIDGE-02 event ABI is unchanged:
`BATTLE_ENDED` (type 5, phase END) carries trainer u16, first-win u8 and
native outcome u8. The header binds native battle/turn, sequence, heartbeat;
authenticated transport binds build/session/run; launch and canonical ingestion
resolve campaign, branch and stable canonical battle/event IDs.

For supported ordinary single trainer battles: outcome 1 means player victory,
2 player defeat, 3 draw. Other existing source outcome codes are not newly
qualified trainer modes. An outcome value or prize text alone is insufficient.
`HandleEndTurn_FinishBattle`, after its TRY_FINISH/FINISHED guard, calls
`PiEvents_End` once before `PiBattle_End`, palette fade and battle-resource
cleanup. Win additionally emits TRAINER_DEFEATED. Neither model code nor host
UI parsing determines this result. The real Gym callback and badge script are
unchanged.

The event queue owns a byte copy, never a battle-state pointer. Its fixed four
records remain bounded. Terminal records retain the same sequence until ACK or
explicit reset/fresh lifecycle; timeout retries use bounded per-frame work and
never block native play. Terminal enqueue can discard unsent nonterminal tail
records (with the existing drop counter) to reserve space, never the in-flight
head or existing terminal records. This supports a completed battle and brief
host absence; it does not promise unlimited offline battles, durable ROM RAM
across power loss, or arbitrary savestate recovery. Queue overflow remains
observable. Host commits before ACK; duplicate delivery returns the same durable
event ID. Exactly-once is an active-branch projection property, not an assertion
that abandoned append-only history disappears.

Tactical provenance is separate. REQUESTED → RESULT_PUBLISHED means a validated
host choice was sent. CONTROLLER_EMITTED means native revalidation emitted the
controller action, not that damage occurred. EXECUTED requires the corresponding
canonical NPC action-resolution event (which can describe a failed move).
An interrupted action instead ends explicitly as CANCELED_BATTLE_ENDED,
CANCELED_TIMEOUT_FALLBACK, CANCELED_RESET, CANCELED_RUN_ABORT or
CANCELED_UNSUPPORTED. These audit records grant no NPC knowledge.

Lifecycle audit IDs bind campaign/branch/session/generation/request/stage. One
terminal disposition is permitted per identity, with same-stage retry idempotency
and conflicting terminal rejection. Existing tactical-audit checkpoint cutoffs
exclude future lifecycle records after paired restore. Revoked-branch cancellation
is diagnostic only and cannot enter the active projection. A fresh host cancels
unfinished prior-process requests; it does not resume or resend an accepted choice.
Old request IDs are retired for that process. Durable canonical terminal receipts
and in-process terminal tombstones prohibit late tactical snapshot scheduling or
result publication. Native Supported() rejects nonzero gBattleOutcome for normal
selection and forced replacement before issuing a request. Final opposing-party
exhaustion is handled by the engine's existing outcome path.

Before freeing the 1036-byte tactical Work allocation, native End stores a small
terminal disposition in the existing 48-byte fixed control: 6 pending canceled,
7 external controller issued, 8 sole engine controller issued, 9 timeout fallback,
10 invalid/stale fallback. Lua reads only this fixed block when pointer is zero;
it never dereferences the freed allocation. These states change no structure size,
wire event format, legal action enumeration, move power or trainer resources.

```mermaid
sequenceDiagram
  participant E as Native battle engine
  participant Q as Fixed event queue
  participant H as Local host
  participant D as SQLite branch
  E->>E: Finish result/reward scripts
  E->>Q: Copy terminal outcome (once)
  E->>E: Copy tactical disposition; free Work
  E->>E: Return to Gym script or whiteout
  Q->>H: Same terminal identity (retry until ACK)
  H->>D: Commit canonical end + mandatory recap obligation
  H->>D: Cancel obsolete tactical work
  H->>Q: ACK committed sequence
  Q->>Q: Retire receipt
```

Automatic mandatory recap obligation creation remains the accepted Puppeteer
service. This repair does not run recap inference, publish a fallback post, or
advance virality. Brock's source-bound `gym` prominence is only a trusted future
HIGH_PROFILE input; no new diffusion is claimed.
