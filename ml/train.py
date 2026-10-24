"""Lambda-0 training on permitted training labels.

AdamW uses the configured learning rate, weight decay, batch size and gradient
clip. Windows stay in stored order. Validation MAE is metres at train-masked
wells, one score per date from the window that ends on that date. Holdout
labels are not read for the loss or the checkpoint choice. A smoke run is one
epoch and is tagged so it cannot be used as the comparative result.
"""
from __future__ import annotations

import json
import math
import random
import subprocess
import time
from pathlib import Path

import numpy as np
import torch

from ml.checkpoint import file_sha256, load_checkpoint, save_checkpoint
from ml.data.sources import load_config
from ml.features import (
    WINDOW,
    assert_windows_inside,
    finite_feature_values,
    load_arrays,
    standardised_depth,
    slice_windows,
)
from ml.graph import build_graph
from ml.infer import predict_ending_windows
from ml.losses import EmptySupervision, masked_standardised_mse, supervision_mask
from ml.model import GCNLSTM


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def resolve_device() -> torch.device:
    if not torch.cuda.is_available():
        return torch.device("cpu")
    try:
        torch.zeros(1, device="cuda")
    except Exception:
        return torch.device("cpu")
    return torch.device("cuda")


def device_label(device: torch.device) -> str:
    if device.type != "cuda":
        return "cpu"
    name = torch.cuda.get_device_name(device)
    return f"cuda:{name}"


