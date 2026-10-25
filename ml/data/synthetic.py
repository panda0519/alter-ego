"""Fictional daily groundwater series.

The wells are not monitoring stations. Depth is a delayed, heterogeneous
response to the cached precipitation plus a seasonal term, a slow well-specific
trend, spatial common noise and autoregressive noise. It is not the prototype
storage update

    Sy * (d[t] - d[t-1]) = beta * ET0[t] + q - alpha * P[t]

and it does not use ET0. Missing days are left empty. Training-period coverage
is kept at or above the configured minimum so the frozen cohort can contain
the target well count; validation and test missingness are not used to redraw wells.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def place_wells(n_wells: int, rng: np.random.Generator) -> pd.DataFrame:
    rows = int(np.ceil(n_wells / 8))
    index = np.arange(n_wells)
    latitude = 23.50 + (index // 8) * 0.04 + rng.normal(0, 0.002, n_wells)
    longitude = 77.40 + (index % 8) * 0.045 + rng.normal(0, 0.002, n_wells)
    if rows < 1:
        raise ValueError("n_wells must be positive")
    return pd.DataFrame(
        {
            "station_id": [f"SYN{i + 1:03d}" for i in range(n_wells)],
            "latitude": latitude,
            "longitude": longitude,
        }
    )


def generate_observations(
    stations: pd.DataFrame,
    dates: pd.DatetimeIndex,
    precip_mm: np.ndarray,
    rng: np.random.Generator,
    train_days: int,
    minimum_train_coverage: float,
) -> pd.DataFrame:
    depth = _depth_m(stations, dates, precip_mm, rng)
    valid = _missingness(depth.shape, rng, train_days, minimum_train_coverage)
    rows = []
    for well, station in enumerate(stations.itertuples(index=False)):
        for day_index, day in enumerate(dates):
            if not valid[day_index, well]:
                continue
            rows.append(
                {
                    "station_id": station.station_id,
                    "latitude": float(station.latitude),
                    "longitude": float(station.longitude),
                    "observed_at": day.strftime("%Y-%m-%d"),
                    "depth_m": float(depth[day_index, well]),
                    "validity": "valid",
                }
            )
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError("synthetic generator produced no observations")
    return frame


def _depth_m(stations: pd.DataFrame, dates: pd.DatetimeIndex, precip_mm: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n_days, n_wells = precip_mm.shape
    if n_wells != len(stations):
        raise ValueError("precipitation columns do not match wells")
    doy = np.array([day.day_of_year for day in dates], dtype=np.float64)
    latitude = stations["latitude"].to_numpy(dtype=np.float64)
    shared = np.zeros(n_days)
    shock = rng.normal(0, 1, n_days)
    for day in range(1, n_days):
        shared[day] = 0.92 * shared[day - 1] + shock[day]
    depth = np.empty((n_days, n_wells), dtype=np.float64)
    for well in range(n_wells):
        decay = 5.0 + (well % 5)
        kernel = np.exp(-np.arange(40) / decay)
        kernel /= kernel.sum()
        driver = np.nan_to_num(precip_mm[:, well], nan=0.0)
        delayed = np.convolve(driver, kernel, mode="full")[:n_days]
        baseline = 10.0 + 0.35 * well + 2.5 * np.sin(np.radians(latitude[well]))
        seasonal = (0.55 + 0.12 * (well % 6)) * np.sin(2 * np.pi * doy / 365.0 + 0.35 * (well % 9))
        trend = ((well % 5) - 2) * 0.0012 * np.arange(n_days)
        local = np.zeros(n_days)
        noise = rng.normal(0, 0.02, n_days)
        for day in range(1, n_days):
            local[day] = 0.75 * local[day - 1] + noise[day]
        gain = 0.0035 + 0.0008 * (well % 4)
        depth[:, well] = baseline + seasonal + trend + local + 0.05 * shared - gain * delayed
    if not np.isfinite(depth).all():
        raise RuntimeError("synthetic depth is not finite")
    return depth


def _missingness(shape: tuple[int, int], rng: np.random.Generator, train_days: int, minimum: float) -> np.ndarray:
    n_days, n_wells = shape
    valid = np.ones(shape, dtype=bool)
    target = max(float(minimum), 0.75)
    for well in range(n_wells):
        placed = False
        for _ in range(30):
            mask = np.ones(n_days, dtype=bool)
            mask[rng.random(n_days) < rng.uniform(0.05, 0.14)] = False
            gap = int(rng.integers(4, 11))
            start = int(rng.integers(0, n_days - gap))
            mask[start : start + gap] = False
            if mask[:train_days].mean() >= target:
                valid[:, well] = mask
                placed = True
                break
        if not placed:
            raise RuntimeError(f"could not keep training coverage for synthetic well {well}")
    return valid
