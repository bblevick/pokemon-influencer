# The puppeteer, memory, reputation, and PokeBook

## 1. The useful metaphor, with a boundary

The puppeteer decides which believable story threads become active and what context each actor receives. It does not make everyone omniscient or control all outcomes. Think of a director constrained by an evidence ledger, actor perspectives, and game rules.

Its high-level goals are continuity, understandable consequences, character identity, and player choice. It must not optimize engagement at any cost or continually make the world more hostile.

The Hermes analogy is bounded memory plus retrieval around a short-lived reasoning session. Game-specific additions are visibility, social delivery, causal provenance, scoped authority, and save-timeline consistency. Do not use a single shared personal-memory file as the world state.

## 2. Four distinct kinds of state

| Layer | Example | Who can use it? |
|---|---|---|
| Canonical event | Player defeated trainer X using the revealed Pokemon Y | Trusted rules; selected views only |
| Observation/exposure | Trainer Z watched that battle or received post P | That observer and scoped services |
| Subjective belief | Z tentatively thinks the player favors Fire attacks | Z's planner, with confidence/evidence |
| Public artifact | X published a challenge on PokeBook | Permitted readers who receive/access it |

Never substitute one layer for another. A post does not establish its claim as true; a true event does not imply universal exposure; a belief does not create an event.

## 3. Suggested persistent tables

Every gameplay-domain key is namespaced by save lineage and branch where applicable.

- `events`: canonical, append-only typed events, source, sequence, game tick, payload hash.
- `npc_profiles`: stable identity, voice, archetype, home, resources, goals, follow policy.
- `social_edges`: directed follows and authored contact relationships; friendship is separate.
- `claims`: structured assertions with origin IDs, truth classification, visibility, permitted use.
- `posts` / `post_replies`: published artifacts, claim references, author and publication state.
- `deliveries`: recipient, artifact, origin, channel, exposure tick; unique for idempotency.
- `memories`: subject-owned episodes/summaries, source references, confidence and retrieval fields.
- `beliefs`: evidence-weighted estimates, support/contradictions, knowledge cutoff.
- `relationships`: familiarity, friendship/trust, respect, rivalry/tension, explanation references.
- `reputation`: regional/faction estimates and aggregate audience counters, not universal truth.
- `training_opportunities` / `roster_plans`: immutable evidence cutoffs and prepared team versions.
- `model_decisions`: inputs/version/output hashes, selected proposal, fallback, token/cost metrics.
- `jobs` / `outbox`: durable scheduled work and external effects awaiting safe publication.
- `checkpoints`: game/host pairing, branch parents, content and schema versions.

SQLite migrations, indexes, unique constraints, and a serialized writer are sufficient for the first local game. A large graph database is not a prerequisite.

## 4. Memory formation

A battle emits only meaningful observations needed for later behavior: species revealed, moves observed, switching decisions, result, and notable moments. Do not preserve an unlimited raw frame trace in every NPC memory.

Create an episodic record for direct experience. Extract tentative predictive features only when supported. Store the number of independent observation opportunities, not just a confident sentence. One battle can justify "used Ember against me" but not "always uses Fire Pokemon."

Suggested mechanics:

- A repeated behavior rate uses a small prior and bounded weighted observations.
- Cap the influence of one battle on a long-term style estimate so 20 turns are not mistaken for 20 independent encounters.
- Correlate posts/reposts with their original battle/event; copied claims do not multiply confidence.
- Mark evidence as direct, verified report, hearsay, or authored rumor.
- Allow later evidence to weaken or reverse a belief; never delete an inconvenient true event.
- Decay the predictive usefulness of old patterns with game progression, not the truth of the underlying event.

Use event/epoch time for decay. Leaving the game closed overnight does not secretly reset friendships or grow opponents.

## 5. Scoped retrieval

First select evidence that the NPC is authorized to know at the requested branch/cutoff. Only then rank it by relevance, significance, recency, and unresolved relationship context. Filtering after retrieval or after prompting is too late.

Initial context budget: roughly 1,200 input tokens for NPC context within a total 2,000-token job budget. Use at most eight structured facts, four short memory summaries, one relationship summary, and the relevant legal-action/candidate list. Exact tokenizer limits are enforced by the chosen adapter.

The NPC packet includes identity, immediate situation, known facts with IDs, uncertain beliefs, goal, constraints, and allowed proposals. It excludes raw world-wide events, other NPCs' private notes, and any secret player data.

Retrieval tools are capability-scoped: `read_own_memory`, `read_delivered_post`, `read_known_relationship`, `list_legal_candidates`, and `read_current_goal`. A trusted director may schedule cross-world processing, but NPC-specific reasoning must still receive the subject's filtered perspective.

## 6. The bounded puppeteer loop

