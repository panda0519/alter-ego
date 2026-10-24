"""Command line for Person B's preparation pipeline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.data.bundle import prepare


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
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
