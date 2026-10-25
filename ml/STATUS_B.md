# Person B status

## Completed positive-lambda export - 2026-10-25

`runs/lambda01` selected epoch 13 at lambda 0.1. `runs/lambda1` selected epoch 6 at lambda 0.2 during the ramp. Neither matches `runs/lambda0` epoch 3. Evaluation exported physics as completed. Run id `b13-physics-syn40-seed42`. Commands, from the repository root with `.venv\Scripts\python.exe`:

- `python -m ml.cli prepare --config ml/configs/prototype.yaml --kind synthetic --output data/processed/active --weather-cache data/cache/power`
- `python -m ml.cli train` for lambda targets 0, 0.1, and 1.0 into `runs/lambda0`, `runs/lambda01`, and `runs/lambda1`
- `python -m ml.cli evaluate --runs runs/lambda0 runs/lambda01 runs/lambda1 --output runs/evaluation`
- `python -m ml.cli export --evaluation runs/evaluation --run-id b13-physics-syn40-seed42 --output artifacts/exports/b13-physics-syn40-seed42`

`tests/test_physics.py::test_positive_lambda_selection_ignores_warmup_epochs` and `tests/test_evaluation.py` passed (8 tests). Field accuracy is not claimed.

## Checkpoint selection fix - 2026-10-25

Positive-lambda training now selects a checkpoint only from epochs after `lambda_zero_epochs`, and only once scheduled lambda is greater than 0. A lambda target of 0 may still select any epoch. Warmup epochs remain in `history.jsonl` and do not reset early stopping. `ml/export` and `publish` can emit `gcn_lstm_physics` as completed only for a distinct checkpoint whose lambda is 0.1 or 1.0. A warmup or lambda-0 weight match is refused.

The paragraph below was the blocker before PyTorch was installed. The completed export above replaces it.

Phase: B12–B13 validation selection, one holdout score, and the final local export are complete. Nodus did not run. No joint rehearsal was held.

Dataset: private `data/processed/active`, `dataset_id` `05902f5167e6a8aefa02386b6437bfa984a2ec3b67e3fffee7c69d7b145c8351`, kind synthetic, seed 42. Unchanged split. This is not field accuracy.

## Handoff for A

Branch: `feature/model`. Commit containing this candidate: `89d85dae75267e3c0ba99abf607f42771fa0c371`.

Run ID: `b12-final-syn40-seed42-r2`

Candidate path: `artifacts/exports/b12-final-syn40-seed42-r2`

Dataset ID and real/synthetic: `05902f5167e6a8aefa02386b6437bfa984a2ec3b67e3fffee7c69d7b145c8351`, synthetic

Export provenance: `run_info.code_revision` is `9ea9652f89dd79f60b8ba7c0d7a39bf32704f43b`. That clean commit contains the Phase 5 implementation `d622419a07177ad35bc49c5e2a5f733a20751aae` plus the status-note commit. Between those two commits only `ml/STATUS_B.md`, `ml/B_PHASE_5_SELF_CHECK.md`, and the Phase 5 checklist changed. The exporter read `git status --porcelain` while that tree was clean.

Training provenance, left as stored in each checkpoint payload and `train_manifest.json`:

- `runs/lambda0` produced the weights used for `gcn_lstm`. Payload `code_revision` `27631dc55c4c65d87e394a54ef0aa5879cb69468+dirty`, epoch 3, lambda target 0. The `+dirty` is the historical working tree at training time. It is not replaced.
- `runs/lambda01` and `runs/lambda1` payloads say `473bd2b4ba3c791028c805ea743e23d9a6281b4f+dirty`, epoch 3, `lambda_at_epoch` 0.0. Those dirty revisions stay in the checkpoint files.

The earlier batch `artifacts/exports/b12-final-syn40-seed42` is preserved. Its `code_revision` remains `57dc6f9a7feec7d9b536da5d2f7929067ba98512+dirty` because that export ran while the Phase 5 implementation was still uncommitted on top of `57dc6f9`. That implementation is now `d622419`. Use `b12-final-syn40-seed42-r2` for the handoff.

Files:

- `predictions.json` sha256 `3a526df6f36bea39e79210ea25def1277fffd124e5af8e0983a06c6ce4681871`
- `metrics.json` sha256 `187889d55c95613d7ef7b8a93b826b7a76ad131f34b8e8b53c71d24543241ec9`
- `run_info.json` sha256 `35be05d273c50bca33d348a27f84d5786be9327dddd52b9b3115da6833e99e4e`
- `agent_context.json` sha256 `7a99db5ff9671f04b83d76e34ef8986e574dfe409717732b8cb811c1fa0109a0`

Generated `2026-10-24T18:03:30Z`. `as_of_date` `2024-12-31`. `artifact_kind` `model_output`. Depth unit `m_below_ground`. `nodus_job_ids` is empty. `checkpoint_sha256` is the lambda-0 file actually used for `gcn_lstm`: `721a5416ed797f10b87ab5d3f439d31107b39681dcd7b480305a994a65916c6a`.

Compared with `b12-final-syn40-seed42`, the only field changes are `meta.run_id`, `meta.generated_at_utc`, and `run_info.code_revision`. Predictions, observations, summaries, metric MAE/RMSE/pairs/wells, evaluation notes, physics assumptions, data sources, and agent limitations are identical. The cause is the new run identity and the clean export revision. No weight, selection, or holdout value changed. The frozen `runs/final_evaluation/evaluation.json` and `predictions.npz` hashes were the same before and after this export. The reload on `cuda:NVIDIA GeForce RTX 5050 Laptop GPU` differed by `0.0` m from that saved grid. The publisher accepted the reload only because it matched the frozen scores within `0.0001` m. It did not retrain, reselect, or adopt a new holdout result.

