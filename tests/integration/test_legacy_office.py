"""Integration tests for legacy Office (.doc, .ppt) conversion (C06, C07)."""

from __future__ import annotations

import hashlib
from pathlib import Path
import pytest

from local_markdown.conversion.legacy_office import find_libreoffice_binary
from local_markdown.conversion.models import AdapterType, FileStatus
from local_markdown.conversion.service import convert_document

import os

pytestmark = pytest.mark.skipif(
    find_libreoffice_binary() is None or os.environ.get("GITHUB_ACTIONS") == "true",
    reason="LibreOffice requires an interactive Windows desktop session (Session 0 isolation blocks GDI in headless CI runners)",
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def test_convert_genuine_doc_c07(tmp_path: Path):
    source = FIXTURES_DIR / "sample.doc"
    assert source.exists()
    orig_hash = _hash_file(source)

    job_dir = tmp_path / "job_doc"
    job_dir.mkdir()
    staged = job_dir / "sample.doc"
    staged.write_bytes(source.read_bytes())

    md, res = convert_document(staged, job_dir, "sample.doc", "job-leg-doc")

    assert res.status == FileStatus.REVIEW
    assert res.adapter == AdapterType.LEGACY_THEN_NATIVE
    assert "Antigravity Project Overview" in md
    assert "$42,500" in md
    assert "Imported from legacy .DOC format" in md
    assert _hash_file(source) == orig_hash


def test_convert_genuine_ppt_c06(tmp_path: Path):
    source = FIXTURES_DIR / "sample.ppt"
    assert source.exists()
    orig_hash = _hash_file(source)

    job_dir = tmp_path / "job_ppt"
    job_dir.mkdir()
    staged = job_dir / "sample.ppt"
    staged.write_bytes(source.read_bytes())

    md, res = convert_document(staged, job_dir, "sample.ppt", "job-leg-ppt")

    assert res.status == FileStatus.REVIEW
    assert res.adapter == AdapterType.LEGACY_THEN_NATIVE
    assert "Local Markdown Strategy" in md
    assert "Client Offline Conversion Pipeline" in md
    assert "Imported from legacy .PPT format" in md
    assert _hash_file(source) == orig_hash