```text
Accepted game event or social trigger
 -> deterministic significance/eligibility filter
 -> compute allowed actors, audiences, actions, and budgets
 -> load the selected actor's scoped context
 -> rules decide ordinary cases
 -> optional model proposes a bounded action for an interesting case
 -> validate facts, authority, social reach, timing, and resources
 -> atomically commit state effects and an outbox item
 -> render/publish/deliver at a safe moment
```

A job can end with `no_op`. More generated content is not inherently better. The puppeteer may choose between a local supportive reply, a friendly challenge, and silence; it cannot manufacture a regional scandal because it sounds engaging.

## 7. Information propagation

Maintain authored contacts and earned follows as directed graph edges. A follow increases delivery eligibility, not guaranteed readership. Location, shared topic, relationship, activity, and privacy determine eligible recipients.

Initial social propagation rules:

- At most one repost hop beyond the original audience in the small slice.
- A unique origin cannot earn follower/reputation credit repeatedly through its own repost chain.
- A recipient records exposure once per artifact/version; a repeated delivery is idempotent.
- A new region does not receive a post solely because the player arrived there. It needs a feed/contact route.
- Parent posts must be visible to a commenter before a reply can be proposed.
- Narrative secrets have explicit publication restrictions even if they are witnessed.
- A visible UI explanation can say "Saw your forest battle through Reed" without showing internal confidence scores.

Start with deterministic or seeded delivery selection. Record the selected deliveries so replay does not reroll who knows what.

## 8. Reputation and relationships

Avoid one global karma score. Track regional visibility/fame, perceived battling skill, helpfulness/trust, and notoriety. Track each named NPC's familiarity, friendship/trust, respect, and rivalry separately.

A direct opponent can update respect immediately from its battle. Other NPCs change only after exposure. Anonymous audience counts can increase from a publication, but that does not automatically update every named actor.

Implement effects as small, bounded tables tied to typed events and evidence. An LLM can propose an emotion label, but the rules decide the permitted numeric delta. Store explanation references for debugging.

Follower count never boosts combat stats. Social consequences initially affect wording, optional challenge readiness, small social interactions, and who pays attention. Required story access, essential items, and the ability to continue must not depend on farming popularity.

## 9. Deliberate rumors versus mistakes

Do not convert accidental model hallucinations into gameplay automatically. They are rejected or replaced with a safe template. Intentional misinformation is a separate authored claim type with origin, confidence, actual truth status, propagation limits, and a correction path.

For the first slice, use one controlled rumor/correction fixture for tests and keep procedural rumor creation disabled. The campaign can add authored rumor events after basic delivery and factuality work.

Prose validation cannot perfectly prove that free text is factually faithful. Therefore mechanical effects depend only on validated typed claims. Use constrained templates/slots for essential facts, entity/number allowlists, and human review of model-generated style. Unsupported content falls back to a template.

## 10. PokeBook interaction specification

### Feed cards

Small author handle, concise body, local topic/location when public, modest engagement, and a reply/challenge indicator. Initial body target: at most 96 allowed characters, with actual game-font width and page count checked after encoding. Model token limits are not a substitute for pixel layout checks.

### Posting flow

After a safe event, queue a draft with approved facts. At a safe overworld prompt: Post, Keep private, or Later. Tone options can be Friendly, Proud, or Competitive. Their mechanical relationship effects are authored and small. The player sees the text before publication.

### Challenges

Show the trainer's identity, known location, ready status, and optional public training note. A training note cannot promise an uncommitted capture. Readiness does not expose the entire private prepared moveset unless an intentional scout/reveal mechanic is later approved.

### Notifications and spam control

Batch follows, avoid repeated feed popups, and reserve interruptions for the player's explicit menu action. At most one highlighted NPC social artifact per major event in the slice, plus compact follow/engagement summaries. Posting is optional; rematches remain available to quiet players who meet the gameplay gates.

### Offline/no-cloud behavior

When the local runtime is active and the LLM is disabled, all social state changes occur normally and templates provide text. An optional label in settings explains that generated writing is disabled; characters should not say "the API failed."

## 11. First-slice cast and content workload

Target about 6-10 persistent profiles rather than simulating every NPC in the first milestone. Bind at least three actual ordinary trainer entries and explicitly annotate any newly authored demonstration character. Include Oak, a rival social role, Brock, a local recipient, and an unrelated recipient who should not learn the private event.

Each enhanced profile needs a stable ID, verified ROM binding, home/allowed maps, archetype, signature lineages, resource tier, personality parameters, follow policy, voice guide, a small set of fallback text, and a rematch predicate. Avoid making content quality depend on a model inventing these foundations.

## 12. Privacy and prompt safety

This is a fictional, local social network. Do not connect actual user accounts or publish real content. A cloud model receives only the minimal sanitized fictional context, not ROM bytes, full saves, API secrets, real identifiers, or unrestricted event logs.

Player handles and authored/generated text are untrusted. Ignore embedded instructions; escape text control codes and path-like content; reject unsafe byte sequences. Keep dialogue appropriate to the intended Pokemon-like tone: no sexual content, targeted slurs, graphic violence, or personal-data requests.
