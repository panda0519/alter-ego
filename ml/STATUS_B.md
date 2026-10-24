# Person B status

Phase: B01–B04 data bundle is prepared locally. Baseline export has not started.

Dataset decision: synthetic. No local groundwater CSV. India-WRIS returned an HTML page, not a series. The CKAN telemetry resource is a 1,639,100,785-byte CSV with no column list or licence in the metadata that was returned; it was not downloaded. `package_show` returned HTTP 403.

Active private bundle: `data/processed/active`. `dataset_id` `05902f5167e6a8aefa02386b6437bfa984a2ec3b67e3fffee7c69d7b145c8351`. `dataset_kind` synthetic. 40 wells, 731 days, 2023-01-01 through 2024-12-31, metres below ground. Roles 22 visible / 10 train_masked / 8 holdout, seed 42. Date cuts 438 / 109 / 184. Minimum training coverage 0.8379. This is not field accuracy.

Weather: NASA POWER v2.10.1, four cached cells, PRECTOTCORR mm/day and 2 m temperatures in C, Hargreaves ET0 with Ra times 0.408. `q` is not estimated.

Environment: `.venv` CPython 3.11.17, torch 2.8.0+cu128 from Phase 0. This phase did not train.

Checks: `ml/B_PHASE_1_SELF_CHECK.md`. `.venv/bin/python -m pytest tests -q` : 15 passed. pip check: `No broken requirements found.` Fixture validator passed. Fixture and `prototype.yaml` hashes unchanged.

Request for A: no schema change. Do not publish `data/processed/active`. The jsonschema format extra from Phase 0 is still waiting on your review. The four-file handoff is still B05 and does not exist yet. When it does, keep `dataset_kind` synthetic and this `dataset_id` unless a new bundle revision replaces it.

Nodus: still PENDING. Package `nodus-compute` 1.0.27 in `.venv-tools`; CLI banner `nodus 0.1.45`. Not logged in. No org, credit, or job.

Git: `feature/model` HEAD `ea04698ad9d8911cf4bdfb267ece1870e4bf0898` (`theravij <2501640100693@psit.ac.in>`). Phase 1 files are uncommitted. Remote `https://github.com/panda0519/alter-ego`. Push was not attempted.

Next: stop before the IDW baseline. Nodus login remains a separate operator step.
