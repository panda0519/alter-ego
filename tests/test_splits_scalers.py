"""Split boundaries, scaler support, and held-out leakage."""
import math

import numpy as np
import pandas as pd
import pytest

from ml.data.bundle import assemble
from ml.data.cleaning import CleanedSeries
from ml.data.splits import assign_roles, role_counts, time_counts, window_end_indices, windows_stay_inside

FEATURE_LAG = 0
FEATURE_AVAILABLE = 1


def _config():
    return {
        "schema_version": "1.0.0",
        "seed": 42,
        "data": {
            "window": 30,
            "stride": 1,
            "windows_cross_partitions": False,
            "holdout_fraction": 0.20,
            "train_masked_fraction_of_remaining": 0.30,
        },
    }


def _bundle(depth, valid, precip_m=None, et0_m=None):
    n_days, n_wells = depth.shape
    dates = pd.date_range("2023-01-01", periods=n_days, freq="D")
    n_train, n_validation, n_test = time_counts(n_days, 0.60, 0.15)
    ids = [f"SYN{i + 1:03d}" for i in range(n_wells)]
    cleaned = CleanedSeries(
        station_ids=ids,
        latitude=23.5 + np.arange(n_wells) * 0.01,
        longitude=77.4 + np.arange(n_wells) * 0.01,
        depth_m=depth,
        depth_valid=valid,
        report={"target_interpolation": False},
    )
    if precip_m is None:
        precip_m = np.full((n_days, n_wells), 0.002)
    if et0_m is None:
        et0_m = np.full((n_days, n_wells), 0.004)
    weather = {
        "precip_mm": precip_m * 1000.0,
        "precip_m_per_day": precip_m,
        "et0_mm": et0_m * 1000.0,
        "et0_m_per_day": et0_m,
        "tmax_c": np.full((n_days, n_wells), 30.0),
        "tmin_c": np.full((n_days, n_wells), 18.0),
        "weather_valid": np.ones((n_days, n_wells), dtype=bool),
        "cells": [],
    }
    keep = np.ones(n_wells, dtype=bool)
    assembled = assemble(cleaned, weather, keep, dates, _config(), n_train, n_validation, n_test)
    return assembled


def _series():
    rng = np.random.default_rng(0)
    depth = 12 + rng.normal(0, 0.2, size=(220, 40))
    valid = rng.random((220, 40)) > 0.05
    valid[:132] = True
    return depth, valid


def test_prototype_counts_and_windows_do_not_cross():
    n_train, n_validation, n_test = time_counts(731, 0.60, 0.15)
    assert (n_train, n_validation, n_test) == (438, 109, 184)
    assert (n_train, n_validation, n_test) != (438, 109, math.floor(0.25 * 731))
    assert role_counts(40, 0.20, 0.30) == (8, 10, 22)
    roles = assign_roles([f"SYN{i + 1:03d}" for i in range(40)], 42, 0.20, 0.30)
    assert [int((roles == name).sum()) for name in ("visible", "train_masked", "holdout")] == [22, 10, 8]
    assert len(set(roles)) == 3
    for start, stop in ((0, 438), (438, 547), (547, 731)):
        ends = window_end_indices(start, stop, 30, 1)
        assert windows_stay_inside(ends, start, stop, 30)
        assert ends.min() - 29 >= start
        assert ends.max() < stop


def test_heldout_mutation_does_not_change_training_scalers_or_features():
    depth, valid = _series()
    original = _bundle(depth, valid)
    mutated = depth.copy()
    holdout = original["roles"] == "holdout"
    mutated[:, holdout] = np.where(valid[:, holdout], 5000.0, np.nan)
    changed = _bundle(mutated, valid)
    assert changed["scalers"] == original["scalers"]
    training_inputs = original["roles"] != "holdout"
    assert np.array_equal(changed["features"][:, training_inputs], original["features"][:, training_inputs], equal_nan=True)
    assert np.all(changed["features"][:, holdout, FEATURE_AVAILABLE] == 0)
    assert np.all(changed["features"][:, holdout, FEATURE_LAG] == 0)


def test_train_masked_labels_affect_the_depth_scaler_and_their_lag_stays_closed():
    depth, valid = _series()
    original = _bundle(depth, valid)
    masked = original["roles"] == "train_masked"
    mutated = depth.copy()
    mutated[:132, masked] = np.where(valid[:132, masked], 80.0, np.nan)
    changed = _bundle(mutated, valid)
    assert changed["scalers"]["depth_mean_m"] != pytest.approx(original["scalers"]["depth_mean_m"])
    assert np.all(original["features"][:, masked, FEATURE_AVAILABLE] == 0)
    assert original["depth_valid"][:, masked].any()


def test_visible_lag_uses_only_the_previous_day():
    depth, valid = _series()
    valid = valid.copy()
    valid[199:202] = True
    original = _bundle(depth, valid)
    visible = np.flatnonzero(original["roles"] == "visible")[0]
    day = 50
    assert original["features"][day, visible, FEATURE_AVAILABLE] == 1
    future = depth.copy()
    future[200, visible] = 400.0
    future_bundle = _bundle(future, valid)
    assert future_bundle["scalers"] == original["scalers"]
    assert np.allclose(future_bundle["features"][day, visible], original["features"][day, visible], equal_nan=True)
    assert np.allclose(future_bundle["features"][200, visible], original["features"][200, visible], equal_nan=True)
    assert future_bundle["features"][201, visible, FEATURE_LAG] != pytest.approx(
        original["features"][201, visible, FEATURE_LAG]
    )
    previous = depth.copy()
    previous[day - 1, visible] = depth[day - 1, visible] + 3.0
    assert _bundle(previous, valid)["features"][day, visible, FEATURE_LAG] != pytest.approx(
        original["features"][day, visible, FEATURE_LAG]
    )


def test_missing_previous_day_uses_the_zero_lag_fill():
    depth, valid = _series()
    visible_probe = _bundle(depth, valid)
    visible = np.flatnonzero(visible_probe["roles"] == "visible")[0]
    valid = valid.copy()
    valid[40, visible] = False
    assembled = _bundle(depth, valid)
    assert assembled["features"][41, visible, FEATURE_AVAILABLE] == 0
    assert assembled["features"][41, visible, FEATURE_LAG] == 0
