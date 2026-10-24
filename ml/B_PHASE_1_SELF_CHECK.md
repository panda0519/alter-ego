# B Phase 1 self-check

Date: 24 October 2026. Branch `feature/model`. HEAD `ea04698ad9d8911cf4bdfb267ece1870e4bf0898`. Phase 1 code is uncommitted. Interpreter: `.venv/bin/python`, CPython 3.11.17. Active bundle: `data/processed/active`, dataset `05902f5167e6a8aefa02386b6437bfa984a2ec3b67e3fffee7c69d7b145c8351`, kind `synthetic`. Nodus login remains PENDING.

| Check | Command or action | Expected | Observed | Result |
|---|---|---|---|---|
| Local raw file | Look for `data/raw` and a supplied CSV | Do not invent a downloaded subset | `data/raw` is absent. No observations file was provided | PASS |
| India-WRIS page | `curl` the timeseries URL, 20 s limit | Record the response, not a guessed table | HTTP 200, 8834 bytes of HTML. No series, units, or coordinates | PASS |
| Telemetry listing metadata | CKAN `resource_show` for `f78f7b15-f325-4c39-a291-f44ad4e95334` | Record size and rights actually returned | CSV name Groundwater Level Collected Telemetric, 1,639,100,785 bytes. No column list and no licence in that payload. `package_show` HTTP 403. CSV not downloaded | PASS |
| Development decision | Choose real or synthetic from the inspection | Synthetic if no approved daily subset exists | Synthetic bundle plus cached POWER weather. Real reader exists for a later approved folder | PASS |
| Prepare command | `.venv/bin/python -m ml.cli prepare --config ml/configs/prototype.yaml --kind synthetic --output data/processed/active` | 40 wells, 731 days, labelled synthetic | Exit 0. `dataset_id` `05902f5167e6a8aefa02386b6437bfa984a2ec3b67e3fffee7c69d7b145c8351`. Roles 22 / 10 / 8. Depths 8.610–27.275 m | PASS |
| Repeat prepare | Same command a second time | Same identity, no second dataset | Same `dataset_id` and `dataset_kind` `synthetic` | PASS |
| POWER cache | Inspect `data/cache/power` | Real NASA files, shared cells | Four JSON files written at 22:02 local by the first prepare. API v2.10.1. Units mm/day and C. Four cells, 14 + 1 + 22 + 3 wells. 0 missing parameter-days. Weather-valid fraction 1. Repeat prepare read the cache | PASS |
| Shapes and windows | Load `bundle.npz` | `(731, 40)` depths and features `(731, 40, 8)`; windows inside partitions | Train windows 409 (29–437), validation 80 (467–546), test 155 (576–730). Partitions 438 / 109 / 184 days | PASS |
| Holdout inputs | Read holdout feature columns from the bundle | Lag and availability stay 0 | Holdout lag max 0 and availability max 0 | PASS |
| Pytest | `.venv/bin/python -m pytest tests -q --tb=line` | Format regression plus data and split invariants | `15 passed in 1.94s` | PASS |
| Held-out leakage | `tests/test_splits_scalers.py` | Extreme holdout depths leave scalers and other wells' features unchanged | Included in the 15 passes. A train-masked training change does move the depth scaler. A test-period visible change does not | PASS |
| No target interpolation | Cleaning test with a missing day and a same-day pair | Median on 1 Jan, gap on 3 Jan stays missing | Included in the 15 passes. Active cleaning report: `target_interpolation` false, 0 negatives | PASS |
| Not the storage equation | Synthetic test residual and same-day rain correlation | Residual is not numerical zero and depth is not a linear copy of same-day rain | Included in the 15 passes | PASS |
| ET0 Ra conversion | Independent FAO calculation for lat 23.5, day 172 | Implementation matches `Ra_MJ * 0.408` | Included in the 15 passes | PASS |
| Fixture and config bytes | `sha256sum` of the four fixtures and `prototype.yaml` | Phase 0 hashes unchanged | All five hashes match `ml/B_PHASE_0` records and `CONTENTS_SHA256.txt` for the config | PASS |
| Export validator | `.venv/bin/python scripts/validate_exports.py contracts/fixtures` | Fixture batch still passes | Exit 0, `PASS: schemas, metadata, dates, series, summaries and metric status consistent.` | PASS |
| pip check | `.venv/bin/python -m pip check` | No broken requirements | `No broken requirements found.` | PASS |
| q calibration | Look at `scalers.json` | Absent until the physics phase | `q_m_per_day` null, status `not_estimated_in_this_phase` | PASS |
| Nodus account | Not run | Stays pending until the operator logs in | No login, org, credit, or job observed in this phase | PENDING |
| Phase 1 commit | Git HEAD after the data work | A real SHA only if a commit exists | HEAD is still `ea04698ad9d8911cf4bdfb267ece1870e4bf0898`. Phase 1 files are uncommitted | PENDING |

The guide checklist is `/home/ghost/hackathon/Alter_Ego_Final_Two_Person_Guide (1)/Alter_Ego_Final_Two_Person_Guide/person_b_ubuntu_cursor/checklists/B_PHASE_01_SELF_CHECK.md`. It was filled from these results. This file is the detailed record inside the checkout.
