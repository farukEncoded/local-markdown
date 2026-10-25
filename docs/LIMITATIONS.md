# Local Markdown: Known Limitations & Boundaries

This document details the technical boundaries, format trade-offs, and intentional design decisions in **Local Markdown 1.0.0**.

---

## 1. Document Format Boundaries

### Spreadsheets (Excel `.xlsx` / `.xls`)
- **Formula Evaluation**: Formulas are extracted as their last-saved cached values. Dynamic formula evaluation without opening Excel is unsupported.
- **Hidden Sheets**: Worksheets marked as hidden in the workbook structure are extracted by default with their sheet names preserved.
- **Charts and Macro Sheets**: Embedded visual charts, PivotTable caches, and Excel 4.0 macro sheets are omitted from text output.

### Word Documents (`.docx` / `.doc`)
- **Macro Blocking**: Macro-enabled files (`.docm`) or legacy `.doc` files containing VBA macro streams are rejected at preflight to prevent malicious code execution.
- **Comments and Revisions**: Tracked changes and comment bubbles are not converted into the main body text.
- **Embedded Objects**: Embedded OLE objects (e.g. an embedded PDF or sound clip inside Word) are ignored.

### Presentations (PowerPoint `.pptx` / `.ppt`)
- **Slide Text Flow**: Text frames and shapes are converted in slide order. Complex overlapping text boxes are linearized.
- **Speaker Notes**: Presenter notes are omitted to prioritize primary slide content for LLMs.
- **Animations and Transitions**: Visual effects are ignored.

### PDFs (`.pdf`)
- **Digital vs. Scanned**: Digital PDFs extract native text layers. If a page contains no text (e.g. a scanned image), it automatically routes through the bundled Tesseract OCR engine.
- **Reading Order**: Multi-column documents are linearized from top-to-bottom and left-to-right. Complex newspaper-style layouts may interleave columns if bounding boxes overlap.
- **Encrypted / Password Protected**: Password-protected PDFs are rejected with a clear preflight message.

### OCR (Scanned PDFs & Images)
- **Language Scope**: Bundled with English trained data (`eng.traineddata`). Non-English languages are not currently bundled.
- **Image Quality**: Degraded scans, low-contrast photocopies, heavily distorted text, or handwriting may have lower recognition confidence and will be flagged with `⚠ Review scan`.
- **Image Size**: Images exceeding 50 MB or 10,000 pixels in either dimension are rejected to prevent out-of-memory denial of service.

---

## 2. LLM Output Normalization

- **Image Payload Stripping**: Base64 data URIs (e.g. `data:image/png;base64,...`) are stripped from Markdown and replaced with clean `![Image: Description]` tags. This prevents massive binary token bloat when sending Markdown to LLMs.
- **Line Ending Normalization**: All exported files standardize on Unix LF (`\n`) line endings regardless of source OS.
- **Preview Truncation**: Documents with output exceeding 200,000 characters are capped in the GUI preview pane for UI responsiveness. A notice is displayed, and the **full, untruncated content** is always written to disk when saving or exporting.

---

## 3. Storage & Process Safety

- **Non-Destructive Guarantee**: Original documents are opened in read-only mode (`rb`) and are never written to, moved, or deleted.
- **Temporary Containment**: Conversions happen inside `%LOCALAPPDATA%\LocalMarkdown\temp`. All temporary directories are isolated by unique job IDs and cleaned up automatically.
- **Junction / Reparse Protection**: File operations verify that target directories remain strictly inside app-owned storage bounds, refusing to follow symbolic links or NTFS directory junctions.
