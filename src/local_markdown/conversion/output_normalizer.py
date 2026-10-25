"""Output normalization for generated Markdown."""

from __future__ import annotations

import re
from typing import List, Optional

# Matches Markdown images with base64 data URIs: ![alt](data:image/...;base64,...)
BASE64_IMAGE_PATTERN = re.compile(
    r"!\[([^\]]*)\]\(data:image/[^;]+;base64,[A-Za-z0-9+/=]+\)",
    re.IGNORECASE,
)


def strip_base64_images(markdown_text: str) -> str:
    """
    Remove inline base64 image payloads to keep text lean and LLM-friendly,
    while preserving alt text / captions as a visible text note.
    """
    def _replace(match: re.Match) -> str:
        alt = match.group(1).strip()
        if alt:
            return f"*[Image: {alt}]*"
        return "*[Embedded image omitted]*"

    return BASE64_IMAGE_PATTERN.sub(_replace, markdown_text)


def normalize_markdown_content(
    basename: str,
    raw_markdown: str,
    notes: Optional[List[str]] = None,
) -> str:
    """
    Produce normalized UTF-8 Markdown with standard LF line endings.
    Adds a minimal document header with the file basename and any review notes.
    """
    # 1. Normalize line endings to LF
    text = raw_markdown.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Strip large base64 image payloads
    text = strip_base64_images(text)

    # 3. Strip trailing whitespace per line without breaking indentation
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines).strip()

    # 4. Construct lean document header
    header_parts = [f"# {basename}\n"]
    if notes:
        for note in notes:
            if note.strip():
                header_parts.append(f"> **Note**: {note.strip()}\n")
        header_parts.append("\n")

    header = "".join(header_parts)
    full_text = f"{header}{text}\n" if text else f"{header}*[No readable content extracted]*\n"
    return full_text
