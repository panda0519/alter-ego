# Start here

The submission demo is described in [README.md](README.md). The notes below are the original setup pack.

This is an implementation plan and setup pack, not a finished prototype.

1. Both read MASTER_PLAN.md and AGENTS.md.
2. Copy the contents into the root of the agreed Git repository. Do not commit the zip itself.
3. Person A opens prompts/A00.md in Codex; Person B opens prompts/B00.md in Cursor.
4. Execute phases in order. Each person reads the shared contract before building.
5. Fixtures are illustrative synthetic UI data. Metrics are explicitly not_run.

Included: shared rules, pinned dependency manifests, model YAML, four JSON schemas,
six-well/60-day UI fixtures, one contract checker, agent instructions, slide outline,
handoff/status templates and 25 small role-specific phase prompts.

Not included: app source, data downloader, synthetic training generator, GCN/LSTM code,
training results, trained weights, working deployment, platform accounts or sponsor runs.
Those are built by the phase prompts and verified on your machines.

Run the bundled contract check after installing ml/requirements-common.txt, or install
jsonschema==4.25.1 in a small separate environment:

    python scripts/validate_exports.py contracts/fixtures

This verifies schema/consistency of export files, not model accuracy or a completed system.
