"""Unit tests for path containment and safe history cleanup."""

from __future__ import annotations

import os
from pathlib import Path
import pytest

from local_markdown.conversion.models import AdapterType, FileStatus
from local_markdown.storage.cleanup import clear_all_history
from local_markdown.storage.history import (
    HistoryEntry,
    add_history_entry,
    list_history_entries,
)
from local_markdown.storage.paths import (
    get_app_data_dir,
    get_jobs_dir,
    get_results_dir,
    is_safe_contained_path,
    ensure_app_data_structure,
)


def test_safe_contained_path(tmp_path: Path):
    base = tmp_path / "app_data"
    base.mkdir()
    child = base / "results" / "file.md"
    assert is_safe_contained_path(child, base) is True

    # Escape attempt
    escape = base / ".." / "external.txt"
    assert is_safe_contained_path(escape, base) is False


def test_clear_all_history_preserves_originals_and_exports(tmp_path: Path, monkeypatch):
    test_data_dir = tmp_path / "LocalMarkdown"
    monkeypatch.setenv("LOCAL_MARKDOWN_DATA_DIR", str(test_data_dir))
    ensure_app_data_structure()

    # Create dummy result in cache
    res_dir = get_results_dir()
    cache_file = res_dir / "test_uuid.md"
    cache_file.write_text("# Test cached markdown", encoding="utf-8")

    # Add entry to history DB
    entry = HistoryEntry(
        id="test_uuid",
        display_name="original.docx",
        extension=".docx",
        input_size=1024,
        status=FileStatus.READY,
        adapter=AdapterType.NATIVE,
        output_bytes=100,
        duration_ms=50,
        result_filename="results/test_uuid.md",
        warnings=[],
        error_message=None,
        created_at=1234567,
    )
    add_history_entry(entry)
    assert len(list_history_entries()) == 1

    # Create external user documents (original and saved export)
    user_folder = tmp_path / "UserDocuments"
    user_folder.mkdir()
    sentinel_original = user_folder / "original.docx"
    sentinel_original.write_bytes(b"ORIGINAL_BYTES_SENTINEL_12345")
    sentinel_export = user_folder / "saved_report.md"
    sentinel_export.write_text("# User Saved Export", encoding="utf-8")

    # Execute clear history
    report = clear_all_history()
    assert report.is_complete_success

    # Assert cache and history DB are purged
    assert not cache_file.exists()
    assert len(list_history_entries()) == 0

    # CRITICAL: Assert user original and saved export are completely untouched!
    assert sentinel_original.exists()
    assert sentinel_original.read_bytes() == b"ORIGINAL_BYTES_SENTINEL_12345"
    assert sentinel_export.exists()
    assert sentinel_export.read_text(encoding="utf-8") == "# User Saved Export"
