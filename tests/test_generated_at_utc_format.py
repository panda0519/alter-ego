"""The shared export checker must reject a bad generated_at_utc.

Changing the same invalid timestamp in every batch file keeps the four meta
objects equal, so a pass would mean date-time format checking did not run.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "validate_exports.py"
FIXTURES = ROOT / "contracts" / "fixtures"
NAMES = ("predictions", "metrics", "run_info", "agent_context")
BAD_TIMESTAMP = "not-a-timestamp"


def _run_checker(folder: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(folder)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_fixture_batch_passes():
    result = _run_checker(FIXTURES)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS:" in result.stdout


def test_bad_generated_at_utc_is_rejected(tmp_path: Path):
    for name in NAMES:
        document = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
        document["meta"]["generated_at_utc"] = BAD_TIMESTAMP
        (tmp_path / f"{name}.json").write_text(
            json.dumps(document),
            encoding="utf-8",
        )
    metas = [
        json.loads((tmp_path / f"{name}.json").read_text(encoding="utf-8"))["meta"]
        for name in NAMES
    ]
    assert all(meta == metas[0] for meta in metas)

    result = _run_checker(tmp_path)
    combined = result.stdout + result.stderr
    assert result.returncode != 0, combined
    assert f"'{BAD_TIMESTAMP}' is not a 'date-time'" in combined
