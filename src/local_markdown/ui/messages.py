"""User-facing messages and confirmation dialog helpers."""

from __future__ import annotations

APP_TITLE = "Local Markdown"
APP_SUBTITLE = "Turn documents into Markdown on your computer"
WORKS_OFFLINE_LABEL = "Works offline"

MSG_EMPTY_STATE = "Add documents to get started."
MSG_SUPPORTED_FORMATS = (
    "Supported: Word (.docx, .doc), PDF (.pdf), Excel (.xlsx, .xls), "
    "PowerPoint (.pptx, .ppt), Images (.png, .jpg, .jpeg)"
)

CONFIRM_CLEAR_HISTORY = (
    "Clear history and stored previews?\n\n"
    "Original documents and saved Markdown files will stay on your computer."
)

MSG_PREVIEW_TRUNCATED = "Showing the first 200,000 characters. Saving includes the full result."
