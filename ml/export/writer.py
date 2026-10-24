"""Write one schema 1.0.0 batch for the IDW baseline.

Neural methods stay all-null with status not_run. The four files are written
to a staging directory, checked, and renamed into the requested run folder
only as a complete batch. An existing run folder is left untouched.
"""
from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from ml.baseline import predict_idw, score_pairs
from ml.infer import shared_label_scores
from ml.data.sources import load_config
from ml.export.contracts import assert_completed_common_mask, run_reference_validator
from ml.export.summaries import summarise, unknown_summary

RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")
METHODS = ("idw", "gcn_lstm", "gcn_lstm_physics")


def load_export_inputs(bundle_dir: Path) -> dict:
    manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    arrays = np.load(bundle_dir / "bundle.npz", allow_pickle=False)
    return {
        "dataset_id": manifest["dataset_id"],
        "dataset_kind": manifest["dataset_kind"],
        "station_ids": [str(item) for item in arrays["station_id"].tolist()],
        "latitude": arrays["latitude"].astype(np.float64),
        "longitude": arrays["longitude"].astype(np.float64),
        "dates": [str(item) for item in arrays["date"].tolist()],
        "depth_m": arrays["depth_m"].astype(np.float64),
        "depth_valid": arrays["depth_valid"].astype(bool),
        "roles": [str(item) for item in arrays["role"].tolist()],
        "n_train": int(arrays["n_train"]),
        "n_validation": int(arrays["n_validation"]),
        "n_test": int(arrays["n_test"]),
    }


def export_baseline(
    config_path: Path,
    bundle: dict,
    run_id: str,
    output: Path,
    generated_at_utc: str | None = None,
    repo_root: Path | None = None,
) -> dict:
    if not RUN_ID.fullmatch(run_id):
        raise ValueError(f"run id is not a single path segment: {run_id}")
    if output.name != run_id:
        raise ValueError("output directory name must equal the run id")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing run folder {output}")
    config = load_config(config_path)
    stamp = generated_at_utc or datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    documents = build_batch(config, bundle, run_id, stamp)
    root = repo_root or Path(config_path).resolve().parents[2]
    attach_runtime_identity(documents, root)
    assert_completed_common_mask(documents["metrics"])
    staging = output.parent / f".staging-{run_id}"
    if staging.exists():
        raise FileExistsError(f"staging folder already exists: {staging}")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging.mkdir()
    try:
        for name, document in documents.items():
            _dump(staging / f"{name}.json", document)
        checked = run_reference_validator(staging, root)
        if checked.returncode != 0:
            raise RuntimeError(checked.stdout + checked.stderr)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    staging.rename(output)
    return documents["metrics"]["meta"]


