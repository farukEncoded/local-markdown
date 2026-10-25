# Local Markdown: Building & Reproducing from Source

This guide provides complete instructions for building the **Local Markdown** standalone Windows desktop application, installer, and portable ZIP from source.

---

## 1. Prerequisites

- **Operating System**: Windows 10 (22H2+) or Windows 11 (64-bit).
- **Python**: Python 3.10 to 3.14 (64-bit). *(Tested with Python 3.14.2 x64)*.
- **Inno Setup**: Inno Setup 6.5+ (command-line compiler `ISCC.exe` in `PATH` or in `%LOCALAPPDATA%\Programs\Inno Setup 6`).
- **PowerShell**: Windows PowerShell 5.1 or PowerShell 7+.

---

## 2. Setting Up the Environment

1. Clone or extract the repository:
   ```powershell
   git clone https://github.com/local-markdown/local-markdown.git
   cd local-markdown
   ```

2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install pinned dependencies:
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements-build.lock
   python -m pip install -e .
   ```

---

## 3. Bundled Vendor Runtimes

Local Markdown includes offline runtimes in the `vendor/` directory:
- `vendor/tesseract/`: Tesseract OCR 5.5.x x64 binaries, DLLs, and `tessdata/eng.traineddata`.
- `vendor/libreoffice/`: Pruned headless LibreOffice 26.x runtime (`program/soffice.com`, `soffice.bin`, and `share/` with non-English dictionaries removed).

Ensure vendor contents match `vendor/components.lock.json`. Verify the structure with:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify-bundle.ps1
```

---

## 4. Running Automated Tests

To run the complete test suite:
```powershell
# Run all unit tests
.\.venv\Scripts\pytest tests/unit -v

# Run all integration tests (OCR & LibreOffice adapters)
.\.venv\Scripts\pytest tests/integration -v

# Run frozen packaging proof (tests compiled binary in isolated environment)
.\.venv\Scripts\pytest tests/packaging/test_frozen_worker.py -v
```

---

## 5. Building Release Artifacts

To execute the complete build pipeline:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1
```

This automated script performs:
1. **Vendor Verification**: Confirms Tesseract and LibreOffice binaries and checksums.
2. **PyInstaller Compilation**: Builds `dist\LocalMarkdown\` with all dependencies, native DLLs, and Magika ONNX models.
3. **Bundle Verification**: Tests file structure and required assets.
4. **Inno Setup Compilation**: Generates `dist_release\LocalMarkdown-Setup-1.0.0-x64.exe`.
5. **Portable ZIP Creation**: Compresses `dist\LocalMarkdown\` into `dist_release\LocalMarkdown-Portable-1.0.0-x64.zip`.
6. **Integrity Hashes**: Computes SHA-256 checksums for both release deliverables.
