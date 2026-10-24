"""Assemble and store one private preparation bundle."""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from ml.data.cleaning import clean_observations
from ml.data.scalers import (
    FEATURE_NAMES,
    build_features,
    coordinate_features,
    fit_depth_scaler,
    fit_weather_scaler,
)
from ml.data.sources import calendar, load_config, read_real_folder
from ml.data.splits import (
    assign_roles,
    select_cohort,
    time_counts,
    training_coverage,
    window_end_indices,
    windows_stay_inside,
)
from ml.data.synthetic import generate_observations, place_wells
from ml.data.weather import weather_for_wells


def prepare(
    config_path: str | Path,
    kind: str,
    output: str | Path,
    input_folder: str | Path | None = None,
    weather_cache: str | Path = "data/cache/power",
    replace: bool = False,
) -> dict:
    if kind not in {"synthetic", "real"}:
        raise ValueError("kind must be synthetic or real")
    config = load_config(config_path)
    dates = calendar(config)
    n_train, n_validation, n_test = time_counts(
        len(dates),
        config["data"]["train_fraction"],
        config["data"]["validation_fraction"],
    )
    cache = Path(weather_cache)
    if kind == "real":
        if input_folder is None:
            raise ValueError("real preparation requires --input-folder")
        raw, source_manifest = read_real_folder(input_folder)
        before = source_manifest["files"]["observations.csv"]["sha256"]
        cleaned = clean_observations(raw, dates, source_manifest["timezone"])
        if source_manifest["files"]["observations.csv"]["sha256"] != before:
            raise RuntimeError("real input file changed while it was read")
        source_manifest["kind"] = "real"
    else:
        rng = np.random.default_rng(int(config["seed"]))
        stations = place_wells(int(config["data"]["target_wells"]), rng)
        preview = weather_for_wells(
            stations["latitude"].to_numpy(),
            stations["longitude"].to_numpy(),
            dates,
            cache,
        )
        raw = generate_observations(
            stations,
            dates,
            preview["precip_mm"],
            rng,
            n_train,
            float(config["data"]["train_min_coverage"]),
        )
        cleaned = clean_observations(raw, dates, "UTC")
        downloaded = {
            (cell["request_latitude"], cell["request_longitude"])
            for cell in preview["cells"]
            if cell["retrieval"] == "download"
        }
        source_manifest = {
            "kind": "synthetic",
            "generator": "delayed_seasonal_spatial_v1",
            "seed": int(config["seed"]),
            "label": "fictional wells and depths; not field measurements",
            "field_accuracy": False,
            "uses_storage_regulariser_equation": False,
            "uses_et0_to_generate_depth": False,
            "missing_driver_precip_treated_as_zero_impulse": True,
            "coordinates": "fictional cluster used to request coarse POWER cells, not surveyed wells",
            "rights": "synthetic series may be regenerated from this seed; NASA POWER weather remains subject to NASA terms",
            "rights_status": "synthetic_plus_nasa_power",
        }
    weather = weather_for_wells(cleaned.latitude, cleaned.longitude, dates, cache)
    if kind == "synthetic":
        for cell in weather["cells"]:
            key = (cell["request_latitude"], cell["request_longitude"])
            if key in downloaded:
                cell["retrieval"] = "download"
    keep = select_cohort(
        cleaned.station_ids,
        training_coverage(cleaned.depth_valid, n_train),
        float(config["data"]["train_min_coverage"]),
    )
    if kind == "synthetic" and int(keep.sum()) != int(config["data"]["target_wells"]):
        raise RuntimeError(
            f"synthetic cohort kept {int(keep.sum())} wells, not the configured {config['data']['target_wells']}"
        )
    assembled = assemble(cleaned, weather, keep, dates, config, n_train, n_validation, n_test)
    assembled["source_manifest"] = source_manifest
    assembled["dataset_kind"] = kind
    assembled["code_revision"] = _code_revision(Path(config_path).resolve().parents[2])
    return _write(Path(output), assembled, replace)