def train_lambda0(
    config_path: Path,
    bundle_dir: Path,
    run_dir: Path,
    lambda_target: float,
    smoke: bool = False,
) -> dict:
    if float(lambda_target) != 0.0:
        raise ValueError("this phase trains lambda 0 only; positive lambda belongs to the physics phase")
    run_dir = Path(run_dir)
    if (run_dir / "checkpoint.pt").exists():
        raise FileExistsError(f"refusing to overwrite checkpoint {run_dir / 'checkpoint.pt'}")
    config = load_config(config_path)
    if config["training"]["optimiser"] != "AdamW":
        raise ValueError("optimiser must be AdamW")
    if config["training"]["shuffle_windows"] is not False:
        raise ValueError("windows are not shuffled")
    bundle = load_arrays(bundle_dir)
    graph = build_graph(
        bundle["latitude"],
        bundle["longitude"],
        bundle["station_ids"],
        neighbours=int(config["graph"]["neighbours"]),
    )
    if graph["station_ids"] != bundle["station_ids"]:
        raise RuntimeError("graph station order left the bundle order")
    n_train = bundle["n_train"]
    n_validation = bundle["n_validation"]
    assert_windows_inside(bundle["train_window_ends"], 0, n_train, int(config["data"]["window"]))
    assert_windows_inside(
        bundle["validation_window_ends"],
        n_train,
        n_train + n_validation,
        int(config["data"]["window"]),
    )
    assert_windows_inside(
        bundle["test_window_ends"],
        n_train + n_validation,
        len(bundle["dates"]),
        int(config["data"]["window"]),
    )
    seed = int(config["seed"])
    set_seed(seed)
    device = resolve_device()
    model = GCNLSTM(config).to(device)
    adjacency = torch.tensor(graph["adjacency"], dtype=torch.float32, device=device)
    training = config["training"]
    if int(config["data"]["window"]) != WINDOW:
        raise ValueError("training windows are 30 days")
    max_epochs = 1 if smoke else int(training["max_epochs"])
    batch_size = int(training["batch_size"])
    ignore_first = int(training["ignore_first_sequence_positions"])
    features = finite_feature_values(bundle["features"])
    targets = standardised_depth(
        bundle["depth_m"],
        bundle["depth_valid"],
        bundle["depth_mean_m"],
        bundle["depth_std_m"],
    )
    train_ends = bundle["train_window_ends"]
    windows = slice_windows(features, train_ends, WINDOW)
    target_windows = slice_windows(targets[:, :, None], train_ends, WINDOW)[:, :, :, 0]
    valid_windows = slice_windows(bundle["depth_valid"][:, :, None], train_ends, WINDOW)[:, :, :, 0]
    mask = supervision_mask(valid_windows, bundle["roles"], ignore_first)
    if int(mask[:, :, bundle["roles"] == "holdout"].sum()) != 0:
        raise RuntimeError("holdout labels entered the training mask")
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(training["learning_rate"]),
        weight_decay=float(training["weight_decay"]),
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    history_path = run_dir / "history.jsonl"
    best_mae = None
    best_epoch = None
    since_best = 0
    started = time.perf_counter()
    epochs_ran = 0
    stopped_early = False
    first_batch_shape = list(windows[:1].shape)
    print(json.dumps({
        "event": "first_batch",
        "shape_B_T_N_F": first_batch_shape,
        "feature_order": list(bundle["feature_names"]),
        "smoke": smoke,
        "device": device_label(device),
    }, allow_nan=False))
    for epoch in range(1, max_epochs + 1):
        model.train()
        squared = 0.0
        supervised = 0
        skipped = 0
        for start in range(0, len(train_ends), batch_size):
            stop = min(start + batch_size, len(train_ends))
            inputs = torch.from_numpy(np.ascontiguousarray(windows[start:stop])).to(device)
            target = torch.from_numpy(np.ascontiguousarray(target_windows[start:stop])).to(device)
            batch_mask = torch.from_numpy(np.ascontiguousarray(mask[start:stop])).to(device)
            optimizer.zero_grad(set_to_none=True)
            prediction = model(inputs, adjacency)
            try:
                loss = masked_standardised_mse(prediction, target, batch_mask)
            except EmptySupervision:
                skipped += 1
                continue
            loss.backward()
            grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), float(training["grad_clip_norm"]))
            if not math.isfinite(float(loss.detach().cpu())) or not math.isfinite(float(grad_norm)):
                raise RuntimeError(f"non-finite training value at epoch {epoch}")
            optimizer.step()
            count = int(batch_mask.sum().item())
            squared += float(loss.detach().cpu()) * count
            supervised += count
        if supervised < 1:
            raise RuntimeError("epoch had no permitted training targets")
        validation_mae = _validation_mae(model, features, adjacency, bundle, device, batch_size)
        if not math.isfinite(validation_mae):
            raise RuntimeError(f"non-finite validation MAE at epoch {epoch}")
        record = {
            "epoch": epoch,
            "data_loss": squared / supervised,
            "lambda": 0.0,
            "physics_loss": None,
            "validation_mae_m": validation_mae,
            "supervised_values": supervised,
            "skipped_empty_batches": skipped,
            "finite": True,
        }
        with history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, allow_nan=False) + "\n")
        epochs_ran = epoch
        if best_mae is None or validation_mae < best_mae:
            best_mae = validation_mae
            best_epoch = epoch
            since_best = 0
            _write_checkpoint(run_dir / "checkpoint.pt", model, adjacency, config, bundle, graph, epoch, validation_mae, smoke, device)
        else:
            since_best += 1
            if not smoke and since_best >= int(training["early_stopping_patience"]):
                stopped_early = True
                break
    elapsed = time.perf_counter() - started
    digest = file_sha256(run_dir / "checkpoint.pt")
    manifest = {
        "run_kind": "lambda0_smoke" if smoke else "lambda0",
        "smoke": smoke,
        "evidence_role": "development_smoke" if smoke else "lambda0_checkpoint",
        "seed": seed,
        "device": device_label(device),
        "python_version": _python_version(),
        "torch_version": torch.__version__,
        "epochs_ran": epochs_ran,
        "best_epoch": best_epoch,
        "best_validation_mae_m": best_mae,
        "stopped_early": stopped_early,
        "elapsed_seconds": elapsed,
        "lambda_target": 0.0,
        "physics": "not_run",
        "dataset_id": bundle["dataset_id"],
        "dataset_kind": bundle["dataset_kind"],
        "code_revision": _code_revision(Path(config_path).resolve().parents[2]),
        "checkpoint_sha256": digest,
        "window_counts": {
            "train": int(len(bundle["train_window_ends"])),
            "validation": int(len(bundle["validation_window_ends"])),
            "test": int(len(bundle["test_window_ends"])),
        },
        "nonfinite_feature_values_filled_with_zero": int((~np.isfinite(bundle["features"])).sum()),
        "field_accuracy": False,
    }
    (run_dir / "train_manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return manifest


def reload_and_predict(run_dir: Path, bundle_dir: Path) -> tuple[dict, dict, np.ndarray]:
    bundle = load_arrays(bundle_dir)
    device = resolve_device()
    model, payload, adjacency = load_checkpoint(Path(run_dir) / "checkpoint.pt", device)
    if payload["smoke"] is True:
        raise RuntimeError("refusing to export predictions from a smoke checkpoint")
    if payload["station_ids"] != bundle["station_ids"]:
        raise RuntimeError("checkpoint station order does not match the bundle")
    features = finite_feature_values(bundle["features"])
    ends = np.concatenate([
        bundle["train_window_ends"],
        bundle["validation_window_ends"],
        bundle["test_window_ends"],
    ])
    predictions = predict_ending_windows(
        model,
        features,
        adjacency,
        ends,
        bundle["depth_mean_m"],
        bundle["depth_std_m"],
        device,
        batch_size=int(payload["config"]["training"]["batch_size"]),
    )
    return bundle, payload, predictions


def _validation_mae(model, features, adjacency, bundle, device, batch_size: int) -> float:
    predictions = predict_ending_windows(
        model,
        features,
        adjacency,
        bundle["validation_window_ends"],
        bundle["depth_mean_m"],
        bundle["depth_std_m"],
        device,
        batch_size=batch_size,
    )
    start = bundle["n_train"]
    stop = start + bundle["n_validation"]
    selected = bundle["roles"] == "train_masked"
    usable = (
        selected.reshape(1, -1)
        & bundle["depth_valid"][start:stop]
        & np.isfinite(bundle["depth_m"][start:stop])
        & np.isfinite(predictions[start:stop])
    )
    if int(usable.sum()) < 1:
        raise RuntimeError("validation has no train-masked pairs")
    errors = np.abs(predictions[start:stop][usable] - bundle["depth_m"][start:stop][usable])
    return float(np.mean(errors))


def _write_checkpoint(path, model, adjacency, config, bundle, graph, epoch: int, validation_mae: float, smoke: bool, device) -> None:
    save_checkpoint(path, {
        "model_state": {name: value.detach().cpu() for name, value in model.state_dict().items()},
        "adjacency": adjacency.detach().cpu(),
        "station_ids": list(bundle["station_ids"]),
        "config": config,
        "scalers": bundle["scalers"],
        "splits": {
            "roles": [str(role) for role in bundle["roles"]],
            "n_train": bundle["n_train"],
            "n_validation": bundle["n_validation"],
            "n_test": bundle["n_test"],
            "train_window_ends": [int(item) for item in bundle["train_window_ends"]],
            "validation_window_ends": [int(item) for item in bundle["validation_window_ends"]],
            "test_window_ends": [int(item) for item in bundle["test_window_ends"]],
            "seed": int(config["seed"]),
        },
        "feature_names": list(bundle["feature_names"]),
        "sigma_m": graph["sigma_m"],
        "code_revision": _code_revision(Path.cwd()),
        "epoch": int(epoch),
        "validation_mae_m": float(validation_mae),
        "lambda_target": 0.0,
        "smoke": bool(smoke),
        "device": device_label(device),
    })


def _python_version() -> str:
    import sys

    return sys.version.split()[0]


def _code_revision(root: Path) -> str:
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return sha + ("+dirty" if dirty.strip() else "")
