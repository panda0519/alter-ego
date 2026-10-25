"""Storage residual, training-only q, and the lambda ramp."""
import numpy as np
import pytest
import torch

from ml.losses import EmptySupervision
from ml.physics import (
    daily_storage_change_m,
    estimate_q,
    residuals_m,
    scheduled_lambda,
    seven_day_change_scale_m,
    window_physics_loss,
)

SY = 0.10
ALPHA = 0.15
BETA = 0.10


def _spec_residual(depth, precip, et0, q, day):
    change = depth[day] - depth[day - 7]
    forcing = 0.0
    for sample in range(day - 6, day + 1):
        forcing += (BETA * et0[sample] + q - ALPHA * precip[sample]) / SY
    return change - forcing


def test_flat_zero_forcing_has_zero_residual_and_signs_follow_recharge_and_depletion():
    assert daily_storage_change_m(0.0, 0.0, 0.0, SY, ALPHA, BETA) == 0.0
    depth = np.full(8, 12.0)
    weather = np.zeros(8)
    valid = np.ones(8, dtype=bool)
    residual, usable = residuals_m(depth, weather, weather, valid, 0.0, SY, ALPHA, BETA)
    assert usable[7]
    assert residual[7] == pytest.approx(0.0)
    recharge = daily_storage_change_m(precip_m_per_day=0.005, et0_m_per_day=0.0, q_m_per_day=0.0, sy=SY, alpha=ALPHA, beta=BETA)
    depletion = daily_storage_change_m(precip_m_per_day=0.0, et0_m_per_day=0.004, q_m_per_day=0.0, sy=SY, alpha=ALPHA, beta=BETA)
    assert recharge < 0.0
    assert depletion > 0.0
    assert recharge == pytest.approx((0.0 - ALPHA * 0.005) / SY)


def test_nonflat_exact_balance_is_zero_and_the_wrong_sign_is_not():
    precip = np.zeros(8)
    et0 = np.zeros(8)
    precip[1:] = 0.01
    depth = np.zeros(8)
    depth[0] = 10.0
    for day in range(1, 8):
        depth[day] = depth[day - 1] + daily_storage_change_m(precip[day], et0[day], 0.0, SY, ALPHA, BETA)
    residual, usable = residuals_m(depth, precip, et0, np.ones(8, dtype=bool), 0.0, SY, ALPHA, BETA)
    assert usable[7]
    assert residual[7] == pytest.approx(0.0, abs=1e-12)
    assert residual[7] == pytest.approx(_spec_residual(depth, precip, et0, 0.0, 7))
    wrong = depth[7] - depth[0]
    for sample in range(1, 8):
        wrong -= (BETA * et0[sample] + 0.0 + ALPHA * precip[sample]) / SY
    assert wrong != pytest.approx(0.0)
    assert residual[7] != pytest.approx(wrong)


def test_missing_weather_is_masked_and_millimetres_are_not_the_metre_input():
    depth = np.linspace(10.0, 10.7, 8)
    precip = np.full(8, 0.002)
    et0 = np.full(8, 0.003)
    valid = np.ones(8, dtype=bool)
    valid[4] = False
    residual, usable = residuals_m(depth, precip, et0, valid, 0.001, SY, ALPHA, BETA)
    assert not usable[7]
    assert np.isnan(residual[7])
    five_mm_per_day = 5.0 / 1000.0
    change = daily_storage_change_m(five_mm_per_day, 0.0, 0.0, SY, ALPHA, BETA)
    assert change == pytest.approx(-ALPHA * five_mm_per_day / SY)
    assert abs(change) < 0.01


