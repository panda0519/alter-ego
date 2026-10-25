"""Score each date from the window that ends on that date.

Overlapping earlier positions are not averaged into the stored prediction.
Dates without an ending window stay missing. Standardised outputs are converted
with the training depth scaler before they leave this module.
"""
from __future__ import annotations

import numpy as np
import torch

from ml.features import WINDOW, finite_feature_values, metres_from_standardised


def predict_ending_windows(
    model: torch.nn.Module,
    features: np.ndarray,
    adjacency: torch.Tensor,
    window_ends: np.ndarray,
    depth_mean_m: float,
    depth_std_m: float,
    device: torch.device,
    batch_size: int = 16,
    window: int = WINDOW,
) -> np.ndarray:
    model.eval()
    values = finite_feature_values(features)
    ends = np.asarray(window_ends, dtype=np.int64)
    if len(ends) != len(np.unique(ends)):
        raise ValueError("window ends repeat a date")
    predictions = np.full(values.shape[:2], np.nan, dtype=np.float64)
    with torch.no_grad():
        for start in range(0, len(ends), batch_size):
            batch = ends[start : start + batch_size]
            slices = np.stack([values[int(end) - window + 1 : int(end) + 1] for end in batch], axis=0)
            inputs = torch.from_numpy(np.ascontiguousarray(slices)).to(device)
            output = model(inputs, adjacency)
            last = output[:, -1, :].detach().cpu().numpy()
            metres = metres_from_standardised(last, depth_mean_m, depth_std_m)
            for row, end in enumerate(batch):
                predictions[int(end)] = metres[row]
    return predictions


def shared_label_scores(
    left_m: np.ndarray,
    right_m: np.ndarray,
    depth_m: np.ndarray,
    depth_valid: np.ndarray,
    roles: np.ndarray,
    start: int,
    stop: int,
    role: str,
) -> dict:
    """Errors on well-dates where both predictions and the label are finite."""
    selected_role = np.asarray(roles) == role
    depth = depth_m[start:stop]
    usable = (
        selected_role.reshape(1, -1)
        & depth_valid[start:stop]
        & np.isfinite(depth)
        & np.isfinite(left_m[start:stop])
        & np.isfinite(right_m[start:stop])
    )
    pairs = int(usable.sum())
    wells = int(np.any(usable, axis=0).sum()) if usable.size else 0
    if pairs < 1:
        return {
            "pairs": 0,
            "wells": 0,
            "left_mae_m": None,
            "left_rmse_m": None,
            "right_mae_m": None,
            "right_rmse_m": None,
        }
    left_error = left_m[start:stop][usable] - depth[usable]
    right_error = right_m[start:stop][usable] - depth[usable]
    return {
        "pairs": pairs,
        "wells": wells,
        "left_mae_m": float(np.mean(np.abs(left_error))),
        "left_rmse_m": float(np.sqrt(np.mean(left_error ** 2))),
        "right_mae_m": float(np.mean(np.abs(right_error))),
        "right_rmse_m": float(np.sqrt(np.mean(right_error ** 2))),
    }