def assemble(cleaned, weather, keep, dates, config, n_train, n_validation, n_test) -> dict:
    station_ids = [station for station, flag in zip(cleaned.station_ids, keep) if flag]
    depth = cleaned.depth_m[:, keep]
    valid = cleaned.depth_valid[:, keep]
    latitude = cleaned.latitude[keep]
    longitude = cleaned.longitude[keep]
    precip_mm = weather["precip_mm"][:, keep]
    precip_m = weather["precip_m_per_day"][:, keep]
    et0_mm = weather["et0_mm"][:, keep]
    et0_m = weather["et0_m_per_day"][:, keep]
    tmax = weather["tmax_c"][:, keep]
    tmin = weather["tmin_c"][:, keep]
    weather_valid = weather["weather_valid"][:, keep]
    roles = assign_roles(
        station_ids,
        int(config["seed"]),
        float(config["data"]["holdout_fraction"]),
        float(config["data"]["train_masked_fraction_of_remaining"]),
    )
    depth_mean, depth_std = fit_depth_scaler(depth, valid, roles, n_train)
    precip_mean, precip_std = fit_weather_scaler(precip_m, weather_valid, roles, n_train)
    et0_mean, et0_std = fit_weather_scaler(et0_m, weather_valid, roles, n_train)
    coordinates = coordinate_features(latitude, longitude)
    features = build_features(
        depth,
        valid,
        precip_m,
        et0_m,
        weather_valid,
        roles,
        dates,
        coordinates,
        depth_mean,
        depth_std,
        precip_mean,
        precip_std,
        et0_mean,
        et0_std,
    )
    window = int(config["data"]["window"])
    stride = int(config["data"]["stride"])
    windows = {
        "train": window_end_indices(0, n_train, window, stride),
        "validation": window_end_indices(n_train, n_train + n_validation, window, stride),
        "test": window_end_indices(n_train + n_validation, len(dates), window, stride),
    }
    if config["data"]["windows_cross_partitions"] is not False:
        raise ValueError("this phase only builds bundles with windows inside each date partition")
    for name, start, stop in (
        ("train", 0, n_train),
        ("validation", n_train, n_train + n_validation),
        ("test", n_train + n_validation, len(dates)),
    ):
        if not windows_stay_inside(windows[name], start, stop, window):
            raise RuntimeError(f"{name} windows leave their date partition")
    coverage = valid[:n_train].mean(axis=0)
    scalers = {
        "depth_mean_m": depth_mean,
        "depth_std_m": depth_std,
        "depth_definition": "population_std_of_valid_training_labels_on_visible_and_train_masked",
        "precip_mean_m_per_day": precip_mean,
        "precip_std_m_per_day": precip_std,
        "et0_mean_m_per_day": et0_mean,
        "et0_std_m_per_day": et0_std,
        "weather_definition": "population_std_of_training_dates_at_visible_wells",
        "x_mean_m": coordinates["x_mean_m"],
        "x_std_m": coordinates["x_std_m"],
        "y_mean_m": coordinates["y_mean_m"],
        "y_std_m": coordinates["y_std_m"],
        "coordinate_definition": "local_equirectangular_metres_then_zscore_on_frozen_cohort",
        "q_m_per_day": None,
        "q_status": "not_estimated_in_this_phase",
    }
    dataset_id = _dataset_id(station_ids, roles, depth, valid, precip_m, et0_m, scalers, int(config["seed"]))
    manifest = {
        "dataset_id": dataset_id,
        "dataset_kind": None,
        "schema_version": config["schema_version"],
        "seed": int(config["seed"]),
        "target_unit": "m_below_ground",
        "weather_unit_for_physics": "m_per_day",
        "start_date": dates[0].strftime("%Y-%m-%d"),
        "end_date": dates[-1].strftime("%Y-%m-%d"),
        "n_days": int(len(dates)),
        "n_wells": int(len(station_ids)),
        "station_ids": station_ids,
        "roles": {name: [station_ids[i] for i, role in enumerate(roles) if role == name] for name in ("visible", "train_masked", "holdout")},
        "role_counts": {name: int((roles == name).sum()) for name in ("visible", "train_masked", "holdout")},
        "date_partitions": _partition_dates(dates, n_train, n_validation),
        "window": window,
        "stride": stride,
        "window_counts": {name: int(len(ends)) for name, ends in windows.items()},
        "scalers": scalers,
        "training_coverage_min": float(coverage.min()),
        "training_coverage_by_well": {station_ids[i]: float(coverage[i]) for i in range(len(station_ids))},
        "missing_fraction": {
            "train": float(1 - valid[:n_train].mean()),
            "validation": float(1 - valid[n_train : n_train + n_validation].mean()),
            "test": float(1 - valid[n_train + n_validation :].mean()),
        },
        "q_status": "not_estimated_in_this_phase",
        "field_accuracy": False,
    }
    return {
        "manifest": manifest,
        "station_ids": station_ids,
        "latitude": latitude,
        "longitude": longitude,
        "dates": dates,
        "depth_m": depth,
        "depth_valid": valid,
        "precip_mm": precip_mm,
        "precip_m_per_day": precip_m,
        "et0_mm": et0_mm,
        "et0_m_per_day": et0_m,
        "tmax_c": tmax,
        "tmin_c": tmin,
        "weather_valid": weather_valid,
        "roles": roles,
        "features": features,
        "windows": windows,
        "coordinates": coordinates,
        "n_train": n_train,
        "n_validation": n_validation,
        "n_test": n_test,
        "cleaning_report": cleaned.report,
        "weather_cells": weather["cells"],
        "scalers": scalers,
    }


