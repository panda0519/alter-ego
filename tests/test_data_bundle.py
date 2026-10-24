"""Invariants for cleaning, weather, synthetic identity and the shared fixtures."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.data.cleaning import clean_observations
from ml.data.sources import calendar, load_config, read_real_folder
from ml.data.synthetic import generate_observations, place_wells
from ml.data.weather import hargreaves_et0_mm, parse_power_payload

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "ml" / "configs" / "prototype.yaml"
FIXTURE_HASHES = {
    "contracts/fixtures/agent_context.json": "c491324f2afd4d1e11588c524e38d910d8b09b2175bc4f3772a6812f8108bc66",
    "contracts/fixtures/metrics.json": "58dfd048747aa29b952eec43661a4680fccec902cb3254157dd1d5223da93a66",
    "contracts/fixtures/predictions.json": "769e34084f8013e1b2dcb595ac7567b13a4d4db05610ff0d57afa9e433d1cdb0",
    "contracts/fixtures/run_info.json": "1fb218412e0b3917ebb4924421181c12354df772a7ea8b9ca2f4ae81f1f5500d",
    "ml/configs/prototype.yaml": "859ac9e4014c4972132233aed5ad1fec1be1ad4cbebeaa7c0ebbac3e32991e32",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_source_fixtures_and_config_stay_byte_identical():
    for relative, expected in FIXTURE_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_prototype_calendar_is_731_days():
    dates = calendar(load_config(CONFIG))
    assert dates[0] == pd.Timestamp("2023-01-01")
    assert dates[-1] == pd.Timestamp("2024-12-31")
    assert len(dates) == 731


def test_daily_median_keeps_gaps_and_does_not_interpolate():
    dates = pd.date_range("2023-01-01", "2023-01-05", freq="D")
    frame = pd.DataFrame(
        [
            ["W1", 23.5, 77.4, "2023-01-01T00:30:00+05:30", 10.0, "valid"],
            ["W1", 23.5, 77.4, "2023-01-01T18:00:00+05:30", 12.0, "valid"],
            ["W1", 23.5, 77.4, "2023-01-01T18:00:00+05:30", 12.0, "valid"],
            ["W1", 23.5, 77.4, "2023-01-02T01:00:00+05:30", 99.0, "suspect"],
            ["W1", 23.5, 77.4, "2023-01-02T09:00:00+05:30", 9.0, "valid"],
            ["W1", 23.5, 77.4, "2023-01-04T00:00:00+05:30", 11.0, "valid"],
        ],
        columns=["station_id", "latitude", "longitude", "observed_at", "depth_m", "validity"],
    )
    cleaned = clean_observations(frame, dates, None)
    assert cleaned.report["exact_duplicate_rows_removed"] == 1
    assert cleaned.depth_m[:, 0].tolist() == pytest.approx([11.0, 9.0, np.nan, 11.0, np.nan], nan_ok=True)
    assert cleaned.depth_valid[:, 0].tolist() == [True, True, False, True, False]
    assert cleaned.report["target_interpolation"] is False


def test_borehole_depth_is_rejected_and_real_file_is_not_modified(tmp_path: Path):
    folder = tmp_path / "raw"
    folder.mkdir()
    table = folder / "observations.csv"
    table.write_text("station_id,latitude,longitude,observed_at,borehole_depth_m\nW1,23.5,77.4,2023-01-01,40\n", encoding="utf-8")
    before = table.read_bytes()
    with pytest.raises(ValueError, match="borehole"):
        read_real_folder(folder)
    assert table.read_bytes() == before


def test_both_depth_columns_keep_the_water_level(tmp_path: Path):
    folder = tmp_path / "raw"
    folder.mkdir()
    (folder / "observations.csv").write_text(
        "station_id,latitude,longitude,observed_at,depth_m,borehole_depth_m\n"
        "W1,23.5,77.4,2023-01-01,8.5,40\n",
        encoding="utf-8",
    )
    frame, manifest = read_real_folder(folder)
    assert "depth_m" in frame.columns
    assert manifest["borehole_columns_present"] == ["borehole_depth_m"]
    cleaned = clean_observations(frame, pd.date_range("2023-01-01", "2023-01-01"), "UTC")
    assert cleaned.depth_m[0, 0] == pytest.approx(8.5)


def test_hargreaves_converts_ra_from_megajoules_to_millimetres():
    latitude = np.array([23.5])
    doy = np.array([172])
    tmax = np.array([40.0])
    tmin = np.array([25.0])
    phi = math.radians(23.5)
    dr = 1 + 0.033 * math.cos(2 * math.pi * 172 / 365)
    delta = 0.409 * math.sin(2 * math.pi * 172 / 365 - 1.39)
    sunset = math.acos(max(-1, min(1, -math.tan(phi) * math.tan(delta))))
    ra_mj = (24 * 60 / math.pi) * 0.0820 * dr * (
        sunset * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(sunset)
    )
    expected = 0.0023 * ((40 + 25) / 2 + 17.8) * math.sqrt(15) * (ra_mj * 0.408)
    actual = hargreaves_et0_mm(latitude, doy[:, None], tmax[:, None], tmin[:, None])
    assert actual[0, 0] == pytest.approx(expected, rel=1e-12)
    assert 3.0 < actual[0, 0] < 12.0


def test_power_fill_and_missing_days_stay_missing():
    dates = pd.date_range("2023-01-01", "2023-01-03", freq="D")
    payload = {
        "header": {"fill_value": -999.0, "time_standard": "LST", "api": {"version": "test"}, "title": "test"},
        "parameters": {
            "PRECTOTCORR": {"units": "mm/day"},
            "T2M_MAX": {"units": "C"},
            "T2M_MIN": {"units": "C"},
        },
        "geometry": {"coordinates": [77.1875, 23.75, 100.0]},
        "properties": {
            "parameter": {
                "PRECTOTCORR": {"20230101": 1.5, "20230102": -999.0},
                "T2M_MAX": {"20230101": 30.0, "20230102": 31.0, "20230103": 29.0},
                "T2M_MIN": {"20230101": 15.0, "20230102": 16.0, "20230103": 14.0},
            }
        },
    }
    parsed = parse_power_payload(payload, dates)
    assert parsed["precip_mm"].tolist() == pytest.approx([1.5, np.nan, np.nan], nan_ok=True)
    assert parsed["tmax_c"][2] == pytest.approx(29.0)
    assert parsed["missing_days"] == 2


def test_synthetic_repeat_is_identical_and_not_the_storage_equation():
    dates = pd.date_range("2023-01-01", periods=220, freq="D")
    stations = place_wells(40, np.random.default_rng(42))
    precip = np.tile(np.linspace(0, 20, 220)[:, None], (1, 40))
    first = generate_observations(stations, dates, precip, np.random.default_rng(42), 132, 0.70)
    second = generate_observations(stations, dates, precip, np.random.default_rng(42), 132, 0.70)
    pd.testing.assert_frame_equal(first, second)
    cleaned = clean_observations(first, dates, "UTC")
    assert cleaned.depth_m.shape == (220, 40)
    assert cleaned.depth_valid.mean() < 1
    sy, alpha, beta = 0.10, 0.15, 0.10
    et0_m = np.full_like(cleaned.depth_m, 0.004)
    precip_m = precip / 1000.0
    delta = cleaned.depth_m[1:] - cleaned.depth_m[:-1]
    residual = sy * delta - beta * et0_m[1:] + alpha * precip_m[1:]
    usable = cleaned.depth_valid[1:] & cleaned.depth_valid[:-1]
    assert np.nanstd(residual[usable]) > 1e-4
    observed = delta[usable]
    driver = precip_m[1:][usable]
    slope = np.corrcoef(driver, observed)[0, 1] ** 2
    assert slope < 0.5
