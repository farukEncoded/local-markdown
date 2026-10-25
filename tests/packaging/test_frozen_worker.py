"""M0 Packaging Proof: Test frozen LocalMarkdown.exe and its worker route."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
DIST_EXE = PROJECT_ROOT / "dist" / "LocalMarkdown" / "LocalMarkdown.exe"
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"


@pytest.fixture(scope="module")
def frozen_exe():
    if not DIST_EXE.exists():
        pytest.skip(f"Frozen executable not found at: {DIST_EXE}")
    return DIST_EXE


def test_frozen_app_structure(frozen_exe):
    dist_dir = frozen_exe.parent
    assert (dist_dir / "LocalMarkdown.exe").exists()
    pyside_dir = (dist_dir / "_internal" / "PySide6") if (dist_dir / "_internal").exists() else (dist_dir / "PySide6")
    assert pyside_dir.exists()
    assert (dist_dir / "resources" / "capabilities.json").exists() or (dist_dir / "_internal" / "resources" / "capabilities.json").exists()


@pytest.mark.parametrize(
    "filename,expected_snippet",
    [
        ("sample.docx", "$42,500"),
        ("sample.xlsx", "150000"),
        ("sample.xls", "1250"),
        ("sample.pptx", "Local Markdown Strategy"),
        ("sample.pdf", "Antigravity Executive Report"),
        ("sample_image.png", "LOCAL MARKDOWN OCR TEST"),
        ("scanned.pdf", "LOCAL MARKDOWN OCR TEST"),
        ("mixed.pdf", "Mixed Document - Page 1 Native"),
        ("sample.doc", "Antigravity Project Overview"),
        ("sample.ppt", "Local Markdown Strategy"),
    ],
)
def test_frozen_worker_converts_core_fixtures(frozen_exe, tmp_path: Path, filename: str, expected_snippet: str):
    source_file = FIXTURES_DIR / filename
    assert source_file.exists()
    orig_bytes = source_file.read_bytes()

    # Set up isolated app data and job folder
    test_data = tmp_path / "app_data"
    job_id = f"frozen-test-{Path(filename).stem}"
    job_dir = test_data / "jobs" / job_id
    job_dir.mkdir(parents=True)

    manifest_path = job_dir / "job.json"
    manifest_data = {
        "job_id": job_id,
        "source_path": str(source_file),
        "display_name": filename,
        "extension": source_file.suffix.lower(),
        "try_ocr": False,
    }
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    # Clean environment without .venv on PATH
    env = os.environ.copy()
    env["LOCAL_MARKDOWN_DATA_DIR"] = str(test_data)
    # Remove python from PATH to simulate environment without Python
    path_entries = [p for p in env.get("PATH", "").split(os.pathsep) if "python" not in p.lower() and ".venv" not in p.lower()]
    env["PATH"] = os.pathsep.join(path_entries)
    if "PYTHONPATH" in env:
        del env["PYTHONPATH"]
    if "PYTHONHOME" in env:
        del env["PYTHONHOME"]

    cmd = [str(frozen_exe), "--worker", str(manifest_path)]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120,
        env=env,
        cwd=str(tmp_path),
    )

    assert proc.returncode == 0, f"Worker failed: stdout={proc.stdout}, stderr={proc.stderr}"

    result_json_file = job_dir / "result.json"
    assert result_json_file.exists()
    result_data = json.loads(result_json_file.read_text(encoding="utf-8"))

    assert result_data["status"] in ("ready", "review")
    assert result_data["output_bytes"] > 0

    result_md = job_dir / "result.md"
    assert result_md.exists()
    md_content = result_md.read_text(encoding="utf-8")
    assert expected_snippet in md_content

    # Original file is completely untouched
    assert source_file.read_bytes() == orig_bytes
