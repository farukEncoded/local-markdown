# Local Markdown: technical handoff for Antigravity

Prepared 25 October 2026. Implement the product in `01-IMPLEMENTATION-PLAN.md`. This file defines the engineering contracts. The acceptance checklist governs release claims.

## 1. Working boundary

Work in the new `local-markdown` project opened by the user. Detect the actual project root instead of assuming the example absolute path. Keep this handoff in `docs/handoff/`. Do not modify the ExBankersClub materials that originally held the handoff package.

Create a standalone application that depends on the released MarkItDown package. Do not copy the upstream repository into this project or build a hosted service. Do not create a remote GitHub repository or publish a release without a separate instruction from the owner.

The primary delivery target is Windows 11 x64, with Windows 10 22H2 x64 as a compatibility target. Verify both before claiming both. ARM and 32-bit builds are outside the initial scope. Record the OS versions actually tested.

## 2. Suggested repository structure

```text
local-markdown/
  pyproject.toml
  requirements-runtime.lock
  requirements-build.lock
  README.md
  LICENSE
  THIRD-PARTY-NOTICES.md
  .gitignore
  src/local_markdown/
    __init__.py
    __main__.py
    app.py
    ui/
      main_window.py
      file_model.py
      history_view.py
      messages.py
      styles.qss
    conversion/
      service.py
      registry.py
      validation.py
      models.py
      pdf_pipeline.py
      ocr.py
      legacy_office.py
      output_normalizer.py
    jobs/
      controller.py
      worker.py
      protocol.py
      windows_process_tree.py
    storage/
      paths.py
      history.py
      cleanup.py
      exports.py
    resources/
      app.ico
      capabilities.json
  vendor/
    README.md
    components.lock.json
  packaging/
    LocalMarkdown.spec
    installer.iss
    hooks/
  scripts/
    bootstrap-dev.ps1
    prepare-vendor.ps1
    build-windows.ps1
    verify-bundle.ps1
  tests/
    fixtures/
    unit/
    integration/
    packaging/
  docs/
    handoff/
    CLIENT-GUIDE.md
    BUILDING.md
    LIMITATIONS.md
    TEST-REPORT.md
    screenshots/
  .github/workflows/windows-build.yml
```

This structure is a starting point. Combine small modules when that makes the code clearer, but retain the conversion/UI/storage boundaries. Keep binary vendor payloads out of ordinary Git history. Build scripts may fetch verified dependencies while the developer is online; client installation and first launch must use the assembled offline payload.

## 3. Dependencies and converter factory

Use Python 3.13 x64, PySide6 Qt Widgets, and `markitdown[docx,pdf,pptx,xlsx,xls]==0.1.9` as the reviewed starting point. Pin all resolved versions and hashes in the Windows lockfiles, including build tools. If a newer version is required, record why and rerun the conversion/packaging checks.

For the conversion factory:

- Construct `MarkItDown(enable_builtins=False, enable_plugins=False, requests_session=deny_network_session)`.
- Explicitly register only `DocxConverter`, `PptxConverter`, `XlsxConverter`, `XlsConverter`, and `PdfConverter` from `markitdown.converters`.
- Use `convert_local()` on a validated app-owned staged file, or `convert_stream()` on its controlled binary stream.
- Read `result.markdown` from the returned result.
- Do not set LLM clients, Azure endpoints, plugin discovery, or remote conversion handlers.
- Do not install the `[all]` extra. Its extra formats/cloud integrations are outside this app's scope.

These public API names were confirmed in the published 0.1.9 wheel. Recheck their behavior in the real application tests; this handoff contains no executable conversion test results.

The denied HTTP session should fail immediately if asked to send a request. This is one defense, not a network sandbox for every third-party parser or child process. Keep inputs and adapters local, disable external resource refresh, and verify process behavior at release testing.

## 4. Supported inputs and preflight

Core allowlist: `.docx`, `.pdf`, `.xlsx`, `.xls`, `.pptx`.

Full-build additions: `.doc`, `.ppt`, `.png`, `.jpg`, `.jpeg`.

Reject unsupported extensions, directories, shortcuts, URI strings, network shares/mapped network locations, nonexistent files, and files whose actual container is inconsistent with the selected format. Do not recursively traverse folders. A cloud-only placeholder should produce “Make this file available offline, then try again” instead of intentionally initiating a cloud download. Do not promise to control unrelated operating-system sync services.

Use standard file dialogs and accept local file drops through Qt's local-file URLs. Do not interpret dropped text as a path or URL to fetch. Read files without writing to their original locations. Revalidate at the time the worker opens the file because it may have changed after selection.

