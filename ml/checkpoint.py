"""Checkpoint payload for one lambda-0 run.

The file keeps the model state, normalised adjacency, station order, config,
scalers, split counts, window ends and the code revision. Loading builds a new
module and copies the state. It does not continue an optimizer.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import torch

from ml.model import GCNLSTM


def save_checkpoint(path: Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, path)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_checkpoint(path: Path, device: torch.device) -> tuple[GCNLSTM, dict, torch.Tensor]:
    payload = torch.load(Path(path), map_location=device, weights_only=False)
    model = GCNLSTM(payload["config"]).to(device)
    model.load_state_dict(payload["model_state"])
    model.eval()
    adjacency = payload["adjacency"].to(device=device, dtype=torch.float32)
    return model, payload, adjacency