def _write(output: Path, assembled: dict, replace: bool) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    existing = output / "manifest.json"
    dataset_id = assembled["manifest"]["dataset_id"]
    if existing.is_file():
        previous = json.loads(existing.read_text(encoding="utf-8"))["dataset_id"]
        if previous != dataset_id and not replace:
            raise FileExistsError(
                f"{output} already holds dataset {previous}. Refusing to overwrite it with {dataset_id}. "
                "Choose a new output directory, or pass --replace to archive the previous bundle under revisions/."
            )
        if previous != dataset_id:
            revision = output / "revisions" / previous
            revision.mkdir(parents=True, exist_ok=True)
            for name in ("manifest.json", "quality_report.json", "source_manifest.json", "scalers.json", "bundle.npz", "observations.csv"):
                path = output / name
                if path.exists():
                    path.replace(revision / name)
    manifest = dict(assembled["manifest"])
    manifest["dataset_kind"] = assembled["dataset_kind"]
    manifest["code_revision"] = assembled["code_revision"]
    manifest["weather_cells"] = assembled["weather_cells"]
    manifest["cleaning"] = assembled["cleaning_report"]
    manifest["source"] = {
        "rights_status": assembled["source_manifest"].get("rights_status"),
        "label": assembled["source_manifest"].get("label") or assembled["source_manifest"].get("depth_meaning"),
    }
    _dump(output / "manifest.json", manifest)
    _dump(output / "scalers.json", assembled["scalers"])
    _dump(output / "source_manifest.json", assembled["source_manifest"])
    quality = {
        "dataset_id": dataset_id,
        "dataset_kind": assembled["dataset_kind"],
        "cleaning": assembled["cleaning_report"],
        "training_coverage_min": manifest["training_coverage_min"],
        "missing_fraction": manifest["missing_fraction"],
        "role_counts": manifest["role_counts"],
        "n_days": manifest["n_days"],
        "n_wells": manifest["n_wells"],
        "weather_cells": [
            {
                "request_latitude": cell["request_latitude"],
                "request_longitude": cell["request_longitude"],
                "n_wells": cell["n_wells"],
                "units": cell["units"],
                "missing_parameter_days": cell["missing_parameter_days"],
                "retrieval": cell["retrieval"],
                "api_version": cell["api_version"],
            }
            for cell in assembled["weather_cells"]
        ],
        "field_accuracy": False,
        "q_status": "not_estimated_in_this_phase",
    }
    _dump(output / "quality_report.json", quality)
    dates = assembled["dates"]
    rows = []
    for well, station_id in enumerate(assembled["station_ids"]):
        for day in range(len(dates)):
            if not assembled["depth_valid"][day, well]:
                continue
            rows.append(
                {
                    "station_id": station_id,
                    "latitude": assembled["latitude"][well],
                    "longitude": assembled["longitude"][well],
                    "date": dates[day].strftime("%Y-%m-%d"),
                    "depth_m": assembled["depth_m"][day, well],
                }
            )
    pd.DataFrame(rows).to_csv(output / "observations.csv", index=False)
    np.savez_compressed(
        output / "bundle.npz",
        station_id=np.array(assembled["station_ids"]),
        latitude=assembled["latitude"],
        longitude=assembled["longitude"],
        date=np.array([day.strftime("%Y-%m-%d") for day in dates]),
        depth_m=assembled["depth_m"],
        depth_valid=assembled["depth_valid"],
        precip_mm=assembled["precip_mm"],
        precip_m_per_day=assembled["precip_m_per_day"],
        et0_mm=assembled["et0_mm"],
        et0_m_per_day=assembled["et0_m_per_day"],
        tmax_c=assembled["tmax_c"],
        tmin_c=assembled["tmin_c"],
        weather_valid=assembled["weather_valid"],
        role=np.array(assembled["roles"], dtype="U16"),
        features=assembled["features"],
        feature_names=np.array(FEATURE_NAMES),
        x_m=assembled["coordinates"]["x_m"],
        y_m=assembled["coordinates"]["y_m"],
        train_window_ends=assembled["windows"]["train"],
        validation_window_ends=assembled["windows"]["validation"],
        test_window_ends=assembled["windows"]["test"],
        n_train=np.array(assembled["n_train"]),
        n_validation=np.array(assembled["n_validation"]),
        n_test=np.array(assembled["n_test"]),
    )
    return manifest


