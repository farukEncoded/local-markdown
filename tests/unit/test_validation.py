"""Unit tests for input document validation and preflight checks."""

from __future__ import annotations

from pathlib import Path
import pytest

from local_markdown.conversion.validation import (
    ValidationError,
    validate_file_preflight,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_valid_files_pass_validation():
    for filename in ["sample.docx", "sample.xlsx", "sample.pptx", "sample.pdf", "sample.xls"]:
        path = FIXTURES_DIR / filename
        assert path.exists()
        validate_file_preflight(path)


def test_corrupt_docx_rejected():
    corrupt_path = FIXTURES_DIR / "corrupt.docx"
    with pytest.raises(ValidationError) as exc:
        validate_file_preflight(corrupt_path)
    assert exc.value.code == "E_INVALID_CONTAINER"


def test_macro_enabled_rejected():
    macro_path = FIXTURES_DIR / "macro.docm"
    with pytest.raises(ValidationError) as exc:
        validate_file_preflight(macro_path)
    assert exc.value.code == "E_MACRO_ENABLED"


def test_missing_file_rejected():
    missing = FIXTURES_DIR / "nonexistent_file_xyz.docx"
    with pytest.raises(ValidationError) as exc:
        validate_file_preflight(missing)
    assert exc.value.code == "E_FILE_NOT_FOUND"


def test_unsupported_extension_rejected(tmp_path: Path):
    exe_file = tmp_path / "test.exe"
    exe_file.write_bytes(b"MZ\x00\x00")
    with pytest.raises(ValidationError) as exc:
        validate_file_preflight(exe_file)
    assert exc.value.code == "E_UNSUPPORTED_TYPE"
