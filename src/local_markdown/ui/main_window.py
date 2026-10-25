"""Main window implementation for Local Markdown desktop application."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QItemSelection, QTimer, Qt
from PySide6.QtGui import QAction, QClipboard, QDragEnterEvent, QDropEvent, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from local_markdown.conversion.models import FileStatus, QueuedFile
from local_markdown.conversion.validation import validate_file_preflight, ValidationError
from local_markdown.jobs.controller import ConversionController
from local_markdown.storage.cleanup import clear_all_history
from local_markdown.storage.exports import export_batch_zip, export_single_markdown
from local_markdown.storage.history import (
    delete_history_entry,
    read_cached_result_markdown,
)
from local_markdown.storage.paths import get_resource_dir
from local_markdown.ui.file_model import FileTableModel
from local_markdown.ui.messages import (
    APP_SUBTITLE,
    APP_TITLE,
    CONFIRM_CLEAR_HISTORY,
    MSG_EMPTY_STATE,
    MSG_PREVIEW_TRUNCATED,
    MSG_SUPPORTED_FORMATS,
    WORKS_OFFLINE_LABEL,
)

MAX_PREVIEW_CHARS = 200_000


class MainWindow(QWidget):
    """The primary desktop window for Local Markdown."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle(APP_TITLE)
        self.resize(1180, 760)
        self.setMinimumSize(880, 560)
        self.setAcceptDrops(True)

        self._controller = ConversionController(self)
        self._model = FileTableModel()

        # Cached preview tracking
        self._current_selected_file: Optional[QueuedFile] = None
        self._current_markdown_full: str = ""

        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # =========================================================================
        # 1. Header Bar: Brand, Privacy Chip & Clear History
        # =========================================================================
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(2, 0, 2, 4)

        # Brand Icon + Title & Subtitle
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(12)

        logo_label = QLabel("M↓")
        logo_label.setStyleSheet(
            "background-color: #2563eb; color: #ffffff; font-weight: 800; font-size: 15px; "
            "padding: 6px 10px; border-radius: 8px; border: 1px solid #3b82f6;"
        )
        logo_label.setFixedHeight(34)
        brand_layout.addWidget(logo_label)

        title_text_layout = QVBoxLayout()
        title_text_layout.setSpacing(2)

        title_label = QLabel(APP_TITLE)
        title_label.setStyleSheet("font-size: 20px; font-weight: 700; color: #f8fafc; letter-spacing: -0.3px;")
        subtitle_label = QLabel("Convert documents to clean Markdown on your computer • Zero cloud dependencies")
        subtitle_label.setStyleSheet("font-size: 12px; color: #94a3b8;")

        title_text_layout.addWidget(title_label)
        title_text_layout.addWidget(subtitle_label)
        brand_layout.addLayout(title_text_layout)

        header_layout.addLayout(brand_layout)
        header_layout.addStretch()

        # Right Header: Offline Badge & Clear History
        right_header_layout = QHBoxLayout()
        right_header_layout.setSpacing(10)

        offline_pill = QLabel("● 100% Offline & Private")
        offline_pill.setStyleSheet(
            "background-color: #064e3b; color: #34d399; font-weight: 600; font-size: 11px; "
            "padding: 5px 12px; border-radius: 13px; border: 1px solid #059669;"
        )
        offline_pill.setFixedHeight(28)
        right_header_layout.addWidget(offline_pill)

        self.btn_clear_history = QPushButton("🧹 Clear history")
        self.btn_clear_history.setObjectName("dangerButton")
        self.btn_clear_history.setFixedHeight(28)
        self.btn_clear_history.clicked.connect(self._on_clear_history_clicked)
        right_header_layout.addWidget(self.btn_clear_history)

        header_layout.addLayout(right_header_layout)
        main_layout.addLayout(header_layout)

        # =========================================================================
        # 2. Main Action Command Deck
        # =========================================================================
        command_deck = QFrame()
        command_deck.setObjectName("commandDeck")
        deck_layout = QHBoxLayout(command_deck)
        deck_layout.setContentsMargins(10, 8, 10, 8)
        deck_layout.setSpacing(8)

        # Left Group: Primary Workflow Actions
        self.btn_add_files = QPushButton("+ Add files")
        self.btn_add_files.setObjectName("primaryButton")
        self.btn_add_files.setToolTip("Add Word, PDF, Excel, PowerPoint or Image files")
        self.btn_add_files.clicked.connect(self._on_add_files_clicked)
        deck_layout.addWidget(self.btn_add_files)

        self.btn_convert = QPushButton("▶ Convert All")
        self.btn_convert.setObjectName("convertButton")
        self.btn_convert.setEnabled(False)
        self.btn_convert.clicked.connect(self._on_convert_clicked)
        deck_layout.addWidget(self.btn_convert)

        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setObjectName("stopButton")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        deck_layout.addWidget(self.btn_stop)

        v_line1 = QFrame()
        v_line1.setObjectName("vLine")
        v_line1.setFrameShape(QFrame.Shape.VLine)
        v_line1.setFrameShadow(QFrame.Shadow.Sunken)
        v_line1.setFixedHeight(24)
        deck_layout.addWidget(v_line1)

        self.btn_scan_read = QPushButton("🔍 Try scan reading")
        self.btn_scan_read.setToolTip("Force bundled OCR on selected PDF or image file")
        self.btn_scan_read.setEnabled(False)
        self.btn_scan_read.clicked.connect(self._on_scan_read_clicked)
        deck_layout.addWidget(self.btn_scan_read)

        deck_layout.addStretch()

        # Right Group: Export & Queue Management
        self.btn_copy = QPushButton("📋 Copy Markdown")
        self.btn_copy.setObjectName("copyButton")
        self.btn_copy.setEnabled(False)
        self.btn_copy.clicked.connect(self._on_copy_clicked)
        deck_layout.addWidget(self.btn_copy)

        self.btn_save_one = QPushButton("💾 Save Markdown")
        self.btn_save_one.setEnabled(False)
        self.btn_save_one.clicked.connect(self._on_save_one_clicked)
        deck_layout.addWidget(self.btn_save_one)

        self.btn_save_zip = QPushButton("📦 Save all as ZIP")
        self.btn_save_zip.setEnabled(False)
        self.btn_save_zip.clicked.connect(self._on_save_zip_clicked)
        deck_layout.addWidget(self.btn_save_zip)

        v_line2 = QFrame()
        v_line2.setObjectName("vLine")
        v_line2.setFrameShape(QFrame.Shape.VLine)
        v_line2.setFrameShadow(QFrame.Shadow.Sunken)
        v_line2.setFixedHeight(24)
        deck_layout.addWidget(v_line2)

        self.btn_remove = QPushButton("✕ Remove")
        self.btn_remove.setEnabled(False)
        self.btn_remove.clicked.connect(self._on_remove_clicked)
        deck_layout.addWidget(self.btn_remove)

        main_layout.addWidget(command_deck)

        # =========================================================================
        # 3. Main Central Workspace (Splitter that expands to fill window)
        # =========================================================================
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # -------------------------------------------------------------------------
        # Left Panel: Document Queue Card
        # -------------------------------------------------------------------------
        left_card = QFrame()
        left_card.setObjectName("cardFrame")
        left_card_layout = QVBoxLayout(left_card)
        left_card_layout.setContentsMargins(14, 14, 14, 12)
        left_card_layout.setSpacing(10)

        # Queue Card Header
        queue_header_layout = QHBoxLayout()
        queue_title = QLabel("Document Queue")
        queue_title.setStyleSheet("font-weight: 700; font-size: 14px; color: #f8fafc;")
        queue_header_layout.addWidget(queue_title)

        self.queue_badge = QLabel("0 documents")
        self.queue_badge.setStyleSheet(
            "background-color: #1e293b; color: #94a3b8; font-size: 11px; "
            "padding: 2px 8px; border-radius: 10px; border: 1px solid #334155;"
        )
        queue_header_layout.addWidget(self.queue_badge)
        queue_header_layout.addStretch()

        self.btn_clear_list = QPushButton("Clear list")
        self.btn_clear_list.setObjectName("cardHeaderBtn")
        self.btn_clear_list.setEnabled(False)
        self.btn_clear_list.clicked.connect(self._on_clear_list_clicked)
        queue_header_layout.addWidget(self.btn_clear_list)

        left_card_layout.addLayout(queue_header_layout)

        # Stack: Empty Dropzone vs TableView
        self.queue_stack = QStackedWidget()

        # Page 0: Empty Dropzone
        dropzone = QFrame()
        dropzone.setObjectName("dropzoneCard")
        dropzone_layout = QVBoxLayout(dropzone)
        dropzone_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dropzone_layout.setSpacing(8)

        icon_label = QLabel("📄 📥")
        icon_label.setStyleSheet("font-size: 38px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dropzone_layout.addWidget(icon_label)

        drop_heading = QLabel("Drop documents here to convert")
        drop_heading.setStyleSheet("font-size: 15px; font-weight: 600; color: #f8fafc; background: transparent;")
        drop_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dropzone_layout.addWidget(drop_heading)

        drop_subtext = QLabel("or click '+ Add files' above to select from your computer")
        drop_subtext.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent;")
        drop_subtext.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dropzone_layout.addWidget(drop_subtext)

        tags_layout = QHBoxLayout()
        tags_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tags_layout.setSpacing(6)
        for tag in ["Word", "PDF", "Excel", "PowerPoint", "Images"]:
            tag_lbl = QLabel(tag)
            tag_lbl.setStyleSheet(
                "background-color: #1a253a; color: #cbd5e1; font-size: 11px; font-weight: 500; "
                "padding: 3px 8px; border-radius: 4px; border: 1px solid #293b5c;"
            )
            tags_layout.addWidget(tag_lbl)
        dropzone_layout.addSpacing(6)
        dropzone_layout.addLayout(tags_layout)

        privacy_sub = QLabel("🔒 Processed completely on your device. Zero network activity.")
        privacy_sub.setStyleSheet("font-size: 11px; color: #059669; margin-top: 6px; background: transparent;")
        privacy_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dropzone_layout.addWidget(privacy_sub)

        self.queue_stack.addWidget(dropzone)

        # Page 1: Populated Table View
        self.table_view = QTableView()
        self.table_view.setModel(self._model)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.verticalHeader().setDefaultSectionSize(36)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setShowGrid(False)
        self.table_view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.queue_stack.addWidget(self.table_view)

        left_card_layout.addWidget(self.queue_stack, 1)

        # Left Card Footer: Supported Formats Note
        formats_label = QLabel(MSG_SUPPORTED_FORMATS)
        formats_label.setStyleSheet("font-size: 11px; color: #64748b;")
        formats_label.setWordWrap(True)
        left_card_layout.addWidget(formats_label)

        splitter.addWidget(left_card)

        # -------------------------------------------------------------------------
        # Right Panel: Markdown Preview Card
        # -------------------------------------------------------------------------
        right_card = QFrame()
        right_card.setObjectName("cardFrame")
        right_card_layout = QVBoxLayout(right_card)
        right_card_layout.setContentsMargins(14, 14, 14, 12)
        right_card_layout.setSpacing(8)

        # Preview Card Header
        preview_header_layout = QHBoxLayout()
        self.preview_title_label = QLabel("Markdown Preview")
        self.preview_title_label.setStyleSheet("font-weight: 700; font-size: 14px; color: #f8fafc;")
        preview_header_layout.addWidget(self.preview_title_label)

        self.preview_meta_badge = QLabel("")
        self.preview_meta_badge.setStyleSheet(
            "background-color: #1e293b; color: #94a3b8; font-size: 11px; "
            "padding: 2px 8px; border-radius: 10px; border: 1px solid #334155;"
        )
        self.preview_meta_badge.setVisible(False)
        preview_header_layout.addWidget(self.preview_meta_badge)
        preview_header_layout.addStretch()

        self.btn_quick_copy = QPushButton("📋 Copy")
        self.btn_quick_copy.setObjectName("cardHeaderBtn")
        self.btn_quick_copy.setEnabled(False)
        self.btn_quick_copy.setToolTip("Copy previewed Markdown to clipboard")
        self.btn_quick_copy.clicked.connect(self._on_copy_clicked)
        preview_header_layout.addWidget(self.btn_quick_copy)

        self.btn_quick_save = QPushButton("💾 Save .md")
        self.btn_quick_save.setObjectName("cardHeaderBtn")
        self.btn_quick_save.setEnabled(False)
        self.btn_quick_save.setToolTip("Save this Markdown file to your computer")
        self.btn_quick_save.clicked.connect(self._on_save_one_clicked)
        preview_header_layout.addWidget(self.btn_quick_save)

        right_card_layout.addLayout(preview_header_layout)

        # Warning Banner
        self.warning_banner = QLabel()
        self.warning_banner.setStyleSheet(
            "background-color: #451a03; color: #fde68a; padding: 8px 12px; "
            "border-radius: 6px; border: 1px solid #b45309; font-size: 12px;"
        )
        self.warning_banner.setVisible(False)
        self.warning_banner.setWordWrap(True)
        right_card_layout.addWidget(self.warning_banner)

        # Preview Note (Truncation)
        self.preview_note = QLabel()
        self.preview_note.setStyleSheet("font-size: 11px; color: #94a3b8; font-style: italic;")
        self.preview_note.setVisible(False)
        right_card_layout.addWidget(self.preview_note)

        # Editor
        self.preview_edit = QPlainTextEdit()
        self.preview_edit.setObjectName("previewEdit")
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setPlaceholderText("Select a converted document from the queue on the left to preview its Markdown.")
        right_card_layout.addWidget(self.preview_edit, 1)

        splitter.addWidget(right_card)
        splitter.setSizes([540, 520])

        # CRITICAL: splitter gets stretch factor 1 to take all available window height!
        main_layout.addWidget(splitter, 1)

        # =========================================================================
        # 4. Bottom Status & Progress Deck
        # =========================================================================
        status_bar_layout = QHBoxLayout()
        status_bar_layout.setContentsMargins(4, 4, 4, 2)

        self.status_label = QLabel(MSG_EMPTY_STATE)
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        status_bar_layout.addWidget(self.status_label)
        status_bar_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedWidth(220)
        self.progress_bar.setVisible(False)
        status_bar_layout.addWidget(self.progress_bar)

        guarantee_label = QLabel("Originals are never modified • Safe local processing")
        guarantee_label.setStyleSheet("color: #64748b; font-size: 11px;")
        status_bar_layout.addWidget(guarantee_label)

        main_layout.addLayout(status_bar_layout)

    def _connect_signals(self) -> None:
        self._controller.job_started.connect(self._on_job_started)
        self._controller.job_progress.connect(self._on_job_progress)
        self._controller.job_finished.connect(self._on_job_finished)
        self._controller.queue_completed.connect(self._on_queue_completed)

    # Drag and Drop handlers
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        paths: List[Path] = []
        for url in urls:
            if url.isLocalFile():
                paths.append(Path(url.toLocalFile()))
        if paths:
            self._add_files_by_paths(paths)

    def _on_add_files_clicked(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Documents to Convert",
            "",
            "Documents (*.docx *.pdf *.xlsx *.xls *.pptx *.doc *.ppt *.png *.jpg *.jpeg);;All Files (*.*)",
        )
        if files:
            self._add_files_by_paths([Path(f) for f in files])

    def _add_files_by_paths(self, paths: List[Path]) -> None:
        added_count = 0
        error_messages = []
        for p in paths:
            try:
                validate_file_preflight(p, allow_legacy_and_images=True)
                queued_item = QueuedFile.from_path(p)
                self._model.add_file(queued_item)
                added_count += 1
            except ValidationError as ve:
                error_messages.append(f"{p.name}: {ve.user_message}")
            except Exception as e:
                error_messages.append(f"{p.name}: {e}")

        if error_messages:
            QMessageBox.warning(
                self,
                "Some files could not be added",
                "\n".join(error_messages[:5]) + (f"\n...and {len(error_messages) - 5} more" if len(error_messages) > 5 else ""),
            )

        self._refresh_queue_view()

    def _refresh_queue_view(self) -> None:
        count = self._model.rowCount()
        if count > 0:
            self.queue_stack.setCurrentIndex(1)
            self.queue_badge.setText(f"{count} file{'s' if count != 1 else ''}")
            self.btn_convert.setText(f"▶ Convert All ({count})")
            self.btn_convert.setEnabled(not self._controller.is_running)
            self.btn_clear_list.setEnabled(not self._controller.is_running)
            if not self._controller.is_running:
                self.status_label.setText(f"{count} document{'s' if count != 1 else ''} queued. Click 'Convert All' to start.")
        else:
            self.queue_stack.setCurrentIndex(0)
            self.queue_badge.setText("0 documents")
            self.btn_convert.setText("▶ Convert All")
            self.btn_convert.setEnabled(False)
            self.btn_clear_list.setEnabled(False)
            if not self._controller.is_running:
                self.status_label.setText(MSG_EMPTY_STATE)

        self._update_button_states()

    def _on_clear_list_clicked(self) -> None:
        if self._controller.is_running:
            return
        self._model.clear()
        self._update_preview(None)
        self._refresh_queue_view()

    def _on_convert_clicked(self) -> None:
        files = self._model.files
        if not files:
            QMessageBox.information(self, "No files", "Please add one or more files to convert.")
            return

        self.btn_convert.setEnabled(False)
        self.btn_convert.setText("⟳ Converting...")
        self.btn_scan_read.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_clear_history.setEnabled(False)
        self.btn_clear_list.setEnabled(False)
        self.progress_bar.setVisible(True)

        self._controller.start_batch(files, force_ocr=False)

    def _on_scan_read_clicked(self) -> None:
        selected_file = self._get_selected_file()
        if not selected_file:
            QMessageBox.information(self, "Select a document", "Please select a document from the list to force scan reading.")
            return

        self.btn_convert.setEnabled(False)
        self.btn_convert.setText("⟳ Scan reading...")
        self.btn_scan_read.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_clear_history.setEnabled(False)
        self.btn_clear_list.setEnabled(False)
        self.progress_bar.setVisible(True)

        self._controller.start_batch([selected_file], force_ocr=True)

    def _on_stop_clicked(self) -> None:
        self._controller.cancel_active_work()
        self.btn_stop.setEnabled(False)
        self.status_label.setText("Stopping conversion...")

    def _on_job_started(self, file_id: str, display_name: str) -> None:
        self._model.update_row_by_id(file_id)
        all_files = self._model.files
        current_idx = next((i for i, f in enumerate(all_files) if f.id == file_id), 0) + 1
        self.status_label.setText(f"Converting ({current_idx}/{len(all_files)}): {display_name}")

    def _on_job_progress(self, file_id: str, detail_message: str) -> None:
        self.status_label.setText(detail_message)

    def _on_job_finished(self, file_id: str, result: object) -> None:
        self._model.update_row_by_id(file_id)
        selected_file = self._get_selected_file()
        if selected_file and selected_file.id == file_id:
            self._update_preview(selected_file)

    def _on_queue_completed(self, ready_count: int, review_count: int, failed_count: int) -> None:
        self.btn_convert.setEnabled(True)
        count = self._model.rowCount()
        self.btn_convert.setText(f"▶ Convert All ({count})" if count > 0 else "▶ Convert All")
        self.btn_scan_read.setEnabled(self._get_selected_file() is not None)
        self.btn_stop.setEnabled(False)
        self.btn_clear_history.setEnabled(True)
        self.btn_clear_list.setEnabled(True)
        self.progress_bar.setVisible(False)

        parts = []
        if ready_count > 0:
            parts.append(f"✓ {ready_count} ready to save")
        if review_count > 0:
            parts.append(f"⚠ {review_count} needs review")
        if failed_count > 0:
            parts.append(f"✕ {failed_count} could not be converted")

        summary = " • ".join(parts) if parts else "Conversion finished."
        self.status_label.setText(summary)
        self._update_button_states()

    def _on_selection_changed(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        selected_file = self._get_selected_file()
        self._update_preview(selected_file)
        self._update_button_states()

    def _get_selected_file(self) -> Optional[QueuedFile]:
        indexes = self.table_view.selectionModel().selectedRows()
        if indexes:
            return self._model.get_file(indexes[0].row())
        return None

    def _update_preview(self, file_item: Optional[QueuedFile]) -> None:
        self._current_selected_file = file_item
        if not file_item:
            self.preview_title_label.setText("Markdown Preview")
            self.preview_meta_badge.setVisible(False)
            self.preview_edit.setPlainText("")
            self.warning_banner.setVisible(False)
            self.preview_note.setVisible(False)
            self._current_markdown_full = ""
            return

        self.preview_title_label.setText(file_item.display_name)

        # Handle Warnings
        if file_item.warnings:
            warn_text = "\n".join([f"⚠️ {w.user_message}" for w in file_item.warnings])
            self.warning_banner.setText(warn_text)
            self.warning_banner.setVisible(True)
        else:
            self.warning_banner.setVisible(False)

        # Handle Failure
        if file_item.status == FileStatus.FAILED:
            self.preview_meta_badge.setText(f"{file_item.extension.upper()} • Error")
            self.preview_meta_badge.setVisible(True)
            self.preview_edit.setPlainText(f"Conversion failed:\n\n{file_item.error_message}")
            self.preview_note.setVisible(False)
            self._current_markdown_full = ""
            return

        # Handle Completed Markdown
        if file_item.status in (FileStatus.READY, FileStatus.REVIEW) and file_item.result_id:
            cached_filename = f"results/{file_item.result_id}.md"
            content = read_cached_result_markdown(cached_filename)
            if content:
                self._current_markdown_full = content
                words = len(content.split())
                chars = len(content)
                self.preview_meta_badge.setText(f"{file_item.extension.upper()} • {words:,} words • {chars:,} chars")
                self.preview_meta_badge.setVisible(True)

                if chars > MAX_PREVIEW_CHARS:
                    display_text = content[:MAX_PREVIEW_CHARS]
                    self.preview_note.setText(MSG_PREVIEW_TRUNCATED)
                    self.preview_note.setVisible(True)
                else:
                    display_text = content
                    self.preview_note.setVisible(False)
                self.preview_edit.setPlainText(display_text)
                return

        # Not yet converted
        self.preview_meta_badge.setText(f"{file_item.extension.upper()} • Ready to convert")
        self.preview_meta_badge.setVisible(True)
        self.preview_edit.setPlainText(f"Status: {file_item.status.value.capitalize()}\n\nClick 'Convert All' to process this document.")
        self.preview_note.setVisible(False)
        self._current_markdown_full = ""

    def _update_button_states(self) -> None:
        selected_file = self._get_selected_file()
        is_ready = selected_file is not None and selected_file.status in (FileStatus.READY, FileStatus.REVIEW)

        self.btn_scan_read.setEnabled(selected_file is not None and not self._controller.is_running)
        self.btn_save_one.setEnabled(is_ready)
        self.btn_quick_save.setEnabled(is_ready)
        self.btn_copy.setEnabled(is_ready and bool(self._current_markdown_full))
        self.btn_quick_copy.setEnabled(is_ready and bool(self._current_markdown_full))
        self.btn_remove.setEnabled(selected_file is not None and not self._controller.is_running)

        has_any_ready = any(f.status in (FileStatus.READY, FileStatus.REVIEW) for f in self._model.files)
        self.btn_save_zip.setEnabled(has_any_ready and not self._controller.is_running)

    def _on_save_one_clicked(self) -> None:
        if not self._current_selected_file or not self._current_markdown_full:
            return

        stem = Path(self._current_selected_file.display_name).stem
        default_name = f"{stem}.md"

        target_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save Markdown Document",
            default_name,
            "Markdown Files (*.md);;All Files (*.*)",
        )
        if target_file:
            try:
                export_single_markdown(self._current_markdown_full, target_file)
                self.status_label.setText(f"Saved: {Path(target_file).name}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Could not save Markdown: {e}")

    def _on_save_zip_clicked(self) -> None:
        ready_files = [f for f in self._model.files if f.status in (FileStatus.READY, FileStatus.REVIEW)]
        if not ready_files:
            return

        target_zip, _ = QFileDialog.getSaveFileName(
            self,
            "Save All Converted Documents as ZIP",
            "converted_markdown_batch.zip",
            "ZIP Archives (*.zip);;All Files (*.*)",
        )
        if target_zip:
            items_to_export = []
            for f in ready_files:
                if f.result_id:
                    content = read_cached_result_markdown(f"results/{f.result_id}.md")
                    if content:
                        items_to_export.append((f.display_name, f.status.value, content, f.warnings))

            try:
                export_batch_zip(items_to_export, target_zip)
                self.status_label.setText(f"Batch exported: {Path(target_zip).name} ({len(items_to_export)} files)")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Could not export batch ZIP: {e}")

    def _on_copy_clicked(self) -> None:
        if self._current_markdown_full:
            clipboard = QApplication.clipboard()
            clipboard.setText(self._current_markdown_full)
            self.btn_copy.setText("✓ Copied!")
            self.btn_quick_copy.setText("✓ Copied!")
            self.status_label.setText("Markdown copied to clipboard.")
            QTimer.singleShot(1500, self._reset_copy_buttons)

    def _reset_copy_buttons(self) -> None:
        self.btn_copy.setText("📋 Copy Markdown")
        self.btn_quick_copy.setText("📋 Copy")

    def _on_remove_clicked(self) -> None:
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            return
        row = indexes[0].row()
        removed = self._model.remove_file_at(row)
        if removed and removed.result_id:
            delete_history_entry(removed.result_id)
        self._update_preview(None)
        self._refresh_queue_view()

    def _on_clear_history_clicked(self) -> None:
        if self._controller.is_running:
            QMessageBox.information(
                self,
                "Conversion in progress",
                "Please wait for active conversion to stop before clearing history.",
            )
            return

        confirm = QMessageBox.question(
            self,
            "Clear History",
            CONFIRM_CLEAR_HISTORY,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            report = clear_all_history()
            self._model.clear()
            self._update_preview(None)
            self._refresh_queue_view()
            if report.is_complete_success:
                self.status_label.setText("History and cached previews cleared.")
            else:
                self.status_label.setText(f"Cleared history with {len(report.failed_files)} warnings.")
