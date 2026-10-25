"""Path resolution and containment validation for Local Markdown."""

from __future__ import annotations

import os
import sys
from pathlib import Path

OWNED_MARKER_FILENAME = ".local-markdown-owned"


def get_app_data_dir() -> Path:
    """Return the root application data directory in %LOCALAPPDATA%."""
    override = os.environ.get("LOCAL_MARKDOWN_DATA_DIR")
    if override:
        path = Path(override).expanduser().resolve()
    else:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            path = Path(local_app_data) / "LocalMarkdown"
        else:
            path = Path.home() / "AppData" / "Local" / "LocalMarkdown"
    return path


def get_results_dir() -> Path:
    """Return the results cache directory."""
    return get_app_data_dir() / "results"


def get_jobs_dir() -> Path:
    """Return the temporary jobs directory."""
    return get_app_data_dir() / "jobs"


def get_logs_dir() -> Path:
    """Return the logs directory."""
    return get_app_data_dir() / "logs"


def get_history_db_path() -> Path:
    """Return the SQLite database path for conversion history."""
    return get_app_data_dir() / "history.sqlite3"


def ensure_app_data_structure() -> Path:
    """Ensure the required app data directory tree and ownership marker exist."""
    root = get_app_data_dir()
    root.mkdir(parents=True, exist_ok=True)

    marker = root / OWNED_MARKER_FILENAME
    if not marker.exists():
        marker.write_text("Local Markdown owned directory\n", encoding="utf-8")

    get_results_dir().mkdir(parents=True, exist_ok=True)
    get_jobs_dir().mkdir(parents=True, exist_ok=True)
    get_logs_dir().mkdir(parents=True, exist_ok=True)

    return root


def is_safe_contained_path(target_path: Path | str, base_dir: Path | str) -> bool:
    """
    Verify that target_path is strictly within base_dir.
    Resolves symlinks and junctions to prevent directory traversal / reparse escapes.
    """
    try:
        target = Path(target_path).resolve(strict=False)
        base = Path(base_dir).resolve(strict=False)

        # Also check realpath in case of Windows subst / junctions
        target_real = Path(os.path.realpath(str(target)))
        base_real = Path(os.path.realpath(str(base)))

        # Must not be equal to base itself if checking containment of child
        # and must be relative to base
        target.relative_to(base)
        target_real.relative_to(base_real)
        return True
    except (ValueError, RuntimeError):
        return False


def get_bundle_dir() -> Path:
    """Return the runtime bundle root (PyInstaller sys._MEIPASS or source tree)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve()
    # In source mode, point to the repository root
    return Path(__file__).resolve().parent.parent.parent.parent


def get_resource_dir() -> Path:
    """Return the resources directory containing icons and capabilities."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundled = Path(sys._MEIPASS) / "local_markdown" / "resources"
        if bundled.exists():
            return bundled
        return Path(sys._MEIPASS) / "resources"
    return Path(__file__).resolve().parent.parent / "resources"


def get_vendor_dir() -> Path:
    """Return the vendor directory containing bundled OCR and LibreOffice runtimes."""
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            meipass_vendor = Path(sys._MEIPASS) / "vendor"
            if meipass_vendor.exists():
                return meipass_vendor
        exe_dir = Path(sys.executable).parent
        internal_vendor = exe_dir / "_internal" / "vendor"
        if internal_vendor.exists():
            return internal_vendor
        root_vendor = exe_dir / "vendor"
        if root_vendor.exists():
            return root_vendor
    return get_bundle_dir() / "vendor"
