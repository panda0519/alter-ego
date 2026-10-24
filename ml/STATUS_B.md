# Person B status

Phase: B00 setup. Local Python 3.11.17 and torch 2.8.0+cu128 are verified. Model implementation has not started.

Dataset decision: pending. No cohort has been frozen and no measurements have been inspected.

GPU check: PASS on the local RTX 5050 Laptop GPU. Driver 595.99.02, compute capability 12.0, 8151 MiB. Torch wheel CUDA 12.8. `nvidia-smi` CUDA Version 13.2. Finite 8x8 forward/backward on `cuda`. This is not a training run.

Environment: uv 0.13.5, CPython 3.11.17, `.venv`. Lock `ml/locks/ubuntu-cuda128-working.txt`. pip check: `No broken requirements found.` System Python remains 3.14.4.

Checks: `ml/B_PHASE_0_SELF_CHECK.md`. Pytest `tests/` : 2 passed. Fixture validator passed. Bad `generated_at_utc` rejected as not a date-time.

Request for A: `ml/requirements-common.txt` now pins `jsonschema[format-nongpl]==4.25.1` so `scripts/validate_exports.py` checks date-time. Original file digest `a1619c46f50f9c53c1940ec9da9c5dec1a5c6a76cc3af7536875ab102b4eceff`. Please review before treating the root requirements story as unchanged. `scripts/validate_exports.py` was not edited.

B05 handoff, when that phase starts: one schema 1.0.0 batch under `artifacts/exports/<run_id>/` with matching meta in `predictions.json`, `metrics.json`, `run_info.json`, and `agent_context.json`. Neural methods stay null / `not_run` until a real neural run. A publishes the whole batch. No batch exists yet.

Nodus: package `nodus-compute` 1.0.27 in `.venv-tools`; CLI banner `nodus 0.1.45`. `whoami` and `get jobs` say not logged in. No org, project, credit balance, MCP install, or job id. No spend.

Git: `feature/model` parent `e756549b7de11368f9af54e7f123f9a412c79f78`. Remote `https://github.com/panda0519/alter-ego`. `origin/main` has no merge-base with this branch and was not merged. `origin/feature/person-a` is `c9317d9b71180db00f43a888405888711da08c26`. Repo-local `.git/config` author is `theravij <2501640100693@psit.ac.in>`. No `~/.gitconfig`. `gh` is not installed. Push was not attempted.

Next: Nodus login is still PENDING. Run `nodus login` in the operator terminal, then `nodus whoami`, before any org, credit, or job claim. Phase 1 model work stays stopped.
