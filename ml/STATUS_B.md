# Person B status

Phase: B05 IDW baseline and the first four-file handoff are complete. Graph construction and network training have not started.

Dataset: `data/processed/active` stays private and gitignored. `dataset_id` `05902f5167e6a8aefa02386b6437bfa984a2ec3b67e3fffee7c69d7b145c8351`. `dataset_kind` synthetic. 40 wells, 731 days, 2023-01-01 through 2024-12-31, metres below ground. Roles 22 visible / 10 train_masked / 8 holdout, seed 42. Date cuts 438 / 109 / 184. This is not field accuracy. Real India-WRIS and CKAN access from Phase 1 is unchanged: no local groundwater CSV, telemetry CSV not downloaded.

Export: `artifacts/exports/b05-idw-syn40-seed42`. Schema 1.0.0. `artifact_kind` model_output. `default_method` idw because `gcn_lstm` and `gcn_lstm_physics` are `not_run` with null predictions, not because IDW won a comparison. Generated `2026-10-24T16:43:49Z`. `as_of_date` 2024-12-31. Chart 2024-11-02 through 2024-12-31 (60 days, all 40 cohort wells). IDW validation MAE 1.0872565960824558 m on 959 train_masked pairs. Holdout test MAE 1.5091486021717957 m, RMSE 2.038250204687411 m, 1319 pairs, 8 wells. `code_revision` inside the JSON is `37eedee9d5c7eccf6c86d6eccf09fd4623030281+dirty`. Python 3.11.17, torch 2.8.0+cu128, device cpu. Checkpoint null. `nodus_job_ids` empty. Physics was not run.

Displayed wells are the 40-well cohort. Scored test wells are the 8 holdout wells. Metric pair counts are the full partitions, not the 60 chart rows. `agent_context.json` is the IDW summary only and has no `observations_m`.

Checks: `ml/B_PHASE_2_SELF_CHECK.md`. `.venv/bin/python -m pytest tests -q --tb=line` : 34 passed in 17.44s. pip check: `No broken requirements found.` `scripts/validate_exports.py` passed on the export and on `contracts/fixtures`. A second baseline command refused to overwrite the folder. `prototype.yaml` sha256 remains `859ac9e4014c4972132233aed5ad1fec1be1ad4cbebeaa7c0ebbac3e32991e32`.

Request for A: validate `artifacts/exports/b05-idw-syn40-seed42` before any copy into `frontend/public/data/`. No schema change. Keep `dataset_kind` synthetic and this `dataset_id`. Do not publish `data/processed/active`. If this batch is rejected, the repair is a new run folder. The jsonschema format extra from Phase 0 is still waiting on your review.

Nodus: still PENDING. Not logged in. No org, credit, or job. No spend.

Git: `feature/model`. Phase 2 handoff commit SHA is filled below after `git commit`. Parent `37eedee9d5c7eccf6c86d6eccf09fd4623030281`. Remote `https://github.com/panda0519/alter-ego`. Push was not attempted.

Next: stop before the graph and GCN. Nodus login remains a separate operator step.
