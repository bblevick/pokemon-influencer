# Pokemon Influencer - endgame concept parking lot

**Status: DEFERRED. Do not implement from this document yet.**

The current release targets the existing campaign through first Champion completion. This file preserves expansion ideas without smuggling them into campaign balance or the first Codex backlog.

## Intended payoff

After becoming Champion, the player meets familiar followers whose personal journeys have continued. The appeal is recognition and accumulated history, not a random parade of perfect counter-teams. A former forest trainer may become a credible specialist while retaining the partner and personality the player remembers.

## Candidate concepts to develop later

### Influencer Circuit

An optional rematch circuit involving the player's recurring cast. Qualification could depend on relationships, invitations, regional representation, and story arcs, not solely follower count. Decide later whether it is a tournament, route-based tour, or invitation board.

### Ambitious traveling followers

A small authored subset can visit new regions of Kanto or other existing game areas. Travel creates an explicit itinerary and acquisition permission. PokeBook can show the trip before a new species appears. Most trainers should remain local; travel is character development, not universal permission for any Pokemon.

### More developed preparation

Larger resource budgets, carefully staged team expansion, deeper tactical models, and additional equipment could become appropriate. They still require legal moves, plausible access, stable Pokemon identities, preparation cutoffs, and no hidden-player information.

### Long-form social arcs

Rivalries, collaborations, reconciliation after misinformation, gym-leader relationships, and a community challenge could turn the accumulated memory graph into authored optional stories. Sponsorship-like content is only a possible fictional quest framework, not real-money integration.

## Decisions intentionally left open

- Which event unlocks each system and whether any existing FireRed postgame is reused.
- Circuit format, prizes, level ranges, team sizes, retry economy, and difficulty modes.
- Number of followers promoted to major characters and selection rules.
- Travel destinations, exceptional acquisition grants, and whether expanded species are ever allowed.
- Whether all trainers keep their campaign lineage core or a few get explicit replacement arcs.
- How much new art, maps, writing, and testing the expansion warrants.
- How returning campaign saves migrate into the new content.

## Extension points to preserve now

Use stable NPC IDs, individual Pokemon lineage IDs, versioned roster plans, authored region/travel permissions, an event ledger, friendship and exposure records, and a data-driven progression predicate system. Add a generic `content_phase` field capable of `campaign` or `endgame` without defining endgame behavior.

An `endgame_enabled` feature flag defaults to false. Core campaign code must not depend on endgame configurations or content. First Champion completion can emit a neutral milestone event for later use; do not start an unfinished circuit or crash while looking for missing endgame files.

## Future approval gate

Before implementing this expansion, write a separate product spec, balance envelope, acquisition policy, migration plan, content roster, and test plan. Review whether the campaign's memory and rematch loop is actually fun first. No campaign trainer receives broader catch pools merely because this document mentions them.
