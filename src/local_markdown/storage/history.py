"""SQLite history persistence and cached result retrieval."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import time
from typing import Any, List, Optional
from dataclasses import dataclass

from local_markdown.conversion.models import ConversionWarning, FileStatus, AdapterType
from local_markdown.storage.paths import (
    get_history_db_path,
    get_results_dir,
    is_safe_contained_path,
    ensure_app_data_structure,
)


@dataclass
class HistoryEntry:
    id: str
    display_name: str
    extension: str
    input_size: int
    status: FileStatus
    adapter: AdapterType
    output_bytes: int
    duration_ms: int
    result_filename: Optional[str]
    warnings: List[ConversionWarning]
    error_message: Optional[str]
    created_at: int


def _get_db_connection() -> sqlite3.Connection:
    ensure_app_data_structure()
    db_path = get_history_db_path()
    conn = sqlite3.connect(str(db_path), timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS conversion_history (
            id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            extension TEXT NOT NULL,
            input_size INTEGER NOT NULL,
            status TEXT NOT NULL,
            adapter TEXT NOT NULL,
            output_bytes INTEGER NOT NULL,
            duration_ms INTEGER NOT NULL,
            result_filename TEXT,
            warnings_json TEXT NOT NULL,
            error_message TEXT,
            created_at INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def add_history_entry(entry: HistoryEntry) -> None:
    """Insert a new history entry. Does NOT store full paths or content."""
    conn = _get_db_connection()
    try:
        warnings_json = json.dumps([w.to_dict() for w in entry.warnings], ensure_ascii=False)
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO conversion_history (
                    id, display_name, extension, input_size, status, adapter,
                    output_bytes, duration_ms, result_filename, warnings_json,
                    error_message, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.id,
                    entry.display_name,
                    entry.extension,
                    entry.input_size,
                    entry.status.value,
                    entry.adapter.value,
                    entry.output_bytes,
                    entry.duration_ms,
                    entry.result_filename,
                    warnings_json,
                    entry.error_message,
                    entry.created_at or int(time.time()),
                ),
            )
    finally:
        conn.close()


def list_history_entries() -> List[HistoryEntry]:
    """Retrieve all history entries sorted from newest to oldest."""
    conn = _get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, display_name, extension, input_size, status, adapter,
                   output_bytes, duration_ms, result_filename, warnings_json,
                   error_message, created_at
            FROM conversion_history
            ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()
        entries: List[HistoryEntry] = []
        for r in rows:
            try:
                raw_warnings = json.loads(r[9]) if r[9] else []
                warnings = [ConversionWarning.from_dict(w) for w in raw_warnings]
            except Exception:
                warnings = []
            entries.append(
                HistoryEntry(
                    id=r[0],
                    display_name=r[1],
                    extension=r[2],
                    input_size=r[3],
                    status=FileStatus(r[4]),
                    adapter=AdapterType(r[5]),
                    output_bytes=r[6],
                    duration_ms=r[7],
                    result_filename=r[8],
                    warnings=warnings,
                    error_message=r[10],
                    created_at=r[11],
                )
            )
        return entries
    finally:
        conn.close()


def get_history_entry(entry_id: str) -> Optional[HistoryEntry]:
    """Retrieve a single history entry by ID."""
    conn = _get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, display_name, extension, input_size, status, adapter,
                   output_bytes, duration_ms, result_filename, warnings_json,
                   error_message, created_at
            FROM conversion_history WHERE id = ?
            """,
            (entry_id,),
        )
        r = cursor.fetchone()
        if not r:
            return None
        try:
            raw_warnings = json.loads(r[9]) if r[9] else []
            warnings = [ConversionWarning.from_dict(w) for w in raw_warnings]
        except Exception:
            warnings = []
        return HistoryEntry(
            id=r[0],
            display_name=r[1],
            extension=r[2],
            input_size=r[3],
            status=FileStatus(r[4]),
            adapter=AdapterType(r[5]),
            output_bytes=r[6],
            duration_ms=r[7],
            result_filename=r[8],
            warnings=warnings,
            error_message=r[10],
            created_at=r[11],
        )
    finally:
        conn.close()


def delete_history_entry(entry_id: str) -> None:
    """Delete a single history entry and its associated cached result file."""
    entry = get_history_entry(entry_id)
    if entry and entry.result_filename:
        res_dir = get_results_dir()
        cached_file = res_dir / Path(entry.result_filename).name
        if is_safe_contained_path(cached_file, res_dir) and cached_file.exists():
            try:
                cached_file.unlink()
            except OSError:
                pass

    conn = _get_db_connection()
    try:
        with conn:
            conn.execute("DELETE FROM conversion_history WHERE id = ?", (entry_id,))
    finally:
        conn.close()


def read_cached_result_markdown(result_filename: Optional[str]) -> Optional[str]:
    """
    Safely read the cached Markdown content.
    Enforces strict directory containment within get_results_dir().
    """
    if not result_filename:
        return None
    res_dir = get_results_dir()
    # Enforce basename only
    target = res_dir / Path(result_filename).name
    if not is_safe_contained_path(target, res_dir) or not target.exists():
        return None
    try:
        return target.read_text(encoding="utf-8")
    except Exception:
        return None
