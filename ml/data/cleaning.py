"""Daily cleaning. Gaps stay empty. Nothing is interpolated or filled from the future."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ml.data.sources import ACCEPTED_VALIDITY


@dataclass
class CleanedSeries:
    station_ids: list[str]
    latitude: np.ndarray
    longitude: np.ndarray
    depth_m: np.ndarray
    depth_valid: np.ndarray
    report: dict


def clean_observations(
    frame: pd.DataFrame,
    dates: pd.DatetimeIndex,
    default_timezone: str | None,
) -> CleanedSeries:
    work = frame.copy()
    if "validity" not in work.columns:
        work["validity"] = ""
    work["validity"] = work["validity"].fillna("").astype(str).str.strip().str.lower()
    exact_duplicates = int(work.duplicated().sum())
    work = work.drop_duplicates()
    work["depth_m"] = pd.to_numeric(work["depth_m"], errors="coerce")
    work["latitude"] = pd.to_numeric(work["latitude"], errors="coerce")
    work["longitude"] = pd.to_numeric(work["longitude"], errors="coerce")
    work["station_id"] = work["station_id"].astype(str)
    work["civil_date"] = [
        _civil_date(value, default_timezone) for value in work["observed_at"].astype(str)
    ]
    code_ok = work["validity"].isin(ACCEPTED_VALIDITY).to_numpy()
    finite_depth = np.isfinite(work["depth_m"].to_numpy(dtype=np.float64))
    rejected_codes = int((~code_ok).sum())
    non_finite = int((code_ok & ~finite_depth).sum())
    accepted = code_ok & finite_depth
    negative = int((work["depth_m"].to_numpy()[accepted] < 0).sum())
    stations = _stations(work)
    usable = work.loc[accepted, ["station_id", "civil_date", "depth_m"]]
    daily = (
        usable.groupby(["station_id", "civil_date"], sort=True)["depth_m"].median().rename("depth_m").reset_index()
    )
    start = dates[0].date()
    end = dates[-1].date()
    outside = int((~daily["civil_date"].between(start, end)).sum())
    daily = daily.loc[daily["civil_date"].between(start, end)]
    ids = stations["station_id"].tolist()
    depth = np.full((len(dates), len(ids)), np.nan, dtype=np.float64)
    index = {station_id: position for position, station_id in enumerate(ids)}
    date_index = {day.date(): position for position, day in enumerate(dates)}
    for row in daily.itertuples(index=False):
        depth[date_index[row.civil_date], index[row.station_id]] = float(row.depth_m)
    valid = np.isfinite(depth)
    report = {
        "exact_duplicate_rows_removed": exact_duplicates,
        "validity_rows_excluded": rejected_codes,
        "non_finite_depths_excluded": non_finite,
        "negative_depths_kept": negative,
        "daily_rows_outside_config_window": outside,
        "aggregation": "median",
        "target_interpolation": False,
        "future_fill": False,
        "universal_range_filter": False,
    }
    return CleanedSeries(
        station_ids=ids,
        latitude=stations["latitude"].to_numpy(dtype=np.float64),
        longitude=stations["longitude"].to_numpy(dtype=np.float64),
        depth_m=depth,
        depth_valid=valid,
        report=report,
    )


def _civil_date(value: str, default_timezone: str | None):
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        if default_timezone is None:
            raise ValueError(f"naive observed_at requires timezone.txt: {value}")
        stamp = stamp.tz_localize(default_timezone)
    return stamp.date()


def _stations(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for station_id, group in frame.groupby("station_id", sort=True):
        latitudes = group["latitude"].to_numpy(dtype=np.float64)
        longitudes = group["longitude"].to_numpy(dtype=np.float64)
        if not np.isfinite(latitudes).all() or not np.isfinite(longitudes).all():
            raise ValueError(f"non-finite coordinate for {station_id}")
        if np.nanmax(latitudes) - np.nanmin(latitudes) > 1e-6 or np.nanmax(longitudes) - np.nanmin(longitudes) > 1e-6:
            raise ValueError(f"station {station_id} has inconsistent coordinates")
        latitude = float(latitudes[0])
        longitude = float(longitudes[0])
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError(f"station {station_id} coordinates are outside decimal degrees")
        rows.append({"station_id": station_id, "latitude": latitude, "longitude": longitude})
    if not rows:
        raise ValueError("no stations in observations")
    stations = pd.DataFrame(rows).sort_values("station_id").reset_index(drop=True)
    if stations["station_id"].duplicated().any():
        raise ValueError("duplicate station id after sorting")
    return stations
