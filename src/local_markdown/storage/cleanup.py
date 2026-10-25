"""Safe cleanup and history erasure routines."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sqlite3
from typing import List, Tuple
from dataclasses import dataclass, field

from local_markdown.storage.paths import (
    get_app_data_dir,
    get_jobs_dir,
    get_logs_dir,
    get_results_dir,
    get_history_db_path,
    is_safe_contained_path,
    OWNED_MARKER_FILENAME,
)


@dataclass
class CleanupReport:
    deleted_results: int = 0
    deleted_jobs: int = 0
    failed_files: List[str] = field(default_factory=list)

    @property
    def is_complete_success(self) -> bool:
        return len(self.failed_files) == 0


def clean_job_directory(job_id: str) -> bool:
    """Delete a temporary job directory after completion or cancellation."""
    if not job_id:
        return False
    jobs_dir = get_jobs_dir()
    job_dir = jobs_dir / job_id
    if not is_safe_contained_path(job_dir, jobs_dir):
        return False
    if job_dir.exists() and job_dir.is_dir():
        try:
            shutil.rmtree(job_dir, ignore_errors=False)
            return True
        except OSError:
            return False
    return True


def clean_stale_jobs() -> int:
    """Clean any abandoned job directories left from prior crashed sessions."""
    jobs_dir = get_jobs_dir()
    if not jobs_dir.exists():
        return 0
    count = 0
    for item in jobs_dir.iterdir():
        if item.is_dir() and is_safe_contained_path(item, jobs_dir):
            try:
                shutil.rmtree(item, ignore_errors=True)
                count += 1
            except OSError:
                pass
    return count


def clear_all_history() -> CleanupReport:
    """
    Safely purge app-owned conversion history, cached Markdown previews,
    and temporary job data.
    Strictly verifies ownership and containment.
    NEVER touches source files, external documents, or user exports.
    """
    report = CleanupReport()
    root = get_app_data_dir()
    marker = root / OWNED_MARKER_FILENAME

    # Safety assertion: root must exist and have the ownership marker
    if not root.exists() or not marker.exists():
        return report

    # 1. Clear cached Markdown results in results/
    res_dir = get_results_dir()
    if res_dir.exists() and is_safe_contained_path(res_dir, root):
        for item in res_dir.glob("*.md"):
            if is_safe_contained_path(item, res_dir):
                try:
                    item.unlink()
                    report.deleted_results += 1
                except OSError as e:
                    report.failed_files.append(f"Result file '{item.name}': {e}")

    # 2. Clear job folders in jobs/
    jobs_dir = get_jobs_dir()
    if jobs_dir.exists() and is_safe_contained_path(jobs_dir, root):
        for item in jobs_dir.iterdir():
            if item.is_dir() and is_safe_contained_path(item, jobs_dir):
                try:
                    shutil.rmtree(item, ignore_errors=False)
                    report.deleted_jobs += 1
                except OSError as e:
                    report.failed_files.append(f"Job directory '{item.name}': {e}")

    # 3. Clear logs/
    logs_dir = get_logs_dir()
    if logs_dir.exists() and is_safe_contained_path(logs_dir, root):
        for item in logs_dir.iterdir():
            if item.is_file() and is_safe_contained_path(item, logs_dir):
                try:
                    item.unlink()
                except OSError:
                    pass

    # 4. Truncate SQLite database tables
    db_path = get_history_db_path()
    if db_path.exists() and is_safe_contained_path(db_path, root):
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            conn.isolation_level = None  # Autocommit mode allows VACUUM
            conn.execute("DELETE FROM conversion_history;")
            conn.execute("VACUUM;")
            conn.close()
        except OSError as e:
            report.failed_files.append(f"History database: {e}")

    return report
