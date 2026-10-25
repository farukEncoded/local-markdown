"""MarkItDown converter registry and isolated factory."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import requests
from markitdown import MarkItDown
from markitdown.converters import (
    DocxConverter,
    PdfConverter,
    PptxConverter,
    XlsConverter,
    XlsxConverter,
)


class DeniedNetworkSession(requests.Session):
    """Network session that unconditionally rejects all outbound requests."""

    def request(self, *args: Any, **kwargs: Any) -> Any:
        raise PermissionError("Outbound network requests are strictly disabled in Local Markdown.")

    def send(self, *args: Any, **kwargs: Any) -> Any:
        raise PermissionError("Outbound network requests are strictly disabled in Local Markdown.")


def create_isolated_markitdown() -> MarkItDown:
    """
    Construct an isolated MarkItDown instance with:
    - Built-in converters disabled (we register only approved local document converters).
    - Plugins disabled.
    - Outbound network requests blocked via DeniedNetworkSession.
    - No remote LLMs or external cloud endpoints.
    """
    session = DeniedNetworkSession()
    md = MarkItDown(
        enable_builtins=False,
        enable_plugins=False,
        requests_session=session,
    )

    # Register only approved local format converters
    md.register_converter(DocxConverter())
    md.register_converter(PptxConverter())
    md.register_converter(XlsxConverter())
    md.register_converter(XlsConverter())
    md.register_converter(PdfConverter())

    return md
