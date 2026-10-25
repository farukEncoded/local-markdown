"""App-bundled offline OCR adapter using local Tesseract."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Optional, Tuple
from PIL import Image

from local_markdown.conversion.models import ConversionWarning
from local_markdown.storage.paths import get_vendor_dir, get_bundle_dir

CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
MAX_PIXELS = 25_000_000  # 25 million pixels limit


def find_tesseract_binary() -> Optional[Path]:
    """Locate the bundled or local Tesseract executable."""
    # 1. Bundled in vendor/tesseract/
    vendor_tess = get_vendor_dir() / "tesseract" / "tesseract.exe"
    if vendor_tess.exists():
        return vendor_tess

    # 2. Frozen alongside executable
    bundle_tess = get_bundle_dir() / "tesseract" / "tesseract.exe"
    if bundle_tess.exists():
        return bundle_tess

    # 3. Check Program Files fallback on host
    prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    pf_tess = Path(prog_files) / "Tesseract-OCR" / "tesseract.exe"
    if pf_tess.exists():
        return pf_tess

    # 4. Check PATH
    import shutil
    path_tess = shutil.which("tesseract")
    if path_tess:
        return Path(path_tess)

    return None


def find_tessdata_dir() -> Optional[Path]:
    """Locate the directory containing eng.traineddata."""
    tess_exe = find_tesseract_binary()
    if tess_exe:
        local_tessdata = tess_exe.parent / "tessdata"
        if (local_tessdata / "eng.traineddata").exists():
            return local_tessdata

    vendor_tessdata = get_vendor_dir() / "tesseract" / "tessdata"
    if (vendor_tessdata / "eng.traineddata").exists():
        return vendor_tessdata

    return None


def is_ocr_available() -> bool:
    """Return True if Tesseract and English traineddata are available."""
    exe = find_tesseract_binary()
    tessdata = find_tessdata_dir()
    return exe is not None and tessdata is not None


def perform_ocr_on_image(
    image_input: Path | Image.Image,
    temp_dir: Path,
    timeout_seconds: int = 30,
) -> Tuple[str, Optional[ConversionWarning]]:
    """
    Perform local OCR on an image file or PIL Image.
    Returns (extracted_text, optional_warning).
    """
    temp_dir = Path(temp_dir).resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    tess_exe = find_tesseract_binary()
    tessdata_dir = find_tessdata_dir()

    if not tess_exe or not tessdata_dir:
        return (
            "",
            ConversionWarning(
                code="WARN_OCR_MISSING",
                user_message="Local OCR engine is not bundled in this build.",
            ),
        )

    # Prepare image path and enforce pixel bounds
    cleanup_temp_image = False
    if isinstance(image_input, Image.Image):
        img = image_input
        # Check pixel bounds
        pixels = img.width * img.height
        if pixels > MAX_PIXELS:
            ratio = (MAX_PIXELS / pixels) ** 0.5
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        img_path = temp_dir / "ocr_input.png"
        img.save(img_path, format="PNG")
        cleanup_temp_image = True
    else:
        img_path = Path(image_input).resolve()
        # Check pixel bound of existing image file
        with Image.open(img_path) as img:
            pixels = img.width * img.height
            if pixels > MAX_PIXELS:
                ratio = (MAX_PIXELS / pixels) ** 0.5
                new_size = (int(img.width * ratio), int(img.height * ratio))
                resized = img.resize(new_size, Image.Resampling.LANCZOS)
                img_path = temp_dir / "ocr_input_resized.png"
                resized.save(img_path, format="PNG")
                cleanup_temp_image = True

    out_base = (temp_dir / "ocr_output").resolve()
    cmd = [
        str(tess_exe),
        str(img_path),
        str(out_base),
        "--tessdata-dir",
        str(tessdata_dir),
        "-l",
        "eng",
    ]

    try:
        env = os.environ.copy()
        env["TESSDATA_PREFIX"] = str(tessdata_dir)
        # Add tesseract folder to PATH so DLLs can load
        env["PATH"] = f"{tess_exe.parent};{env.get('PATH', '')}"

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            creationflags=CREATE_NO_WINDOW,
            cwd=str(temp_dir),
            env=env,
        )

        out_txt = out_base.with_suffix(".txt")
        if out_txt.exists():
            text = out_txt.read_text(encoding="utf-8", errors="replace").strip()
            out_txt.unlink(missing_ok=True)
            warning = ConversionWarning(
                code="WARN_OCR_USED",
                user_message="Review scanned text. Check names and numbers.",
            )
            return text, warning
        else:
            return "", ConversionWarning(
                code="WARN_OCR_EMPTY",
                user_message="No readable text detected by OCR.",
            )

    except subprocess.TimeoutExpired:
        return "", ConversionWarning(
            code="WARN_OCR_TIMEOUT",
            user_message=f"OCR timed out after {timeout_seconds} seconds.",
        )
    except Exception as e:
        return "", ConversionWarning(
            code="WARN_OCR_FAILED",
            user_message=f"OCR processing error: {e}",
        )
    finally:
        if cleanup_temp_image and img_path.exists():
            img_path.unlink(missing_ok=True)