Check OOXML ZIP metadata for pathological entry counts and decompressed sizes before opening the document. Do not extract archive members to arbitrary filesystem paths. Treat password/encryption failures and macro-enabled formats as explicit unsupported cases. Inspect legacy OLE files for embedded VBA projects before handing them to the legacy importer; add an explicit `olefile` dependency if used for that validation.

## 5. Worker model and cancellation

Use a persistent GUI controller with a sequential queue. Start a new worker process for each file. Never parse documents, perform large file copies, or wait for child processes on the UI thread.

Allow only one GUI instance to own the data root, using a QLockFile or equivalent verified lock. A second launch should bring the existing window forward or explain that the app is already open. Worker mode bypasses the GUI-instance lock. Crash recovery must not purge a job owned by a live process or another Windows session.

Use a single application entry point with an early `--worker <manifest-path>` route before creating `QApplication`. In source mode launch the module through the chosen Python interpreter; in frozen mode relaunch the bundled executable with the worker arguments. Test both routes. Hide any child console window.

Use QProcess to manage the worker and a Windows Job Object, or an equally verified Windows mechanism, to own the worker's complete process tree. Cancel/timeout/app exit must terminate only the app's current job and its children. Never kill every process named `soffice.exe` or interfere with a user's open Office applications.

Keep IPC file-based so it works with a windowed frozen executable that has no standard console streams:

1. Controller creates an owned UUID job directory and `job.json`.
2. Worker reads the manifest, validates paths, copies the source into that directory, and converts it.
3. Worker writes `progress.json` with atomic replacement. Controller polls it through a nonblocking Qt timer.
4. Worker writes `result.md` and a terminal `result.json`, also atomically.
5. Controller validates job ID, schema, output size, and contained paths; then commits the result to history.
6. Controller clears the job directory after completion, cancellation, or failure. Startup recovery clears only stale app-owned jobs and marks interrupted work accurately.

The worker is a crash/cancellation boundary, not an OS security sandbox. Keep this distinction in technical documentation.

## 6. Data contracts

Use typed records or dataclasses. At minimum:

```text
QueuedFile:
  id: UUID
  source_path: absolute path, current session / temporary job only
  display_name: basename
  extension: normalized extension
  input_size: integer bytes
  status: queued | running | ready | review | failed | cancelled

ConversionResult:
  job_id: UUID
  status: ready | review | failed | cancelled
  result_file: relative app-owned result filename, optional
  warnings: list of {code, user_message, page_numbers?}
  error_code: optional controlled value
  pages_total / pages_native / pages_ocr / pages_unreadable: optional counts
  sheets_found / slides_found: optional counts
  output_bytes: integer
  duration_ms: integer
  adapter: native | ocr | legacy_then_native
```

Stored history must not contain original full paths or document contents in database fields. Store the basename, job/result ID, time, status, adapter, size, and controlled warnings. Result text lives in a contained UUID-named cache file. Export paths are session state, not prerequisites for history deletion.

Use schema versions and atomic commits. A file becomes `ready` only after its nonempty output is safely committed. A `review` result can be exported with warnings. `failed` and `cancelled` items have no normal Markdown export. If some PDF pages were unreadable, preserve page markers, clearly mark the result `review`, and include a visible warning in the Markdown as well as the UI.

For batch export, include only ready/review results and a `conversion-summary.txt` listing basenames, statuses, and warnings. Do not include originals, temporary files, full paths, or stack traces. Exclude failed results rather than generating plausible empty substitutes.

## 7. Markdown behavior

Write UTF-8 with LF line endings. Preserve extracted text, numbers, section order, and supported structure. Avoid generative rewriting, aggressive whitespace changes, or cleanup rules that destroy tables and code blocks.

Use one small document header containing the source basename. Add an OCR/import/incomplete-page note when applicable. Do not add machine paths, user account names, arbitrary summaries, or a large boilerplate preamble.

Use a read-only QPlainTextEdit for preview so document content is treated as inert text. Limit the displayed preview while preserving the complete cached/exported result. Label truncated previews: “Showing the first part. Saving includes the full result.” Never fetch linked images or open links automatically.

Remove base64 image payloads that are unusable in this text workflow without deleting nearby captions or alt text. Record that embedded diagrams/images may be omitted; do not infer their contents. Test named numbers and structured content rather than Markdown byte equality across library upgrades.

Workbook expectations: preserve worksheet names and order and explain stored values versus formula calculations. Warn on hidden sheets and formula cells with absent cached values where detectable. Do not refresh external data, run macros, or recalculate. When a workbook contains only formulas with no cached results, do not report a fully successful extraction of the missing values.

