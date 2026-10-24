# Person B status

Phase: B10–B11 storage regulariser and the two positive-lambda trains are complete locally. Nodus did not run. Final comparison and selection have not started.

Dataset: private `data/processed/active`, `dataset_id` `05902f5167e6a8aefa02386b6437bfa984a2ec3b67e3fffee7c69d7b145c8351`, kind synthetic, seed 42. Unchanged split. This is not field accuracy.

Physics: Sy 0.10, alpha 0.15, beta 0.10, no lateral flow. Weather is metres per day. On the active bundle, 32 permitted wells had at least 30 training pairs. The unclipped median was `-0.0002466964234525377` m/day, so frozen `q_m_per_day` is 0.0. Seven-day training-change scale is `0.1533439339108233` m, above the 0.05 m floor. Holdout wells were not used for q or the scale.

Local runs, all on `cuda:NVIDIA GeForce RTX 5050 Laptop GPU`, Python 3.11.17, torch 2.8.0+cu128:

| Run | Directory | Epochs | Best epoch | Best validation MAE | Checkpoint lambda | sha256 |
|---|---|---|---|---|---|---|
| lambda 0 | `runs/lambda0` | 11 | 3 | 0.8598469860694834 m | 0 | `721a5416ed797f10b87ab5d3f439d31107b39681dcd7b480305a994a65916c6a` |
| lambda 0.1 | `runs/lambda01` | 11 | 3 | 0.8598469860694834 m | 0 | `9d25379341630a1cf554918b1b7f14df3d9acacef56ba3b479b631591fcd9f16` |
| lambda 1 | `runs/lambda1` | 11 | 3 | 0.8598469860694834 m | 0 | `03d35a4d54f912bf42448826e671ace47b7b670d31a6411dcb8b8c30ed90f742` |

Epochs 1–5 used lambda 0. Epochs 6–10 ramped, and epoch 11 held the target. Those later epochs had higher validation MAE, so the kept weights match the lambda-0 checkpoint exactly. Positive lambda was applied and logged. It was not selected, and it is not an accuracy improvement. No holdout score was computed for these two runs, and no new export was written.

Latest export remains `artifacts/exports/b09-gcn-lstm-lambda0-syn40-seed42`. `gcn_lstm_physics` there is still `not_run`. `b05-idw-syn40-seed42` was not edited.

Checks: `ml/B_PHASE_4_SELF_CHECK.md`. `.venv/bin/python -m pytest tests -q --tb=line` : 54 passed in 26.85s. pip check: `No broken requirements found.` Fixture and b09 validators passed. A repeat lambda-0.1 command refused to overwrite `runs/lambda01/checkpoint.pt`. `prototype.yaml` sha256 remains `859ac9e4014c4972132233aed5ad1fec1be1ad4cbebeaa7c0ebbac3e32991e32`.

Nodus: PENDING. `.venv-tools/bin/nodus` is `nodus 0.1.45`. `whoami`, `get jobs`, and `explain job` all exit 1 with `not logged in`. No org, credit, estimate, or job id. The unsent request is in `ml/B_PHASE_4_NODUS.md`. No spend.

Request for A: do not treat `runs/lambda01` or `runs/lambda1` as a selected physics model. Their kept weights are the lambda-0 warmup. The b09 folder is still the latest schema batch. No schema change.

Git: `feature/model`. Phase 4 handoff commit SHA is filled below after `git commit`. Parent `473bd2b4ba3c791028c805ea743e23d9a6281b4f`. Remote `https://github.com/panda0519/alter-ego`. Push was not attempted.

Next: stop before final evaluation and selection. Nodus login remains a separate operator step.
