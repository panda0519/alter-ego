"""One dense GCN layer and one unidirectional LSTM.

Input is B, T, N, 8. The graph mixes wells before a linear map 8 -> 32, ReLU,
and the external dropout. The LSTM sees each well's own 32-wide sequence:
B, T, N, 32 is permuted to B, N, T, 32 and reshaped to (B*N), T, 32. The head
maps 32 -> 1 and restores B, T, N. Internal LSTM dropout stays 0 because there
is one layer. The LSTM is not bidirectional.
"""
from __future__ import annotations

import torch
from torch import nn


class GCNLSTM(nn.Module):
    def __init__(self, config: dict):
        super().__init__()
        model = config["model"]
        if int(model["gcn_layers"]) != 1 or int(model["lstm_layers"]) != 1:
            raise ValueError("this phase builds one GCN layer and one LSTM layer")
        if int(model["gcn_hidden"]) != 32 or int(model["lstm_hidden"]) != 32:
            raise ValueError("hidden width must be 32")
        if model["bidirectional"] is not False:
            raise ValueError("LSTM must be unidirectional")
        if float(model["internal_lstm_dropout"]) != 0.0:
            raise ValueError("a one-layer LSTM uses internal dropout 0")
        if int(config["features"]["count"]) != 8:
            raise ValueError("the GCN input width is the eight frozen features")
        self.gcn = nn.Linear(8, 32)
        self.activation = nn.ReLU()
        self.dropout = nn.Dropout(float(model["external_dropout"]))
        self.lstm = nn.LSTM(
            input_size=32,
            hidden_size=32,
            num_layers=1,
            batch_first=True,
            dropout=0.0,
            bidirectional=False,
        )
        self.head = nn.Linear(32, 1)

    def forward(self, features: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        if features.ndim != 4 or features.shape[-1] != 8:
            raise ValueError("features must have shape B, T, N, 8")
        if adjacency.ndim != 2 or adjacency.shape[0] != features.shape[2]:
            raise ValueError("adjacency does not match the well axis")
        adjacency = adjacency.to(dtype=features.dtype)
        mixed = torch.einsum("ij,btjf->btif", adjacency, features)
        hidden = self.dropout(self.activation(self.gcn(mixed)))
        batch, time, wells, channels = hidden.shape
        sequence = hidden.permute(0, 2, 1, 3).contiguous().reshape(batch * wells, time, channels)
        temporal, _ = self.lstm(sequence)
        depth = self.head(temporal).reshape(batch, wells, time).permute(0, 2, 1).contiguous()
        if depth.shape != (batch, time, wells):
            raise RuntimeError("restored prediction axes are not B, T, N")
        return depth
