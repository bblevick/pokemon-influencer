# AI contract skeletons v1

Draft 2020-12 JSON Schemas with closed objects, bounded arrays/strings, versioned host-domain packets. `.invalid` IDs are local registry identifiers; validation never fetches remote schemas. Examples are fictional authored fixtures, not gameplay/provider evidence.

Run `.venv/bin/python tools/validate_ai_contracts.py` using existing jsonschema==4.26.0. Schema constraints cannot prove authorized provenance, current state or cross-packet legality. Those remain deterministic domain-validator obligations documented in `../../docs/system1_battle_decisions.md`. The static checker includes illustrative correlation/membership checks only, not a runtime battle validator. Freeze/extend contracts with explicit versions before actual integration.

D22 realignment: these v1 skeletons remain unchanged historical fixtures. They lack the shared PreparationEnvelope/Selection/Commitment contracts and envelope-bound StrategicIntent/locked preparation battle correlation. Normative target definitions are in `../../docs/preparation_envelope.md`, with conflict/migration gates in `../../docs/architecture_realignment.md`. PREP-01 defines bounded schemas/fixtures before STRATEGY-01 consumes them; SYSTEM1-01A/B require separate installation and legal-action execution evidence. Schema validation is not gameplay coverage.