def build_batch(config: dict, bundle: dict, run_id: str, generated_at_utc: str) -> dict:
    predictions = predict_idw(
        bundle["depth_m"],
        bundle["depth_valid"],
        np.array(bundle["roles"]),
        bundle["latitude"],
        bundle["longitude"],
        power=float(config["baseline"]["power"]),
        max_donors=int(config["baseline"]["max_donors"]),
    )
    n_train = bundle["n_train"]
    n_validation = bundle["n_validation"]
    n_days = len(bundle["dates"])
    validation = score_pairs(
        predictions,
        bundle["depth_m"],
        bundle["depth_valid"],
        np.array(bundle["roles"]),
        n_train,
        n_train + n_validation,
        "train_masked",
    )
    test = score_pairs(
        predictions,
        bundle["depth_m"],
        bundle["depth_valid"],
        np.array(bundle["roles"]),
        n_train + n_validation,
        n_days,
        "holdout",
    )
    if validation["pairs"] < 1 or test["pairs"] < 1:
        raise RuntimeError(
            "IDW has no validation or test pairs. Refusing a completed status with invented counts: "
            f"validation_pairs={validation['pairs']} test_pairs={test['pairs']}"
        )
    export_index = _history_index(bundle, int(config["export"]["history_days"]))
    export_dates = [bundle["dates"][index] for index in export_index]
    meta = _meta(config, bundle, run_id, generated_at_utc, export_dates[-1])
    wells = []
    for well, station_id in enumerate(bundle["station_ids"]):
        idw = [_number(predictions[index, well]) for index in export_index]
        observed = [
            _number(bundle["depth_m"][index, well]) if bundle["depth_valid"][index, well] else None
            for index in export_index
        ]
        idw_summary = summarise(export_dates, idw, int(config["export"]["change_days"]))
        wells.append(
            {
                "id": station_id,
                "latitude": float(bundle["latitude"][well]),
                "longitude": float(bundle["longitude"][well]),
                "role": bundle["roles"][well],
                "observations_m": observed,
                "predictions_m": {
                    "idw": idw,
                    "gcn_lstm": [None] * len(export_dates),
                    "gcn_lstm_physics": [None] * len(export_dates),
                },
                "summaries": {
                    "idw": idw_summary,
                    "gcn_lstm": unknown_summary("method_not_run"),
                    "gcn_lstm_physics": unknown_summary("method_not_run"),
                },
            }
        )
    metrics = {
        "meta": meta,
        "evaluation": {
            "test_group": "holdout",
            "same_common_mask": True,
            "split_seed": int(config["seed"]),
            "notes": (
                "IDW only. Each holdout test date and each train-masked validation date is scored once. "
                "Pairs require a finite IDW prediction and a valid label. Neural methods were not run, "
                "so they are not on this mask. Chart dates are the last exported test days and are not the metric count."
            ),
        },
        "methods": {
            "idw": {
                "status": "completed",
                "validation_mae_m": validation["mae_m"],
                "validation_pairs": validation["pairs"],
                "test_mae_m": test["mae_m"],
                "test_rmse_m": test["rmse_m"],
                "test_pairs": test["pairs"],
                "test_wells": test["wells"],
                "lambda": None,
            },
            "gcn_lstm": _not_run(),
            "gcn_lstm_physics": _not_run(),
        },
    }
    info = {
        "meta": meta,
        "code_revision": None,
        "checkpoint_sha256": None,
        "python_version": sys.version.split()[0],
        "torch_version": _torch_version(),
        "device": "cpu",
        "nodus_job_ids": [],
        "selected_positive_lambda": None,
        "physics_assumptions": [
            "Physics regulariser was not run. q was not estimated. This export is the IDW baseline only."
        ],
        "data_sources": _sources(bundle),
    }
    agent = {
        "meta": meta,
        "limitations": [
            f"Dataset {bundle['dataset_id']} is {bundle['dataset_kind']}. Synthetic results are not field accuracy.",
            "Historical reconstruction only. This is not a live sensor feed or a forecast.",
            "Default method is IDW because the neural runs have status not_run. IDW was not compared with a trained model.",
            "Priority thresholds are prototype inspection labels, not official warnings.",
            "The chart shows the exported test dates. Metric pair counts cover the full validation and test partitions.",
            "Displayed wells are the frozen cohort. Test metrics use holdout wells only.",
        ],
        "wells": [
            {
                "id": well["id"],
                "role": well["role"],
                "method": meta["default_method"],
                "latest_depth_m": well["summaries"]["idw"]["latest_depth_m"],
                "change_30d_m": well["summaries"]["idw"]["change_30d_m"],
                "priority": well["summaries"]["idw"]["priority"],
                "reason_codes": list(well["summaries"]["idw"]["reason_codes"]),
            }
            for well in wells
        ],
    }
    return {
        "predictions": {"meta": meta, "dates": export_dates, "wells": wells},
        "metrics": metrics,
        "run_info": info,
        "agent_context": agent,
    }


def export_gcn_lstm_batch(
    config_path: Path,
    bundle: dict,
    run_id: str,
    output: Path,
    neural_m: np.ndarray,
    *,
    lambda_value: float,
    checkpoint_sha256: str,
    device: str,
    generated_at_utc: str | None = None,
    repo_root: Path | None = None,
) -> dict:
    """Write IDW plus a completed lambda-0 GCN-LSTM. Physics stays not_run.

    Metric pairs are the well-dates where both completed methods have a finite
    prediction and the permitted label exists. The IDW chart series itself is
    still the full baseline. Default method is the lower of the two common-mask
    validation MAEs. A tie stays with IDW. This is not the later positive-lambda
    comparison.
    """
    if float(lambda_value) != 0.0:
        raise ValueError("this export is the lambda 0 GCN-LSTM")
    if not RUN_ID.fullmatch(run_id):
        raise ValueError(f"run id is not a single path segment: {run_id}")
    if output.name != run_id:
        raise ValueError("output directory name must equal the run id")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing run folder {output}")
    config = load_config(config_path)
    stamp = generated_at_utc or datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    documents = _documents_with_neural(config, bundle, run_id, stamp, neural_m, lambda_value, checkpoint_sha256, device)
    root = repo_root or Path(config_path).resolve().parents[2]
    attach_runtime_identity(documents, root)
    assert_completed_common_mask(documents["metrics"])
    staging = output.parent / f".staging-{run_id}"
    if staging.exists():
        raise FileExistsError(f"staging folder already exists: {staging}")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging.mkdir()
    try:
        for name, document in documents.items():
            _dump(staging / f"{name}.json", document)
        checked = run_reference_validator(staging, root)
        if checked.returncode != 0:
            raise RuntimeError(checked.stdout + checked.stderr)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    staging.rename(output)
    return documents["metrics"]["meta"]


