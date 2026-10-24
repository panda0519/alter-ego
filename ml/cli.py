"""Command line for Person B's preparation pipeline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.data.bundle import prepare
from ml.export.writer import export_baseline, load_export_inputs


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
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
