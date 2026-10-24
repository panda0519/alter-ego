# Person B status

Phase: B12–B13 validation selection, one holdout score, and the final local export are complete. Nodus did not run. No joint rehearsal was held.

Dataset: private `data/processed/active`, `dataset_id` `05902f5167e6a8aefa02386b6437bfa984a2ec3b67e3fffee7c69d7b145c8351`, kind synthetic, seed 42. Unchanged split. This is not field accuracy.

## Handoff for A

Run ID: `b12-final-syn40-seed42`

Candidate path: `artifacts/exports/b12-final-syn40-seed42`

Dataset ID and real/synthetic: `05902f5167e6a8aefa02386b6437bfa984a2ec3b67e3fffee7c69d7b145c8351`, synthetic

Code revision inside the JSON: `57dc6f9a7feec7d9b536da5d2f7929067ba98512+dirty`. Do not rewrite it. Implementation commit: `d622419a07177ad35bc49c5e2a5f733a20751aae`.

Files:

- `predictions.json` sha256 `98895a2fc6621d4796d8374be53b44eaddfd185ab6cff601d1a7141cf2261b0b`
- `metrics.json` sha256 `20d128942244bfef7501d1c12f833a0711cd6ad68a8813fb8ead86f7413ca4d2`
- `run_info.json` sha256 `680a69619e2a80dfc0f187f9ee5402780622718c368873b7533e75cb30ef9c27`
- `agent_context.json` sha256 `4cb88404f192c768f76937a2e2c708433f825835785fde057ee4730a95672c79`

Generated `2026-10-24T17:51:02Z`. `as_of_date` `2024-12-31`. `artifact_kind` `model_output`. Depth unit `m_below_ground`. `nodus_job_ids` is empty. `checkpoint_sha256` is the lambda-0 file actually used for `gcn_lstm`: `721a5416ed797f10b87ab5d3f439d31107b39681dcd7b480305a994a65916c6a`.

Validator: `.venv/bin/python scripts/validate_exports.py artifacts/exports/b12-final-syn40-seed42` exited 0. The same checker passed `contracts/fixtures`, `artifacts/exports/b05-idw-syn40-seed42` and `artifacts/exports/b09-gcn-lstm-lambda0-syn40-seed42`. JSON validity does not prove scientific correctness. A publishes `frontend/public/data` after A's own validation. B did not copy the batch there.

Default method and validation selection: `gcn_lstm`. Common validation mask, 713 pairs and 10 train-masked wells: IDW MAE `1.1042053369012759` m, GCN-LSTM MAE `0.8598469860694834` m. That choice was locked before the holdout score. A tie would have stayed with IDW.

Held-out test pairs/wells: 1109 pairs, 8 contributing wells, shared by the two completed methods. IDW MAE `1.4958895956006706` m, RMSE `2.034039534948381` m. GCN-LSTM MAE `1.626403108513909` m, RMSE `2.0547485083440558` m. Holdout valid labels are 1319, so coverage is 1109/1319. The chart is 60 dates, `2024-11-02` through `2024-12-31`, and 40 displayed wells. Those chart rows are not the metric pair count, and the 8 scored wells are not a bound for the full cohort. The holdout GCN error is higher than IDW. It was not used to change the default.

Known limitations:

- Both positive-lambda runs selected epoch 3 during lambda-zero warmup. Their `model_state` tensors equal `runs/lambda0`. File hashes differ because the payloads differ. Lambda 0.1 checkpoint `9d25379341630a1cf554918b1b7f14df3d9acacef56ba3b479b631591fcd9f16`. Lambda 1 checkpoint `03d35a4d54f912bf42448826e671ace47b7b670d31a6411dcb8b8c30ed90f742`. Epoch 11 validation MAE was `1.0392382262757345` m at lambda 0.1 and `2.1220102426551093` m at lambda 1, both worse than epoch 3. Positive regularisation ran and was not selected. These weights are not a physics-trained gain.
- Schema gap, left unchanged: `contracts/metrics.schema.json` allows method status `not_run`, `completed`, or `failed` only, and method objects have `additionalProperties` false. There is no status for a finished positive-lambda run whose selected checkpoint is still the warmup. `gcn_lstm_physics` is `not_run` with null metrics. `selected_positive_lambda` is null. The notes, caption, physics assumptions and agent limitations say why. Please do not relabel that method completed. A new status would be a contract change for A to propose.
- Frozen q is `0.0` m/day after clipping the unclipped median `-0.0002466964234525377` m/day. Eligible permitted wells: 32. Residual scale `0.1533439339108233` m. Sy 0.10, alpha 0.15, beta 0.10. No lateral flow. These are assumed constants.
- Same-device reload difference was `0.0` m. A CPU reload of the CUDA grid differed by `0.0009213380646091451` m, above the `0.0001` m tolerance, and was refused. Bitwise equality across devices is not claimed.
- Synthetic data stays labelled. It does not establish field accuracy. No live monitoring, forecast, or official threshold is claimed.

Nodus evidence: none. `.venv-tools/bin/nodus whoami` on 24 October 2026 exited 1 with `not logged in`. Version banner `nodus 0.1.45`. No estimate, credit balance, or job id. The unsent local caps remain in `ml/B_PHASE_4_NODUS.md`. No cloud command was run.

## What the model does

The graph is dense. Each well uses up to 6 other wells, haversine distance, Gaussian weights from the median positive neighbour distance, a symmetric union, self-loops, and symmetric degree normalisation. One linear graph convolution maps the 8 features to 32 and applies ReLU. Dropout 0.1 is outside the recurrent layer. One unidirectional LSTM, hidden size 32, reads each well's 30-day sequence after the station axis is folded into the batch and then restored. The head writes one depth per day and well. Output shape is batch by 30 by stations.

The physics term is an assumed local storage penalty, not a flow model. With depth positive downward, `Sy * (d[t] - d[t-1])` is compared with `beta * ET0[t] + q - alpha * P[t]`. The exported network never applied a positive lambda, because validation kept the warmup checkpoint.

## Checks

`ml/B_PHASE_5_SELF_CHECK.md`. `.venv/bin/python -m pytest tests -q --tb=line`: 61 passed in 27.06s. pip check: `No broken requirements found.` Repeat evaluate and repeat export both exited 1 by refusing an existing folder. `b05-idw-syn40-seed42` and `b09-gcn-lstm-lambda0-syn40-seed42` were not edited.

Git: `feature/model` handoff `d622419a07177ad35bc49c5e2a5f733a20751aae`. Parent `57dc6f9a7feec7d9b536da5d2f7929067ba98512`. Remote `https://github.com/panda0519/alter-ego`. Push was not attempted.

Next: stop. Rehearsals are PENDING until they actually happen. Nodus login remains an operator step. A alone publishes and validates before acceptance.
