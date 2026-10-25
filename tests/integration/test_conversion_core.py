"""Integration tests for core document conversions on synthetic fixtures."""

from __future__ import annotations

import hashlib
from pathlib import Path
import pytest

from local_markdown.conversion.models import FileStatus
from local_markdown.conversion.service import convert_document

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def test_convert_docx(tmp_path: Path):
    source = FIXTURES_DIR / "sample.docx"
    orig_hash = _hash_file(source)

    job_dir = tmp_path / "job_docx"
    job_dir.mkdir()
    staged = job_dir / "sample.docx"
    staged.write_bytes(source.read_bytes())

    md, res = convert_document(staged, job_dir, "sample.docx", "job-1")

    assert res.status == FileStatus.READY
    assert "Antigravity Project Overview" in md
    assert "$42,500" in md
    assert "Quarter" in md
    assert "Margin" in md

    # Verify source was not modified
    assert _hash_file(source) == orig_hash


def test_convert_xlsx_with_hidden_sheets(tmp_path: Path):
    source = FIXTURES_DIR / "sample.xlsx"
    orig_hash = _hash_file(source)

    job_dir = tmp_path / "job_xlsx"
    job_dir.mkdir()
    staged = job_dir / "sample.xlsx"
    staged.write_bytes(source.read_bytes())

    md, res = convert_document(staged, job_dir, "sample.xlsx", "job-2")

    # Has hidden sheet warning so status is review
    assert res.status == FileStatus.REVIEW
    assert any(w.code == "WARN_HIDDEN_SHEETS" for w in res.warnings)
    assert "Engineering" in md
    assert "150000" in md

    # Verify source was not modified
    assert _hash_file(source) == orig_hash


def test_convert_xls(tmp_path: Path):
    source = FIXTURES_DIR / "sample.xls"
    orig_hash = _hash_file(source)

    job_dir = tmp_path / "job_xls"
    job_dir.mkdir()
    staged = job_dir / "sample.xls"
    staged.write_bytes(source.read_bytes())

    md, res = convert_document(staged, job_dir, "sample.xls", "job-3")

    assert res.status == FileStatus.READY
    assert "Licenses" in md
    assert "1250" in md

    # Verify source was not modified
    assert _hash_file(source) == orig_hash


def test_convert_pptx(tmp_path: Path):
    source = FIXTURES_DIR / "sample.pptx"
    orig_hash = _hash_file(source)

    job_dir = tmp_path / "job_pptx"
    job_dir.mkdir()
    staged = job_dir / "sample.pptx"
    staged.write_bytes(source.read_bytes())

    md, res = convert_document(staged, job_dir, "sample.pptx", "job-4")

    assert res.status == FileStatus.READY
    assert "Local Markdown Strategy" in md
    assert "Client Offline Conversion Pipeline" in md

    # Verify source was not modified
    assert _hash_file(source) == orig_hash


def test_convert_pdf(tmp_path: Path):
    source = FIXTURES_DIR / "sample.pdf"
    orig_hash = _hash_file(source)

    job_dir = tmp_path / "job_pdf"
    job_dir.mkdir()
    staged = job_dir / "sample.pdf"
    staged.write_bytes(source.read_bytes())

    md, res = convert_document(staged, job_dir, "sample.pdf", "job-5")

    assert res.status == FileStatus.READY
    assert "Antigravity Executive Report" in md
    assert "Financial Conclusion" in md

    # Verify source was not modified
    assert _hash_file(source) == orig_hash
