# Local Markdown: start here

Prepared for Faruk Munshi on 25 October 2026.

**Build a Windows desktop app that turns local documents into Markdown.** The client opens an app icon, adds one or several files, clicks Convert, and saves the results. Conversion runs on the computer. Original documents remain untouched.

This is an implementation handoff, not a finished app. No application, installer, GitHub repository, or public release has been created by this package.

## Decisions already made

| Item | Decision |
|---|---|
| Working app name | Local Markdown |
| Proposed repository name | `local-markdown` |
| User | A Windows user who should never need a command line |
| Main inputs | English Word, PDF, Excel, and PowerPoint documents |
| Interface | Native desktop window |
| Conversion | Single file and batch |
| Outputs | Save an individual `.md`; save a batch as a ZIP; copy selected Markdown |
| Privacy | Offline conversion; no account, API key, analytics, or document upload |
| Deletion | Clear app history, cached previews, and temporary working files only |
| Client delivery | One self-contained Windows installer, with a portable ZIP as a secondary option |
| Source distribution | A separate public-ready repository depending on MarkItDown |

The full client build includes English scan reading and import of genuine legacy `.doc` / `.ppt` files. Develop those after the core app. They add packaging work and increase the download size. A core pilot that lacks them must be labelled as a pilot with its smaller support list.

## Use this package

1. Create a new, empty project folder, for example `C:\Users\infor\OneDrive\Documents\local-markdown`.
2. Extract `Local-Markdown-Antigravity-Handoff-2026-10-25.zip` into that folder. The archive creates `docs/handoff/`.
3. Open the new project folder in Antigravity.
4. Copy the contents of `docs/handoff/03-ANTIGRAVITY-PROMPT.md` into Antigravity.
5. Keep the final build and test report. Source code running on the developer's computer is not sufficient evidence that the client's installer works.

The example project location is a suggestion, not a folder already created. The ExBankersClub folder contains the handoff artifacts only; build this as its own project.

## Reading order

- [01-IMPLEMENTATION-PLAN.md](01-IMPLEMENTATION-PLAN.md): product scope, architecture, milestones, and delivery.
- [02-ANTIGRAVITY-HANDOFF.md](02-ANTIGRAVITY-HANDOFF.md): concrete implementation contracts and file structure.
- [04-ACCEPTANCE-AND-RELEASE-CHECKLIST.md](04-ACCEPTANCE-AND-RELEASE-CHECKLIST.md): tests and release gates.
- [05-REPOSITORY-REVIEW-AND-SOURCES.md](05-REPOSITORY-REVIEW-AND-SOURCES.md): source findings, version baseline, and limits.
- [06-CLIENT-QUICKSTART-DRAFT.md](06-CLIENT-QUICKSTART-DRAFT.md): a short guide to update against the finished app.

## Recommended implementation

Use Python 3.13 x64, PySide6 Qt Widgets, and MarkItDown 0.1.9 with only the required format extras. Package the application with PyInstaller in one-folder mode and wrap it in an Inno Setup installer. Bundle Tesseract with English language data for scans. Bundle a verified LibreOffice runtime for `.doc` / `.ppt` normalization.

The client installs this package once. Python, Qt, conversion libraries, and the extra readers live inside the delivered package. The client does not install these separately or configure their paths.

Start with a packaging proof before investing in interface polish. MarkItDown's dependency resources, the frozen worker process, and the bundled readers must work on a clean Windows machine.

## Definition of done

The app can be installed and launched by a standard Windows user without Python, Git, Office, a command prompt, or an internet connection. It converts the supported sample files individually and in a mixed batch, exports correct files, and clears only its own data. Its final installer passes the acceptance checklist, with untested cases stated explicitly.