def _documents_with_neural(config, bundle, run_id, generated_at_utc, neural_m, lambda_value, checkpoint_sha256, device) -> dict:
    idw = predict_idw(
        bundle["depth_m"],
        bundle["depth_valid"],
        np.array(bundle["roles"]),
        bundle["latitude"],
        bundle["longitude"],
        power=float(config["baseline"]["power"]),
        max_donors=int(config["baseline"]["max_donors"]),
    )
    neural = np.asarray(neural_m, dtype=np.float64)
    if neural.shape != idw.shape:
        raise ValueError("neural predictions do not match the bundle grid")
    n_train = bundle["n_train"]
    n_validation = bundle["n_validation"]
    n_days = len(bundle["dates"])
    roles = np.array(bundle["roles"])
    validation = shared_label_scores(
        idw, neural, bundle["depth_m"], bundle["depth_valid"], roles,
        n_train, n_train + n_validation, "train_masked",
    )
    test = shared_label_scores(
        idw, neural, bundle["depth_m"], bundle["depth_valid"], roles,
        n_train + n_validation, n_days, "holdout",
    )
    if validation["pairs"] < 1 or test["pairs"] < 1:
        raise RuntimeError(
            "IDW and GCN-LSTM have no shared validation or test pairs. "
            f"validation_pairs={validation['pairs']} test_pairs={test['pairs']}"
        )
    unrestricted = score_pairs(
        idw, bundle["depth_m"], bundle["depth_valid"], roles,
        n_train, n_train + n_validation, "train_masked",
    )
    if validation["left_mae_m"] < validation["right_mae_m"]:
        default_method = "idw"
    elif validation["right_mae_m"] < validation["left_mae_m"]:
        default_method = "gcn_lstm"
    else:
        default_method = "idw"
    export_index = _history_index(bundle, int(config["export"]["history_days"]))
    export_dates = [bundle["dates"][index] for index in export_index]
    meta = _meta(config, bundle, run_id, generated_at_utc, export_dates[-1])
    meta["default_method"] = default_method
    meta["caption"] = (
        f"Lambda 0 GCN-LSTM and IDW on the {bundle['dataset_kind']} dataset {bundle['dataset_id']}. "
        "Physics was not run. Default method is the lower common-mask validation MAE. "
        "This is not field accuracy."
    )
    change_days = int(config["export"]["change_days"])
    wells = []
    for well, station_id in enumerate(bundle["station_ids"]):
        idw_series = [_number(idw[index, well]) for index in export_index]
        neural_series = [_number(neural[index, well]) for index in export_index]
        observed = [
            _number(bundle["depth_m"][index, well]) if bundle["depth_valid"][index, well] else None
            for index in export_index
        ]
        wells.append({
            "id": station_id,
            "latitude": float(bundle["latitude"][well]),
            "longitude": float(bundle["longitude"][well]),
            "role": bundle["roles"][well],
            "observations_m": observed,
            "predictions_m": {
                "idw": idw_series,
                "gcn_lstm": neural_series,
                "gcn_lstm_physics": [None] * len(export_dates),
            },
            "summaries": {
                "idw": summarise(export_dates, idw_series, change_days),
                "gcn_lstm": summarise(export_dates, neural_series, change_days, "gcn_lstm_ending_window"),
                "gcn_lstm_physics": unknown_summary("method_not_run"),
            },
        })
    metrics = {
        "meta": meta,
        "evaluation": {
            "test_group": "holdout",
            "same_common_mask": True,
            "split_seed": int(config["seed"]),
            "notes": (
                "Completed methods share well-dates with a finite IDW prediction, a finite lambda-0 "
                "GCN-LSTM prediction, and a valid label. Validation uses train_masked wells. Test uses "
                "holdout wells. Each date is one pair. gcn_lstm_physics was not run and is outside this mask. "
                f"Unrestricted IDW validation MAE on train_masked labels is {unrestricted['mae_m']} m "
                f"over {unrestricted['pairs']} pairs; the IDW metric in this file is the common mask, "
                "not that unrestricted score. Chart rows are the exported test dates and are not the pair count. "
                "Positive-lambda selection is later."
            ),
        },
        "methods": {
            "idw": _scored(validation, test, "left", None),
            "gcn_lstm": _scored(validation, test, "right", float(lambda_value)),
            "gcn_lstm_physics": _not_run(),
        },
    }
    info = {
        "meta": meta,
        "code_revision": None,
        "checkpoint_sha256": checkpoint_sha256,
        "python_version": sys.version.split()[0],
        "torch_version": _torch_version(),
        "device": device,
        "nodus_job_ids": [],
        "selected_positive_lambda": None,
        "physics_assumptions": [
            "Physics regulariser was not run. q was not estimated.",
            "gcn_lstm was trained at lambda 0 with masked standardised MSE only.",
            "gcn_lstm_physics is not_run. This default is not a positive-lambda selection.",
        ],
        "data_sources": _sources(bundle) + [
            "GCN-LSTM uses the frozen eight features and previous-day visible lags.",
            "Each neural date is the last position of the window ending on that date.",
            f"Checkpoint sha256 {checkpoint_sha256}. Device {device}.",
        ],
    }
    method_key = default_method
    agent = {
        "meta": meta,
        "limitations": [
            f"Dataset {bundle['dataset_id']} is {bundle['dataset_kind']}. Synthetic results are not field accuracy.",
            "Historical reconstruction only. This is not a live sensor feed or a forecast.",
            (
                f"Default method is {default_method} by lower common-mask validation MAE "
                f"(IDW {validation['left_mae_m']} m, lambda-0 GCN-LSTM {validation['right_mae_m']} m). "
                "Physics was not run, so this is not the later positive-lambda comparison."
            ),
            "Priority thresholds are prototype inspection labels, not official warnings.",
            "The chart shows the exported test dates. Metric pair counts are the common mask, not the chart length.",
            "Displayed wells are the frozen cohort. Test metrics use holdout wells only.",
        ],
        "wells": [
            {
                "id": well["id"],
                "role": well["role"],
                "method": method_key,
                "latest_depth_m": well["summaries"][method_key]["latest_depth_m"],
                "change_30d_m": well["summaries"][method_key]["change_30d_m"],
                "priority": well["summaries"][method_key]["priority"],
                "reason_codes": list(well["summaries"][method_key]["reason_codes"]),
            }
            for well in wells
        ],
    }
    return {
        "predictions": {"meta": meta, "dates": export_dates, "wells": wells},
        "metrics": metrics,
        "run_info": info,
        "agent_context": agent,
    }


