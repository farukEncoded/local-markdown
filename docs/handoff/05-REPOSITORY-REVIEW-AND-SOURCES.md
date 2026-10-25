# MarkItDown repository review and source register

Reviewed 25 October 2026 for the Local Markdown Windows wrapper. This is a targeted source/dependency review, not a repository-wide audit or a conversion benchmark.

## 1. Verified baseline

| Item | Observed value |
|---|---|
| Upstream | `microsoft/markitdown` |
| GitHub main snapshot | `7482c092d9c0074a89803c9fdb63a969e7fe17fc` |
| Commit timestamp reported by GitHub API | `2026-10-22T22:31:47Z` |
| Published PyPI version reviewed | `0.1.9` |
| Wheel | `markitdown-0.1.9-py3-none-any.whl` |
| Wheel SHA-256 | `52f59c48bea9cf887224c56247f648d68beb7aa7af5a12d414748210c83c20ea` |
| PyPI wheel upload timestamp | `2026-10-21T19:41:18.650705Z` |
| Python requirement | `>=3.10,<3.15` |
| Upstream license | MIT |

The wheel was fetched into memory, its SHA-256 matched against PyPI metadata, and its Python source inspected. No package installation, sample conversion, GUI launch, or installer run was performed. GitHub main and a published wheel can differ even when their version strings match; use the wheel/lockfile for reproducible implementation.

