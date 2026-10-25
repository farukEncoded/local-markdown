Build Local Markdown in the new project folder I have opened. This is a standalone Windows desktop app for a nontechnical client who converts everyday English documents into Markdown for use in LLMs.

First read these files in this project:

1. `docs/handoff/00-START-HERE.md`
2. `docs/handoff/01-IMPLEMENTATION-PLAN.md`
3. `docs/handoff/02-ANTIGRAVITY-HANDOFF.md`
4. `docs/handoff/04-ACCEPTANCE-AND-RELEASE-CHECKLIST.md`
5. `docs/handoff/05-REPOSITORY-REVIEW-AND-SOURCES.md`

The requirements are already clarified. Use the supplied decisions and proceed with implementation. Resolve routine details yourself. Ask only if a consequential blocker prevents progress; continue independent work while it is unresolved.

The client experience must be: click app icon → add one or several files → Convert → preview → save Markdown. Single conversion and batch conversion use the same simple interface. Support individual `.md` exports, batch ZIP export, manual copy, cancellation, persistent local result history, and Clear History. Keep all originals and manually saved exports untouched when clearing app history.

Use a native desktop window with Python 3.13 x64, PySide6 Qt Widgets, and MarkItDown as a library. Start from the reviewed `markitdown[docx,pdf,pptx,xlsx,xls]==0.1.9` dependency and lock compatible versions and hashes. Keep conversion in cancellable child processes so the interface stays responsive.

Follow the milestones in order:

- M0: prove that a frozen Windows app and its worker convert synthetic DOCX, text PDF, XLSX, XLS, and PPTX files on a clean machine without Python or Office.
- M1–M2: complete the conversion engine, batch queue, desktop interface, safe exports, history, and deletion behavior.
- M3: add English OCR for scanned/mixed PDFs and PNG/JPEG images using app-bundled Tesseract, English language data, and local PDF rendering.
- M4: add genuine older `.doc` and `.ppt` import using an app-bundled, isolated LibreOffice runtime before MarkItDown conversion. Keep this separate from any installed Office software. Disable macros and external refresh and verify the resulting files.
- M5: assemble and test the complete per-user offline installer and portable ZIP. Update the client guide against the actual interface.

The small core pilot can be delivered early with a clear support list. The full client release includes OCR and genuine `.doc` / `.ppt` support. Do not advertise missing capabilities or quietly replace those requirements with instructions for the client to install developer tools.

Everything needed at runtime must be bundled. The client must not install Python, Git, packages, OCR engines, or Office readers, set environment variables, or run commands. No account, API key, cloud service, telemetry, remote resource loading, automatic update request, or first-run download. Use only approved local converters and narrow local conversion APIs. Preview document content as inert text.

Create real synthetic fixtures and verify important content, page/sheet/slide coverage, duplicate filenames, partial batch failure, cancellation, and source-file preservation. Test Clear History against app-owned files, originals, and separately saved exports. Do not log document content or retain original full paths in persistent history. Implement bounded parsing, app-owned temporary storage, and contained cleanup as specified.

Package with PyInstaller in one-folder/windowed mode and Inno Setup for a per-user install. Verify Qt plugins, Magika models/native libraries, PDF resources, OCR language data, and the legacy reader in the frozen build. Test the final artifact with internet disabled, including first launch, and separately check for unwanted outbound activity during a normal run.

Prepare a public-ready repository with source, dependency locks, build scripts, required licenses/notices, synthetic fixtures, README, illustrated client guide, limitations, and a Windows build workflow. Keep client documents, caches, build outputs, private keys, and local environments out of Git. Prepare release artifacts and notes locally; do not create a remote repository or publish without my separate instruction.

Work through the implementation rather than stopping at an architecture proposal or a source-only demo. If the available environment prevents a required clean-machine test or reader build, finish the work you can and record the exact unverified item. Do not fabricate passing tests, installer files, signing, performance numbers, or supported formats.

At each milestone report briefly: what works, what was actually tested, and what remains. At completion provide the installer and complete portable ZIP paths, SHA-256 hashes, exact tested versions/OS, screenshots, measured package sizes, test report, and any remaining limitations. Keep all existing project files safe and keep this app separate from unrelated workspaces.
