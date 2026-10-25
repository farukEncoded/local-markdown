"""PDF inspection, native extraction, and mixed-mode per-page OCR pipeline."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List, Optional, Tuple
import pypdfium2 as pdfium

from local_markdown.conversion.models import ConversionWarning
from local_markdown.conversion.ocr import perform_ocr_on_image, is_ocr_available
from local_markdown.conversion.validation import ValidationError

MAX_PDF_PAGES = 300
MAX_OCR_PAGES = 50
SPARSE_TEXT_THRESHOLD = 30  # Alphanumeric chars per page to consider native text adequate
TARGET_OCR_DPI = 250


def convert_pdf_document(
    pdf_path: Path,
    temp_dir: Path,
    force_ocr: bool = False,
    markitdown_instance: Any = None,
) -> Tuple[str, List[ConversionWarning], dict[str, int]]:
    """
    Process a PDF document:
    - If pure text PDF and not force_ocr: convert directly via MarkItDown.
    - If mixed or scanned: inspect pages and process per-page in order.
    Returns: (raw_markdown, warnings, stats_dict)
    """
    doc = pdfium.PdfDocument(str(pdf_path))
    num_pages = len(doc)

    if num_pages == 0:
        doc.close()
        raise ValidationError("E_EMPTY_PDF", "PDF contains no pages.")

    if num_pages > MAX_PDF_PAGES:
        doc.close()
        raise ValidationError(
            "E_PDF_PAGE_LIMIT",
            f"PDF has {num_pages} pages, which exceeds the limit of {MAX_PDF_PAGES} pages.",
        )

    # Inspect native text on each page
    pages_to_ocr: List[int] = []  # 0-indexed page indices
    page_texts: List[str] = []
    blank_pages: List[int] = []

    for i in range(num_pages):
        page = doc[i]
        textpage = page.get_textpage()
        text = textpage.get_text_range().strip()
        alnum_count = sum(1 for c in text if c.isalnum())
        page_texts.append(text)

        if force_ocr:
            pages_to_ocr.append(i)
        elif alnum_count < SPARSE_TEXT_THRESHOLD:
            # Check if page is truly blank or has image content
            # If text is empty and no images, could be blank page
            if alnum_count == 0:
                # We will check if rendering produces non-white content
                pages_to_ocr.append(i)
            else:
                # Some sparse text exists; treat as OCR candidate to capture any image text
                pages_to_ocr.append(i)

    warnings: List[ConversionWarning] = []
    stats = {
        "pages_total": num_pages,
        "pages_native": 0,
        "pages_ocr": 0,
        "pages_unreadable": 0,
    }

    # Case 1: All pages have sufficient native text and force_ocr is False
    if len(pages_to_ocr) == 0 and not force_ocr:
        doc.close()
        stats["pages_native"] = num_pages
        # Use native MarkItDown conversion
        from local_markdown.conversion.registry import create_isolated_markitdown
        md = markitdown_instance or create_isolated_markitdown()
        result = md.convert_local(str(pdf_path))
        return result.markdown or "", warnings, stats

    # Case 2: Per-page pipeline needed (scans or mixed PDF)
    if len(pages_to_ocr) > MAX_OCR_PAGES:
        doc.close()
        raise ValidationError(
            "E_OCR_PAGE_LIMIT",
            f"Document requires OCR for {len(pages_to_ocr)} pages, exceeding the limit of {MAX_OCR_PAGES} OCR pages.",
        )

    ocr_ready = is_ocr_available()
    assembled_sections: List[str] = []
    ocr_pages_done: List[int] = []

    for idx in range(num_pages):
        page_num = idx + 1
        page = doc[idx]

        if idx in pages_to_ocr:
            if not ocr_ready:
                # OCR requested but engine unavailable
                native_fallback = page_texts[idx]
                if native_fallback:
                    assembled_sections.append(f"## Page {page_num}\n\n{native_fallback}")
                    stats["pages_native"] += 1
                else:
                    assembled_sections.append(f"## Page {page_num}\n\n*[Page unreadable: OCR engine not bundled]*")
                    stats["pages_unreadable"] += 1
                warnings.append(
                    ConversionWarning(
                        code="WARN_OCR_UNAVAILABLE",
                        user_message=f"Page {page_num} requires OCR, but the OCR engine is unavailable.",
                        page_numbers=[page_num],
                    )
                )
                continue

            # Render page to image at TARGET_OCR_DPI
            scale = TARGET_OCR_DPI / 72.0
            bitmap = page.render(scale=scale)
            pil_image = bitmap.to_pil()

            ocr_text, ocr_warn = perform_ocr_on_image(pil_image, temp_dir)
            bitmap.close()

            if ocr_text:
                assembled_sections.append(f"## Page {page_num}\n\n{ocr_text}")
                stats["pages_ocr"] += 1
                ocr_pages_done.append(page_num)
            elif page_texts[idx]:
                # Fallback to sparse native text
                assembled_sections.append(f"## Page {page_num}\n\n{page_texts[idx]}")
                stats["pages_native"] += 1
            else:
                assembled_sections.append(f"## Page {page_num}\n\n*[Blank or unreadable page]*")
                stats["pages_unreadable"] += 1

        else:
            # Native text page
            # Wrap native text with page heading
            native_content = page_texts[idx]
            assembled_sections.append(f"## Page {page_num}\n\n{native_content}")
            stats["pages_native"] += 1

    doc.close()

    if ocr_pages_done:
        warnings.append(
            ConversionWarning(
                code="WARN_OCR_USED",
                user_message=f"Review scanned text on pages: {', '.join(str(p) for p in ocr_pages_done)}. Check names and numbers.",
                page_numbers=ocr_pages_done,
            )
        )

    full_markdown = "\n\n".join(assembled_sections)
    return full_markdown, warnings, stats
