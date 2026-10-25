"""In-app update checker and self-updater for Local Markdown."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QProgressDialog,
    QWidget,
)

from local_markdown import __version__

GITHUB_OWNER = "farukEncoded"
GITHUB_REPO = "local-markdown"
GITHUB_API_RELEASES_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"


def _parse_version(v_str: str) -> tuple[int, ...]:
    """Parse a version tag like 'v1.0.1' or '1.0.0' into an integer tuple."""
    clean = v_str.lstrip("vV").strip()
    parts = []
    for p in clean.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    return tuple(parts)


class UpdateCheckWorker(QThread):
    """Background thread to query GitHub Releases API without blocking UI."""

    update_found = Signal(str, str, str)  # tag_name, download_url, release_notes
    up_to_date = Signal()
    check_failed = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

    def run(self) -> None:
        try:
            req = urllib.request.Request(
                GITHUB_API_RELEASES_URL,
                headers={
                    "User-Agent": f"LocalMarkdown-App/{__version__}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status != 200:
                    self.check_failed.emit(f"HTTP error {response.status}")
                    return
                data = json.loads(response.read().decode("utf-8"))

            latest_tag = data.get("tag_name", "")
            latest_version = _parse_version(latest_tag)
            current_version = _parse_version(__version__)

            if latest_version > current_version:
                # Find the installer asset
                download_url = ""
                for asset in data.get("assets", []):
                    name = asset.get("name", "")
                    if name.endswith(".exe") and "Setup" in name:
                        download_url = asset.get("browser_download_url", "")
                        break

                body = data.get("body", "A new version of Local Markdown is available.")
                self.update_found.emit(latest_tag, download_url, body)
            else:
                self.up_to_date.emit()
        except Exception as e:
            self.check_failed.emit(str(e))


class AppUpdater(QObject):
    """Coordinates checking for updates, prompting the user, and launching the installer."""

    def __init__(self, parent_widget: Optional[QWidget] = None) -> None:
        super().__init__(parent_widget)
        self._parent = parent_widget
        self._worker: Optional[UpdateCheckWorker] = None
        self._silent_if_current: bool = False

    def check_for_updates(self, silent_if_current: bool = False) -> None:
        """Query GitHub Releases API in background."""
        self._silent_if_current = silent_if_current
        self._worker = UpdateCheckWorker(self)
        self._worker.update_found.connect(self._on_update_found)
        self._worker.up_to_date.connect(self._on_up_to_date)
        self._worker.check_failed.connect(self._on_check_failed)
        self._worker.start()

    def _on_update_found(self, tag: str, download_url: str, notes: str) -> None:
        if not download_url:
            QMessageBox.information(
                self._parent,
                "Update Available",
                f"Local Markdown {tag} is available!\n\nPlease visit https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases to download.",
            )
            return

        choice = QMessageBox.question(
            self._parent,
            "Update Available",
            f"A new version of Local Markdown ({tag}) is available!\n\n"
            f"Current version: v{__version__}\n"
            f"Latest version: {tag}\n\n"
            f"Would you like to download and install this update now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if choice == QMessageBox.StandardButton.Yes:
            self._download_and_install(download_url, tag)

    def _on_up_to_date(self) -> None:
        if not self._silent_if_current:
            QMessageBox.information(
                self._parent,
                "Up to Date",
                f"You are running the latest version of Local Markdown (v{__version__}).",
            )

    def _on_check_failed(self, error: str) -> None:
        if not self._silent_if_current:
            QMessageBox.warning(
                self._parent,
                "Update Check Failed",
                f"Could not connect to GitHub to check for updates.\n\nError: {error}",
            )

    def _download_and_install(self, url: str, tag: str) -> None:
        progress = QProgressDialog("Downloading update...", "Cancel", 0, 100, self._parent)
        progress.setWindowTitle("Downloading Update")
        progress.setWindowModality(progress.windowModality())
        progress.show()

        temp_dir = Path(tempfile.gettempdir())
        target_path = temp_dir / f"LocalMarkdown-Setup-{tag}.exe"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": f"LocalMarkdown-App/{__version__}"})
            with urllib.request.urlopen(req) as resp, open(target_path, "wb") as f:
                total_size = resp.length or 0
                downloaded = 0
                block_size = 1024 * 64

                while True:
                    if progress.wasCanceled():
                        target_path.unlink(missing_ok=True)
                        return

                    chunk = resp.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        progress.setValue(percent)
                        progress.setLabelText(f"Downloading update... {percent}% ({downloaded // (1024*1024)} MB)")
                    QApplication.processEvents()

            progress.close()

            # Launch the installer and exit current app cleanly
            QMessageBox.information(
                self._parent,
                "Ready to Install",
                "The update has been downloaded. Local Markdown will now close to complete installation.",
            )

            subprocess.Popen([str(target_path)])
            QApplication.quit()

        except Exception as e:
            progress.close()
            QMessageBox.critical(self._parent, "Download Error", f"Failed to download update: {e}")
