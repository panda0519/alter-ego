"""Simplified local storage residual.

Depth is positive downward, in metres. Precipitation and ET0 are metres per
day, not z-scores and not millimetres. The daily relation is

    Sy * (d[t] - d[t-1]) ~= beta * ET0[t] + q - alpha * P[t]

q is one frozen global value. It is the median, clipped below at zero, of
per-well means on permitted consecutive training pairs. Holdout wells and
validation or test dates do not enter q or the residual scale. There is no
lateral flow and no per-well pumping parameter.

The seven-day residual at t uses predictions in metres:

    r[t] = d_hat[t] - d_hat[t-7]
           - sum((beta * ET0[u] + q - alpha * P[u]) / Sy, u=t-6..t)

A missing weather day anywhere in that sum drops the residual. The loss is the
mean square of r divided by the training-only standard deviation of permitted
observed seven-day depth changes, and that divisor is at least 0.05 m.
"""
from __future__ import annotations

import math

import numpy as np
import torch

from ml.losses import EmptySupervision


def physics_constants(config: dict) -> dict:
    physics = config["physics"]
    if physics["formulation"] != "simplified_local_storage_7day":
        raise ValueError("physics formulation is not the simplified seven-day storage residual")
    if physics["lateral_flow"] is not False:
        raise ValueError("lateral flow is outside this regulariser")
    if physics["weather_unit"] != "m_per_day":
        raise ValueError("physics weather must be metres per day")
    if physics["q_mode"] != "frozen_global_training_estimate":
        raise ValueError("q must be one frozen training estimate")
    return {
        "specific_yield": float(physics["specific_yield_assumed"]),
        "alpha": float(physics["effective_rainfall_fraction_assumed"]),
        "beta": float(physics["et0_coupling_assumed"]),
        "min_pairs": int(physics["q_min_valid_daily_pairs_per_well"]),
        "residual_days": int(physics["residual_days"]),
        "minimum_scale_m": float(physics["minimum_residual_scale_m"]),
    }


def scheduled_lambda(epoch: int, target: float, zero_epochs: int, ramp_epochs: int) -> float:
    """Epochs 1..zero stay at 0. The next ramp_epochs move linearly onto target."""
    if epoch < 1:
        raise ValueError("epoch numbers start at 1")
    if zero_epochs < 0 or ramp_epochs < 1:
        raise ValueError("lambda warmup and ramp must match the prototype")
    if epoch <= zero_epochs:
        return 0.0
    if epoch >= zero_epochs + ramp_epochs:
        return float(target)
    step = epoch - zero_epochs
    return float(target) * step / float(ramp_epochs)


def checkpoint_epoch_eligible(epoch: int, lambda_target: float, lambda_at_epoch: float, lambda_zero_epochs: int) -> bool:
    """A zero target may keep any epoch. A positive target keeps only post-warmup epochs with lambda active."""
    if not math.isfinite(float(lambda_target)) or float(lambda_target) < 0.0:
        raise ValueError("lambda target must be finite and non-negative")
    if math.isclose(float(lambda_target), 0.0, rel_tol=0.0, abs_tol=0.0):
        return True
    return int(epoch) > int(lambda_zero_epochs) and float(lambda_at_epoch) > 0.0


def daily_storage_change_m(precip_m_per_day: float, et0_m_per_day: float, q_m_per_day: float, sy: float, alpha: float, beta: float) -> float:
    if sy == 0.0:
        raise ValueError("specific yield is zero")
    return (beta * float(et0_m_per_day) + float(q_m_per_day) - alpha * float(precip_m_per_day)) / sy


def estimate_q(
    depth_m: np.ndarray,
    depth_valid: np.ndarray,
    precip_m: np.ndarray,
    et0_m: np.ndarray,
    weather_valid: np.ndarray,
    roles: np.ndarray,
    n_train: int,
    sy: float,
    alpha: float,
    beta: float,
    min_pairs: int,
) -> dict:
    permitted = (np.asarray(roles) == "visible") | (np.asarray(roles) == "train_masked")
    means = []
    for well in np.flatnonzero(permitted):
        terms = []
        for day in range(1, int(n_train)):
            if not depth_valid[day, well] or not depth_valid[day - 1, well]:
                continue
            if not weather_valid[day, well]:
                continue
            precip = float(precip_m[day, well])
            et0 = float(et0_m[day, well])
            if not math.isfinite(precip) or not math.isfinite(et0):
                continue
            delta = float(depth_m[day, well] - depth_m[day - 1, well])
            terms.append(sy * delta - beta * et0 + alpha * precip)
        if len(terms) >= int(min_pairs):
            means.append(float(np.mean(np.array(terms, dtype=np.float64))))
    if not means:
        return {
            "q_m_per_day": None,
            "eligible_wells": 0,
            "status": "not_estimable",
        }
    median = float(np.median(np.array(means, dtype=np.float64)))
    return {
        "q_m_per_day": max(0.0, median),
        "eligible_wells": len(means),
        "status": "frozen_training_estimate",
        "unclipped_median_m_per_day": median,
    }