def test_q_and_scale_ignore_holdout_and_later_partitions():
    days = 40
    wells = 3
    depth = np.zeros((days, wells))
    valid = np.ones((days, wells), dtype=bool)
    precip = np.zeros((days, wells))
    et0 = np.zeros((days, wells))
    weather = np.ones((days, wells), dtype=bool)
    roles = np.array(["visible", "train_masked", "holdout"])
    depth[:, 0] = np.arange(days) * 0.2
    depth[:, 1] = np.arange(days) * 0.4
    depth[:, 2] = 1000.0
    n_train = 31
    original = estimate_q(depth, valid, precip, et0, weather, roles, n_train, SY, ALPHA, BETA, min_pairs=30)
    assert original["eligible_wells"] == 2
    assert original["q_m_per_day"] == pytest.approx(SY * 0.3)
    mutated = depth.copy()
    mutated[:, 2] = -5000.0
    mutated[n_train:, :2] = 8000.0
    again = estimate_q(mutated, valid, precip, et0, weather, roles, n_train, SY, ALPHA, BETA, min_pairs=30)
    assert again["q_m_per_day"] == pytest.approx(original["q_m_per_day"])
    assert again["eligible_wells"] == original["eligible_wells"]
    short = valid.copy()
    short[30, 0] = False
    dropped = estimate_q(depth, short, precip, et0, weather, roles, n_train, SY, ALPHA, BETA, min_pairs=30)
    assert dropped["eligible_wells"] == 1
    negative = depth.copy()
    negative[:, 0] = -np.arange(days)
    negative[:, 1] = -np.arange(days) * 2
    clipped = estimate_q(negative, valid, precip, et0, weather, roles, n_train, SY, ALPHA, BETA, min_pairs=30)
    assert clipped["unclipped_median_m_per_day"] < 0.0
    assert clipped["q_m_per_day"] == 0.0
    scale = seven_day_change_scale_m(depth, valid, roles, n_train, 7, 0.05)
    mutated_scale = seven_day_change_scale_m(mutated, valid, roles, n_train, 7, 0.05)
    assert scale["scale_m"] == pytest.approx(mutated_scale["scale_m"])
    tiny = np.zeros_like(depth)
    tiny[:, 0] = np.arange(days) * 0.001
    tiny[:, 1] = np.arange(days) * 0.001
    floored = seven_day_change_scale_m(tiny, valid, roles, n_train, 7, 0.05)
    assert floored["std_m"] < 0.05
    assert floored["scale_m"] == 0.05


def test_window_loss_matches_the_residual_scale_and_has_a_finite_gradient():
    depth = torch.zeros(1, 10, 1)
    depth[0, :, 0] = torch.linspace(10.0, 11.0, 10)
    precip = torch.zeros(1, 10, 1)
    et0 = torch.zeros(1, 10, 1)
    weather = torch.ones(1, 10, 1, dtype=torch.bool)
    loss = window_physics_loss(depth, precip, et0, weather, 0.0, 1.0, 0.0, 0.5, SY, ALPHA, BETA, ignore_first=7)
    expected = []
    values = depth[0, :, 0].numpy()
    for day in range(7, 10):
        expected.append(((values[day] - values[day - 7]) / 0.5) ** 2)
    assert float(loss) == pytest.approx(float(np.mean(expected)))
    varied = depth.clone().detach().requires_grad_(True)
    learned = window_physics_loss(varied, precip, et0, weather, 0.0, 1.0, 0.0, 0.5, SY, ALPHA, BETA, ignore_first=7)
    learned.backward()
    assert torch.isfinite(varied.grad).all()
    assert float(varied.grad.abs().sum()) > 0.0
    blocked = weather.clone()
    blocked[0, :, 0] = False
    with pytest.raises(EmptySupervision):
        window_physics_loss(depth, precip, et0, blocked, 0.0, 1.0, 0.0, 0.5, SY, ALPHA, BETA, ignore_first=7)


def test_positive_lambda_ramps_after_five_zero_epochs():
    assert [scheduled_lambda(epoch, 1.0, 5, 5) for epoch in range(1, 6)] == [0.0, 0.0, 0.0, 0.0, 0.0]
    assert scheduled_lambda(6, 1.0, 5, 5) == pytest.approx(0.2)
    assert scheduled_lambda(10, 0.1, 5, 5) == pytest.approx(0.1)
    assert scheduled_lambda(11, 0.1, 5, 5) == pytest.approx(0.1)
    assert scheduled_lambda(40, 1.0, 5, 5) == pytest.approx(1.0)
