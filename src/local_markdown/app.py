"""Application lifecycle and single-instance GUI bootstrap."""

from __future__ import annotations

import sys
from pathlib import Path
from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication, QMessageBox

from local_markdown.storage.cleanup import clean_stale_jobs
from local_markdown.storage.paths import ensure_app_data_structure, get_app_data_dir, get_resource_dir
from local_markdown.ui.main_window import MainWindow


def run_app() -> int:
    """Initialize and run the Local Markdown desktop application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Local Markdown")
    app.setOrganizationName("LocalMarkdown")

    # Ensure app data directories exist
    data_dir = ensure_app_data_structure()

    # Single-instance lock
    lock_file_path = data_dir / "local_markdown.lock"
    lock_file = QLockFile(str(lock_file_path))
    lock_file.setStaleLockTime(30000)

    if not lock_file.tryLock(100):
        # Already running
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Local Markdown")
        msg.setText("Local Markdown is already running on your computer.")
        msg.exec()
        return 0

    # Startup recovery: remove stale jobs from prior crashes
    clean_stale_jobs()

    # Load stylesheet
    style_path = Path(__file__).parent / "ui" / "styles.qss"
    if style_path.exists():
        try:
            qss = style_path.read_text(encoding="utf-8")
            app.setStyleSheet(qss)
        except Exception:
            pass

    window = MainWindow()
    window.show()

    ret = app.exec()
    lock_file.unlock()
    return ret
