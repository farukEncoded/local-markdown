"""Qt Table Model representing queued and converted documents."""

from __future__ import annotations

from typing import Any, List, Optional
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor, QFont

from local_markdown.conversion.models import FileStatus, QueuedFile


class FileTableModel(QAbstractTableModel):
    """Table model for managing the document conversion queue in the GUI."""

    COLUMNS = ["Document", "Format", "Size", "Status"]

    def __init__(self, files: Optional[List[QueuedFile]] = None) -> None:
        super().__init__()
        self._files: List[QueuedFile] = files or []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._files)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._files)):
            return None

        file_item = self._files[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return file_item.display_name
            elif col == 1:
                return file_item.extension.lstrip(".").upper()
            elif col == 2:
                return self._format_size(file_item.input_size)
            elif col == 3:
                return self._format_status(file_item)

        elif role == Qt.ItemDataRole.ForegroundRole:
            if col == 0:
                return QColor("#f8fafc")
            elif col == 1:
                ext = file_item.extension.lower()
                if ext == ".pdf":
                    return QColor("#f87171")
                elif ext in [".docx", ".doc"]:
                    return QColor("#60a5fa")
                elif ext in [".xlsx", ".xls"]:
                    return QColor("#34d399")
                elif ext in [".pptx", ".ppt"]:
                    return QColor("#fb923c")
                else:
                    return QColor("#c084fc")
            elif col == 2:
                return QColor("#94a3b8")
            elif col == 3:
                if file_item.status == FileStatus.READY:
                    return QColor("#34d399")
                elif file_item.status == FileStatus.RUNNING:
                    return QColor("#38bdf8")
                elif file_item.status == FileStatus.REVIEW:
                    return QColor("#fbbf24")
                elif file_item.status == FileStatus.FAILED:
                    return QColor("#f87171")
                elif file_item.status == FileStatus.CANCELLED:
                    return QColor("#94a3b8")
                return QColor("#94a3b8")

        elif role == Qt.ItemDataRole.FontRole:
            if col == 0:
                font = QFont("Segoe UI", 10)
                font.setBold(True)
                return font
            elif col == 1:
                font = QFont("Segoe UI", 9)
                font.setBold(True)
                return font
            elif col == 3:
                font = QFont("Segoe UI", 9)
                font.setBold(True)
                return font

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 1:
                return Qt.AlignmentFlag.AlignCenter
            elif col == 2:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            elif col == 3:
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        elif role == Qt.ItemDataRole.ToolTipRole:
            if file_item.error_message:
                return f"Error: {file_item.error_message}"
            if file_item.warnings:
                return "\n".join([f"Warning: {w.user_message}" for w in file_item.warnings])
            return file_item.display_name

        return None

    def add_file(self, file_item: QueuedFile) -> None:
        """Append a new file to the model."""
        row = len(self._files)
        self.beginInsertRows(QModelIndex(), row, row)
        self._files.append(file_item)
        self.endInsertRows()

    def remove_file_at(self, row: int) -> Optional[QueuedFile]:
        """Remove file at specified row."""
        if 0 <= row < len(self._files):
            self.beginRemoveRows(QModelIndex(), row, row)
            removed = self._files.pop(row)
            self.endRemoveRows()
            return removed
        return None

    def clear(self) -> None:
        """Clear all files from model."""
        self.beginResetModel()
        self._files.clear()
        self.endResetModel()

    def get_file(self, row: int) -> Optional[QueuedFile]:
        if 0 <= row < len(self._files):
            return self._files[row]
        return None

    def find_row_by_id(self, file_id: str) -> int:
        for idx, f in enumerate(self._files):
            if f.id == file_id:
                return idx
        return -1

    def update_row_by_id(self, file_id: str) -> None:
        row = self.find_row_by_id(file_id)
        if row >= 0:
            self.dataChanged.emit(self.index(row, 0), self.index(row, len(self.COLUMNS) - 1))

    @property
    def files(self) -> List[QueuedFile]:
        return self._files

    @staticmethod
    def _format_size(num_bytes: int) -> str:
        if num_bytes < 1024:
            return f"{num_bytes} B"
        elif num_bytes < 1024 * 1024:
            return f"{num_bytes / 1024:.1f} KB"
        else:
            return f"{num_bytes / (1024 * 1024):.1f} MB"

    @staticmethod
    def _format_status(item: QueuedFile) -> str:
        if item.status == FileStatus.QUEUED:
            return "● Ready"
        elif item.status == FileStatus.RUNNING:
            return "⟳ Converting..."
        elif item.status == FileStatus.READY:
            return "✓ Ready to save"
        elif item.status == FileStatus.REVIEW:
            return "⚠ Review scan"
        elif item.status == FileStatus.FAILED:
            return f"✕ Failed: {item.error_message or 'Error'}"
        elif item.status == FileStatus.CANCELLED:
            return "⏹ Cancelled"
        return "Unknown"
