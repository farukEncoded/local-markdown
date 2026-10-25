"""Unit tests for atomic single export and batch ZIP generation."""

from __future__ import annotations

from pathlib import Path
import zipfile

from local_markdown.conversion.models import ConversionWarning
from local_markdown.storage.exports import (
    export_batch_zip,
    export_single_markdown,
    sanitize_filename,
)


def test_sanitize_filename():
    assert sanitize_filename("Report: Q3/2026*?.docx") == "Report_ Q3_2026__.docx"
    assert sanitize_filename("CON.md") == "_CON.md"
    assert sanitize_filename("  test  ") == "test"


def test_export_single_markdown(tmp_path: Path):
    target = tmp_path / "exports" / "test.md"
    export_single_markdown("# Heading\n\nContent", target)
    assert target.exists()
    assert target.read_text(encoding="utf-8") == "# Heading\n\nContent"


def test_export_batch_zip_duplicate_handling(tmp_path: Path):
    items = [
        ("report.docx", "ready", "# Report 1", []),
        ("report.docx", "ready", "# Report 2", [ConversionWarning("WARN", "Review text")]),
        ("notes.txt", "review", "# Notes", []),
    ]
    zip_dest = tmp_path / "batch.zip"
    export_batch_zip(items, zip_dest)

    assert zip_dest.exists()
    with zipfile.ZipFile(zip_dest, "r") as zf:
        namelist = zf.namelist()
        assert "report.md" in namelist
        assert "report (2).md" in namelist
        assert "notes.md" in namelist
        assert "conversion-summary.txt" in namelist

        summary = zf.read("conversion-summary.txt").decode("utf-8")
        assert "report.md" in summary
        assert "report (2).md" in summary
        assert "Total documents converted: 3" in summary