def _dataset_id(station_ids, roles, depth, valid, precip_m, et0_m, scalers, seed: int) -> str:
    digest = hashlib.sha256()
    digest.update(str(seed).encode())
    digest.update("|".join(station_ids).encode())
    digest.update("|".join(str(role) for role in roles).encode())
    stored = np.where(valid, depth, 0.0)
    digest.update(np.ascontiguousarray(stored).tobytes())
    digest.update(np.ascontiguousarray(valid).tobytes())
    digest.update(np.ascontiguousarray(np.nan_to_num(precip_m, nan=-1.0)).tobytes())
    digest.update(np.ascontiguousarray(np.nan_to_num(et0_m, nan=-1.0)).tobytes())
    digest.update(json.dumps(_plain(scalers), sort_keys=True, allow_nan=False).encode())
    return digest.hexdigest()


def _partition_dates(dates: pd.DatetimeIndex, n_train: int, n_validation: int) -> dict:
    def span(start: int, stop: int) -> dict:
        return {
            "start": dates[start].strftime("%Y-%m-%d"),
            "end": dates[stop - 1].strftime("%Y-%m-%d"),
            "n_days": int(stop - start),
            "start_index": int(start),
            "end_index_exclusive": int(stop),
        }

    return {
        "train": span(0, n_train),
        "validation": span(n_train, n_train + n_validation),
        "test": span(n_train + n_validation, len(dates)),
    }


def _plain(value):
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, np.ndarray):
        return _plain(value.tolist())
    if isinstance(value, np.generic):
        return _plain(value.item())
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("refusing to write a non-finite JSON number")
        return value
    return value


def _dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(_plain(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _code_revision(root: Path) -> str:
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return sha + ("+dirty" if dirty.strip() else "")
