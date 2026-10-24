"""Inverse-distance baseline.

Donors are other visible wells with a valid depth on the previous calendar day.
The target's own reading is never a donor, and train-masked or holdout readings
are never donors. At most `max_donors` nearest wells are used, with weight
1/distance^power. A donor at exactly zero haversine distance, from a duplicate
coordinate, receives a finite share: the prediction is the mean of the selected
zero-distance donors and every positive-distance donor in that selection gets
weight zero. If no donor exists, the prediction is missing. It is not zero and
it is not the hidden well's own previous depth.

Each well-date is predicted once. Distances use a spherical Earth radius of
6,371,000 m.
"""
from __future__ import annotations

import math

import numpy as np

EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: np.ndarray, lon1: np.ndarray, lat2: float, lon2: float) -> np.ndarray:
    phi1 = np.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * math.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_M * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def predict_idw(
    depth_m: np.ndarray,
    depth_valid: np.ndarray,
    roles: np.ndarray,
    latitude: np.ndarray,
    longitude: np.ndarray,
    power: float = 2.0,
    max_donors: int = 6,
) -> np.ndarray:
    if power <= 0 or max_donors < 1:
        raise ValueError("IDW power and max_donors must be positive")
    n_days, n_wells = depth_m.shape
    predictions = np.full((n_days, n_wells), np.nan, dtype=np.float64)
    visible = np.flatnonzero(np.asarray(roles) == "visible")
    for day in range(1, n_days):
        available = [int(index) for index in visible if depth_valid[day - 1, index]]
        if not available:
            continue
        donor_index = np.array(available, dtype=int)
        donor_depth = depth_m[day - 1, donor_index]
        for target in range(n_wells):
            keep = donor_index != target
            if not np.any(keep):
                continue
            chosen_depth = donor_depth[keep]
            distance = haversine_m(
                latitude[donor_index[keep]],
                longitude[donor_index[keep]],
                float(latitude[target]),
                float(longitude[target]),
            )
            predictions[day, target] = _weight(chosen_depth, distance, power, max_donors)
    return predictions


def score_pairs(
    predictions: np.ndarray,
    depth_m: np.ndarray,
    depth_valid: np.ndarray,
    roles: np.ndarray,
    start: int,
    stop: int,
    role: str,
) -> dict:
    """One error per well-date. Missing predictions are not scored and are not zeros."""
    selected = np.asarray(roles) == role
    errors = []
    wells = 0
    for well in np.flatnonzero(selected):
        count = 0
        for day in range(start, stop):
            if not depth_valid[day, well] or not math.isfinite(predictions[day, well]):
                continue
            errors.append(float(predictions[day, well] - depth_m[day, well]))
            count += 1
        if count:
            wells += 1
    if not errors:
        return {"pairs": 0, "wells": 0, "mae_m": None, "rmse_m": None}
    array = np.array(errors, dtype=np.float64)
    return {
        "pairs": int(array.size),
        "wells": int(wells),
        "mae_m": float(np.mean(np.abs(array))),
        "rmse_m": float(np.sqrt(np.mean(array ** 2))),
    }


def _weight(values: np.ndarray, distance: np.ndarray, power: float, max_donors: int) -> float:
    order = np.argsort(distance, kind="mergesort")[:max_donors]
    chosen_distance = distance[order]
    chosen_values = values[order]
    zeros = chosen_distance == 0.0
    if np.any(zeros):
        return float(np.mean(chosen_values[zeros]))
    weights = 1.0 / np.power(chosen_distance, power)
    if not np.isfinite(weights).all() or float(np.sum(weights)) == 0.0:
        raise RuntimeError("IDW weights are not finite")
    return float(np.sum(weights * chosen_values) / np.sum(weights))
