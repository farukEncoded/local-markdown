# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

project_root = Path.cwd()
src_dir = project_root / "src"

datas = [
    (str(src_dir / "local_markdown" / "ui" / "styles.qss"), "local_markdown/ui"),
    (str(src_dir / "local_markdown" / "resources"), "local_markdown/resources"),
    (str(src_dir / "local_markdown" / "resources"), "resources"),
    (str(project_root / "vendor"), "vendor"),
]

binaries = []
hiddenimports = [
    "local_markdown",
    "local_markdown.app",
    "local_markdown.__main__",
    "local_markdown.ui.main_window",
    "local_markdown.ui.file_model",
    "local_markdown.ui.messages",
    "local_markdown.conversion.service",
    "local_markdown.conversion.registry",
    "local_markdown.conversion.validation",
    "local_markdown.conversion.models",
    "local_markdown.conversion.pdf_pipeline",
    "local_markdown.conversion.ocr",
    "local_markdown.conversion.legacy_office",
    "local_markdown.conversion.output_normalizer",
    "local_markdown.jobs.controller",
    "local_markdown.jobs.worker",
    "local_markdown.jobs.protocol",
    "local_markdown.jobs.windows_process_tree",
    "local_markdown.storage.paths",
    "local_markdown.storage.history",
    "local_markdown.storage.cleanup",
    "local_markdown.storage.exports",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "docx",
    "openpyxl",
    "xlrd",
    "pptx",
    "olefile",
    "reportlab",
]

# Collect dependencies
for pkg in ["magika", "pdfminer", "pypdfium2", "onnxruntime", "markitdown", "PIL"]:
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas.extend(pkg_datas)
    binaries.extend(pkg_binaries)
    hiddenimports.extend(pkg_hidden)

a = Analysis(
    [str(src_dir / "local_markdown" / "__main__.py")],
    pathex=[str(src_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LocalMarkdown",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(src_dir / "local_markdown" / "resources" / "app.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="LocalMarkdown",
)
