# Local Markdown: acceptance and release checklist

Prepared 25 October 2026. **All application checks below are planned and have not been run by this handoff.** The documents and ZIP can be validated independently; that does not validate the future application.

Use PASS, FAIL, or NOT RUN for each check. Record the exact installer/portable artifact hash, app version, OS build, component versions, test date, and evidence. A source run does not pass a frozen-build check. A mocked adapter does not pass a real conversion check.

## A. Content fixtures

Create synthetic fixtures whose expected content is known. Use no client or confidential documents in the public repository. Confirm legacy fixtures are genuine old-format files, not renamed modern files.

| ID | Fixture / action | Required evidence |
|---|---|---|
| C01 | DOCX with headings, paragraphs, lists, table, URL, and specific numbers | Key text/numbers and supported structure survive; links are not fetched |
| C02 | Multi-page text PDF with headings, table, and two-column section | Page coverage and representative values verified; reading-order limitations recorded |
| C03 | XLSX with multiple sheets, dates, numbers, empty cells, formulas, and a hidden sheet | Names/order and stored values checked; hidden-sheet/formula-cache behavior explained |
| C04 | Genuine XLS workbook | Representative values and worksheet names survive through the XLS adapter |
| C05 | PPTX with several slides, tables, grouped text, notes, and an image | Text/slide order checked; notes behavior and image omissions documented |
| C06 | Genuine `.ppt` presentation | Bundled importer works with no existing Office/LibreOffice; expected text survives |
| C07 | Genuine `.doc` document | Bundled importer produces valid intermediate and expected final text |
| C08 | Clean English scanned PDF | Expected phrases/numbers found; output clearly flagged for OCR review |
| C09 | Mixed PDF: native page, scanned page, blank page, native page | All pages accounted for in order; no duplicate native+OCR content; blank page not invented |
| C10 | English PNG/JPEG document photo, including a rotated sample | Readable text extracted where feasible; uncertainty/failure explained |
| C11 | Sparse-text PDF that defeats the automatic scan heuristic | Try scan reading works and preserves one output section per original page |
| C12 | Password-protected, corrupt, empty, unsupported, and extension-disguised files | Accurate user messages; no crash or false-success empty export |

For OCR, require known text from representative clean printed samples. Do not present a universal accuracy percentage based on a few documents. Capture actual quality on difficult samples and document it.

## B. Desktop workflow

| ID | Action | Expected behavior |
|---|---|---|
| U01 | Install and open app using shortcuts | No terminal or environment setup |
| U02 | Add one file; convert; preview; save `.md` | Complete task through the UI with a valid UTF-8 result |
| U03 | Add a mixed 10-file batch including one corrupt file | Healthy files complete; failed file explained; UI remains responsive |
| U04 | Save all as ZIP | Exactly the ready/review results plus summary; no originals or private paths |
| U05 | Add same-named inputs from different folders/extensions | Stable distinct output names; no overwritten result |
| U06 | Stop during ordinary conversion, OCR, and legacy import | Owned process tree ends; completed results remain; partial files not labelled ready |
| U07 | Close/reopen during active work; repeat after a simulated crash | Interrupted work marked accurately; contained temporary cleanup; no orphan reader |
| U08 | Open history after relaunch; save an earlier result | Result available without reopening original; no persistent original full path |
| U09 | Save over an existing export or cancel Save As | Explicit overwrite choice; cancelled save causes no damage |
| U10 | Use long names, spaces, non-ASCII names, and reserved-name-like inputs | Safe filenames and functioning paths in installed and portable builds |
| U11 | Inspect on 100%, 150%, and 200% Windows scaling; keyboard-only navigation | Controls readable, reachable, and not clipped |
| U12 | Large result exceeds preview length | Preview limit labelled; full supported output preserved on export |
| U13 | Exceed each configured processing/storage limit | Clear limit explanation; no silent export truncation or stuck UI |

## C. Original preservation and cleanup

Before each relevant test, record source-file hashes and modification times and create a separately saved Markdown/ZIP export as a sentinel. After conversion, cancellation, crash recovery, Remove, Clear History, upgrade, and uninstall, verify the originals and sentinels remain intact. Reading may affect operating-system access metadata; the app must not write original content or modification timestamps.