## 8. PDF and scan adapter

For a normal text PDF, keep the native MarkItDown path. For scan handling, use pypdfium2 for local page inspection/rendering and app-bundled Tesseract with app-bundled English data. Use Pillow for bounded image preprocessing where needed.

The PDF planner must inspect every page. A low native alphanumeric count can flag a page for OCR, but a sparse page is not automatically a scan; distinguish blank pages where possible. Make thresholds configurable in code, not a first-run settings screen. Preserve native text that exists on sparse pages.

If every page has adequate text, use normal whole-document conversion. If OCR is needed on any pages, use a per-page pipeline: create a temporary single-page PDF for native pages and convert it through MarkItDown; render and OCR the remaining pages; assemble exactly one section per original page in source order. Do not append whole-document text and per-page OCR together. Clean the intermediates immediately.

Provide **Try scan reading** on a selected PDF to force the OCR path when the heuristic misses image text. Forced OCR still uses one output per page, warns about OCR, and respects the same limits. Do not automatically OCR every embedded Office image in this release.

Set English explicitly and resolve `tesseract.exe`, DLLs, and `tessdata/eng.traineddata` from the app resources. Use an argument list with `shell=False`, a controlled working directory and temporary paths, bounded time, and no visible console. A direct subprocess adapter is sufficient; a second OCR wrapper library is not required.

A missing OCR runtime is a build capability failure, not a signal to call a cloud API. The core pilot can show a friendly unsupported-scan message; the full release must pass OCR preflight. Test visible output against known printed text, not merely an executable version check.

## 9. Legacy Office adapter

The full build uses its own pinned LibreOffice runtime. Keep it separate from any installed copy and from the user's existing profile. A supported reader tree must be included in the installer/portable bundle; an untested copy of only `soffice.exe` is insufficient.

Invoke the app-local executable with a unique `-env:UserInstallation=<job-profile-file-URI>`, headless/no-first-run options, `--convert-to docx` or `--convert-to pptx`, and an owned output directory. Derive the file URI with a path API, not manual space escaping. Pass arguments directly without a shell. Verify actual flags and output filters against the pinned runtime.

Configure the isolated profile to disable macro execution, external link updates, recovery prompts, and update checks. Reject macro-bearing legacy files before import. Do not use normal launch parameters alone as evidence that macros or external refresh are disabled. Include fixtures/canaries demonstrating the policy without executing malicious content.

Wait for the conversion with timeout and process-tree ownership. Check that the expected intermediate exists, is nonempty, is a valid modern Office container, and is contained in the current job. Then pass it to the same MarkItDown adapter. Include an older-format review warning. Delete the temporary source copy, converted Office file, and private LibreOffice profile after use.

Resolve packaging/source availability, notices, and the runtime's redistribution requirements against the exact version used. If the bundled reader cannot be delivered, report it explicitly as an unfinished full-build milestone; do not make the client install or configure it through a command prompt.

## 10. UI state and wording

Keep one resizable desktop window with a file list and preview. Use system fonts, keyboard focus states, native dialogs, a simple app icon, and adequate contrast. Target an initial size around 1050 × 720, with a usable smaller layout and 100–200% Windows display scaling.

| Condition | Wording / behavior |
|---|---|
| Empty | “Add documents to get started.” |
| Batch active | “Converting 3 of 8: report.pdf”; Stop available |
| Successful | “Ready to save” |
| OCR used | “Review scanned text. Check names and numbers.” |
| No text | “No readable text found. Try scan reading or use a clearer document.” |
| Locked file | “This file is password protected. Save an unlocked copy and try again.” |
| Unsupported | “This file type is not supported by this build.”; list supported types |
| Source unavailable | “This file could not be opened. Check that it is available on this computer.” |
| Missing bundled reader | Explain capability failure and show support/build information; never suggest installing Python |
| Clear history | “Clear history and stored previews? Original documents and saved Markdown files will stay.” |

Convert processes queued files only. Completed history must not be reconverted by accident. Disable Clear History during active work until Stop completes. Do not remove an active job's data underneath its process. The app must remain usable after one file fails.

## 11. Initial engineering limits

These are starting defaults to validate, not measured performance promises:

