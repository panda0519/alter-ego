# B Phase 2 self-check

Date: 24 October 2026. Branch `feature/model`. Parent `37eedee9d5c7eccf6c86d6eccf09fd4623030281`. Interpreter `.venv/bin/python`, CPython 3.11.17, torch 2.8.0+cu128. IDW ran on CPU. Bundle `data/processed/active`, dataset `05902f5167e6a8aefa02386b6437bfa984a2ec3b67e3fffee7c69d7b145c8351`, kind `synthetic`. Run `b05-idw-syn40-seed42`. Nodus login remains PENDING. No graph or network training was started.

| Check | Command or action | Expected | Observed | Result |
|---|---|---|---|---|
| Baseline geometry | `.venv/bin/python -m pytest tests/test_baseline.py -q` | Power-2 IDW from previous-day visible donors only; missing if none; finite zero-distance mean; cap of 6 | Included in the full suite below. Equatorial distances use radius 6,371,000 m. Self depth 999 and same-day donor 1000 are ignored. No visible donor is NaN, not 0 and not the hidden well's own depth. Duplicate coordinates average the selected zero-distance donors. Eight donors at equal value keep the six nearest | PASS |
| Evaluation masks | Score the active bundle once | Finite errors on permitted labels, or an explicit unavailable state | Validation train_masked MAE 1.0872565960824558 m on 959 pairs. Holdout test MAE 1.5091486021717957 m, RMSE 2.038250204687411 m, 1319 pairs, 8 wells. 1319 is greater than 8. These are synthetic reconstruction errors, not field accuracy | PASS |
| Export command | `.venv/bin/python -m ml.cli baseline --config ml/configs/prototype.yaml --bundle data/processed/active --run-id b05-idw-syn40-seed42 --output artifacts/exports/b05-idw-syn40-seed42` | Four files, schema 1.0.0, one new folder | Exit 0. `dataset_kind` synthetic, `artifact_kind` model_output, `default_method` idw, `as_of_date` 2024-12-31, generated `2026-10-24T16:43:49Z` | PASS |
| Reference checker | `.venv/bin/python scripts/validate_exports.py artifacts/exports/b05-idw-syn40-seed42` | Schema and semantic PASS | Exit 0. `PASS: schemas, metadata, dates, series, summaries and metric status consistent.` The checker states it does not certify training, leakage, physics, or accuracy | PASS |
| No overwrite | Repeat the same baseline command | Existing folder stays untouched | Exit 1. `FileExistsError: refusing to overwrite existing run folder artifacts/exports/b05-idw-syn40-seed42` | PASS |
| Negative exports | `tests/test_exports.py` mutations against the unchanged checker | Reject bad timestamp, meta, duplicate ids, duplicate dates, series length, non-finite JSON, summary priority, agent mismatch, and a fixture marked completed | Included in the 34 passes. The non-finite case writes a JSON `NaN` latitude and the checker rejects it | PASS |
| Common mask | Completed methods in the real metrics file | `test_pairs >= test_wells`; completed methods share pair and well counts | IDW is the only completed method: 1319 pairs and 8 wells. `gcn_lstm` and `gcn_lstm_physics` are `not_run` with null errors and zero counts, so they are outside the comparison | PASS |
| Honest labels | Read the four JSON files | Neural null / `not_run`; agent has no withheld series | Both neural prediction series are entirely null. `observations_m` is present for dashboard reveal and absent from `agent_context.json`. `checkpoint_sha256` null. `nodus_job_ids` []. `selected_positive_lambda` null. Device `cpu`. `code_revision` `37eedee9d5c7eccf6c86d6eccf09fd4623030281+dirty` | PASS |
| Chart versus metrics | Compare exported dates with metric counts | Last 60 test dates on the chart; metrics cover the full partitions | Chart dates 2024-11-02 through 2024-12-31, 60 days, 40 wells, 0 IDW nulls in that window. 1319 test pairs are not 60 chart rows | PASS |
| Pytest | `.venv/bin/python -m pytest tests -q --tb=line` | Phase 2 tests plus the earlier data, split, and format tests | `34 passed in 17.44s` | PASS |
| pip check | `.venv/bin/python -m pip check` | No broken requirements | `No broken requirements found.` | PASS |
| Fixture validator | `.venv/bin/python scripts/validate_exports.py contracts/fixtures` | Unchanged fixture batch still passes | Exit 0, same PASS line as above | PASS |
| Config bytes | `sha256sum ml/configs/prototype.yaml` | Phase 0 hash unchanged | `859ac9e4014c4972132233aed5ad1fec1be1ad4cbebeaa7c0ebbac3e32991e32` | PASS |
| Nodus account | Not run | Stays pending until the operator logs in | No login, org, credit, or job in this phase | PENDING |
| Handoff commit | Git commit of this phase on `feature/model` | A real SHA, no push | `f102d3a590dadf5cb052ea9c92effcf3adffafe6`. The JSON `code_revision` stays `37eedee9d5c7eccf6c86d6eccf09fd4623030281+dirty` and was not rewritten. Not pushed | PASS |

File SHA-256:

- `predictions.json` `5a831861c61374ed6db8411426f55169f197c42a074fa454096fa06e8b509504`
- `metrics.json` `aa744a24e80ed92d1d578c58e445c5d118b4ee31c3c5211b262f19874984bb01`
- `run_info.json` `59911d8a96adcab7ce1b813f408fbef11b31230e5ff762ec729aca2a270aa410`
- `agent_context.json` `657f11ca4103794080a00c8f78e516349a42921d20d8bfb6bb65b26a4086fed3`

Public distribution: the four JSON files contain labelled synthetic depths and coordinates. They do not contain NASA POWER grids or the private `bundle.npz`. They are suitable to commit for A's review. They are not field measurements and not a claim of operational accuracy.

Displayed wells are the frozen cohort of 40. Evaluated test wells are the 8 holdout wells. Those sets are not the same. A publishes `frontend/public/data/` only after A's own validation. A rejected batch needs a new run folder.