def seven_day_change_scale_m(
    depth_m: np.ndarray,
    depth_valid: np.ndarray,
    roles: np.ndarray,
    n_train: int,
    residual_days: int,
    minimum_scale_m: float,
) -> dict:
    permitted = (np.asarray(roles) == "visible") | (np.asarray(roles) == "train_masked")
    changes = []
    for well in np.flatnonzero(permitted):
        for day in range(int(residual_days), int(n_train)):
            earlier = day - int(residual_days)
            if not depth_valid[day, well] or not depth_valid[earlier, well]:
                continue
            change = float(depth_m[day, well] - depth_m[earlier, well])
            if math.isfinite(change):
                changes.append(change)
    if len(changes) < 2:
        return {"std_m": None, "scale_m": None, "pairs": len(changes), "status": "not_estimable"}
    std = float(np.std(np.array(changes, dtype=np.float64), ddof=0))
    if not math.isfinite(std):
        return {"std_m": None, "scale_m": None, "pairs": len(changes), "status": "not_estimable"}
    return {
        "std_m": std,
        "scale_m": max(float(minimum_scale_m), std),
        "pairs": len(changes),
        "status": "permitted_training_7day_change_std",
    }


def residuals_m(
    depth_m: np.ndarray,
    precip_m: np.ndarray,
    et0_m: np.ndarray,
    weather_valid: np.ndarray,
    q_m_per_day: float,
    sy: float,
    alpha: float,
    beta: float,
    residual_days: int = 7,
) -> tuple[np.ndarray, np.ndarray]:
    """Residual and validity for one well-day axis. Shape (T,) or (T, N)."""
    depth = np.asarray(depth_m, dtype=np.float64)
    precip = np.asarray(precip_m, dtype=np.float64)
    et0 = np.asarray(et0_m, dtype=np.float64)
    weather = np.asarray(weather_valid, dtype=bool)
    residual = np.full(depth.shape, np.nan, dtype=np.float64)
    usable = np.zeros(depth.shape, dtype=bool)
    days = depth.shape[0]
    for day in range(int(residual_days), days):
        change = depth[day] - depth[day - int(residual_days)]
        forcing = np.zeros(change.shape, dtype=np.float64)
        ok = np.ones(change.shape, dtype=bool)
        for offset in range(int(residual_days)):
            sample = day - int(residual_days) + 1 + offset
            forcing = forcing + (beta * et0[sample] + float(q_m_per_day) - alpha * precip[sample]) / sy
            ok = ok & weather[sample] & np.isfinite(precip[sample]) & np.isfinite(et0[sample])
        residual[day] = np.where(ok, change - forcing, np.nan)
        usable[day] = ok & np.isfinite(change)
    return residual, usable


def window_physics_loss(
    prediction_z: torch.Tensor,
    precip_m: torch.Tensor,
    et0_m: torch.Tensor,
    weather_valid: torch.Tensor,
    depth_mean_m: float,
    depth_std_m: float,
    q_m_per_day: float,
    scale_m: float,
    sy: float,
    alpha: float,
    beta: float,
    ignore_first: int,
    residual_days: int = 7,
) -> torch.Tensor:
    if scale_m <= 0.0 or sy == 0.0:
        raise ValueError("physics scale and specific yield must be positive")
    depth = prediction_z * float(depth_std_m) + float(depth_mean_m)
    start = max(int(ignore_first), int(residual_days))
    squares = []
    for day in range(start, depth.shape[1]):
        change = depth[:, day, :] - depth[:, day - int(residual_days), :]
        forcing = torch.zeros_like(change)
        ok = torch.ones_like(change, dtype=torch.bool)
        for offset in range(int(residual_days)):
            sample = day - int(residual_days) + 1 + offset
            forcing = forcing + (beta * et0_m[:, sample, :] + float(q_m_per_day) - alpha * precip_m[:, sample, :]) / sy
            sample_ok = weather_valid[:, sample, :].to(dtype=torch.bool)
            sample_ok = sample_ok & torch.isfinite(precip_m[:, sample, :]) & torch.isfinite(et0_m[:, sample, :])
            ok = ok & sample_ok
        normalised = (change - forcing) / float(scale_m)
        if int(ok.sum().item()) == 0:
            continue
        chosen = normalised[ok]
        squares.append(chosen * chosen)
    if not squares:
        raise EmptySupervision("no physics residuals have the required weather")
    stacked = torch.cat(squares)
    if not torch.isfinite(stacked).all():
        raise ValueError("physics residual is not finite")
    return torch.mean(stacked)
