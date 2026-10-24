"""Checkpoint reload, metre inversion and one-date inference."""
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from torch import nn

from ml.checkpoint import file_sha256, load_checkpoint, save_checkpoint
from ml.features import metres_from_standardised
from ml.infer import predict_ending_windows, shared_label_scores
from ml.model import GCNLSTM
from ml.train import set_seed


ROOT = Path(__file__).resolve().parents[1]


def _config():
    return {
        "features": {"count": 8},
        "model": {
            "gcn_layers": 1,
            "gcn_hidden": 32,
            "lstm_layers": 1,
            "lstm_hidden": 32,
            "bidirectional": False,
            "internal_lstm_dropout": 0.0,
            "external_dropout": 0.0,
            "output": "depth_sequence_B_T_N",
        },
        "seed": 42,
    }


class _Position(torch.nn.Module):
    def forward(self, features, adjacency):
        batch, time, wells, _channels = features.shape
        position = torch.arange(time, device=features.device, dtype=features.dtype)
        return position.view(1, time, 1).expand(batch, time, wells)


def test_each_date_is_scored_from_the_window_that_ends_there():
    features = np.zeros((12, 2, 8), dtype=np.float32)
    ends = np.array([9, 10, 11])
    predicted = predict_ending_windows(
        _Position(),
        features,
        torch.eye(2),
        ends,
        depth_mean_m=0.0,
        depth_std_m=1.0,
        device=torch.device("cpu"),
        batch_size=2,
        window=10,
    )
    assert predicted.shape == (12, 2)
    assert np.isnan(predicted[:9]).all()
    assert np.allclose(predicted[9:], 9.0)
    assert metres_from_standardised(np.array([1.5]), 10.0, 2.0)[0] == pytest.approx(13.0)


def test_shared_mask_drops_a_missing_method_and_keeps_equal_counts():
    depth = np.array([[1.0, 5.0], [2.0, 6.0], [4.0, 7.0]])
    valid = np.ones_like(depth, dtype=bool)
    valid[1, 1] = False
    roles = np.array(["holdout", "visible"])
    left = np.array([[1.5, 0.0], [9.0, 0.0], [5.0, 0.0]])
    right = np.array([[np.nan, 0.0], [np.nan, 0.0], [6.0, 0.0]])
    scored = shared_label_scores(left, right, depth, valid, roles, 0, 3, "holdout")
    assert scored["pairs"] == 1
    assert scored["wells"] == 1
    assert scored["left_mae_m"] == pytest.approx(1.0)
    assert scored["right_mae_m"] == pytest.approx(2.0)
    assert scored["pairs"] >= scored["wells"]


def test_checkpoint_reloads_in_a_fresh_process(tmp_path: Path):
    set_seed(42)
    model = GCNLSTM(_config())
    with torch.no_grad():
        nn.init.constant_(model.gcn.weight, 0.02)
        nn.init.zeros_(model.gcn.bias)
    adjacency = torch.eye(2)
    path = tmp_path / "checkpoint.pt"
    save_checkpoint(path, {
        "model_state": model.state_dict(),
        "adjacency": adjacency,
        "station_ids": ["a", "b"],
        "config": _config(),
        "scalers": {"depth_mean_m": 10.0, "depth_std_m": 2.0},
        "splits": {"n_train": 1, "n_validation": 1, "n_test": 1, "seed": 42},
        "feature_names": ["lag_depth_z"] * 8,
        "sigma_m": 1.0,
        "code_revision": "test",
        "epoch": 1,
        "validation_mae_m": 0.5,
        "lambda_target": 0.0,
        "smoke": False,
        "device": "cpu",
    })
    loaded, payload, loaded_adjacency = load_checkpoint(path, torch.device("cpu"))
    features = torch.ones(1, 30, 2, 8)
    with torch.no_grad():
        expected = model.eval()(features, adjacency)
        actual = loaded(features, loaded_adjacency)
    assert torch.allclose(expected, actual)
    assert payload["splits"]["seed"] == 42
    assert payload["scalers"]["depth_std_m"] == 2.0
    digest = file_sha256(path)
    script = tmp_path / "reload_checkpoint.py"
    output = tmp_path / "forward.npy"
    script.write_text(
        "import sys\n"
        "from pathlib import Path\n"
        "import numpy as np\n"
        "import torch\n"
        "from ml.checkpoint import load_checkpoint\n"
        "model, _payload, adjacency = load_checkpoint(Path(sys.argv[1]), torch.device('cpu'))\n"
        "features = torch.ones(1, 30, 2, 8)\n"
        "with torch.no_grad():\n"
        "    values = model(features, adjacency).cpu().numpy()\n"
        "np.save(sys.argv[2], values)\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        [sys.executable, str(script), str(path), str(output)],
        check=False,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    fresh = np.load(output)
    assert np.allclose(fresh, expected.detach().cpu().numpy())
    assert len(digest) == 64
