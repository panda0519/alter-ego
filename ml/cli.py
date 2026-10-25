"""Command line for Person B's preparation pipeline."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from ml.data.bundle import prepare
from ml.evaluate import evaluate, publish
from ml.export.writer import export_baseline, export_gcn_lstm_batch, load_export_inputs
from ml.train import reload_and_predict, train_lambda0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ml.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare", help="build a private observation bundle")
    prepare_parser.add_argument("--config", required=True)
    prepare_parser.add_argument("--kind", choices=("synthetic", "real"), required=True)
    prepare_parser.add_argument("--output", required=True)
    prepare_parser.add_argument("--input-folder", default=None)
    prepare_parser.add_argument("--weather-cache", default="data/cache/power")
    prepare_parser.add_argument(
        "--replace",
        action="store_true",
        help="archive a different dataset already present in --output under revisions/",
    )
    baseline_parser = sub.add_parser("baseline", help="export an IDW baseline batch")
    baseline_parser.add_argument("--config", required=True)
    baseline_parser.add_argument("--bundle", required=True)
    baseline_parser.add_argument("--run-id", required=True)
    baseline_parser.add_argument("--output", required=True)
    train_parser = sub.add_parser("train", help="train the lambda-0 GCN-LSTM")
    train_parser.add_argument("--config", required=True)
    train_parser.add_argument("--bundle", required=True)
    train_parser.add_argument("--lambda-target", required=True, type=float)
    train_parser.add_argument("--run-dir", required=True)
    train_parser.add_argument("--smoke", action="store_true")
    train_parser.add_argument("--run-id", default=None)
    train_parser.add_argument("--output", default=None)
    evaluate_parser = sub.add_parser("evaluate", help="select on validation, then score holdout once")
    evaluate_parser.add_argument("--config", required=True)
    evaluate_parser.add_argument("--bundle", required=True)
    evaluate_parser.add_argument("--runs", nargs="+", required=True)
    evaluate_parser.add_argument("--output", required=True)
    export_parser = sub.add_parser("export", help="reload the selected checkpoint and write one batch")
    export_parser.add_argument("--config", required=True)
    export_parser.add_argument("--bundle", required=True)
    export_parser.add_argument("--evaluation", required=True)
    export_parser.add_argument("--run-id", required=True)
    export_parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        manifest = prepare(
            config_path=args.config,
            kind=args.kind,
            output=args.output,
            input_folder=args.input_folder,
            weather_cache=args.weather_cache,
            replace=args.replace,
        )
        print(json.dumps({
            "dataset_id": manifest["dataset_id"],
            "dataset_kind": manifest["dataset_kind"],
            "n_wells": manifest["n_wells"],
            "n_days": manifest["n_days"],
            "role_counts": manifest["role_counts"],
            "date_partitions": manifest["date_partitions"],
            "training_coverage_min": manifest["training_coverage_min"],
            "missing_fraction": manifest["missing_fraction"],
            "output": str(Path(args.output)),
        }, indent=2, allow_nan=False))
        return 0
    if args.command == "baseline":
        bundle = load_export_inputs(Path(args.bundle))
        meta = export_baseline(Path(args.config), bundle, args.run_id, Path(args.output))
        print(json.dumps({
            "run_id": meta["run_id"],
            "dataset_id": meta["dataset_id"],
            "dataset_kind": meta["dataset_kind"],
            "default_method": meta["default_method"],
            "as_of_date": meta["as_of_date"],
            "output": str(Path(args.output)),
        }, indent=2, allow_nan=False))
        return 0
    if args.command == "train":
        if (args.run_id or args.output) and not math.isclose(args.lambda_target, 0.0, rel_tol=0.0, abs_tol=0.0):
            raise ValueError("positive-lambda selection is a later phase; this command does not export it")
        manifest = train_lambda0(
            Path(args.config),
            Path(args.bundle),
            Path(args.run_dir),
            args.lambda_target,
            smoke=args.smoke,
        )
        exported = None
        if args.run_id or args.output:
            if args.smoke:
                raise ValueError("a smoke run is not exported")
            if not args.run_id or not args.output:
                raise ValueError("export needs both --run-id and --output")
            _bundle, payload, neural = reload_and_predict(Path(args.run_dir), Path(args.bundle))
            if float(payload["lambda_target"]) != 0.0 or payload["smoke"] is True:
                raise RuntimeError("export requires the lambda-0 checkpoint")
            export_inputs = load_export_inputs(Path(args.bundle))
            exported = export_gcn_lstm_batch(
                Path(args.config),
                export_inputs,
                args.run_id,
                Path(args.output),
                neural,
                lambda_value=0.0,
                checkpoint_sha256=manifest["checkpoint_sha256"],
                device=manifest["device"],
            )
        print(json.dumps({
            "run_kind": manifest["run_kind"],
            "smoke": manifest["smoke"],
            "device": manifest["device"],
            "epochs_ran": manifest["epochs_ran"],
            "best_epoch": manifest["best_epoch"],
            "best_validation_mae_m": manifest["best_validation_mae_m"],
            "elapsed_seconds": manifest["elapsed_seconds"],
            "checkpoint_sha256": manifest["checkpoint_sha256"],
            "dataset_id": manifest["dataset_id"],
            "export": None if exported is None else str(Path(args.output)),
            "default_method": None if exported is None else exported["default_method"],
        }, indent=2, allow_nan=False))
        return 0
    if args.command == "evaluate":
        document = evaluate(Path(args.config), Path(args.bundle), [Path(item) for item in args.runs], Path(args.output))
        print(json.dumps({
            "default_method": document["default_method"],
            "default_locked_before_test": document["default_locked_before_test"],
            "positive_lambda_selection": document["positive_lambda_selection"],
            "gcn_lstm_physics_status": document["gcn_lstm_physics_status"],
            "selected_positive_lambda": document["selected_positive_lambda"],
            "validation": document["validation"],
            "test": document["test"],
            "holdout_valid_labels": document["holdout_valid_labels"],
            "displayed_wells": document["displayed_wells"],
            "calibration": document["calibration"],
            "device": document["device"],
            "lambda0_checkpoint_sha256": document["lambda0_checkpoint_sha256"],
            "output": str(Path(args.output)),
        }, indent=2, allow_nan=False))
        return 0
    if args.command == "export":
        meta = publish(Path(args.config), Path(args.bundle), Path(args.evaluation), args.run_id, Path(args.output))
        print(json.dumps({
            "run_id": meta["run_id"],
            "dataset_id": meta["dataset_id"],
            "dataset_kind": meta["dataset_kind"],
            "default_method": meta["default_method"],
            "as_of_date": meta["as_of_date"],
            "output": str(Path(args.output)),
        }, indent=2, allow_nan=False))
        return 0
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
