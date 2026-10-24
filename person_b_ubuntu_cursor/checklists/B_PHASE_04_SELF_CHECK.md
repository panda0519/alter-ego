# B Phase4 self-check — Ubuntu + Cursor

Filled 24 October 2026 from this checkout on `feature/model`. Parent `473bd2b4ba3c791028c805ea743e23d9a6281b4f`. Interpreter `.venv/bin/python`, CPython 3.11.17, torch 2.8.0+cu128. Dataset `05902f5167e6a8aefa02386b6437bfa984a2ec3b67e3fffee7c69d7b145c8351`, kind synthetic. The guide copy is the same table.

| Check | Command/action | Expected | Observed / evidence | Status |
|---|---|---|---|---|
| Physics | Test exact balance, sign, units, masks and gradients | Correct seven-day regulariser and finite gradients | `tests/test_physics.py` inside `54 passed in 26.85s`. Flat zero forcing residual is 0. Recharge decreases depth. Depletion increases depth. Wrong rainfall sign is nonzero. Non-flat exact balance residual is 0. 5 mm/day is used as 0.005 m/day. Missing weather is masked. Gradient is finite and nonzero | PASS |
| Calibration | Mutate heldout/test values and compare q/scale | Training-only frozen calibration/normalisation | Mutation test leaves q and the seven-day scale unchanged. Active bundle: 32 eligible wells, unclipped median `-0.0002466964234525377` m/day, clipped q `0.0`, scale `0.1533439339108233` m. Floor 0.05 m was not needed for that scale. Sy 0.10, alpha 0.15, beta 0.10 | PASS |
| Comparative runs | Inspect actual same-split/seed lambda0/0.1/1 logs | Warmup/ramp and genuine checkpoints/statuses | GPU RTX 5050. Lambda 0.1 in `runs/lambda01` and lambda 1 in `runs/lambda1`: 11 epochs, best epoch 3, validation MAE `0.8598469860694834` m. Epochs 1–5 lambda 0. Epoch 6 is 0.02 or 0.2. Epoch 10 reaches the target. Kept weights equal the lambda-0 checkpoint. Later validation MAE was worse, so positive lambda was not selected. No new export and no holdout score | PASS |
| Nodus budget | Inspect actual estimate, review, credits and caps | Bounded approved request; no purchases | `nodus whoami` exit 1, `not logged in`. No `~/.nodus`, no `NODUS_` variables, no credit balance, no estimate. Intended caps are recorded in `ml/B_PHASE_4_NODUS.md` and were not submitted | PENDING |
| Nodus execution | Retrieve actual job/checkpoint/log/config/code SHA | Meaningful training with actual image/environment evidence | Not run. `nodus explain job` also exit 1, so the server schema was not read. `nodus run --help` was read locally. No job id | PENDING |
| Blocked or failed work | Review missing account/capacity and failed runs | Explicit PENDING/failed status; no invented IDs | Login is the blocker. Local physics and both positive-lambda trains finished. No job id was invented. MCP `user-nodus` was in error and was not authenticated from here | PASS |

Detail record: `ml/B_PHASE_4_SELF_CHECK.md`. Handoff commit SHA is in `ml/STATUS_B.md` after the commit.
