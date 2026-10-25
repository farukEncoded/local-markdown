"""Integration tests for offline OCR pipeline (C08, C09, C10, C11)."""

from __future__ import annotations

import hashlib
from pathlib import Path
import pytest

from local_markdown.conversion.models import AdapterType, FileStatus
from local_markdown.conversion.ocr import find_tesseract_binary
from local_markdown.conversion.service import convert_document

pytestmark = pytest.mark.skipif(
    find_tesseract_binary() is None,
    reason="Tesseract OCR runtime not staged in this environment",
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def test_standalone_image_ocr_c10(tmp_path: Path):
    source = FIXTURES_DIR / "sample_image.png"
    orig_hash = _hash_file(source)

    job_dir = tmp_path / "job_img"
    job_dir.mkdir()
    staged = job_dir / "sample_image.png"
    staged.write_bytes(source.read_bytes())

    md, res = convert_document(staged, job_dir, "sample_image.png", "job-ocr-img")

    assert res.status == FileStatus.REVIEW
    assert res.adapter == AdapterType.OCR
    assert "LOCAL MARKDOWN OCR TEST" in md
    assert "Extracted from image via local OCR" in md
    assert _hash_file(source) == orig_hash


def test_clean_scanned_pdf_c08(tmp_path: Path):
    source = FIXTURES_DIR / "scanned.pdf"
    orig_hash = _hash_file(source)

    job_dir = tmp_path / "job_scanned"
    job_dir.mkdir()
    staged = job_dir / "scanned.pdf"
    staged.write_bytes(source.read_bytes())

    md, res = convert_document(staged, job_dir, "scanned.pdf", "job-ocr-scan")

    assert res.status == FileStatus.REVIEW
    assert res.adapter == AdapterType.OCR
    assert "LOCAL MARKDOWN OCR TEST" in md
    assert any(w.code == "WARN_OCR_USED" for w in res.warnings)
    assert _hash_file(source) == orig_hash


def test_mixed_pdf_pipeline_c09(tmp_path: Path):
    source = FIXTURES_DIR / "mixed.pdf"
    orig_hash = _hash_file(source)

    job_dir = tmp_path / "job_mixed"
    job_dir.mkdir()
    staged = job_dir / "mixed.pdf"
    staged.write_bytes(source.read_bytes())

    md, res = convert_document(staged, job_dir, "mixed.pdf", "job-ocr-mix")

    assert res.status == FileStatus.REVIEW
    assert res.pages_total == 4
    assert res.pages_native == 2
    assert res.pages_ocr == 1
    assert res.pages_unreadable == 1

    # Check page order and content
    assert "## Page 1" in md
    assert "Mixed Document - Page 1 Native" in md
    assert "## Page 2" in md
    assert "LOCAL MARKDOWN OCR TEST" in md
    assert "## Page 3" in md
    assert "*[Blank or unreadable page]*" in md
    assert "## Page 4" in md
    assert "Mixed Document - Page 4 Native Conclusion" in md

    assert _hash_file(source) == orig_hash
