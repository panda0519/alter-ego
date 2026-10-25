"""Export batch contract, negative batches, and the extra common-mask rule."""
import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from ml.export.contracts import assert_completed_common_mask, run_reference_validator
from ml.export.summaries import summarise
from ml.export.writer import export_baseline

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "ml" / "configs" / "prototype.yaml"


def _bundle():
    n_train, n_validation, n_test = 80, 40, 70
    n_days = n_train + n_validation + n_test
    dates = np.array(
        [np.datetime64("2023-01-01") + np.timedelta64(day, "D") for day in range(n_days)]
    )
    date_text = [str(day) for day in dates]
    depth = np.full((n_days, 4), 10.0)
    depth[:, 2] = 12.0
    depth[:, 3] = 14.0
    for well in range(4):
        depth[:, well] = depth[:, well] + np.linspace(0, 1.5, n_days)
    valid = np.ones((n_days, 4), dtype=bool)
    valid[10, 0] = False
    return {
        "dataset_id": "unit-export-bundle",
        "dataset_kind": "synthetic",
        "station_ids": ["A", "B", "C", "D"],
        "latitude": np.array([23.5, 23.51, 23.52, 23.53]),
        "longitude": np.array([77.4, 77.41, 77.42, 77.43]),
        "dates": date_text,
        "depth_m": depth,
        "depth_valid": valid,
        "roles": ["visible", "visible", "train_masked", "holdout"],
        "n_train": n_train,
        "n_validation": n_validation,
        "n_test": n_test,
    }


def _write(tmp_path: Path, run_id: str = "unit-idw-1") -> Path:
    output = tmp_path / run_id
    export_baseline(
        CONFIG,
        _bundle(),
        run_id,
        output,
        generated_at_utc="2026-10-24T12:00:00Z",
        repo_root=ROOT,
    )
    return output


def _load(folder: Path) -> dict:
    return {
        name: json.loads((folder / f"{name}.json").read_text(encoding="utf-8"))
        for name in ("predictions", "metrics", "run_info", "agent_context")
    }


def _save(folder: Path, documents: dict) -> None:
    for name, document in documents.items():
        (folder / f"{name}.json").write_text(json.dumps(document), encoding="utf-8")


def test_summary_uses_the_calendar_day_thirty_back():
    dates = [f"2024-11-{day:02d}" for day in range(1, 31)] + [f"2024-12-{day:02d}" for day in range(1, 31)]
    assert len(dates) == 60
    predictions = [1.0] * 60
    predictions[-1] = 1.6
    summary = summarise(dates, predictions, 30)
    assert summary["change_30d_m"] == pytest.approx(0.6)
    assert summary["priority"] == "high"
    predictions[-1] = None
    assert summarise(dates, predictions, 30)["priority"] == "unknown"


