"""Checks around the shared export checker.

scripts/validate_exports.py stays unchanged. These checks add the completed-mask
rules that the root checker does not state: a completed method has at least as
many test pairs as test wells, and every completed method shares that pair count
and well count.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_reference_validator(folder: Path, repo_root: Path | None = None) -> subprocess.CompletedProcess[str]:
    root = repo_root or Path(__file__).resolve().parents[2]
    checker = root / "scripts" / "validate_exports.py"
    return subprocess.run(
        [sys.executable, str(checker), str(folder)],
        capture_output=True,
        text=True,
        check=False,
    )


def assert_completed_common_mask(metrics: dict) -> None:
    completed = [method for method in metrics["methods"].values() if method["status"] == "completed"]
    for method in completed:
        if method["test_pairs"] < method["test_wells"]:
            raise ValueError("completed test_pairs is smaller than test_wells")
        if method["test_pairs"] < 1 or method["test_wells"] < 1:
            raise ValueError("completed evaluation needs pairs and wells")
    if len(completed) > 1:
        pairs = {method["test_pairs"] for method in completed}
        wells = {method["test_wells"] for method in completed}
        if len(pairs) != 1 or len(wells) != 1:
            raise ValueError("completed methods do not share one test mask")
