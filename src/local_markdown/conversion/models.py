"""Data models and contracts for conversion jobs and results."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional
import uuid


class FileStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    READY = "ready"
    REVIEW = "review"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AdapterType(str, Enum):
    NATIVE = "native"
    OCR = "ocr"
    LEGACY_THEN_NATIVE = "legacy_then_native"


@dataclass
class ConversionWarning:
    code: str
    user_message: str
    page_numbers: Optional[List[int]] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConversionWarning:
        return cls(
            code=data.get("code", "WARNING"),
            user_message=data.get("user_message", ""),
            page_numbers=data.get("page_numbers"),
        )


@dataclass
class QueuedFile:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_path: Path = field(default_factory=Path)
    display_name: str = ""
    extension: str = ""
    input_size: int = 0
    status: FileStatus = FileStatus.QUEUED
    result_id: Optional[str] = None
    warnings: List[ConversionWarning] = field(default_factory=list)
    error_message: Optional[str] = None
    output_bytes: int = 0

    @classmethod
    def from_path(cls, path: Path | str) -> QueuedFile:
        p = Path(path).resolve()
        stat = p.stat()
        return cls(
            source_path=p,
            display_name=p.name,
            extension=p.suffix.lower(),
            input_size=stat.st_size,
            status=FileStatus.QUEUED,
        )


@dataclass
class ConversionResult:
    job_id: str
    status: FileStatus
    result_file: Optional[str] = None  # e.g. "results/<UUID>.md"
    warnings: List[ConversionWarning] = field(default_factory=list)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    pages_total: Optional[int] = None
    pages_native: Optional[int] = None
    pages_ocr: Optional[int] = None
    pages_unreadable: Optional[int] = None
    sheets_found: Optional[int] = None
    slides_found: Optional[int] = None
    output_bytes: int = 0
    duration_ms: int = 0
    adapter: AdapterType = AdapterType.NATIVE

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        d["adapter"] = self.adapter.value
        d["warnings"] = [w.to_dict() for w in self.warnings]
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConversionResult:
        warnings = [ConversionWarning.from_dict(w) for w in data.get("warnings", [])]
        return cls(
            job_id=data["job_id"],
            status=FileStatus(data.get("status", "failed")),
            result_file=data.get("result_file"),
            warnings=warnings,
            error_code=data.get("error_code"),
            error_message=data.get("error_message"),
            pages_total=data.get("pages_total"),
            pages_native=data.get("pages_native"),
            pages_ocr=data.get("pages_ocr"),
            pages_unreadable=data.get("pages_unreadable"),
            sheets_found=data.get("sheets_found"),
            slides_found=data.get("slides_found"),
            output_bytes=data.get("output_bytes", 0),
            duration_ms=data.get("duration_ms", 0),
            adapter=AdapterType(data.get("adapter", "native")),
        )