def test_baseline_batch_passes_the_reference_checker(tmp_path: Path):
    folder = _write(tmp_path)
    result = run_reference_validator(folder, ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    documents = _load(folder)
    assert documents["predictions"]["meta"] == documents["agent_context"]["meta"]
    metrics = documents["metrics"]["methods"]
    assert metrics["idw"]["status"] == "completed"
    assert metrics["idw"]["test_pairs"] >= metrics["idw"]["test_wells"] >= 1
    assert metrics["gcn_lstm"]["status"] == "not_run"
    assert metrics["gcn_lstm_physics"]["status"] == "not_run"
    assert metrics["gcn_lstm"]["test_mae_m"] is None
    neural = documents["predictions"]["wells"][0]["predictions_m"]["gcn_lstm"]
    assert neural == [None] * len(documents["predictions"]["dates"])
    assert "observations_m" not in documents["agent_context"]["wells"][0]
    assert documents["run_info"]["checkpoint_sha256"] is None
    assert documents["run_info"]["nodus_job_ids"] == []
    assert len(documents["predictions"]["dates"]) == 60
    assert metrics["idw"]["test_pairs"] != 60


def test_existing_run_folder_is_not_overwritten(tmp_path: Path):
    _write(tmp_path)
    with pytest.raises(FileExistsError):
        _write(tmp_path)


def test_completed_methods_must_share_the_test_mask():
    one = {"methods": {"idw": {"status": "completed", "test_pairs": 4, "test_wells": 2}}}
    assert_completed_common_mask(one)
    mismatched = {
        "methods": {
            "idw": {"status": "completed", "test_pairs": 4, "test_wells": 2},
            "gcn_lstm": {"status": "completed", "test_pairs": 4, "test_wells": 1},
        }
    }
    with pytest.raises(ValueError, match="test mask"):
        assert_completed_common_mask(mismatched)
    with pytest.raises(ValueError, match="test_pairs"):
        assert_completed_common_mask(
            {"methods": {"idw": {"status": "completed", "test_pairs": 1, "test_wells": 2}}}
        )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        ("timestamp", "date-time"),
        ("meta", "metadata mismatch"),
        ("duplicate-id", "duplicate well ID"),
        ("duplicate-date", "dates must be unique"),
        ("length", "prediction length"),
        ("nonfinite", "non-finite"),
        ("summary", "priority mismatch"),
        ("agent", "agent summary mismatch"),
    ],
)
def test_reference_checker_rejects_bad_batches(tmp_path: Path, mutate: str, message: str):
    source = _write(tmp_path, "unit-idw-good")
    folder = tmp_path / f"bad-{mutate}"
    shutil.copytree(source, folder)
    documents = _load(folder)
    if mutate == "timestamp":
        for document in documents.values():
            document["meta"]["generated_at_utc"] = "not-a-timestamp"
        _save(folder, documents)
    elif mutate == "meta":
        documents["metrics"]["meta"]["run_id"] = "other-run"
        _save(folder, documents)
    elif mutate == "duplicate-id":
        documents["predictions"]["wells"][1]["id"] = documents["predictions"]["wells"][0]["id"]
        _save(folder, documents)
    elif mutate == "duplicate-date":
        documents["predictions"]["dates"][1] = documents["predictions"]["dates"][0]
        _save(folder, documents)
    elif mutate == "length":
        documents["predictions"]["wells"][0]["predictions_m"]["idw"].pop()
        _save(folder, documents)
    elif mutate == "nonfinite":
        text = (folder / "predictions.json").read_text(encoding="utf-8")
        replaced, count = __import__("re").subn(
            r'"latest_depth_m": [-0-9.eE]+',
            '"latest_depth_m": NaN',
            text,
            count=1,
        )
        assert count == 1
        (folder / "predictions.json").write_text(replaced, encoding="utf-8")
    elif mutate == "summary":
        well = documents["predictions"]["wells"][0]
        series = [1.0] * len(well["predictions_m"]["idw"])
        series[-1] = 2.0
        well["predictions_m"]["idw"] = series
        well["summaries"]["idw"]["latest_depth_m"] = 2.0
        well["summaries"]["idw"]["change_30d_m"] = 1.0
        well["summaries"]["idw"]["priority"] = "normal"
        _save(folder, documents)
    elif mutate == "agent":
        documents["agent_context"]["wells"][0]["latest_depth_m"] = 12345.0
        _save(folder, documents)
    result = run_reference_validator(folder, ROOT)
    assert result.returncode != 0
    assert message in (result.stdout + result.stderr)


def test_fixture_cannot_claim_a_completed_evaluation(tmp_path: Path):
    folder = tmp_path / "fixture"
    folder.mkdir()
    for name in ("predictions", "metrics", "run_info", "agent_context"):
        shutil.copy(ROOT / "contracts" / "fixtures" / f"{name}.json", folder / f"{name}.json")
    documents = _load(folder)
    for document in documents.values():
        document["meta"]["artifact_kind"] = "fixture"
    documents["metrics"]["methods"]["idw"]["status"] = "completed"
    documents["metrics"]["methods"]["idw"]["validation_mae_m"] = 0.1
    documents["metrics"]["methods"]["idw"]["validation_pairs"] = 2
    documents["metrics"]["methods"]["idw"]["test_mae_m"] = 0.1
    documents["metrics"]["methods"]["idw"]["test_rmse_m"] = 0.1
    documents["metrics"]["methods"]["idw"]["test_pairs"] = 2
    documents["metrics"]["methods"]["idw"]["test_wells"] = 1
    _save(folder, documents)
    result = run_reference_validator(folder, ROOT)
    assert result.returncode != 0
    assert "fixture cannot claim completed evaluation" in (result.stdout + result.stderr)