def _scored(validation: dict, test: dict, side: str, lambda_value: float | None) -> dict:
    return {
        "status": "completed",
        "validation_mae_m": validation[f"{side}_mae_m"],
        "validation_pairs": validation["pairs"],
        "test_mae_m": test[f"{side}_mae_m"],
        "test_rmse_m": test[f"{side}_rmse_m"],
        "test_pairs": test["pairs"],
        "test_wells": test["wells"],
        "lambda": lambda_value,
    }


def attach_runtime_identity(documents: dict, repo_root: Path) -> dict:
    documents["run_info"]["code_revision"] = _code_revision(repo_root)
    documents["run_info"]["python_version"] = sys.version.split()[0]
    documents["run_info"]["torch_version"] = _torch_version()
    return documents


def _history_index(bundle: dict, history_days: int) -> list[int]:
    test_start = bundle["n_train"] + bundle["n_validation"]
    test_days = list(range(test_start, len(bundle["dates"])))
    if len(test_days) < 2:
        raise ValueError("test partition is too short to export")
    chosen = test_days[-history_days:]
    return chosen


def _meta(config: dict, bundle: dict, run_id: str, generated_at_utc: str, as_of: str) -> dict:
    kind = bundle["dataset_kind"]
    return {
        "schema_version": config["schema_version"],
        "run_id": run_id,
        "dataset_id": bundle["dataset_id"],
        "dataset_kind": kind,
        "artifact_kind": "model_output",
        "generated_at_utc": generated_at_utc,
        "as_of_date": as_of,
        "default_method": "idw",
        "depth_unit": "m_below_ground",
        "caption": (
            f"IDW baseline on the {kind} dataset {bundle['dataset_id']}. "
            "Neural methods were not run. This is not field accuracy."
        ),
    }


def _not_run() -> dict:
    return {
        "status": "not_run",
        "validation_mae_m": None,
        "validation_pairs": 0,
        "test_mae_m": None,
        "test_rmse_m": None,
        "test_pairs": 0,
        "test_wells": 0,
        "lambda": None,
    }


def _sources(bundle: dict) -> list[str]:
    sources = [
        f"{bundle['dataset_kind']} bundle {bundle['dataset_id']}",
        "IDW uses previous-day visible depths only, power 2, at most 6 donors.",
    ]
    if bundle["dataset_kind"] == "synthetic":
        sources.append("Fictional wells. NASA POWER weather forced the synthetic generator and is not a well gauge.")
    return sources


def _number(value: float) -> float | None:
    if value is None or not math.isfinite(float(value)):
        return None
    return float(value)


def _dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _torch_version() -> str:
    import torch

    return torch.__version__


def _code_revision(root: Path) -> str:
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return sha + ("+dirty" if dirty.strip() else "")
