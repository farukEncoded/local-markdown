"""Integration test for the worker subprocess IPC and execution."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from local_markdown.jobs.protocol import read_json_safely, write_atomic_json
from local_markdown.storage.paths import get_jobs_dir, ensure_app_data_structure

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_worker_process_execution(tmp_path: Path, monkeypatch):
    test_data = tmp_path / "app_data"
    monkeypatch.setenv("LOCAL_MARKDOWN_DATA_DIR", str(test_data))
    ensure_app_data_structure()

    job_id = "test-worker-job-1"
    job_dir = get_jobs_dir() / job_id
    job_dir.mkdir(parents=True)

    source_docx = FIXTURES_DIR / "sample.docx"
    orig_bytes = source_docx.read_bytes()

    manifest_path = job_dir / "job.json"
    write_atomic_json(
        manifest_path,
        {
            "job_id": job_id,
            "source_path": str(source_docx),
            "display_name": "sample.docx",
            "extension": ".docx",
            "try_ocr": False,
        },
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["LOCAL_MARKDOWN_DATA_DIR"] = str(test_data)

    cmd = [
        sys.executable,
        "-m",
        "local_markdown",
        "--worker",
        str(manifest_path),
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    assert res.returncode == 0

    result_json = read_json_safely(job_dir / "result.json")
    assert result_json is not None
    assert result_json["status"] == "ready"
    assert result_json["output_bytes"] > 0

    result_md = job_dir / "result.md"
    assert result_md.exists()
    content = result_md.read_text(encoding="utf-8")
    assert "Antigravity Project Overview" in content
    assert "$42,500" in content

    # Source document must remain byte-identical
    assert source_docx.read_bytes() == orig_bytes
