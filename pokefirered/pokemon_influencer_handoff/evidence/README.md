# Validation evidence

`handoff_validation.json` records 59 successful package checks and nine schema-valid reference records. The checks cover file presence, instruction-file size, configuration invariants, cross-record references, selected illustrative roster budgets, and rejection of several malformed records.

No ROM was built or modified. No emulator, gameplay, full legality catalog, battle policy, model provider, save migration, or release patch was tested. Those are future milestones in `docs/test_plan.md`.

Re-run with `python tools/validate_handoff.py`. The current checker uses the pinned package dependency in `requirements-handoff.txt`. Re-running changes the report timestamp and therefore the checksum manifest; regenerate that manifest before distributing a modified package.
