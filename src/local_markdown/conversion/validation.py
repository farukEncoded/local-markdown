"""Preflight validation for inputs before conversion."""

from __future__ import annotations

import os
from pathlib import Path
import zipfile
from typing import Optional, Set

try:
    import olefile
except ImportError:
    olefile = None

CORE_EXTENSIONS: Set[str] = {".docx", ".pdf", ".xlsx", ".xls", ".pptx"}
FULL_EXTENSIONS: Set[str] = CORE_EXTENSIONS | {".doc", ".ppt", ".png", ".jpg", ".jpeg"}

MAX_INPUT_BYTES = 100 * 1024 * 1024  # 100 MiB
MAX_OOXML_ENTRIES = 20000
MAX_OOXML_DECOMPRESSED_BYTES = 500 * 1024 * 1024  # 500 MiB


class ValidationError(Exception):
    def __init__(self, code: str, user_message: str):
        super().__init__(user_message)
        self.code = code
        self.user_message = user_message


def validate_file_preflight(
    path: Path | str,
    allow_legacy_and_images: bool = True,
) -> None:
    """
    Perform preflight validation on an input document.
    Raises ValidationError with a client-safe code and message if invalid.
    """
    p = Path(path)

    if not p.exists():
        raise ValidationError("E_FILE_NOT_FOUND", "This file could not be found.")

    if p.is_dir():
        raise ValidationError("E_IS_DIRECTORY", "Folders cannot be converted directly. Please select individual files.")

    ext = p.suffix.lower()

    if ext in {".lnk", ".url"}:
        raise ValidationError("E_SHORTCUT", "Shortcuts and links are not supported. Please select the original document.")

    if ext in {".docm", ".xlsm", ".pptm"}:
        raise ValidationError("E_MACRO_ENABLED", "Macro-enabled files (.docm, .xlsm, .pptm) are not supported for safety.")

    allowed = FULL_EXTENSIONS if allow_legacy_and_images else CORE_EXTENSIONS
    if ext not in allowed:
        types_str = ", ".join(sorted(allowed))
        raise ValidationError(
            "E_UNSUPPORTED_TYPE",
            f"The '{ext}' file type is not supported by this build. Supported: {types_str}",
        )

    try:
        size = p.stat().st_size
    except OSError as e:
        raise ValidationError("E_ACCESS_DENIED", f"Cannot read file properties: {e}")

    if size == 0:
        raise ValidationError("E_EMPTY_FILE", "This file is empty (0 bytes).")

    if size > MAX_INPUT_BYTES:
        raise ValidationError(
            "E_TOO_LARGE",
            f"File size ({size / (1024*1024):.1f} MiB) exceeds the maximum limit of {MAX_INPUT_BYTES // (1024*1024)} MiB.",
        )

    # Inspect containers according to extension
    if ext in {".docx", ".pptx", ".xlsx"}:
        _validate_ooxml_container(p)
    elif ext == ".pdf":
        _validate_pdf_container(p)
    elif ext in {".xls", ".doc", ".ppt"}:
        _validate_ole_container(p, ext)
    elif ext in {".png", ".jpg", ".jpeg"}:
        _validate_image_container(p)


def _validate_ooxml_container(path: Path) -> None:
    """Validate OOXML (ZIP container) entries, decompression ratio, and macros."""
    if not zipfile.is_zipfile(path):
        raise ValidationError("E_INVALID_CONTAINER", "This file is corrupted or not a valid Office document.")

    try:
        with zipfile.ZipFile(path, "r") as zf:
            namelist = zf.namelist()
            if len(namelist) > MAX_OOXML_ENTRIES:
                raise ValidationError("E_OOXML_LIMIT", f"Document archive contains too many entries ({len(namelist)}).")

            total_uncompressed = 0
            for info in zf.infolist():
                total_uncompressed += info.file_size
                if total_uncompressed > MAX_OOXML_DECOMPRESSED_BYTES:
                    raise ValidationError("E_OOXML_LIMIT", "Document uncompressed size exceeds safety limits.")

                # Check for password encryption
                if info.flag_bits & 0x1:
                    raise ValidationError(
                        "E_PASSWORD_PROTECTED",
                        "This file is password protected. Save an unlocked copy and try again.",
                    )

                # Check for macro projects
                lower_name = info.filename.lower()
                if "vbaProject.bin" in lower_name or lower_name.endswith("vba"):
                    raise ValidationError("E_MACRO_ENABLED", "Document contains embedded macros, which are disabled.")

    except zipfile.BadZipFile:
        raise ValidationError("E_INVALID_CONTAINER", "This file is corrupted or not a valid Office document.")
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError("E_CORRUPTED", f"Failed inspecting document container: {e}")


def _validate_pdf_container(path: Path) -> None:
    """Validate PDF header and encryption."""
    with open(path, "rb") as f:
        header = f.read(1024)
        if b"%PDF-" not in header:
            raise ValidationError("E_INVALID_CONTAINER", "The file is not a valid PDF document.")

    # Try opening with pypdfium2 to check if password protected or corrupt
    try:
        import pypdfium2 as pdfium
        try:
            doc = pdfium.PdfDocument(str(path))
            # Access page count
            _ = len(doc)
            doc.close()
        except pdfium.PdfiumError as pe:
            err_msg = str(pe).lower()
            if "password" in err_msg or "encrypt" in err_msg:
                raise ValidationError(
                    "E_PASSWORD_PROTECTED",
                    "This file is password protected. Save an unlocked copy and try again.",
                )
            raise ValidationError("E_INVALID_CONTAINER", f"PDF structure error: {pe}")
    except ImportError:
        pass


def _validate_ole_container(path: Path, ext: str) -> None:
    """Validate legacy OLE container (.xls, .doc, .ppt) and check for VBA macros."""
    with open(path, "rb") as f:
        magic = f.read(8)
        # Standard OLE Compound File header is \xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1
        if magic != b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            raise ValidationError(
                "E_INVALID_CONTAINER",
                f"The file is not a valid legacy OLE {ext.upper()} document.",
            )

    if olefile is not None:
        try:
            if olefile.isOleFile(str(path)):
                with olefile.OleFileIO(str(path)) as ole:
                    # Check for VBA or macros
                    for stream in ole.listdir():
                        stream_path = "/".join(stream).lower()
                        if "vba" in stream_path or "macro" in stream_path:
                            raise ValidationError(
                                "E_MACRO_ENABLED",
                                "Legacy document contains embedded macros, which are disabled.",
                            )
                        if "encryptedpackage" in stream_path:
                            raise ValidationError(
                                "E_PASSWORD_PROTECTED",
                                "This file is password protected. Save an unlocked copy and try again.",
                            )
        except ValidationError:
            raise
        except Exception:
            # If inspection fails, allow converter to handle or fail
            pass


def _validate_image_container(path: Path) -> None:
    """Validate image header using Pillow."""
    try:
        from PIL import Image
        with Image.open(path) as img:
            img.verify()
    except Exception:
        raise ValidationError("E_INVALID_CONTAINER", "The file is not a valid or readable image.")
