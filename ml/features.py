"""Window tensors for the frozen eight-feature bundle.

Column construction stays in ml.data.scalers.build_features. This module only
checks that order and slices windows that already lie inside one date
partition. Visible lag is whatever that builder stored from the previous day.
Train-masked and holdout wells keep lag 0 and availability 0.

Non-finite feature values become standardised 0 at the model boundary. That
fill is not a look-ahead and it does not rewrite the stored bundle. Current-day
weather in the window is the historical value for that day.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ml.data.scalers import FEATURE_NAMES

WINDOW = 30


def load_arrays(bundle_dir: Path) -> dict:
    folder = Path(bundle_dir)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    scalers = json.loads((folder / "scalers.json").read_text(encoding="utf-8"))
    arrays = np.load(folder / "bundle.npz", allow_pickle=False)
    names = tuple(str(item) for item in arrays["feature_names"].tolist())
    if names != FEATURE_NAMES:
        raise ValueError(f"bundle feature order is {names}")
    features = arrays["features"].astype(np.float64)
    if features.shape[-1] != 8:
        raise ValueError("feature axis is not 8")
    return {
        "dataset_id": manifest["dataset_id"],
        "dataset_kind": manifest["dataset_kind"],
        "station_ids": [str(item) for item in arrays["station_id"].tolist()],
        "latitude": arrays["latitude"].astype(np.float64),
        "longitude": arrays["longitude"].astype(np.float64),
        "dates": [str(item) for item in arrays["date"].tolist()],
        "depth_m": arrays["depth_m"].astype(np.float64),
        "depth_valid": arrays["depth_valid"].astype(bool),
        "precip_m_per_day": arrays["precip_m_per_day"].astype(np.float64),
        "et0_m_per_day": arrays["et0_m_per_day"].astype(np.float64),
        "weather_valid": arrays["weather_valid"].astype(bool),
        "roles": np.array([str(item) for item in arrays["role"].tolist()]),
        "features": features,
        "feature_names": names,
        "train_window_ends": arrays["train_window_ends"].astype(np.int64),
        "validation_window_ends": arrays["validation_window_ends"].astype(np.int64),
        "test_window_ends": arrays["test_window_ends"].astype(np.int64),
        "n_train": int(arrays["n_train"]),
        "n_validation": int(arrays["n_validation"]),
        "n_test": int(arrays["n_test"]),
        "depth_mean_m": float(scalers["depth_mean_m"]),
        "depth_std_m": float(scalers["depth_std_m"]),
        "scalers": scalers,
    }


def assert_windows_inside(ends: np.ndarray, start: int, stop: int, window: int = WINDOW) -> None:
    ends = np.asarray(ends, dtype=np.int64)
    if len(ends) == 0:
        raise ValueError("partition has no windows")
    opens = ends - (window - 1)
    if np.any(opens < start) or np.any(ends >= stop) or np.any(np.diff(ends) < 1):
        raise ValueError("a window leaves its date partition or repeats a date")


def slice_windows(features: np.ndarray, ends: np.ndarray, window: int = WINDOW) -> np.ndarray:
    ends = np.asarray(ends, dtype=np.int64)
    chosen = [features[int(end) - window + 1 : int(end) + 1] for end in ends]
    stacked = np.stack(chosen, axis=0)
    if stacked.shape[1:] != (window, features.shape[1], features.shape[2]):
        raise RuntimeError("window slice does not match the source feature grid")
    return stacked


def finite_feature_values(features: np.ndarray) -> np.ndarray:
    values = np.array(features, dtype=np.float32, copy=True)
    values[~np.isfinite(values)] = 0.0
    return values


def standardised_depth(depth_m: np.ndarray, depth_valid: np.ndarray, mean_m: float, std_m: float) -> np.ndarray:
    if std_m == 0.0:
        raise ValueError("depth scaler standard deviation is zero")
    target = np.zeros(depth_m.shape, dtype=np.float32)
    usable = depth_valid & np.isfinite(depth_m)
    target[usable] = ((depth_m[usable] - mean_m) / std_m).astype(np.float32)
    return target


def metres_from_standardised(values: np.ndarray, mean_m: float, std_m: float) -> np.ndarray:
    return np.asarray(values, dtype=np.float64) * float(std_m) + float(mean_m)
