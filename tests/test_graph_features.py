"""Graph invariants and causal window features."""
import math

import numpy as np
import pandas as pd
import pytest

from ml.baseline import EARTH_RADIUS_M
from ml.data.scalers import FEATURE_NAMES, build_features, coordinate_features
from ml.data.splits import window_end_indices
from ml.features import assert_windows_inside, finite_feature_values, slice_windows
from ml.graph import build_graph


def test_two_well_gaussian_is_finite_symmetric_and_not_identity():
    graph = build_graph(np.array([0.0, 0.0]), np.array([0.0, 1.0]), ["a", "b"], neighbours=6)
    distance = EARTH_RADIUS_M * math.radians(1.0)
    weight = math.exp(-0.5)
    degree = 1.0 + weight
    expected = weight / degree
    assert graph["k"] == 1
    assert graph["sigma_m"] == pytest.approx(distance)
    assert graph["adjacency"].shape == (2, 2)
    assert np.isfinite(graph["adjacency"]).all()
    assert np.allclose(graph["adjacency"], graph["adjacency"].T)
    assert graph["adjacency"][0, 1] == pytest.approx(expected)
    assert graph["adjacency"][0, 0] == pytest.approx(1.0 / degree)
    assert not np.allclose(graph["adjacency"], np.eye(2))


def test_station_order_is_the_matrix_order_and_neighbour_shift_changes_weights():
    latitude = np.array([0.0, 0.0, 0.0])
    longitude = np.array([0.0, 1.0, 3.0])
    original = build_graph(latitude, longitude, ["s0", "s1", "s2"], neighbours=1)
    assert original["station_ids"] == ["s0", "s1", "s2"]
    moved = longitude.copy()
    moved[1] = 2.5
    shifted = build_graph(latitude, moved, ["s0", "s1", "s2"], neighbours=1)
    assert not np.allclose(original["adjacency"], shifted["adjacency"])
    flipped = build_graph(latitude[::-1], longitude[::-1], ["s2", "s1", "s0"], neighbours=1)
    assert flipped["station_ids"] == ["s2", "s1", "s0"]
    assert np.allclose(flipped["adjacency"], original["adjacency"][::-1][:, ::-1])


def test_duplicate_coordinates_one_node_and_zero_scale_stay_finite():
    duplicate = build_graph(np.array([0.0, 0.0, 1.0]), np.zeros(3), ["a", "b", "c"], neighbours=6)
    assert np.isfinite(duplicate["adjacency"]).all()
    assert duplicate["symmetric_weights"][0, 1] == 1.0
    alone = build_graph(np.array([10.0]), np.array([20.0]), ["only"], neighbours=6)
    assert alone["k"] == 0
    assert alone["sigma_m"] is None
    assert np.allclose(alone["adjacency"], [[1.0]])
    stacked = build_graph(np.zeros(4), np.zeros(4), ["w0", "w1", "w2", "w3"], neighbours=6)
    assert stacked["sigma_m"] == 1.0
    assert np.isfinite(stacked["adjacency"]).all()
    assert stacked["k"] == 3


def test_neighbour_cap_matches_min_of_six_and_other_wells():
    longitude = np.arange(8, dtype=float)
    graph = build_graph(np.zeros(8), longitude, [f"w{i}" for i in range(8)], neighbours=6)
    assert graph["k"] == 6
    assert np.count_nonzero(graph["directed_weights"], axis=1).tolist() == [6] * 8


def test_hidden_lags_stay_zero_and_future_depth_does_not_enter_features():
    days = pd.date_range("2023-01-01", periods=6, freq="D")
    depth = np.arange(24, dtype=float).reshape(6, 4)
    valid = np.ones_like(depth, dtype=bool)
    roles = np.array(["visible", "train_masked", "holdout", "visible"])
    coordinates = coordinate_features(np.array([0.0, 0.1, 0.2, 0.3]), np.array([0.0, 0.1, 0.2, 0.3]))
    weather = np.ones((6, 4))
    built = build_features(depth, valid, weather, weather, valid, roles, days, coordinates, 10.0, 2.0, 0.0, 1.0, 0.0, 1.0)
    assert built.shape[-1] == 8
    assert tuple(FEATURE_NAMES) == (
        "lag_depth_z", "lag_available", "precipitation_z", "et0_z", "doy_sin", "doy_cos", "x_z", "y_z",
    )
    assert np.all(built[:, 1, 0] == 0.0) and np.all(built[:, 1, 1] == 0.0)
    assert np.all(built[:, 2, 0] == 0.0) and np.all(built[:, 2, 1] == 0.0)
    assert built[0, 0, 1] == 0.0
    assert built[3, 0, 0] == pytest.approx((depth[2, 0] - 10.0) / 2.0)
    assert built[3, 0, 0] != pytest.approx((depth[3, 0] - 10.0) / 2.0)
    changed = depth.copy()
    changed[5, 0] = 5000.0
    changed[:, 2] = -4000.0
    later = build_features(changed, valid, weather, weather, valid, roles, days, coordinates, 10.0, 2.0, 0.0, 1.0, 0.0, 1.0)
    assert np.array_equal(later[:4], built[:4])
    missing = valid.copy()
    missing[2, 0] = False
    gap = build_features(depth, missing, weather, weather, valid, roles, days, coordinates, 10.0, 2.0, 0.0, 1.0, 0.0, 1.0)
    assert gap[3, 0, 0] == 0.0 and gap[3, 0, 1] == 0.0


def test_windows_stay_inside_one_partition_and_align_to_their_dates():
    ends = window_end_indices(10, 50, 30, 1)
    assert_windows_inside(ends, 10, 50, 30)
    with pytest.raises(ValueError):
        assert_windows_inside(np.array([39]), 11, 50, 30)
    features = np.arange(80 * 3 * 8, dtype=float).reshape(80, 3, 8)
    windows = slice_windows(features, ends, 30)
    assert windows.shape == (len(ends), 30, 3, 8)
    assert np.array_equal(windows[0, -1], features[ends[0]])
    assert np.array_equal(windows[0, 0], features[ends[0] - 29])
    broken = features.copy()
    broken[~np.isfinite(broken)] = broken[~np.isfinite(broken)]
    broken[0, 0, 2] = np.nan
    filled = finite_feature_values(broken)
    assert filled[0, 0, 2] == 0.0
    assert np.isnan(broken[0, 0, 2])