| ID | Action | Expected behavior |
|---|---|---|
| D01 | Convert each supported format | Original bytes unchanged; no adjacent lock/intermediate files created by the app |
| D02 | Remove one completed history entry | Only that record/cache removed; original and saved export remain |
| D03 | Clear History while idle | App history, previews, finished job copies, and history diagnostics removed; originals/exports remain |
| D04 | Attempt Clear History while active | Disabled until Stop finishes; no cleanup/worker race |
| D05 | Inject invalid cached paths and a reparse/junction escape in a controlled test directory | Cleanup refuses to follow it; unrelated sentinel files survive |
| D06 | Make a cached file temporarily undeletable | App explains incomplete cleanup and supports retry; no false success |
| D07 | Inspect history and logs | No document content in logs, no original full paths in persistent history |
| D08 | Uninstall / reinstall / upgrade | Documented data-retention behavior; no deletion of originals or exports |

## D. Offline and process behavior

| ID | Environment / action | Expected behavior |
|---|---|---|
| O01 | Clean standard-user Windows account; no Python, Git, Office, OCR, or LibreOffice | Install and all required conversions work from bundled resources |
| O02 | Network disabled before installation and first launch | No bootstrap download or setup failure; all full-build formats work |
| O03 | Network disabled during batch, save, history clear, relaunch | Normal completion for local files |
| O04 | Normal online run with app/child-process network activity monitored | No application-initiated document transfer, telemetry, update/model request, or resource fetch |
| O05 | Fixtures containing remote hyperlinks, image references, and external spreadsheet links | Text may be retained; remote content is not fetched or refreshed |
| O06 | Legacy file containing a macro project, plus controlled policy canaries | File rejected as specified; no macro execution or external refresh |
| O07 | Missing/renamed bundled OCR or legacy component | Preflight/capability failure is explicit; no cloud fallback or false format claim |
| O08 | User has LibreOffice already open | Conversion/cancellation neither reuses their profile nor kills their session |
| O09 | Portable app moved to another local folder | All resources resolve relative to app; no dependency on build-machine paths |

O02 demonstrates offline operation. O04 separately examines attempts while networking is available. Do not substitute one for the other. Operating-system sync/security processes are distinct from application requests; describe the actual observation rather than claiming control over them.

## E. Installer, source, and release

- [ ] Build on Windows using pinned runtime/build dependency versions and verified vendor hashes.
- [ ] Test the exact frozen worker route, Qt plugins, Magika models/native libraries, PDF data, OCR data, and legacy runtime.
- [ ] Test the final installer as a standard user, including its app-local native runtime dependencies.
- [ ] Test Windows 11 x64 and Windows 10 22H2 x64 separately before claiming support for each.
- [ ] Test an upgrade from the pilot/previous build, with history present.
- [ ] Measure installer size, portable ZIP size, installed disk usage, startup behavior, and representative conversion times. State the machine used.
- [ ] Include actual runtime capabilities, component/source manifest, licenses, notices, and applicable source/relinking information for shipped dependencies.
- [ ] Publish no confidential fixtures, cached documents, local paths, tokens, signing keys, or developer environments in source or artifacts.
- [ ] Prepare README and screenshots that match the final UI and support list.
- [ ] Update the client guide by actually following it on the packaged app.
- [ ] Create SHA-256 checksums for exact deliverables and associate them with the test report.
- [ ] State signing status accurately. Do not claim that an unsigned or signed build will never receive a Windows warning.
- [ ] Prepare GitHub release notes locally. Remote publication requires a separate owner instruction.

## Release classification

**Core pilot:** C01–C05 and applicable workflow/deletion/offline/packaging checks pass; OCR and legacy support visibly unavailable. An installer can be demonstrated as a pilot, not the full requested client app.

**Full client build:** All required core, OCR, genuine `.doc` / `.ppt`, preservation, offline, and packaging checks pass for the declared OS targets. Difficult-sample fidelity limits may be documented, but missing readers or unrun clean-machine checks cannot be hidden under a generic “tested” label.

**Prepared but unverified:** Source, builds, or scripts exist but some required checks have not run. List those checks and their practical impact. Do not call this client-ready.

## Required final test report

Include: app version; artifact filenames and hashes; OS/account details; Python/MarkItDown/Qt/OCR/LibreOffice versions; bundled resources; pass/fail/not-run results by ID; key-content evidence; source-preservation results; network observations; measured sizes/times; screenshots; known limitations; and the exact next action for each incomplete item.