| Limit | Initial value |
|---|---:|
| Files per batch | 100 |
| Input per file | 100 MiB |
| Active workers | 1 |
| PDF pages per file | 300 |
| OCR pages per file | 50 |
| Rendered page/image size | 25 million pixels |
| Approximate OCR render resolution | 250 DPI, reduced to honor the pixel bound |
| Extracted output per file | 20 MiB |
| Visible preview | 200,000 characters |
| Result cache | 500 MiB; stop with a save/clear explanation before exceeding it |
| Native conversion deadline | 120 seconds per file |
| Legacy import deadline | 120 seconds before native extraction |
| OCR deadline | 30 seconds per page; 600 seconds overall per file |
| OOXML entry count / decompressed total | 20,000 entries / 500 MiB |

Reject or clearly report a limit instead of silently truncating export content. A truncated preview is allowed because the exported result remains complete. Process PDF pages and images sequentially; release raster buffers promptly. Tune limits using recorded tests and apply changes consistently to UI messages, code, and documentation.

## 12. Storage, exports, and cleanup

Use separate resolved install and data roots. The data tree should resemble:

```text
%LOCALAPPDATA%/LocalMarkdown/
  .local-markdown-owned
  history.sqlite3
  results/<UUID>.md
  jobs/<UUID>/
  logs/                 # controlled codes/timing only, no content or source paths
```

Treat stored result names as identifiers, not trusted arbitrary paths. Before deletion, verify containment within the intended owned data directory and reject symlinks/junctions/reparse escapes. Keep deletion functions separate from export functions. Do not recursively delete a path merely because a database record or settings file supplies it.

Clear History closes relevant handles, clears records and cached results, clears finished/stale job data and history-related diagnostics, then updates the UI. On a locked-file failure, explain what remains and allow retry; do not falsely display a completed wipe. Normal deletion is not forensic erasure.

For exports use a native Save As dialog, safe basename-derived names, atomic writes, and an overwrite confirmation. Never auto-overwrite a source or a user file. Handle case-insensitive collisions in batch names deterministically: `report.md`, `report (2).md`, etc. Sanitize path separators, reserved Windows names, and trailing characters. ZIP member names must be plain relative basenames. Do not store result paths based on user filenames inside the cache.

Remove/Clear History never deletes a manually saved `.md` or `.zip`, even if it came from the app. Keep the installation out of cleanup routines. Default uninstallation should preserve user data unless a distinct, clearly labelled app-data removal choice is selected; this still excludes original files and exports.

## 13. Packaging contract

Use PyInstaller one-folder mode, windowed, from an isolated Windows build environment. Pin the Python patch version and build tools. Build on Windows rather than assuming cross-compilation.

The spec/hooks must explicitly verify:

- Qt platform plugins and the Widgets dependencies used by the UI.
- MarkItDown converter imports and dependency package metadata.
- Magika model/configuration files and ONNX/native runtime dependencies used by file detection.
- PDF/font/encoding data required by PDFMiner and related packages.
- pypdfium2's native PDFium library, Pillow dependencies, and notices.
- Tesseract executable, required DLLs, English trained data, and licenses.
- LibreOffice runtime tree, profile template, filters, required native runtimes, and notices.
- The frozen worker route, executable-relative paths, and no console flashes.

Detect required resources at startup without downloading anything. The build should generate `capabilities.json` from the payload actually verified, including component versions. Full-release preflight fails when a required reader or data file is missing. Do not advertise support from hardcoded capabilities disconnected from the bundle.

Use Inno Setup for a per-user offline installer under `%LOCALAPPDATA%\Programs\LocalMarkdown`, with `PrivilegesRequired=lowest`, a Start menu shortcut, optional desktop shortcut, and an uninstaller. Keep a stable application identifier for upgrades. Test upgrades, installation with spaces, standard-user permissions, and uninstall behavior.

Record the size of both the installer and the installed payload. Do not promise a tiny executable: bundling the legacy reader and OCR trades a larger package for fewer client setup steps. Test on a clean machine with no developer tools or document readers installed.

## 14. Required deliverables from the build

1. Working source, locked dependencies, focused tests, synthetic fixtures, and build scripts.
2. Core pilot package early, labelled with its actual capabilities.
3. Full Windows installer and complete portable ZIP after all required readers pass.
4. Artifact SHA-256 checksums and a component/version/source manifest.
5. README, illustrated client guide, limitations, licenses/notices, and build instructions.
6. Screenshots of empty, queued, completed, review/error, history, and clear-history states.
7. Test report naming exact artifact hashes, operating systems, environment, pass/fail/unrun cases, observed sizes, and remaining gaps.
8. Public-ready GitHub workflow and release notes, without client documents or automatic publication.

Use `04-ACCEPTANCE-AND-RELEASE-CHECKLIST.md` as the release gate. Report finished work, verified behavior, and remaining limitations separately. Do not describe a source-only run, a mocked conversion, or an untested installer as a client-ready app.
