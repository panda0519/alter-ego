"""IDW donor rules, geometry and scored pairs."""
import math

import numpy as np
import pytest

from ml.baseline import EARTH_RADIUS_M, predict_idw, score_pairs


def _equator(n_days: int, values_by_well: dict[int, float], roles: list[str]):
    n_wells = len(roles)
    depth = np.full((n_days, n_wells), np.nan)
    valid = np.zeros((n_days, n_wells), dtype=bool)
    for well, value in values_by_well.items():
        depth[:, well] = value
        valid[:, well] = True
    latitude = np.zeros(n_wells)
    return depth, valid, np.array(roles), latitude


def test_idw_matches_inverse_distance_squared_and_ignores_today_and_self():
    depth, valid, roles, latitude = _equator(
        2,
        {0: 999.0, 1: 10.0, 2: 30.0},
        ["holdout", "visible", "visible"],
    )
    depth[1, 1] = 1000.0
    longitude = np.array([0.0, 1.0, 2.0])
    predicted = predict_idw(depth, valid, roles, latitude, longitude, power=2.0, max_donors=6)
    distance_1 = EARTH_RADIUS_M * math.radians(1.0)
    distance_2 = EARTH_RADIUS_M * math.radians(2.0)
    weight_1 = 1.0 / distance_1**2
    weight_2 = 1.0 / distance_2**2
    expected = (weight_1 * 10.0 + weight_2 * 30.0) / (weight_1 + weight_2)
    assert predicted[1, 0] == pytest.approx(expected)
    assert predicted[1, 0] != pytest.approx(999.0)
    assert predicted[1, 0] != pytest.approx(1000.0)
    assert math.isnan(predicted[0, 0])


def test_no_visible_donor_is_missing_not_zero_or_hidden_persistence():
    depth, valid, roles, latitude = _equator(2, {0: 12.0, 1: 8.0}, ["holdout", "train_masked"])
    longitude = np.array([0.0, 0.01])
    predicted = predict_idw(depth, valid, roles, latitude, longitude)
    assert math.isnan(predicted[1, 0])
    assert predicted[1, 0] != 0.0


def test_train_masked_reading_is_not_a_donor():
    depth, valid, roles, latitude = _equator(
        2,
        {0: 12.0, 1: 3.0, 2: 10.0},
        ["holdout", "train_masked", "visible"],
    )
    longitude = np.array([0.0, 0.01, 1.0])
    predicted = predict_idw(depth, valid, roles, latitude, longitude)
    assert predicted[1, 0] == pytest.approx(10.0)


def test_duplicate_coordinates_use_a_finite_zero_distance_mean():
    depth, valid, roles, latitude = _equator(
        2,
        {1: 7.0, 2: 9.0, 3: 100.0},
        ["holdout", "visible", "visible", "visible"],
    )
    longitude = np.array([0.0, 0.0, 0.0, 1.0])
    predicted = predict_idw(depth, valid, roles, latitude, longitude, max_donors=6)
    assert predicted[1, 0] == pytest.approx(8.0)
    assert math.isfinite(predicted[1, 0])


def test_at_most_six_nearest_donors():
    roles = ["holdout"] + ["visible"] * 8
    values = {index: (4.0 if index <= 6 else 100.0) for index in range(1, 9)}
    depth, valid, role_array, latitude = _equator(2, values, roles)
    longitude = np.array([0.0] + [0.1 * index for index in range(1, 9)])
    predicted = predict_idw(depth, valid, role_array, latitude, longitude, max_donors=6)
    assert predicted[1, 0] == pytest.approx(4.0)


def test_scored_pairs_match_an_independent_mean():
    predictions = np.array([[np.nan, np.nan], [3.0, 10.0], [5.0, np.nan]])
    depth = np.array([[1.0, 1.0], [1.0, 7.0], [2.0, 9.0]])
    valid = np.ones((3, 2), dtype=bool)
    valid[2, 1] = False
    roles = np.array(["holdout", "train_masked"])
    scored = score_pairs(predictions, depth, valid, roles, 1, 3, "holdout")
    errors = np.array([3.0 - 1.0, 5.0 - 2.0])
    assert scored["pairs"] == 2
    assert scored["wells"] == 1
    assert scored["mae_m"] == pytest.approx(np.mean(np.abs(errors)))
    assert scored["rmse_m"] == pytest.approx(np.sqrt(np.mean(errors**2)))
