"""Controller for scheduling, executing, and cancelling worker conversion jobs."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys
import time
from typing import Callable, List, Optional
import uuid

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from local_markdown.conversion.models import (
    ConversionResult,
    ConversionWarning,
    FileStatus,
    QueuedFile,
    AdapterType,
)
from local_markdown.jobs.protocol import read_json_safely, write_atomic_json
from local_markdown.jobs.windows_process_tree import ProcessTreeJob
from local_markdown.storage.cleanup import clean_job_directory
from local_markdown.storage.history import (
    HistoryEntry,
    add_history_entry,
)
from local_markdown.storage.paths import (
    get_jobs_dir,
    get_results_dir,
    is_safe_contained_path,
)


class ConversionController(QObject):
    """Manages queue execution, child process workers, and job cancellation."""

    # Signals
    job_started = Signal(str, str)  # (file_id, display_name)
    job_progress = Signal(str, str)  # (file_id, status_message)
    job_finished = Signal(str, object)  # (file_id, ConversionResult)
    queue_completed = Signal(int, int, int)  # (ready_count, review_count, failed_count)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._queue: List[QueuedFile] = []
        self._current_index: int = -1
        self._current_file: Optional[QueuedFile] = None
        self._process: Optional[QProcess] = None
        self._process_tree_job: Optional[ProcessTreeJob] = None
        self._poll_timer: Optional[QTimer] = None
        self._current_job_id: Optional[str] = None
        self._current_job_dir: Optional[Path] = None
        self._is_running: bool = False

        self._counts = {"ready": 0, "review": 0, "failed": 0}

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start_batch(self, files: List[QueuedFile], force_ocr: bool = False) -> None:
        """Start converting a batch of queued files."""
        if self._is_running:
            return

        self._queue = [f for f in files if f.status in (FileStatus.QUEUED, FileStatus.FAILED, FileStatus.CANCELLED)]
        if not self._queue:
            return

        self._counts = {"ready": 0, "review": 0, "failed": 0}
        self._current_index = 0
        self._is_running = True
        self._force_ocr = force_ocr
        self._process_next()

    def cancel_active_work(self) -> None:
        """Cancel current job and any remaining queued files."""
        if not self._is_running:
            return

        # 1. Terminate current process tree immediately via Win32 Job Object
        if self._process_tree_job:
            self._process_tree_job.terminate()
            self._process_tree_job = None

        if self._process:
            self._process.kill()
            self._process.waitForFinished(1000)
            self._process = None

        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer = None

        # Clean current job directory
        if self._current_job_id:
            clean_job_directory(self._current_job_id)

        if self._current_file:
            self._current_file.status = FileStatus.CANCELLED
            cancel_result = ConversionResult(
                job_id=self._current_job_id or "cancelled",
                status=FileStatus.CANCELLED,
                error_message="Conversion stopped by user.",
            )
            self.job_finished.emit(self._current_file.id, cancel_result)

        # Mark remaining queued files as cancelled
        for idx in range(self._current_index + 1, len(self._queue)):
            f = self._queue[idx]
            f.status = FileStatus.CANCELLED
            res = ConversionResult(
                job_id=str(uuid.uuid4()),
                status=FileStatus.CANCELLED,
                error_message="Batch stopped before this file was processed.",
            )
            self.job_finished.emit(f.id, res)

        self._is_running = False
        self.queue_completed.emit(self._counts["ready"], self._counts["review"], self._counts["failed"])

    def _process_next(self) -> None:
        """Execute the next item in the queue."""
        if self._current_index >= len(self._queue):
            self._is_running = False
            self.queue_completed.emit(self._counts["ready"], self._counts["review"], self._counts["failed"])
            return

        self._current_file = self._queue[self._current_index]
        self._current_job_id = str(uuid.uuid4())
        self._current_job_dir = get_jobs_dir() / self._current_job_id
        self._current_job_dir.mkdir(parents=True, exist_ok=True)

        self._current_file.status = FileStatus.RUNNING
        self._current_file.result_id = self._current_job_id
        self.job_started.emit(self._current_file.id, self._current_file.display_name)

        # Prepare job manifest
        manifest_path = self._current_job_dir / "job.json"
        manifest_data = {
            "job_id": self._current_job_id,
            "source_path": str(self._current_file.source_path),
            "display_name": self._current_file.display_name,
            "extension": self._current_file.extension,
            "try_ocr": getattr(self, "_force_ocr", False),
        }
        write_atomic_json(manifest_path, manifest_data)

        # Launch worker via QProcess
        self._process = QProcess(self)
        self._process_tree_job = ProcessTreeJob()

        if getattr(sys, "frozen", False):
            program = sys.executable
            args = ["--worker", str(manifest_path)]
        else:
            program = sys.executable
            args = ["-m", "local_markdown", "--worker", str(manifest_path)]

        self._process.setProgram(program)
        self._process.setArguments(args)
        self._process.finished.connect(self._on_worker_finished)

        self._process.start()
        if self._process.waitForStarted(2000):
            pid = self._process.processId()
            if pid > 0 and self._process_tree_job:
                self._process_tree_job.assign_pid(pid)

            # Start progress polling timer (every 100ms)
            self._poll_timer = QTimer(self)
            self._poll_timer.timeout.connect(self._poll_progress)
            self._poll_timer.start(100)
        else:
            self._on_worker_startup_failed()

    def _poll_progress(self) -> None:
        """Poll progress.json for UI status updates."""
        if not self._current_job_dir or not self._current_file:
            return
        progress_path = self._current_job_dir / "progress.json"
        data = read_json_safely(progress_path)
        if data and "detail" in data:
            self.job_progress.emit(self._current_file.id, data["detail"])

    def _on_worker_startup_failed(self) -> None:
        """Handle worker startup failure."""
        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer = None

        if self._current_file:
            self._current_file.status = FileStatus.FAILED
            self._current_file.error_message = "Failed to launch conversion worker process."
            res = ConversionResult(
                job_id=self._current_job_id or "error",
                status=FileStatus.FAILED,
                error_message="Worker process failed to start.",
            )
            self._counts["failed"] += 1
            self.job_finished.emit(self._current_file.id, res)

        if self._current_job_id:
            clean_job_directory(self._current_job_id)

        self._current_index += 1
        self._process_next()

    def _on_worker_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        """Handle normal worker completion."""
        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer = None

        if self._process_tree_job:
            self._process_tree_job.close()
            self._process_tree_job = None

        if not self._current_file or not self._current_job_dir:
            return

        result_path = self._current_job_dir / "result.json"
        markdown_path = self._current_job_dir / "result.md"
        result_data = read_json_safely(result_path)

        if result_data:
            result = ConversionResult.from_dict(result_data)
        else:
            result = ConversionResult(
                job_id=self._current_job_id,
                status=FileStatus.FAILED,
                error_message=f"Worker terminated unexpectedly (exit code {exit_code}).",
            )

        # If success (ready or review), commit output markdown to cache and history
        if result.status in (FileStatus.READY, FileStatus.REVIEW) and markdown_path.exists():
            target_cache_file = get_results_dir() / f"{result.job_id}.md"
            try:
                # Copy/move result.md into results cache
                shutil.copy2(markdown_path, target_cache_file)
                result.result_file = f"results/{result.job_id}.md"

                # Commit to SQLite history
                history_entry = HistoryEntry(
                    id=result.job_id,
                    display_name=self._current_file.display_name,
                    extension=self._current_file.extension,
                    input_size=self._current_file.input_size,
                    status=result.status,
                    adapter=result.adapter,
                    output_bytes=result.output_bytes,
                    duration_ms=result.duration_ms,
                    result_filename=result.result_file,
                    warnings=result.warnings,
                    error_message=result.error_message,
                    created_at=int(time.time()),
                )
                add_history_entry(history_entry)

            except Exception as e:
                result.status = FileStatus.FAILED
                result.error_message = f"Failed to commit result to cache: {e}"

        # Update file state
        self._current_file.status = result.status
        self._current_file.warnings = result.warnings
        self._current_file.error_message = result.error_message
        self._current_file.output_bytes = result.output_bytes

        if result.status == FileStatus.READY:
            self._counts["ready"] += 1
        elif result.status == FileStatus.REVIEW:
            self._counts["review"] += 1
        else:
            self._counts["failed"] += 1

        self.job_finished.emit(self._current_file.id, result)

        # Cleanup job folder
        if self._current_job_id:
            clean_job_directory(self._current_job_id)

        self._process = None
        self._current_job_id = None
        self._current_job_dir = None
        self._current_index += 1

        # Process next
        self._process_next()