Validator: `.venv/bin/python scripts/validate_exports.py artifacts/exports/b12-final-syn40-seed42-r2` exited 0. `b12-final-syn40-seed42`, `b05-idw-syn40-seed42`, `b09-gcn-lstm-lambda0-syn40-seed42`, and `contracts/fixtures` were already valid and were not modified. JSON validity does not prove scientific correctness. A publishes `frontend/public/data` after A's own validation. B did not copy the batch there.

Default method and validation selection: `gcn_lstm`. Common validation mask, 713 pairs and 10 train-masked wells: IDW MAE `1.1042053369012759` m, GCN-LSTM MAE `0.8598469860694834` m. That choice was locked before the holdout score. A tie would have stayed with IDW.

Held-out test pairs/wells: 1109 pairs, 8 contributing wells, shared by the two completed methods. IDW MAE `1.4958895956006706` m, RMSE `2.034039534948381` m. GCN-LSTM MAE `1.626403108513909` m, RMSE `2.0547485083440558` m. Holdout valid labels are 1319, so coverage is 1109/1319. The chart is 60 dates, `2024-11-02` through `2024-12-31`, and 40 displayed wells. Those chart rows are not the metric pair count, and the 8 scored wells are not a bound for the full cohort. The holdout GCN error is higher than IDW. It was not used to change the default.

Known limitations:

- Both positive-lambda runs selected epoch 3 during lambda-zero warmup. Their `model_state` tensors equal `runs/lambda0`. File hashes differ because the payloads differ. Lambda 0.1 checkpoint `9d25379341630a1cf554918b1b7f14df3d9acacef56ba3b479b631591fcd9f16`. Lambda 1 checkpoint `03d35a4d54f912bf42448826e671ace47b7b670d31a6411dcb8b8c30ed90f742`. Epoch 11 validation MAE was `1.0392382262757345` m at lambda 0.1 and `2.1220102426551093` m at lambda 1, both worse than epoch 3. Positive regularisation ran and was not selected. These weights are not a physics-trained gain.
- Schema gap, left unchanged: `contracts/metrics.schema.json` allows method status `not_run`, `completed`, or `failed` only, and method objects have `additionalProperties` false. There is no status for a finished positive-lambda run whose selected checkpoint is still the warmup. `gcn_lstm_physics` is `not_run` with null metrics. `selected_positive_lambda` is null. The notes, caption, physics assumptions and agent limitations say why. Please do not relabel that method completed. A new status would be a contract change for A to propose.
- Frozen q is `0.0` m/day after clipping the unclipped median `-0.0002466964234525377` m/day. Eligible permitted wells: 32. Residual scale `0.1533439339108233` m. Sy 0.10, alpha 0.15, beta 0.10. No lateral flow. These are assumed constants.
- Same-device RTX reload difference was `0.0` m for both the original export and `b12-final-syn40-seed42-r2`. A CPU reload of the CUDA grid differed by `0.0009213380646091451` m. That is above the `0.0001` m tolerance, so the publisher refuses a CPU grid. The tolerance was not widened. The RTX series is the reproduced result. A CPU process is outside that tolerance.
- Synthetic data stays labelled. It does not establish field accuracy. No live monitoring, forecast, or official threshold is claimed.

Nodus: PENDING. `.venv-tools/bin/nodus whoami` on 24 October 2026 exited 1 with `not logged in`. Version banner `nodus 0.1.45`. No estimate, credit balance, or job id. The unsent local caps remain in `ml/B_PHASE_4_NODUS.md`. No cloud command was run.

Rehearsals: PENDING. No joint demonstration rehearsal was held. No deck, recording, or receipt exists.

## What the model does

The graph is dense. Each well uses up to 6 other wells, haversine distance, Gaussian weights from the median positive neighbour distance, a symmetric union, self-loops, and symmetric degree normalisation. One linear graph convolution maps the 8 features to 32 and applies ReLU. Dropout 0.1 is outside the recurrent layer. One unidirectional LSTM, hidden size 32, reads each well's 30-day sequence after the station axis is folded into the batch and then restored. The head writes one depth per day and well. Output shape is batch by 30 by stations.

The physics term is an assumed local storage penalty, not a flow model. With depth positive downward, `Sy * (d[t] - d[t-1])` is compared with `beta * ET0[t] + q - alpha * P[t]`. The exported network never applied a positive lambda, because validation kept the warmup checkpoint.

## Checks

`ml/B_PHASE_5_SELF_CHECK.md`. `.venv/bin/python -m pytest tests -q --tb=line`: 61 passed in 27.06s. pip check: `No broken requirements found.` Repeat evaluate and repeat export both exited 1 by refusing an existing folder. `b05-idw-syn40-seed42` and `b09-gcn-lstm-lambda0-syn40-seed42` were not edited.

Git: `feature/model` candidate `89d85dae75267e3c0ba99abf607f42771fa0c371`. Export process revision `9ea9652f89dd79f60b8ba7c0d7a39bf32704f43b`. Remote `https://github.com/panda0519/alter-ego`. Push was not attempted. Tracked files contain no checkpoint, `bundle.npz`, processed bundle, cache, or credential. `frontend/.env.example` has an empty `VITE_AGENT37_URL`. `runs/` and `data/processed/` stay gitignored.

Next: stop. A alone publishes `frontend/public/data` and validates before acceptance. Nodus login and the three rehearsals remain operator steps.