[Pinned repository snapshot](https://github.com/microsoft/markitdown/tree/7482c092d9c0074a89803c9fdb63a969e7fe17fc), [versioned package](https://pypi.org/project/markitdown/0.1.9/), [package metadata](https://pypi.org/pypi/markitdown/0.1.9/json)

## 2. What the review establishes

**A separate wrapper is the intended extension route.** Upstream maintains a library and CLI and directs GUI/service applications into separate projects that depend on the published package. This supports a separate public `local-markdown` repository. [Project guidance](https://github.com/microsoft/markitdown#what-to-contribute)

**The library has the right primary converters.** Required extras exist for PDF, DOCX, PPTX, XLSX, and XLS. Installing only these is more appropriate than `[all]` for this app's scope. [Package configuration](https://github.com/microsoft/markitdown/blob/7482c092d9c0074a89803c9fdb63a969e7fe17fc/packages/markitdown/pyproject.toml)

**Local conversion APIs and a restricted registry are available.** The released wheel contains `convert_local`, `convert_stream`, `register_converter`, `enable_builtins`, and `enable_plugins`. The five converter classes named in the handoff are exported. These enable the wrapper to register the intended formats and avoid URL-capable input routing. [Core source](https://github.com/microsoft/markitdown/blob/7482c092d9c0074a89803c9fdb63a969e7fe17fc/packages/markitdown/src/markitdown/_markitdown.py)

**MarkItDown should not be presented as a complete offline OCR solution.** The reviewed PDF converter uses native PDF text/table extraction. The reviewed image converter extracts metadata and optionally uses a configured multimodal LLM for descriptions. A self-contained local scan reader must be added explicitly. [PDF source](https://github.com/microsoft/markitdown/blob/7482c092d9c0074a89803c9fdb63a969e7fe17fc/packages/markitdown/src/markitdown/converters/_pdf_converter.py), [image source](https://github.com/microsoft/markitdown/blob/7482c092d9c0074a89803c9fdb63a969e7fe17fc/packages/markitdown/src/markitdown/converters/_image_converter.py)

**Word and PowerPoint labels need exact extensions.** The built-in Word and presentation converters reviewed accept `.docx` and `.pptx`. Genuine `.doc` / `.ppt` support needs an additional import step; it must not be inferred from generic README format names. [DOCX source](https://github.com/microsoft/markitdown/blob/7482c092d9c0074a89803c9fdb63a969e7fe17fc/packages/markitdown/src/markitdown/converters/_docx_converter.py), [PPTX source](https://github.com/microsoft/markitdown/blob/7482c092d9c0074a89803c9fdb63a969e7fe17fc/packages/markitdown/src/markitdown/converters/_pptx_converter.py)

**Spreadsheet extraction is a values/text workflow.** The XLSX/XLS implementation reads sheets through pandas with the relevant Excel engine and turns them into Markdown tables. It does not provide a spreadsheet recalculation engine. Cached values, hidden sheets, and sparse data need fixtures and documented behavior. [Spreadsheet source](https://github.com/microsoft/markitdown/blob/7482c092d9c0074a89803c9fdb63a969e7fe17fc/packages/markitdown/src/markitdown/converters/_xlsx_converter.py)

**Content extraction differs from visual reproduction.** The intended use is LLM/text-analysis input, with supported structure retained where possible. This fits the client's aim but does not establish perfect layouts, tables, diagrams, handwriting, or complete extraction from every document. [README](https://github.com/microsoft/markitdown/blob/7482c092d9c0074a89803c9fdb63a969e7fe17fc/README.md)

## 3. Design implications

These are implementation judgments made for the confirmed workflow, not claims that upstream ships them:

- Use PySide6 for the native desktop wrapper, with no local web server to start or manage.
- Freeze and test a minimum app first. File-detection model assets and native dependencies can fail only after packaging, even when source conversion works.
- Keep conversion in a child process and process the batch sequentially. This favors predictable memory use and cancellation over maximum throughput.
- Use local Tesseract for the occasional English scans/photos. Add pypdfium2 to inspect/render PDF pages; no cloud vision service is needed for the planned feature.
- Use a bundled LibreOffice import adapter for actual `.doc` / `.ppt` files. This adds substantial payload and packaging complexity; measure it rather than assuming a small download.
- Retain result history in app-owned storage and keep exports separate so Clear History can safely preserve user files.
- Verify the final installer on a clean machine. Dependency declarations and a successful development run are insufficient distribution evidence.

## 4. Supporting primary documentation

| Component / question | Primary source | Use in this handoff |
|---|---|---|
| PySide6 packaging | [Qt for Python and PyInstaller](https://doc.qt.io/qtforpython-6/deployment/deployment-pyinstaller.html) | Native Python GUI can be packaged; verify current hooks and resources |
| Bundled runtime | [PyInstaller operating mode](https://pyinstaller.org/en/stable/operating-mode.html) | One-folder executable/dependency distribution |
| Per-user install | [Inno Setup privileges](https://jrsoftware.org/ishelp/topic_setup_privilegesrequired.htm) | `PrivilegesRequired=lowest` for a compatible non-elevated payload |
| Local OCR | [Tesseract manual](https://tesseract-ocr.github.io/tessdoc/) | Local printed-text OCR, with binary and trained data packaged explicitly |
| PDF renderer | [pypdfium2 repository](https://github.com/pypdfium2-team/pypdfium2) | Local PDFium bindings and native library packaging |
| Legacy import | [LibreOffice startup parameters](https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html) | Headless conversion, explicit output directory, separate profile |
| Upstream license | [MarkItDown MIT license](https://github.com/microsoft/markitdown/blob/7482c092d9c0074a89803c9fdb63a969e7fe17fc/LICENSE) | Preserve upstream notices in shipped components |
| Qt licenses | [Qt for Python commercial/open-source information](https://doc.qt.io/qtforpython-6/commercial/index.html), [third-party licenses](https://doc.qt.io/qtforpython-6/licenses.html) | Review terms and notices for exact modules/version distributed |
| Legacy runtime licenses | [LibreOffice licenses](https://www.libreoffice.org/about-us/licenses/) | Account for bundled runtime and its component/source obligations |

The wrapper may use an MIT license for its own code. Third-party components retain their own terms; collect the actual distributed license texts, notices, source availability information, and relevant build/relinking information. Do not label the complete binary bundle as exclusively MIT.

## 5. What remains unverified

- Exact output quality on the client's real documents.
- Frozen Windows app behavior and resource collection.
- Runtime and vendor-tool versions beyond the reviewed MarkItDown baseline.
- Redistributable, app-local Windows OCR and LibreOffice payload assembly.
- Legacy import fidelity, macro/external-resource policy, and mixed-page OCR thresholds.
- Windows 10/11 compatibility, standard-user install, clean-machine and offline behavior.
- Installer size, performance, signing, and Windows security reputation.
- Any public GitHub repository, workflow run, release, or client installation.

The implementation plan is feasible with known components. These checks determine whether a particular build actually meets the promise.
