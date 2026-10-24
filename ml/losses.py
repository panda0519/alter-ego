"""Masked standardised depth loss.

Supervision is visible and train-masked labels. Holdout labels are not in the
mask. The first sequence positions are ignored so the recurrent state can
start. An empty mask raises. It does not return a zero loss.
"""
from __future__ import annotations

import numpy as np
import torch


class EmptySupervision(RuntimeError):
    pass


def supervision_mask(depth_valid: np.ndarray, roles: np.ndarray, ignore_first: int) -> np.ndarray:
    if depth_valid.ndim != 3:
        raise ValueError("validity windows must be B, T, N")
    permitted = np.isin(roles, ("visible", "train_masked"))
    mask = np.asarray(depth_valid, dtype=bool) & permitted.reshape(1, 1, -1)
    if ignore_first > 0:
        mask[:, : int(ignore_first), :] = False
    return mask


def masked_standardised_mse(prediction: torch.Tensor, target: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    selected = mask.to(dtype=torch.bool)
    count = int(selected.sum().item())
    if count == 0:
        raise EmptySupervision("no permitted targets in this batch")
    residual = prediction - target
    chosen = residual[selected]
    if not torch.isfinite(chosen).all():
        raise ValueError("supervised residual is not finite")
    return torch.mean(chosen * chosen)
