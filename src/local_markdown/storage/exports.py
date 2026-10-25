"""Export handlers for single Markdown files and batch ZIP archives."""

from __future__ import annotations

import os
from pathlib import Path
import re
from typing import List, Tuple
import zipfile

from local_markdown.conversion.models import ConversionWarning

RESERVED_WINDOWS_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


def sanitize_filename(name: str) -> str:
    """Sanitize a filename for safe Windows filesystem and ZIP member naming."""
    # Replace illegal Windows characters: < > : " / \ | ? *
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    # Strip leading/trailing spaces and dots
    sanitized = sanitized.strip(" .")
    if not sanitized:
        sanitized = "unnamed_document"

    stem = Path(sanitized).stem.upper()
    if stem in RESERVED_WINDOWS_NAMES:
        sanitized = f"_{sanitized}"

    return sanitized


def get_unique_filename(existing_names: set[str], desired_name: str) -> str:
    """Deterministically resolve duplicate names: doc.md -> doc (2).md, etc."""
    lower_existing = {n.lower() for n in existing_names}
    if desired_name.lower() not in lower_existing:
        existing_names.add(desired_name)
        return desired_name

    stem = Path(desired_name).stem
    suffix = Path(desired_name).suffix
    counter = 2
    while True:
        candidate = f"{stem} ({counter}){suffix}"
        if candidate.lower() not in lower_existing:
            existing_names.add(candidate)
            return candidate
        counter += 1


def export_single_markdown(markdown_content: str, destination_path: Path | str) -> Path:
    """
    Export Markdown to destination atomically.
    Ensures UTF-8 encoding and LF line endings.
    """
    dest = Path(destination_path).resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)

    temp_dest = dest.with_suffix(".tmp_export")
    with open(temp_dest, "w", encoding="utf-8", newline="\n") as f:
        f.write(markdown_content)
        f.flush()
        os.fsync(f.fileno())

    os.replace(temp_dest, dest)
    return dest


def export_batch_zip(
    ready_items: List[Tuple[str, str, str, List[ConversionWarning]]],
    zip_destination: Path | str,
) -> Path:
    """
    Export a batch of converted documents as a ZIP archive.
    ready_items is a list of tuples: (display_name, status, markdown_text, warnings).
    Includes a conversion-summary.txt at the root of the archive.
    """
    dest = Path(zip_destination).resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp_zip = dest.with_suffix(".tmp_zip")

    used_names: set[str] = set()
    summary_lines = [
        "Local Markdown - Batch Conversion Summary",
        "========================================",
        f"Total documents converted: {len(ready_items)}",
        "",
        "Files in this archive:",
    ]

    with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for display_name, status, content, warnings in ready_items:
            base_stem = Path(display_name).stem
            sanitized_stem = sanitize_filename(base_stem)
            target_name = get_unique_filename(used_names, f"{sanitized_stem}.md")

            # Write document markdown
            encoded = content.encode("utf-8")
            zf.writestr(target_name, encoded)

            # Record in summary
            warn_str = ""
            if warnings:
                warn_msgs = [f"[{w.code}] {w.user_message}" for w in warnings]
                warn_str = f" | Warnings: {'; '.join(warn_msgs)}"
            summary_lines.append(f"- {target_name} (from '{display_name}', status: {status}){warn_str}")

        summary_lines.append("")
        summary_lines.append("Converted locally with Local Markdown.")
        summary_text = "\n".join(summary_lines) + "\n"
        zf.writestr("conversion-summary.txt", summary_text.encode("utf-8"))

    os.replace(temp_zip, dest)
    return dest
