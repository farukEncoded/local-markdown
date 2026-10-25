"""Legacy Office document (.doc, .ppt) normalization via isolated LibreOffice."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Optional, Tuple
import zipfile

from local_markdown.conversion.models import ConversionWarning
from local_markdown.conversion.validation import ValidationError
from local_markdown.storage.paths import get_vendor_dir, get_bundle_dir

CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
LEGACY_CONVERSION_TIMEOUT_SECONDS = 120


def find_libreoffice_binary() -> Optional[Path]:
    """Locate the bundled or local LibreOffice executable (soffice.com preferred for CLI, or soffice.exe)."""
    names = ["soffice.com", "soffice.exe"] if sys.platform == "win32" else ["soffice"]

    # 1. Bundled in vendor/libreoffice/program/
    for name in names:
        vendor_soffice = get_vendor_dir() / "libreoffice" / "program" / name
        if vendor_soffice.exists():
            return vendor_soffice

    # 2. Frozen alongside executable
    for name in names:
        bundle_soffice = get_bundle_dir() / "libreoffice" / "program" / name
        if bundle_soffice.exists():
            return bundle_soffice

    # 3. Check Program Files fallback on host
    for pf_name in ("ProgramFiles", "ProgramFiles(x86)"):
        pf = os.environ.get(pf_name)
        if pf:
            for name in names:
                candidate = Path(pf) / "LibreOffice" / "program" / name
                if candidate.exists():
                    return candidate

    # 4. Check PATH
    for name in ("soffice.com", "soffice"):
        which_soffice = shutil.which(name)
        if which_soffice:
            return Path(which_soffice)

    return None


def is_legacy_office_available() -> bool:
    """Return True if LibreOffice runtime is detected."""
    return find_libreoffice_binary() is not None


def convert_legacy_to_modern(
    source_path: Path,
    job_dir: Path,
    target_format: str,  # "docx" or "pptx"
) -> Tuple[Path, ConversionWarning]:
    """
    Convert a legacy .doc or .ppt file into a modern intermediate (.docx or .pptx)
    using an isolated, headless LibreOffice profile.
    """
    soffice_exe = find_libreoffice_binary()
    if not soffice_exe:
        raise ValidationError(
            "E_LEGACY_UNAVAILABLE",
            "The legacy Office importer runtime is not available in this build.",
        )

    source_path = Path(source_path).resolve()
    job_dir = Path(job_dir).resolve()

    # Create isolated user installation directory for this specific job
    profile_dir = job_dir / "lo_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    out_dir = job_dir / "lo_out"
    out_dir.mkdir(parents=True, exist_ok=True)

    profile_uri = profile_dir.as_uri()

    cmd = [
        str(soffice_exe),
        f"-env:UserInstallation={profile_uri}",
        "--headless",
        "--invisible",
        "--nocrashreport",
        "--nodefault",
        "--nofirststartwizard",
        "--nolockcheck",
        "--nologo",
        "--norestore",
        "--convert-to",
        target_format,
        str(source_path),
        "--outdir",
        str(out_dir),
    ]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=LEGACY_CONVERSION_TIMEOUT_SECONDS,
            creationflags=CREATE_NO_WINDOW,
            cwd=str(job_dir),
        )

        expected_file = out_dir / f"{source_path.stem}.{target_format}"
        if not expected_file.exists() or expected_file.stat().st_size == 0:
            raise ValidationError(
                "E_LEGACY_CONVERSION_FAILED",
                f"Failed to convert legacy document: intermediate {target_format.upper()} was not created.",
            )

        # Validate that intermediate is a valid ZIP/OOXML
        if not zipfile.is_zipfile(expected_file):
            raise ValidationError(
                "E_INVALID_INTERMEDIATE",
                f"Converted intermediate {target_format.upper()} is corrupted.",
            )

        warning = ConversionWarning(
            code="WARN_LEGACY_IMPORT",
            user_message=f"Converted from legacy {source_path.suffix.upper()} format. Please review formatting and tables.",
        )
        return expected_file, warning

    except subprocess.TimeoutExpired:
        raise ValidationError(
            "E_LEGACY_TIMEOUT",
            f"Legacy conversion timed out after {LEGACY_CONVERSION_TIMEOUT_SECONDS} seconds.",
        )
    finally:
        # Cleanup isolated profile
        if profile_dir.exists():
            shutil.rmtree(profile_dir, ignore_errors=True)
