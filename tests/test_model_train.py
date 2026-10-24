"""GCN-LSTM axes, graph influence, masked loss and one finite step."""
import numpy as np
import pytest
import torch
from torch import nn

from ml.losses import EmptySupervision, masked_standardised_mse, supervision_mask
from ml.model import GCNLSTM
from ml.train import set_seed


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
            "external_dropout": 0.1,
            "output": "depth_sequence_B_T_N",
        },
    }


def _positive_model():
    set_seed(42)
    model = GCNLSTM(_config())
    model.eval()
    with torch.no_grad():
        nn.init.constant_(model.gcn.weight, 0.05)
        nn.init.zeros_(model.gcn.bias)
        nn.init.constant_(model.head.weight, 0.05)
        nn.init.zeros_(model.head.bias)
    return model


def test_output_shape_and_well_permutation_stay_aligned():
    model = _positive_model()
    features = torch.rand(2, 30, 4, 8)
    adjacency = torch.tensor([
        [0.5, 0.5, 0.0, 0.0],
        [0.5, 0.5, 0.0, 0.0],
        [0.0, 0.0, 0.7, 0.3],
        [0.0, 0.0, 0.3, 0.7],
    ])
    output = model(features, adjacency)
    assert output.shape == (2, 30, 4)
    assert model.lstm.bidirectional is False
    assert model.lstm.dropout == 0.0
    permutation = torch.tensor([2, 0, 3, 1])
    permuted_features = features[:, :, permutation, :]
    permuted_adjacency = adjacency[permutation][:, permutation]
    permuted_output = model(permuted_features, permuted_adjacency)
    assert torch.allclose(permuted_output, output[:, :, permutation], atol=1e-5)


def test_neighbour_change_affects_output_and_gradient_reaches_that_well():
    model = _positive_model()
    features = torch.rand(1, 30, 3, 8) + 0.2
    identity = torch.eye(3)
    connected = torch.tensor([
        [0.5, 0.5, 0.0],
        [0.5, 0.5, 0.0],
        [0.0, 0.0, 1.0],
    ])
    with torch.no_grad():
        alone = model(features, identity)
        mixed = model(features, connected)
    assert not torch.allclose(alone, mixed)
    features = features.clone().requires_grad_(True)
    prediction = model(features, connected)
    prediction[0, -1, 0].backward()
    assert torch.isfinite(features.grad).all()
    assert torch.isfinite(model.gcn.weight.grad).all()
    assert float(features.grad[0, :, 1, :].abs().sum()) > 0.0
    assert float(model.gcn.weight.grad.abs().sum()) > 0.0


def test_train_and_eval_dropout_modes_differ_and_one_step_stays_finite():
    set_seed(42)
    model = GCNLSTM(_config())
    features = torch.rand(2, 30, 4, 8)
    adjacency = torch.eye(4)
    model.train()
    first = model(features, adjacency)
    second = model(features, adjacency)
    assert not torch.allclose(first, second)
    model.eval()
    with torch.no_grad():
        left = model(features, adjacency)
        right = model(features, adjacency)
    assert torch.allclose(left, right)
    model.train()
    target = torch.zeros(2, 30, 4)
    mask = torch.zeros(2, 30, 4, dtype=torch.bool)
    mask[:, 7:, :3] = True
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.0001)
    optimizer.zero_grad()
    loss = masked_standardised_mse(model(features, adjacency), target, mask)
    loss.backward()
    grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()
    assert math_finite(loss) and math_finite(grad_norm)


def test_loss_ignores_startup_positions_holdout_and_empty_masks():
    prediction = torch.zeros(1, 30, 2)
    target = torch.zeros(1, 30, 2)
    mask = torch.ones(1, 30, 2, dtype=torch.bool)
    mask[:, :7, :] = False
    target[0, 0, 0] = 5.0
    assert float(masked_standardised_mse(prediction, target, mask)) == 0.0
    target[0, 7, 0] = 2.0
    assert float(masked_standardised_mse(prediction, target, mask)) == pytest.approx(4.0 / int(mask.sum()))
    roles = np.array(["visible", "holdout"])
    valid = np.ones((1, 30, 2), dtype=bool)
    built = supervision_mask(valid, roles, ignore_first=7)
    assert built[:, :, 1].sum() == 0
    assert built[:, :7, :].sum() == 0
    with pytest.raises(EmptySupervision):
        masked_standardised_mse(prediction, target, torch.zeros_like(mask))


def test_same_seed_builds_the_same_initial_weights():
    set_seed(42)
    first = GCNLSTM(_config()).gcn.weight.detach().clone()
    set_seed(42)
    second = GCNLSTM(_config()).gcn.weight.detach().clone()
    assert torch.equal(first, second)


def math_finite(value) -> bool:
    number = float(value.detach() if hasattr(value, "detach") else value)
    return number == number and number not in (float("inf"), float("-inf"))
