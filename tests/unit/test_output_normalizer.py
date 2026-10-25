"""Unit tests for output markdown normalization and base64 image stripping."""

from __future__ import annotations

from local_markdown.conversion.output_normalizer import (
    normalize_markdown_content,
    strip_base64_images,
)


def test_strip_base64_images():
    raw = "Here is an image: ![Company Logo](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==) and some text."
    cleaned = strip_base64_images(raw)
    assert "data:image/png;base64" not in cleaned
    assert "*[Image: Company Logo]*" in cleaned
    assert "and some text." in cleaned


def test_normalize_markdown_content():
    raw = "Line 1\r\nLine 2\r\n\r\nLine 3   \r\n"
    notes = ["Review scanned text."]
    res = normalize_markdown_content("report.pdf", raw, notes=notes)

    assert res.startswith("# report.pdf\n")
    assert "> **Note**: Review scanned text." in res
    assert "\r" not in res
    assert "Line 1\nLine 2\n\nLine 3" in res
