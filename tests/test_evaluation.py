"""Validation selection, one common mask, and a fresh checkpoint load."""
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from torch import nn

from ml.checkpoint import load_checkpoint, save_checkpoint
from ml.evaluate import choose_default, max_abs_difference, require_same_device, score_common, select_positive_checkpoint
from ml.model import GCNLSTM

ROOT = Path(__file__).resolve().parents[1]


def test_positive_lambda_tie_does_not_become_a_physics_model():
    selection = select_positive_checkpoint([
        {"run": "runs/lambda1", "lambda_target": 1.0, "validation_mae_m": 0.86, "used_positive_lambda": False},
        {"run": "runs/lambda01", "lambda_target": 0.1, "validation_mae_m": 0.86, "used_positive_lambda": False},
    ])
    assert selection["tie"] is True
    assert selection["selected_lambda_target"] == 0.1
    assert selection["export_physics"] is False
    assert "test" not in selection["rule"]


def test_a_lower_validation_mae_can_select_a_real_positive_checkpoint():
    selection = select_positive_checkpoint([
        {"run": "warmup", "lambda_target": 0.1, "validation_mae_m": 1.0, "used_positive_lambda": False},
        {"run": "later", "lambda_target": 1.0, "validation_mae_m": 0.4, "used_positive_lambda": True},
    ])
    assert selection["selected_run"] == "later"
    assert selection["export_physics"] is True


def test_default_follows_validation_mae_and_keeps_idw_on_a_tie():
    assert choose_default({"idw": 1.2, "gcn_lstm": 0.8}) == "gcn_lstm"
    assert choose_default({"gcn_lstm": 0.5, "idw": 0.5}) == "idw"


def test_common_mask_counts_each_date_once_and_rejects_an_empty_mask():
    depth = np.array([[1.0, 4.0], [2.0, 5.0], [3.0, 6.0]])
    valid = np.ones_like(depth, dtype=bool)
    roles = np.array(["holdout", "visible"])
    left = np.array([[1.5, 0.0], [np.nan, 0.0], [4.0, 0.0]])
    right = np.array([[np.nan, 0.0], [np.nan, 0.0], [5.0, 0.0]])
    scored = score_common({"idw": left, "gcn_lstm": right}, depth, valid, roles, 0, 3, "holdout")
    assert scored["pairs"] == 1
    assert scored["wells"] == 1
    assert scored["pairs"] >= scored["wells"]
    assert scored["methods"]["idw"]["mae_m"] == pytest.approx(1.0)
    assert scored["methods"]["gcn_lstm"]["mae_m"] == pytest.approx(2.0)
    with pytest.raises(RuntimeError, match="empty"):
        score_common({"idw": np.full_like(depth, np.nan)}, depth, valid, roles, 0, 3, "holdout")


def test_a_different_device_is_not_mixed_into_the_saved_grid():
    with pytest.raises(RuntimeError, match="refusing to mix"):
        require_same_device("cuda:NVIDIA GeForce RTX 5050 Laptop GPU", "cpu")


def test_prediction_difference_rejects_a_disagreement_on_missing_dates():
    left = np.array([[1.0], [np.nan]])
    assert max_abs_difference(left, np.array([[1.0 + 1e-6], [np.nan]])) == pytest.approx(1e-6)
    with pytest.raises(ValueError):
        max_abs_difference(left, np.array([[1.0], [2.0]]))


def test_fresh_process_keeps_the_station_axis(tmp_path: Path):
    torch.manual_seed(42)
    model = GCNLSTM({
        "features": {"count": 8},
        "model": {
            "gcn_layers": 1, "gcn_hidden": 32, "lstm_layers": 1, "lstm_hidden": 32,
            "bidirectional": False, "internal_lstm_dropout": 0.0, "external_dropout": 0.0,
            "output": "depth_sequence_B_T_N",
        },
    })
    with torch.no_grad():
        nn.init.constant_(model.gcn.weight, 0.02)
        nn.init.zeros_(model.gcn.bias)
    path = tmp_path / "checkpoint.pt"
    save_checkpoint(path, {
        "model_state": model.state_dict(),
        "adjacency": torch.eye(2),
        "station_ids": ["a", "b"],
        "config": {
            "features": {"count": 8},
            "model": {
                "gcn_layers": 1, "gcn_hidden": 32, "lstm_layers": 1, "lstm_hidden": 32,
                "bidirectional": False, "internal_lstm_dropout": 0.0, "external_dropout": 0.0,
                "output": "depth_sequence_B_T_N",
            },
            "training": {"batch_size": 16},
        },
        "scalers": {"depth_mean_m": 10.0, "depth_std_m": 2.0},
        "splits": {"seed": 42},
        "smoke": False,
        "lambda_target": 0.0,
    })
    loaded, payload, adjacency = load_checkpoint(path, torch.device("cpu"))
    features = torch.ones(1, 30, 2, 8)
    with torch.no_grad():
        expected = loaded(features, adjacency).cpu().numpy()
    script = tmp_path / "fresh_infer.py"
    output = tmp_path / "pred.npy"
    script.write_text(
        "import sys\nfrom pathlib import Path\nimport numpy as np\nimport torch\n"
        "from ml.checkpoint import load_checkpoint\n"
        "model, payload, adjacency = load_checkpoint(Path(sys.argv[1]), torch.device('cpu'))\n"
        "assert payload['station_ids'] == ['a', 'b']\n"
        "features = torch.ones(1, 30, 2, 8)\n"
        "with torch.no_grad():\n"
        "    values = model(features, adjacency).cpu().numpy()\n"
        "assert values.shape == (1, 30, 2)\n"
        "np.save(sys.argv[2], values)\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        [sys.executable, str(script), str(path), str(output)],
        cwd=ROOT, env=env, capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    fresh = np.load(output)
    assert fresh.shape[-1] == 2
    assert np.allclose(fresh, expected)
