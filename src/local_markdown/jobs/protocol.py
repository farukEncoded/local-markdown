"""IPC protocol and atomic file operations for worker communication."""

from __future__ import annotations

import json
import os
from pathlib import Path
import time
from typing import Any, Dict, Optional


def write_atomic_json(file_path: Path, data: Dict[str, Any]) -> None:
    """Write data to JSON file atomically using a temporary file and replace."""
    target = file_path.resolve()
    temp_path = target.with_suffix(".tmp")
    serialized = json.dumps(data, indent=2, ensure_ascii=False)
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(serialized)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_path, target)


def read_json_safely(file_path: Path, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """Read a JSON file safely, retrying on transient Windows sharing/lock errors."""
    for attempt in range(max_retries):
        try:
            if not file_path.exists():
                return None
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            if attempt < max_retries - 1:
                time.sleep(0.05)
            else:
                return None
    return None
