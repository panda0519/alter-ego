"""Validation selection and one holdout score.

Positive-lambda checkpoints are ranked by the validation MAE stored with the
checkpoint. A tie keeps the smaller lambda target. That choice does not look
at holdout labels. If the selected checkpoint did not apply a positive lambda,
or its weights match the lambda-0 checkpoint, it is not exported as a completed
physics model. The schema has no status for that case.

The exported default is the completed method with the lower common-mask
validation MAE. Holdout errors are computed after that choice and do not
change it. Each date is the last position of the window that ends on it.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import torch

from ml.baseline import predict_idw
from ml.checkpoint import file_sha256, load_checkpoint
from ml.data.sources import load_config
from ml.export.writer import export_final_batch, load_export_inputs
from ml.features import load_arrays
from ml.infer import predict_ending_windows
from ml.physics import estimate_q, physics_constants, seven_day_change_scale_m
from ml.train import device_label, resolve_device

METHOD_ORDER = ("idw", "gcn_lstm", "gcn_lstm_physics")
PREDICTION_ATOL_M = 1e-4
SCHEMA_GAP = (
    "Metrics status is only not_run, completed, or failed. A positive-lambda run whose "
    "selected checkpoint is still the lambda-0 warmup is none of those. This export leaves "
    "gcn_lstm_physics as not_run instead of labelling those weights as a completed physics model."
)


def select_positive_checkpoint(candidates: list[dict]) -> dict:
    if not candidates:
        raise ValueError("no positive-lambda checkpoint was supplied")
    ordered = sorted(candidates, key=lambda item: (float(item["validation_mae_m"]), float(item["lambda_target"])))
    winner = ordered[0]
    tied = [
        item for item in candidates
        if float(item["validation_mae_m"]) == float(winner["validation_mae_m"])
    ]
    used_positive = bool(winner["used_positive_lambda"])
    return {
        "rule": "lowest checkpoint validation MAE, then smaller lambda target",
        "selected_run": winner["run"],
        "selected_lambda_target": float(winner["lambda_target"]),
        "validation_mae_m": float(winner["validation_mae_m"]),
        "used_positive_lambda": used_positive,
        "tie": len(tied) > 1,
        "tied_lambda_targets": [float(item["lambda_target"]) for item in tied],
        "export_physics": used_positive,
    }


def choose_default(validation_mae_m: dict[str, float]) -> str:
    if not validation_mae_m:
        raise ValueError("no completed method has a validation MAE")
    unknown = set(validation_mae_m) - set(METHOD_ORDER)
    if unknown:
        raise ValueError(f"unknown method {sorted(unknown)}")
    return min(validation_mae_m, key=lambda name: (float(validation_mae_m[name]), METHOD_ORDER.index(name)))


def score_common(
    predictions: dict[str, np.ndarray],
    depth_m: np.ndarray,
    depth_valid: np.ndarray,
    roles: np.ndarray,
    start: int,
    stop: int,
    role: str,
) -> dict:
    if not predictions:
        raise RuntimeError("common mask is empty; refusing to invent errors")
    selected = np.asarray(roles) == role
    depth = depth_m[start:stop]
    usable = selected.reshape(1, -1) & depth_valid[start:stop] & np.isfinite(depth)
    for values in predictions.values():
        usable = usable & np.isfinite(values[start:stop])
    pairs = int(usable.sum())
    wells = int(np.any(usable, axis=0).sum()) if usable.size else 0
    if pairs < 1 or wells < 1:
        raise RuntimeError("common mask is empty; refusing to invent errors")
    if pairs < wells:
        raise RuntimeError("completed pairs are fewer than contributing wells")
    scored = {"pairs": pairs, "wells": wells, "methods": {}}
    for name, values in predictions.items():
        error = values[start:stop][usable] - depth[usable]
        scored["methods"][name] = {
            "mae_m": float(np.mean(np.abs(error))),
            "rmse_m": float(np.sqrt(np.mean(np.square(error)))),
        }
    return scored


def max_abs_difference(left: np.ndarray, right: np.ndarray) -> float:
    if left.shape != right.shape:
        raise ValueError("prediction grids do not match")
    missing = np.isnan(left) ^ np.isnan(right)
    if np.any(missing):
        raise ValueError("prediction grids do not share the same missing dates")
    present = ~np.isnan(left)
    if not np.any(present):
        return 0.0
    return float(np.max(np.abs(left[present] - right[present])))


def evaluate(config_path: Path, bundle_dir: Path, run_dirs: list[Path], output: Path) -> dict:
    output = Path(output)
    if (output / "evaluation.json").exists():
        raise FileExistsError(f"refusing to overwrite {output / 'evaluation.json'}")
    config = load_config(config_path)
    bundle = load_arrays(bundle_dir)
    records = [_run_record(Path(path), bundle["dataset_id"]) for path in run_dirs]
    lambda0 = _require_lambda0(records)
    positive = [record for record in records if record["lambda_target"] > 0.0]
    selection = select_positive_checkpoint(positive)
    weights_match = _weights_match(Path(lambda0["run"]) / "checkpoint.pt", Path(selection["selected_run"]) / "checkpoint.pt")
    export_physics = bool(selection["export_physics"]) and not weights_match
    if not export_physics:
        selection = {**selection, "export_physics": False, "weights_match_lambda0": weights_match}
    else:
        selection = {**selection, "weights_match_lambda0": False}
    calibration = _calibration(bundle, config)
    if calibration["q_status"] != "frozen_training_estimate" or calibration["q_m_per_day"] is None:
        raise RuntimeError("physics calibration is not estimable from permitted training pairs")
    for record in positive:
        saved_q = record["q_m_per_day"]
        if saved_q is not None and abs(float(saved_q) - float(calibration["q_m_per_day"])) > 1e-12:
            raise RuntimeError(f"{record['run']} saved a different q than the bundle")
    device = resolve_device()
    neural = _infer(Path(lambda0["run"]), bundle, device)
    physics = None
    completed = {"idw": _idw(config, bundle), "gcn_lstm": neural}
    if export_physics:
        physics = _infer(Path(selection["selected_run"]), bundle, device)
        completed["gcn_lstm_physics"] = physics
    n_train = bundle["n_train"]
    n_validation = bundle["n_validation"]
    test_start = n_train + n_validation
    validation = score_common(
        completed, bundle["depth_m"], bundle["depth_valid"], bundle["roles"],
        n_train, test_start, "train_masked",
    )
    default_method = choose_default({name: validation["methods"][name]["mae_m"] for name in completed})
    test = score_common(
        completed, bundle["depth_m"], bundle["depth_valid"], bundle["roles"],
        test_start, len(bundle["dates"]), "holdout",
    )
    possible = int((bundle["depth_valid"][test_start:] & (bundle["roles"] == "holdout").reshape(1, -1)).sum())
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output / "predictions.npz", gcn_lstm=neural, **({} if physics is None else {"gcn_lstm_physics": physics}))
    document = {
        "dataset_id": bundle["dataset_id"],
        "dataset_kind": bundle["dataset_kind"],
        "seed": int(config["seed"]),
        "device": device_label(device),
        "prediction_atol_m": PREDICTION_ATOL_M,
        "lambda0_run": lambda0["run"],
        "lambda0_checkpoint_sha256": lambda0["checkpoint_sha256"],
        "positive_lambda_selection": selection,
        "schema_gap": None if export_physics else SCHEMA_GAP,
        "gcn_lstm_physics_status": "completed" if export_physics else "not_run",
        "selected_positive_lambda": selection["selected_lambda_target"] if export_physics else None,
        "calibration": calibration,
        "default_method": default_method,
        "default_locked_before_test": True,
        "validation": validation,
        "test": test,
        "holdout_valid_labels": possible,
        "displayed_wells": len(bundle["station_ids"]),
        "station_ids": bundle["station_ids"],
        "runs": records,
        "field_accuracy": False,
    }
    (output / "evaluation.json").write_text(json.dumps(document, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return document


def require_same_device(saved_device: str, current_device: str) -> None:
    if saved_device != current_device:
        raise RuntimeError(f"refusing to mix {current_device} inference with evaluation device {saved_device}")


def publish(config_path: Path, bundle_dir: Path, evaluation_dir: Path, run_id: str, output: Path) -> dict:
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing run folder {output}")
    evaluation_dir = Path(evaluation_dir)
    evaluation = json.loads((evaluation_dir / "evaluation.json").read_text(encoding="utf-8"))
    status = evaluation["gcn_lstm_physics_status"]
    if status not in {"not_run", "completed"}:
        raise RuntimeError(f"unsupported physics status {status}")
    saved = np.load(evaluation_dir / "predictions.npz")
    neural, device = reload_neural(Path(evaluation["lambda0_run"]), bundle_dir)
    require_same_device(evaluation["device"], device)
    difference = max_abs_difference(saved["gcn_lstm"], neural)
    if difference > float(evaluation["prediction_atol_m"]):
        raise RuntimeError(f"reloaded predictions differ by {difference} m")
    physics = None
    if status == "completed":
        selection = evaluation["positive_lambda_selection"]
        lam = evaluation.get("selected_positive_lambda")
        if not selection.get("used_positive_lambda") or selection.get("weights_match_lambda0"):
            raise RuntimeError("refusing to export a warmup or lambda-0 checkpoint as completed physics")
        if lam is None or not (math.isclose(float(lam), 0.1) or math.isclose(float(lam), 1.0)):
            raise RuntimeError("completed physics requires lambda 0.1 or 1.0")
        physics, physics_device = reload_neural(Path(selection["selected_run"]), bundle_dir)
        require_same_device(evaluation["device"], physics_device)
        physics_difference = max_abs_difference(saved["gcn_lstm_physics"], physics)
        if physics_difference > float(evaluation["prediction_atol_m"]):
            raise RuntimeError(f"reloaded physics predictions differ by {physics_difference} m")
        difference = max(difference, physics_difference)
    config = load_config(config_path)
    bundle = load_arrays(bundle_dir)
    completed = {"idw": _idw(config, bundle), "gcn_lstm": neural}
    if physics is not None:
        completed["gcn_lstm_physics"] = physics
    n_train = bundle["n_train"]
    test_start = n_train + bundle["n_validation"]
    validation = score_common(
        completed, bundle["depth_m"], bundle["depth_valid"], bundle["roles"],
        n_train, test_start, "train_masked",
    )
    test = score_common(
        completed, bundle["depth_m"], bundle["depth_valid"], bundle["roles"],
        test_start, len(bundle["dates"]), "holdout",
    )
    fresh_default = choose_default({name: validation["methods"][name]["mae_m"] for name in completed})
    if fresh_default != evaluation["default_method"]:
        raise RuntimeError("reloaded validation MAE changed the default method")
    _close_enough(validation, evaluation["validation"])
    _close_enough(test, evaluation["test"])
    meta = export_final_batch(
        config_path,
        load_export_inputs(bundle_dir),
        run_id,
        Path(output),
        neural,
        evaluation,
        validation=validation,
        test=test,
        device=device,
        physics_m=physics,
    )
    (evaluation_dir / "reload_check.json").write_text(json.dumps({
        "max_abs_difference_m": difference,
        "device": device,
        "default_method": fresh_default,
        "prediction_atol_m": evaluation["prediction_atol_m"],
    }, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return meta


def _close_enough(fresh: dict, locked: dict) -> None:
    if fresh["pairs"] != locked["pairs"] or fresh["wells"] != locked["wells"]:
        raise RuntimeError("reloaded common-mask counts changed")
    for name, scores in fresh["methods"].items():
        for key in ("mae_m", "rmse_m"):
            if abs(scores[key] - locked["methods"][name][key]) > PREDICTION_ATOL_M:
                raise RuntimeError(f"reloaded {name} {key} moved")


def reload_neural(run_dir: Path, bundle_dir: Path) -> tuple[np.ndarray, str]:
    bundle = load_arrays(bundle_dir)
    device = resolve_device()
    return _infer(Path(run_dir), bundle, device), device_label(device)


def _run_record(run_dir: Path, dataset_id: str) -> dict:
    manifest = json.loads((run_dir / "train_manifest.json").read_text(encoding="utf-8"))
    if manifest["dataset_id"] != dataset_id:
        raise ValueError(f"{run_dir} belongs to a different dataset")
    if manifest.get("smoke") is True:
        raise ValueError(f"{run_dir} is a smoke run")
    digest = file_sha256(run_dir / "checkpoint.pt")
    if digest != manifest["checkpoint_sha256"]:
        raise ValueError(f"{run_dir} checkpoint does not match its manifest")
    used = manifest.get("selected_checkpoint_used_positive_lambda")
    if used is None:
        used = float(manifest.get("best_epoch_lambda") or 0.0) > 0.0
    return {
        "run": str(run_dir),
        "lambda_target": float(manifest["lambda_target"]),
        "validation_mae_m": float(manifest["best_validation_mae_m"]),
        "best_epoch": int(manifest["best_epoch"]),
        "best_epoch_lambda": manifest.get("best_epoch_lambda"),
        "used_positive_lambda": bool(used),
        "checkpoint_sha256": digest,
        "q_m_per_day": manifest.get("q_m_per_day"),
        "q_eligible_wells": manifest.get("q_eligible_wells"),
        "residual_scale_m": manifest.get("residual_scale_m"),
    }


def _require_lambda0(records: list[dict]) -> dict:
    matches = [record for record in records if record["lambda_target"] == 0.0]
    if len(matches) != 1:
        raise ValueError("evaluation needs exactly one lambda-0 run")
    return matches[0]


def _weights_match(left: Path, right: Path) -> bool:
    if left.resolve() == right.resolve():
        return True
    first = torch.load(left, map_location="cpu", weights_only=False)["model_state"]
    second = torch.load(right, map_location="cpu", weights_only=False)["model_state"]
    return first.keys() == second.keys() and all(torch.equal(first[name], second[name]) for name in first)


def _calibration(bundle: dict, config: dict) -> dict:
    constants = physics_constants(config)
    estimated = estimate_q(
        bundle["depth_m"], bundle["depth_valid"], bundle["precip_m_per_day"], bundle["et0_m_per_day"],
        bundle["weather_valid"], bundle["roles"], bundle["n_train"],
        constants["specific_yield"], constants["alpha"], constants["beta"], constants["min_pairs"],
    )
    scale = seven_day_change_scale_m(
        bundle["depth_m"], bundle["depth_valid"], bundle["roles"], bundle["n_train"],
        constants["residual_days"], constants["minimum_scale_m"],
    )
    return {
        "q_m_per_day": estimated["q_m_per_day"],
        "unclipped_median_m_per_day": estimated.get("unclipped_median_m_per_day"),
        "eligible_wells": estimated["eligible_wells"],
        "q_status": estimated["status"],
        "scale_m": scale["scale_m"],
        "scale_status": scale["status"],
    }


def _infer(run_dir: Path, bundle: dict, device: torch.device) -> np.ndarray:
    model, payload, adjacency = load_checkpoint(run_dir / "checkpoint.pt", device)
    if payload.get("smoke") is True:
        raise RuntimeError("refusing to evaluate a smoke checkpoint")
    if list(payload["station_ids"]) != bundle["station_ids"]:
        raise RuntimeError("checkpoint station order does not match the bundle")
    ends = np.concatenate([
        bundle["train_window_ends"],
        bundle["validation_window_ends"],
        bundle["test_window_ends"],
    ])
    return predict_ending_windows(
        model,
        bundle["features"],
        adjacency,
        ends,
        bundle["depth_mean_m"],
        bundle["depth_std_m"],
        device,
        batch_size=int(payload["config"]["training"]["batch_size"]),
    )


def _idw(config: dict, bundle: dict) -> np.ndarray:
    return predict_idw(
        bundle["depth_m"],
        bundle["depth_valid"],
        bundle["roles"],
        bundle["latitude"],
        bundle["longitude"],
        power=float(config["baseline"]["power"]),
        max_donors=int(config["baseline"]["max_donors"]),
    )
