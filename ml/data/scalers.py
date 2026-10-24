"""Scalers and model features.

Depth mean and standard deviation use valid training labels on visible and
train_masked wells. Holdout depths are excluded. Weather mean and standard
deviation use training dates at visible wells only. Coordinates are known
metadata and are standardised across the frozen cohort. Population standard
deviation (ddof 0) is the recorded definition.

Visible wells receive the previous day's own depth only. Train-masked and
holdout wells get lag 0 and availability 0. A missing previous day uses the
same fill. Weather gaps stay NaN. No feature reads a later day.
"""
from __future__ import annotations

import math

import numpy as np

FEATURE_NAMES = (
    "lag_depth_z",
    "lag_available",
    "precipitation_z",
    "et0_z",
    "doy_sin",
    "doy_cos",
    "x_z",
    "y_z",
)


def fit_depth_scaler(depth_m: np.ndarray, depth_valid: np.ndarray, roles: np.ndarray, n_train: int) -> tuple[float, float]:
    permitted = (roles == "visible") | (roles == "train_masked")
    values = depth_m[:n_train][:, permitted][depth_valid[:n_train][:, permitted]]
    return _mean_std(values, "depth")


def fit_weather_scaler(values: np.ndarray, weather_valid: np.ndarray, roles: np.ndarray, n_train: int) -> tuple[float, float]:
    visible = roles == "visible"
    sample = values[:n_train][:, visible][weather_valid[:n_train][:, visible]]
    return _mean_std(sample, "weather")


def coordinate_features(latitude: np.ndarray, longitude: np.ndarray) -> dict:
    lat0 = float(np.mean(latitude))
    lon0 = float(np.mean(longitude))
    x_m = (longitude - lon0) * 111_320.0 * math.cos(math.radians(lat0))
    y_m = (latitude - lat0) * 110_540.0
    x_mean, x_std = _mean_std(x_m, "local_x")
    y_mean, y_std = _mean_std(y_m, "local_y")
    return {
        "latitude_origin_deg": lat0,
        "longitude_origin_deg": lon0,
        "x_m": x_m,
        "y_m": y_m,
        "x_mean_m": x_mean,
        "x_std_m": x_std,
        "y_mean_m": y_mean,
        "y_std_m": y_std,
        "x_z": (x_m - x_mean) / x_std,
        "y_z": (y_m - y_mean) / y_std,
    }


def build_features(
    depth_m: np.ndarray,
    depth_valid: np.ndarray,
    precip_m: np.ndarray,
    et0_m: np.ndarray,
    weather_valid: np.ndarray,
    roles: np.ndarray,
    dates,
    coordinates: dict,
    depth_mean: float,
    depth_std: float,
    precip_mean: float,
    precip_std: float,
    et0_mean: float,
    et0_std: float,
) -> np.ndarray:
    n_days, n_wells = depth_m.shape
    features = np.full((n_days, n_wells, 8), np.nan, dtype=np.float64)
    doy = np.array([day.day_of_year for day in dates], dtype=np.float64)
    features[:, :, 4] = np.sin(2 * np.pi * doy / 365.0)[:, None]
    features[:, :, 5] = np.cos(2 * np.pi * doy / 365.0)[:, None]
    features[:, :, 6] = coordinates["x_z"][None, :]
    features[:, :, 7] = coordinates["y_z"][None, :]
    precip_z = (precip_m - precip_mean) / precip_std
    et0_z = (et0_m - et0_mean) / et0_std
    features[:, :, 2] = np.where(weather_valid, precip_z, np.nan)
    features[:, :, 3] = np.where(weather_valid, et0_z, np.nan)
    features[:, :, 0] = 0.0
    features[:, :, 1] = 0.0
    visible = roles == "visible"
    previous_valid = np.zeros_like(depth_valid)
    previous_valid[1:] = depth_valid[:-1]
    previous_depth = np.zeros_like(depth_m)
    previous_depth[1:] = depth_m[:-1]
    use_lag = visible[None, :] & previous_valid
    lag_z = (previous_depth - depth_mean) / depth_std
    features[:, :, 0] = np.where(use_lag, lag_z, 0.0)
    features[:, :, 1] = np.where(use_lag, 1.0, 0.0)
    return features


def _mean_std(values: np.ndarray, name: str) -> tuple[float, float]:
    values = np.asarray(values, dtype=np.float64)
    if values.size < 2 or not np.isfinite(values).all():
        raise ValueError(f"not enough finite {name} values to fit a scaler")
    mean = float(values.mean())
    std = float(values.std(ddof=0))
    if std == 0.0 or not math.isfinite(std) or not math.isfinite(mean):
        raise ValueError(f"{name} scaler is degenerate")
    return mean, std
