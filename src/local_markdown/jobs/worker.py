"""Worker child-process implementation for isolated document conversion."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys
import traceback
from typing import Any, Dict

from local_markdown.conversion.models import (
    ConversionResult,
    FileStatus,
    AdapterType,
)
from local_markdown.conversion.service import convert_document
from local_markdown.conversion.validation import ValidationError
from local_markdown.jobs.protocol import read_json_safely, write_atomic_json
from local_markdown.storage.paths import (
    get_jobs_dir,
    is_safe_contained_path,
    ensure_app_data_structure,
)


def run_worker_process(manifest_path_str: str) -> int:
    """
    Main worker routine executed when spawned with --worker <manifest_path>.
    Operates strictly inside the assigned temporary job directory.
    """
    manifest_path = Path(manifest_path_str).resolve()
    manifest = read_json_safely(manifest_path)
    if not manifest:
        sys.stderr.write(f"Cannot read worker manifest: {manifest_path}\n")
        return 1

    job_id = manifest["job_id"]
    source_path = Path(manifest["source_path"]).resolve()
    display_name = manifest.get("display_name", source_path.name)
    try_ocr = manifest.get("try_ocr", False)

    job_dir = get_jobs_dir() / job_id
    if not is_safe_contained_path(job_dir, get_jobs_dir()):
        sys.stderr.write(f"Job path outside safety boundary: {job_dir}\n")
        return 2

    job_dir.mkdir(parents=True, exist_ok=True)
    progress_file = job_dir / "progress.json"
    result_file = job_dir / "result.json"
    markdown_file = job_dir / "result.md"

    try:
        # Step 1: Staging - copy read-only source into private job folder
        write_atomic_json(
            progress_file,
            {"job_id": job_id, "step": "staging", "detail": "Preparing private workspace..."},
        )
        staged_dir = job_dir / "staged"
        staged_dir.mkdir(exist_ok=True)
        staged_copy = staged_dir / display_name
        shutil.copy2(source_path, staged_copy)

        # Step 2: Conversion
        write_atomic_json(
            progress_file,
            {"job_id": job_id, "step": "converting", "detail": f"Converting {display_name}..."},
        )

        final_markdown, result = convert_document(
            staged_path=staged_copy,
            job_dir=job_dir,
            display_name=display_name,
            job_id=job_id,
            force_ocr=try_ocr,
        )

        # Write result markdown
        with open(markdown_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(final_markdown)

        # Write terminal result JSON
        write_atomic_json(result_file, result.to_dict())
        return 0

    except ValidationError as ve:
        err_result = ConversionResult(
            job_id=job_id,
            status=FileStatus.FAILED,
            error_code=ve.code,
            error_message=ve.user_message,
        )
        write_atomic_json(result_file, err_result.to_dict())
        return 0

    except Exception as exc:
        err_result = ConversionResult(
            job_id=job_id,
            status=FileStatus.FAILED,
            error_code="E_UNEXPECTED",
            error_message=f"Conversion error: {exc}",
        )
        write_atomic_json(result_file, err_result.to_dict())
        return 0
