"""Dense haversine graph in frozen station order.

k is min(neighbours, N-1). Each well keeps that many other wells, nearest
haversine distance first. Ties keep the earlier station index because the
neighbour sort is stable.

Gaussian weight is exp(-0.5 * (distance / sigma)^2). sigma is the median of
the selected neighbour distances that are strictly positive. A distance of
exactly 0, from duplicate coordinates, has weight 1. If every selected
neighbour distance is 0, sigma is recorded as 1 metre and those edges still
have weight 1, so the scale is never a divisor of zero.

The directed neighbour weights are symmetrised by union-max. Self-loops are
then set to 1 and the matrix is normalised by the symmetric degree,
D^(-1/2) A D^(-1/2). A one-well graph has no neighbour scale and normalises
to [[1]]. Rows and columns follow the station ids passed in. They are not
reordered.
"""
from __future__ import annotations

import math

import numpy as np

from ml.baseline import EARTH_RADIUS_M


def pairwise_haversine_m(latitude: np.ndarray, longitude: np.ndarray) -> np.ndarray:
    lat = np.radians(np.asarray(latitude, dtype=np.float64))
    lon = np.radians(np.asarray(longitude, dtype=np.float64))
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_M * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def build_graph(latitude: np.ndarray, longitude: np.ndarray, station_ids: list[str], neighbours: int = 6) -> dict:
    latitude = np.asarray(latitude, dtype=np.float64)
    longitude = np.asarray(longitude, dtype=np.float64)
    if latitude.shape != longitude.shape or latitude.ndim != 1:
        raise ValueError("latitude and longitude must be one well axis")
    if len(station_ids) != len(latitude):
        raise ValueError("station ids do not match coordinates")
    if neighbours < 1:
        raise ValueError("neighbour count must be positive")
    n_wells = len(station_ids)
    distances = pairwise_haversine_m(latitude, longitude)
    np.fill_diagonal(distances, 0.0)
    k = min(int(neighbours), n_wells - 1)
    directed = np.zeros((n_wells, n_wells), dtype=np.float64)
    selected: list[float] = []
    if k > 0:
        blocked = distances.copy()
        np.fill_diagonal(blocked, np.inf)
        chosen = np.argsort(blocked, axis=1, kind="mergesort")[:, :k]
        for well in range(n_wells):
            for other in chosen[well]:
                selected.append(float(blocked[well, other]))
        positive = [distance for distance in selected if distance > 0.0 and math.isfinite(distance)]
        sigma_m = float(np.median(np.array(positive, dtype=np.float64))) if positive else 1.0
        for well in range(n_wells):
            for other in chosen[well]:
                distance = float(blocked[well, other])
                directed[well, other] = 1.0 if distance == 0.0 else math.exp(-0.5 * (distance / sigma_m) ** 2)
    else:
        sigma_m = None
    symmetric = np.maximum(directed, directed.T)
    np.fill_diagonal(symmetric, 1.0)
    degree = symmetric.sum(axis=1)
    degree = np.where(degree > 0.0, degree, 1.0)
    scale = 1.0 / np.sqrt(degree)
    adjacency = scale[:, None] * symmetric * scale[None, :]
    if not np.isfinite(adjacency).all() or not np.isfinite(symmetric).all():
        raise RuntimeError("graph weights are not finite")
    return {
        "station_ids": list(station_ids),
        "distances_m": distances,
        "directed_weights": directed,
        "symmetric_weights": symmetric,
        "adjacency": adjacency,
        "sigma_m": sigma_m,
        "k": int(k),
    }
