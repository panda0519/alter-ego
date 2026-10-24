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
