# Local Markdown: Acceptance & Release Test Report

**Report Date**: 26 October 2026  
**App Version**: 1.0.0  
**Build Environment**: Windows 11 x64, Python 3.14.2, PyInstaller 6.22.3, Inno Setup 6.7.3  
**Signing Status**: Unsigned (development/open-source build; standard SmartScreen prompt applies)

---

## 1. Release Deliverables & Hashes

The following production artifacts were built and verified:

| Deliverable | Path | Size | SHA-256 Hash |
|---|---|---|---|
| **Setup Installer** | `dist_release/LocalMarkdown-Setup-1.0.0-x64.exe` | 446,827,220 bytes | `78DA69F8AB6D756163DB350847E09841BA443D57E4A8CEF010C98DD2D0A5870D` |
| **Portable ZIP** | `dist_release/LocalMarkdown-Portable-1.0.0-x64.zip` | 711,781,389 bytes | `F5E255DFE50D161607F009F9F2E7804F0986C97C9A4B41EC9302AB50A268D05E` |

---

## 2. Acceptance Matrix Results

### Section A: Content Fixtures
| ID | Description | Status | Evidence / Notes |
|---|---|---|---|
| C01 | DOCX with headings, tables, links | **PASS** | Heading hierarchy and tables preserved; links inert; tested in `test_conversion_core.py`. |
| C02 | Multi-page text PDF | **PASS** | Extracted via native PDF pipeline; verified text coverage. |
| C03 | XLSX with sheets, dates, formulas | **PASS** | Worksheet names and cached formula values preserved; hidden sheets extracted. |
| C04 | Genuine XLS workbook | **PASS** | Converted via MarkItDown XLS adapter; numbers and text survive. |
| C05 | PPTX presentations | **PASS** | Slides converted in sequential order; shape text linearized. |
| C06 | Genuine `.ppt` presentation | **PASS** | Successfully converted via isolated LibreOffice headless adapter. |
| C07 | Genuine `.doc` document | **PASS** | Converted via isolated LibreOffice headless adapter; verified in `test_legacy_office.py`. |
| C08 | Clean English scanned PDF | **PASS** | OCR applied via bundled Tesseract; text extracted; status marked `Review scan`. |
| C09 | Mixed PDF (native + scanned + blank) | **PASS** | Native pages extracted cleanly, image pages run OCR; blank page handled without error. |
| C10 | English PNG/JPEG image photo | **PASS** | Extracted via bundled OCR pipeline; verified in `test_ocr_pipeline.py`. |
| C11 | Sparse-text PDF requiring forced OCR | **PASS** | "Try scan reading" forces OCR pipeline per-page. |
| C12 | Corrupt, empty, unsupported, macro files | **PASS** | Macro files (`.docm`) rejected; corrupt files return explicit error message without crashing. |

### Section B: Desktop Workflow
| ID | Description | Status | Evidence / Notes |
|---|---|---|---|
| U01 | Install and open via shortcuts | **PASS** | Verified via Inno Setup per-user install and desktop shortcut. |
| U02 | Add file, convert, preview, save `.md` | **PASS** | Complete workflow verified; preview rendered in UI; `.md` exported. |
| U03 | Mixed batch with one corrupt file | **PASS** | Batch conversion finishes healthy files and marks corrupt file as failed. |
| U04 | Save all as ZIP | **PASS** | ZIP contains only completed `.md` files + `conversion-summary.txt`; no originals leaked. |
| U05 | Duplicate input file names | **PASS** | Handled with distinct output stems (`file.md`, `file_1.md`). |
| U06 | Stop during active conversion | **PASS** | Win32 Job Object kills entire process tree cleanly. |
| U07 | Crash recovery & stale cleanup | **PASS** | `clean_stale_jobs()` removes orphaned temp directories on next launch. |
| U08 | Persistent history & preview | **PASS** | Stored in SQLite (`history.db`) with hashed IDs; full paths not persisted. |
| U09 | Overwrite prompt on save | **PASS** | Native OS file dialog prompts before overwriting. |
| U10 | Filenames with spaces / non-ASCII | **PASS** | Handled safely in all conversion paths. |
| U11 | High DPI / Windows Scaling | **PASS** | PySide6 Qt 6 automatically respects OS scaling; tested at 100% and 150%. |
| U12 | Large result preview cap | **PASS** | Previews capped at 200,000 chars with notice; full text preserved on disk. |
| U13 | Limit enforcement | **PASS** | Preflight limits (file size > 500 MB) enforced with clear error messages. |

### Section C: Original Preservation & Cleanup
| ID | Description | Status | Evidence / Notes |
|---|---|---|---|
| D01 | Original files unchanged | **PASS** | Source file SHA-256 hashes verified before and after conversion; zero modification. |
| D02 | Remove single history item | **PASS** | Deletes SQLite row and cached preview file; original file untouched. |
| D03 | Clear History while idle | **PASS** | Clears history database and cached files; originals and user exports untouched. |
| D04 | Clear History while active | **PASS** | Button disabled during active conversion to prevent race conditions. |
| D05 | Reparse / junction escape protection | **PASS** | Containment checks prevent deletion outside `%LOCALAPPDATA%\LocalMarkdown`. |
| D06 | Safe error reporting on delete fail | **PASS** | `CleanupReport` tracks failures and reports incomplete deletions safely. |
| D07 | Zero document content in logs | **PASS** | Only file IDs and error codes logged; no private document text. |
| D08 | Clean uninstall | **PASS** | Silent uninstall verified; removes application directory cleanly. |

### Section D: Offline & Process Behavior
| ID | Description | Status | Evidence / Notes |
|---|---|---|---|
| O01 | Clean standard-user Windows account | **PASS** | Runs without admin privileges or Python on `PATH`. |
| O02 | Network disabled before launch | **PASS** | Zero remote calls or bootstrap downloads; fully offline. |
| O03 | Network disabled during batch | **PASS** | Conversions proceed locally without error. |
| O04 | Zero outbound network requests | **PASS** | `DeniedNetworkSession` blocks HTTP/HTTPS attempts from within converters. |
| O05 | Remote hyperlinks in documents | **PASS** | Hyperlink text preserved; URLs are not fetched or followed. |
| O06 | VBA macro containment | **PASS** | Macro streams detected and rejected before entering conversion engine. |
| O07 | Missing bundled component report | **PASS** | Preflight checks verify vendor existence before invoking adapters. |
| O08 | User has LibreOffice open | **PASS** | Headless adapter uses dedicated `--env:UserInstallation` profile; zero interference. |
| O09 | Portable app moved to other folder | **PASS** | Relative path resolution (`sys._MEIPASS` / `_internal`) verified in portable build. |
