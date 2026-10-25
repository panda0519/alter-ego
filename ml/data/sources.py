"""Prototype config and the approved local real-observation format.

Real preparation reads one folder. It does not call a groundwater download API.
The approved file is observations.csv with these columns:

- station_id
- latitude, longitude: decimal degrees, WGS84
- observed_at: YYYY-MM-DD or ISO-8601
- depth_m: time-varying water level, metres below ground
- validity: optional. Blank, valid, ok, and accepted are kept. Any other token
  is excluded from that day's median and counted in the quality report.

Optional timezone.txt is one IANA name used when observed_at has no offset.
Optional rights.txt is copied into the source manifest. Borehole or well
construction depth is not a water-level series. A file that supplies only
borehole_depth_m or well_depth_m is rejected.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import yaml

ACCEPTED_VALIDITY = {"", "valid", "ok", "accepted"}
OPTIONAL_FILES = {"observations.csv", "timezone.txt", "rights.txt"}
BOREHOLE_COLUMNS = {"borehole_depth_m", "well_depth_m", "borehole_depth", "well_depth"}


def load_config(path: str | Path) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    data = config["data"]
    if data["daily_step"] != 1:
        raise ValueError("daily_step must be 1")
    if data["target_unit"] != "m_below_ground":
        raise ValueError("target_unit must be m_below_ground")
    if tuple(config["features"]["order"]) != (
        "lag_depth_z",
        "lag_available",
        "precipitation_z",
        "et0_z",
        "doy_sin",
        "doy_cos",
        "x_z",
        "y_z",
    ):
        raise ValueError("feature order does not match the frozen prototype")
    if int(config["features"]["count"]) != 8:
        raise ValueError("feature count must be 8")
    if config["data"]["lag_fill"] != "standardised_zero_with_mask":
        raise ValueError("lag_fill must be standardised_zero_with_mask")
    return config


def calendar(config: dict) -> pd.DatetimeIndex:
    start = pd.Timestamp(config["data"]["start_date"])
    end = pd.Timestamp(config["data"]["end_date"])
    dates = pd.date_range(start, end, freq="D")
    if len(dates) < 1:
        raise ValueError("configuration dates are empty")
    return dates


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_real_folder(folder: str | Path) -> tuple[pd.DataFrame, dict]:
    root = Path(folder)
    if not root.is_dir():
        raise FileNotFoundError(f"real input folder does not exist: {root}")
    unexpected = sorted(p.name for p in root.iterdir() if p.name not in OPTIONAL_FILES and not p.name.startswith("."))
    if unexpected:
        raise ValueError(
            "real input folder must contain observations.csv and optional timezone.txt and rights.txt; "
            f"found {unexpected}"
        )
    table_path = root / "observations.csv"
    if not table_path.is_file():
        raise FileNotFoundError(f"missing {table_path}")
    timezone = None
    timezone_path = root / "timezone.txt"
    if timezone_path.is_file():
        timezone = timezone_path.read_text(encoding="utf-8").strip()
        if not timezone:
            raise ValueError("timezone.txt is empty")
    rights = None
    rights_path = root / "rights.txt"
    if rights_path.is_file():
        rights = rights_path.read_text(encoding="utf-8").strip()
    frame = pd.read_csv(table_path)
    _reject_borehole_only(frame)
    required = {"station_id", "latitude", "longitude", "observed_at", "depth_m"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"observations.csv is missing columns: {missing}")
    manifest = {
        "format": "alter-ego-observations-csv-v1",
        "input_folder": str(root.resolve()),
        "files": {
            "observations.csv": {"sha256": file_sha256(table_path), "rows": int(len(frame))},
        },
        "timezone": timezone,
        "rights": rights,
        "rights_status": "stated_by_local_file" if rights else "not_stated",
        "depth_column": "depth_m",
        "depth_meaning": "time-varying water level, metres below ground",
        "borehole_columns_present": sorted(BOREHOLE_COLUMNS & set(frame.columns)),
        "aggregation": "daily_median_of_accepted_validity",
        "interpolation": False,
    }
    if timezone_path.is_file():
        manifest["files"]["timezone.txt"] = {"sha256": file_sha256(timezone_path)}
    if rights_path.is_file():
        manifest["files"]["rights.txt"] = {"sha256": file_sha256(rights_path)}
    return frame, manifest


def _reject_borehole_only(frame: pd.DataFrame) -> None:
    columns = set(frame.columns)
    if "depth_m" in columns:
        return
    found = sorted(BOREHOLE_COLUMNS & columns)
    if found:
        raise ValueError(
            "refusing to use borehole or well construction depth as the groundwater reading: "
            + ", ".join(found)
        )
