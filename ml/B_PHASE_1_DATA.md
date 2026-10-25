# B Phase 1 data decision and bundle

Development bundle: synthetic. No approved groundwater file was in this checkout, and none was downloaded. The private bundle is `data/processed/active`. It is gitignored. It is not a public export and it is not field accuracy.

## Real-data inspection

- `data/raw` was absent. No local CSV was supplied.
- India-WRIS `https://indiawris.gov.in/wris/#/timeseriesdata` returned HTTP 200 and an 8834-byte HTML page. No time series, units, or coordinates were in that response.
- CKAN `resource_show` for `f78f7b15-f325-4c39-a291-f44ad4e95334` succeeded. Name: Groundwater Level Collected Telemetric. Format: CSV. Size: 1,639,100,785 bytes. The metadata names groundwater level and discharge and does not list columns, a validity code, a time step, or a licence. `package_show` for `e068e959-4d85-4287-809d-772bf2b2d83c` returned HTTP 403, so the package licence was not observed.
- The CSV was not downloaded. Borehole depth was not used. Quarterly readings were not expanded into daily labels.

Decision: build the prototype on the synthetic generator and cached NASA POWER weather. A real folder can be prepared later with `--kind real` once an approved file exists. That path does not add a downloader.

## Real folder contract

`--input-folder` must contain `observations.csv` and may contain `timezone.txt` and `rights.txt`. Required columns are `station_id`, `latitude`, `longitude`, `observed_at`, and `depth_m` (metres below ground, the time-varying level). A file that has only `borehole_depth_m` or `well_depth_m` is rejected. Accepted validity tokens are blank, `valid`, `ok`, and `accepted`. Other tokens stay out of the daily median. Same-day accepted readings use the median. Exact duplicate rows are dropped. Dates are the civil date of the timestamp. The config calendar is not filled by interpolation. Days with no accepted reading stay missing.

## Active synthetic bundle

Command:

`.venv/bin/python -m ml.cli prepare --config ml/configs/prototype.yaml --kind synthetic --output data/processed/active`

Repeated once. Both runs reported the same identity.

- `dataset_id`: `05902f5167e6a8aefa02386b6437bfa984a2ec3b67e3fffee7c69d7b145c8351`
- `dataset_kind`: `synthetic`
- Python: `.venv` CPython 3.11.17
- Code revision at prepare time: `ea04698ad9d8911cf4bdfb267ece1870e4bf0898+dirty`
- Seed 42. Stations `SYN001`–`SYN040`. Shape `depth_m` `(731, 40)`.
- Dates 2023-01-01 through 2024-12-31. Unit `m_below_ground`.
- Finite synthetic depths in this bundle: 8.610 m to 27.275 m. No negative depths kept.
- Valid fraction 0.9006. Minimum training coverage 0.8379, so all 40 wells stayed in the cohort. Coverage used only the training dates.
- Missing fraction after the split was frozen: train 0.1006, validation 0.1000, test 0.0963. Test missingness was not used to drop wells.

Partitions, using floor for the first two fractions and the remainder for test:

| Partition | Start | End | Days | Window ends |
|---|---|---|---|---|
| train | 2023-01-01 | 2024-03-13 | 438 | 409 ends, indices 29–437 |
| validation | 2024-03-14 | 2024-06-30 | 109 | 80 ends, indices 467–546 |
| test | 2024-07-01 | 2024-12-31 | 184 | 155 ends, indices 576–730 |

`floor(0.25 * 731)` is 182, which is not the test length. The test length is the remainder, 184. Every stored 30-day window sits inside one partition.

Frozen roles, seed 42, counts 22 / 10 / 8:

- visible: SYN001 SYN002 SYN003 SYN004 SYN007 SYN009 SYN010 SYN012 SYN013 SYN014 SYN015 SYN016 SYN018 SYN020 SYN023 SYN024 SYN027 SYN030 SYN034 SYN035 SYN037 SYN039
- train_masked: SYN011 SYN021 SYN022 SYN025 SYN026 SYN028 SYN029 SYN031 SYN032 SYN036
- holdout: SYN005 SYN006 SYN008 SYN017 SYN019 SYN033 SYN038 SYN040

Holdout and train-masked lags in `features` are 0 with availability 0. Visible lags use the previous day only. Depth scaler: population mean 17.809486191543808 m and standard deviation 3.9222247447329615 m on valid training labels of visible and train-masked wells. Weather scalers use training dates at visible wells. `q` is null and `not_estimated_in_this_phase`.

Coordinates are a fictional cluster around 23.5 N, 77.4 E used only to choose POWER cells. They are not surveyed wells and not a selected monitored region.

## Weather

NASA POWER daily API v2.10.1, community AG, time standard LST, parameters PRECTOTCORR (`mm/day`), T2M_MAX (`C`), T2M_MIN (`C`), 20230101–20241231. Four representative cells, cached under `data/cache/power/`:

| Request cell | Wells | Response elevation m | Missing parameter-days |
|---|---|---|---|
| 23.75 N, 77.1875 E | 14 | recorded in the manifest | 0 |
| 23.25 N, 77.1875 E | 1 | recorded in the manifest | 0 |
| 23.75 N, 77.8125 E | 22 | recorded in the manifest | 0 |
| 23.25 N, 77.8125 E | 3 | recorded in the manifest | 0 |

The first prepare created those four JSON files. A later prepare read the cache and kept the same `dataset_id`. Fill value `-999` is treated as missing. This run had no filled days. Wells in one cell share one precipitation series. That is not a gauge at each well. Hargreaves ET0 uses latitude, day of year, Tmax and Tmin, with Ra converted from MJ/m2/day to mm/day by 0.408. ET0 is a reference estimate. Physics forcing is stored in m/day. The depth generator uses delayed precipitation, seasonality, trends and noise. It does not use ET0 and it is not the storage update `Sy * (d[t] - d[t-1]) = beta * ET0[t] + q - alpha * P[t]`.

## Handoff for A

No contract field changes. UI fixtures and `ml/configs/prototype.yaml` are byte-identical to the Phase 0 hashes. Do not publish this bundle as `frontend/public/data`. The next model handoff is still the four-file schema 1.0.0 batch, and it has not been written. When it exists, `dataset_kind` must stay `synthetic` and `dataset_id` must be this id unless a new immutable bundle replaces it.
