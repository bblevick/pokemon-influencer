# PREP host packets

`envelope.schema.json` and `candidate.schema.json` are closed schema1 packets, consumed by `prep.domain`. Packet validity is not a grant: only a freshly issued `PreparationEnvelope` from the active `PrepStore` carries trusted state. Models must not instantiate Context, mutate a packet or create an opportunity.

The envelope hash covers normalized constraints before adding its own ID/hash. A candidate's semantic hash covers schema/envelope ID, exact complete party/order, native battle-item slots, development paths, costs and acquisition count; proof/neutral descriptors are recomputed, not treated as authority. The separately hashed generation result contains current bounded candidate IDs, unchanged fallback option, versions, examination/pruning/rejection diagnostics and selectedCandidateID=null. `resolve_preparation_bundle` returns these correlated objects without creating a circular hash dependency.

Active generation is deterministic: no seed/draw, model, matchup score or chosen winner. Eligibility and validation use source catalog, content/adaptation/generator/validator versions, active lineage/resource/epoch state and paired evidence. Serialization alone cannot authenticate those inputs. Revalidation with the active store is mandatory before later commitment; restore/branch/cutoff/ownership/reservation changes invalidate prior capabilities.

Future cap1/2 acquisition envelopes are expressly scenario-only qualification interfaces. The eligible-origin resolver is executable; sampling/capture outcomes/complete acquisition packages are gated by PREP-ACQ-01. Selection, actual resource consumption/commitment and native installation schemas belong to SYSTEM1-01A. Historical schemas/ai v1 are preserved unchanged.
