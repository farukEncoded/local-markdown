# Local Markdown Vendor Runtimes

This folder contains app-local, redistributable binary runtimes for offline conversion:

1. **Tesseract-OCR (`vendor/tesseract/`)**:
   - Version: 5.5.3 (x64 Windows)
   - License: Apache License 2.0
   - Purpose: Offline printed English optical character recognition for scanned PDFs and images.
   - Pinned Data: `tessdata/eng.traineddata`

2. **LibreOffice Standalone Runtime (`vendor/libreoffice/`)**:
   - Version: 26.8.1.1 (x64 Windows)
   - License: Mozilla Public License 2.0 (MPL-2.0)
   - Purpose: Headless conversion of legacy binary Office files (`.doc`, `.ppt`) into modern OOXML intermediates (`.docx`, `.pptx`).
   - Profile: Executed with `-env:UserInstallation` pointing to a per-job isolated temporary directory with macros and external updates disabled.
