# Person B status

Phase: B06–B09 graph, windows, GCN-LSTM and lambda-0 training are complete. The physics regulariser has not been started.

Dataset: private `data/processed/active`, `dataset_id` `05902f5167e6a8aefa02386b6437bfa984a2ec3b67e3fffee7c69d7b145c8351`, kind synthetic, seed 42. 40 wells, roles 22 / 10 / 8, date cuts 438 / 109 / 184. Windows 409 / 80 / 155, all inside their partitions. This is not field accuracy.

First handoff kept: `artifacts/exports/b05-idw-syn40-seed42` was not edited. Unrestricted IDW validation MAE remains 1.0872565960824558 m on 959 train-masked pairs.

Lambda 0: local checkpoint `runs/lambda0/checkpoint.pt` (gitignored), sha256 `721a5416ed797f10b87ab5d3f439d31107b39681dcd7b480305a994a65916c6a`. Device actually used: `cuda:NVIDIA GeForce RTX 5050 Laptop GPU`. Python 3.11.17, torch 2.8.0+cu128. 11 epochs, early stop, best epoch 3, validation MAE 0.8598469860694834 m, elapsed 1.113 s. Physics loss was not computed. A one-epoch smoke in `runs/lambda0-smoke` is tagged `development_smoke` and was not exported.

New export: `artifacts/exports/b09-gcn-lstm-lambda0-syn40-seed42`. Schema 1.0.0. Generated `2026-10-24T17:08:20Z`. `as_of_date` 2024-12-31. Chart 2024-11-02 through 2024-12-31, 40 displayed wells. `gcn_lstm` completed at lambda 0. `gcn_lstm_physics` is `not_run` with null predictions. Common validation mask: 713 pairs, IDW MAE 1.1042053369012759 m, GCN-LSTM MAE 0.8598469860694834 m. Common holdout mask: 1109 pairs, 8 wells, IDW MAE 1.4958895956006706 m, GCN-LSTM MAE 1.626403108513909 m. Default method is `gcn_lstm` because its validation MAE is lower. The holdout MAE is higher than IDW and was not used to pick the default or the checkpoint. `code_revision` inside the JSON is `27631dc55c4c65d87e394a54ef0aa5879cb69468+dirty`.

Checks: `ml/B_PHASE_3_SELF_CHECK.md`. `.venv/bin/python -m pytest tests -q --tb=line` : 48 passed in 23.29s. pip check: `No broken requirements found.` `scripts/validate_exports.py` passed on the new export and on `contracts/fixtures`. A repeat train refused to overwrite `runs/lambda0/checkpoint.pt`. `prototype.yaml` sha256 remains `859ac9e4014c4972132233aed5ad1fec1be1ad4cbebeaa7c0ebbac3e32991e32`.

Request for A: validate `artifacts/exports/b09-gcn-lstm-lambda0-syn40-seed42` before any copy into `frontend/public/data/`. No schema change. Keep `dataset_kind` synthetic and this `dataset_id`. The b05 folder is still the IDW-only batch. This default is not the positive-lambda selection. If this batch is rejected, the repair is a new run folder.

Nodus: still PENDING. Not logged in. No org, credit, or job. No spend.

Git: `feature/model`. Phase 3 handoff commit SHA is filled below after `git commit`. Parent `27631dc55c4c65d87e394a54ef0aa5879cb69468`. Remote `https://github.com/panda0519/alter-ego`. Push was not attempted.

Next: stop before the physics regulariser. Nodus login remains a separate operator step.
