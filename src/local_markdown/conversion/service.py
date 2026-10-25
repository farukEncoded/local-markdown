"""Top-level conversion orchestrator coordinating adapters, warnings, and normalization."""

from __future__ import annotations

import os
from pathlib import Path
import time
from typing import List, Optional, Tuple

from local_markdown.conversion.models import (
    AdapterType,
    ConversionResult,
    ConversionWarning,
    FileStatus,
)
from local_markdown.conversion.output_normalizer import normalize_markdown_content
from local_markdown.conversion.pdf_pipeline import convert_pdf_document
from local_markdown.conversion.registry import create_isolated_markitdown
from local_markdown.conversion.validation import (
    ValidationError,
    validate_file_preflight,
)
from local_markdown.conversion.ocr import perform_ocr_on_image, is_ocr_available
from local_markdown.conversion.legacy_office import convert_legacy_to_modern


def convert_document(
    staged_path: Path,
    job_dir: Path,
    display_name: str,
    job_id: str,
    force_ocr: bool = False,
) -> Tuple[str, ConversionResult]:
    """
    Convert a single staged document file inside job_dir.
    Returns (final_markdown, ConversionResult).
    """
    start_time = time.perf_counter()
    warnings: List[ConversionWarning] = []
    adapter = AdapterType.NATIVE
    header_notes: List[str] = []

    ext = staged_path.suffix.lower()

    # Preflight validation
    validate_file_preflight(staged_path, allow_legacy_and_images=True)

    stats = {
        "pages_total": None,
        "pages_native": None,
        "pages_ocr": None,
        "pages_unreadable": None,
        "sheets_found": None,
        "slides_found": None,
    }

    raw_markdown = ""

    # Route based on extension
    if ext == ".pdf":
        raw_markdown, pdf_warnings, pdf_stats = convert_pdf_document(
            staged_path,
            temp_dir=job_dir,
            force_ocr=force_ocr,
        )
        warnings.extend(pdf_warnings)
        stats.update(pdf_stats)
        if pdf_stats.get("pages_ocr", 0) > 0 or force_ocr:
            adapter = AdapterType.OCR
            header_notes.append("Contains text extracted with local OCR. Review names and numbers.")

    elif ext in {".png", ".jpg", ".jpeg"}:
        adapter = AdapterType.OCR
        if not is_ocr_available():
            raise ValidationError(
                "E_OCR_UNAVAILABLE",
                "The local OCR engine is not available in this build.",
            )
        text, ocr_warn = perform_ocr_on_image(staged_path, temp_dir=job_dir)
        if ocr_warn:
            warnings.append(ocr_warn)
        raw_markdown = text
        header_notes.append("Extracted from image via local OCR. Review names and numbers.")

    elif ext in {".doc", ".ppt"}:
        adapter = AdapterType.LEGACY_THEN_NATIVE
        target_modern = "docx" if ext == ".doc" else "pptx"
        modern_path, leg_warn = convert_legacy_to_modern(
            staged_path,
            job_dir=job_dir,
            target_format=target_modern,
        )
        warnings.append(leg_warn)
        header_notes.append(f"Imported from legacy {ext.upper()} format via local Office runtime.")

        # Convert the modern intermediate via MarkItDown
        md = create_isolated_markitdown()
        res = md.convert_local(str(modern_path))
        raw_markdown = res.markdown or ""

    elif ext in {".xlsx", ".xls"}:
        adapter = AdapterType.NATIVE
        # Inspect for hidden sheets
        hidden_sheets: List[str] = []
        if ext == ".xlsx":
            try:
                import openpyxl
                wb = openpyxl.load_workbook(staged_path, read_only=False, data_only=True)
                hidden_sheets = [s.title for s in wb.worksheets if s.sheet_state != "visible"]
                stats["sheets_found"] = len(wb.worksheets)
                wb.close()
            except Exception:
                pass
        elif ext == ".xls":
            try:
                import xlrd
                book = xlrd.open_workbook(str(staged_path), on_demand=True)
                hidden_sheets = [sheet.name for sheet in book.sheets() if sheet.visibility != 0]
                stats["sheets_found"] = len(book.sheets())
                book.release_resources()
            except Exception:
                pass

        if hidden_sheets:
            warnings.append(
                ConversionWarning(
                    code="WARN_HIDDEN_SHEETS",
                    user_message=f"Workbook contains hidden sheets: {', '.join(hidden_sheets)}.",
                )
            )

        md = create_isolated_markitdown()
        res = md.convert_local(str(staged_path))
        raw_markdown = res.markdown or ""

    else:
        # .docx, .pptx
        adapter = AdapterType.NATIVE
        md = create_isolated_markitdown()
        res = md.convert_local(str(staged_path))
        raw_markdown = res.markdown or ""

    # Normalize output Markdown
    final_markdown = normalize_markdown_content(
        basename=display_name,
        raw_markdown=raw_markdown,
        notes=header_notes,
    )

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
    output_bytes = len(final_markdown.encode("utf-8"))

    # Determine status: REVIEW if OCR or warnings, otherwise READY
    status = FileStatus.REVIEW if (adapter == AdapterType.OCR or len(warnings) > 0) else FileStatus.READY

    result = ConversionResult(
        job_id=job_id,
        status=status,
        result_file=f"results/{job_id}.md",
        warnings=warnings,
        output_bytes=output_bytes,
        duration_ms=elapsed_ms,
        adapter=adapter,
        pages_total=stats["pages_total"],
        pages_native=stats["pages_native"],
        pages_ocr=stats["pages_ocr"],
        pages_unreadable=stats["pages_unreadable"],
        sheets_found=stats["sheets_found"],
        slides_found=stats["slides_found"],
    )

    return final_markdown, result
