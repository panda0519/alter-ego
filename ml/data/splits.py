"""Chronological partitions and the frozen well roles.

Date cuts use floor for the training fraction and floor for the validation
fraction. The test partition is the remainder, so it is not a second independent
floor that could overlap the earlier cuts. A window is emitted only when every
day of that window sits inside one partition.
"""
from __future__ import annotations

import math

import numpy as np


def time_counts(n_days: int, train_fraction: float, validation_fraction: float) -> tuple[int, int, int]:
    n_train = int(math.floor(float(train_fraction) * n_days))
    n_validation = int(math.floor(float(validation_fraction) * n_days))
    n_test = n_days - n_train - n_validation
    if min(n_train, n_validation, n_test) < 1:
        raise ValueError("date partitions are empty")
    return n_train, n_validation, n_test


def training_coverage(depth_valid: np.ndarray, n_train: int) -> np.ndarray:
    return depth_valid[:n_train].mean(axis=0)


def select_cohort(station_ids: list[str], coverage: np.ndarray, minimum: float) -> np.ndarray:
    if len(station_ids) != len(coverage):
        raise ValueError("coverage does not match station ids")
    keep = coverage >= float(minimum)
    if int(keep.sum()) < 2:
        raise ValueError("fewer than two wells meet the training coverage minimum")
    return keep


def role_counts(n_wells: int, holdout_fraction: float, masked_fraction_of_remaining: float) -> tuple[int, int, int]:
    n_holdout = int(round(float(holdout_fraction) * n_wells))
    n_masked = int(round(float(masked_fraction_of_remaining) * (n_wells - n_holdout)))
    n_visible = n_wells - n_holdout - n_masked
    if min(n_holdout, n_masked, n_visible) < 1:
        raise ValueError(f"role counts are not usable: {n_holdout}, {n_masked}, {n_visible}")
    return n_holdout, n_masked, n_visible


def assign_roles(station_ids: list[str], seed: int, holdout_fraction: float, masked_fraction_of_remaining: float) -> np.ndarray:
    n_wells = len(station_ids)
    n_holdout, n_masked, _ = role_counts(n_wells, holdout_fraction, masked_fraction_of_remaining)
    order = np.random.default_rng(seed).permutation(n_wells)
    roles = np.empty(n_wells, dtype=object)
    roles[order[:n_holdout]] = "holdout"
    roles[order[n_holdout : n_holdout + n_masked]] = "train_masked"
    roles[order[n_holdout + n_masked :]] = "visible"
    if set(roles) != {"visible", "train_masked", "holdout"}:
        raise RuntimeError("role assignment missed a group")
    return roles


def window_end_indices(start: int, stop: int, window: int, stride: int) -> np.ndarray:
    if window < 1 or stride < 1:
        raise ValueError("window and stride must be positive")
    first = start + window - 1
    if first >= stop:
        return np.array([], dtype=np.int64)
    return np.arange(first, stop, stride, dtype=np.int64)


def windows_stay_inside(ends: np.ndarray, start: int, stop: int, window: int) -> bool:
    if len(ends) == 0:
        return False
    opens = ends - (window - 1)
    return bool(np.all(opens >= start) and np.all(ends < stop))
