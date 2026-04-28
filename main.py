import sys
import json
import os
import base64
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QSplitter, QListWidget, QTextEdit, QToolBar,
    QAction, QInputDialog, QMessageBox, QLabel,
    QFileDialog, QDialog, QDialogButtonBox,
    QFormLayout, QSpinBox,
)
from PyQt5.QtGui import (
    QFont, QKeySequence, QIcon, QTextImageFormat,
    QPixmap, QImage, QDesktopServices,
)
from PyQt5.QtCore import Qt, QSize, QUrl, QByteArray, QBuffer
from PyQt5.QtPrintSupport import QPrinter

SAVE_FILE = "notes_data.json"

DARK = """
    QMainWindow, QWidget {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    QTextEdit {
        background-color: #2b2b2b;
        color: #ffffff;
        border: 1px solid #3a3a3a;
    }
    QListWidget {
        background-color: #2b2b2b;
        color: #ffffff;
        border: 1px solid #3a3a3a;
    }
    QListWidget::item:selected {
        background-color: #3a3a3a;
    }
    QToolBar {
        background-color: #1e1e1e;
        border-bottom: 1px solid #3a3a3a;
    }
    QStatusBar {
        background-color: #1e1e1e;
        color: #aaaaaa;
    }
    QLabel {
        color: #aaaaaa;
    }
"""

LIGHT = """
    QMainWindow, QWidget {
        background-color: #f5f5f5;
        color: #000000;
    }
    QTextEdit {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #cccccc;
    }
    QListWidget {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #cccccc;
    }
    QListWidget::item:selected {
        background-color: #e0e0e0;
    }
    QToolBar {
        background-color: #f5f5f5;
        border-bottom: 1px solid #cccccc;
    }
    QStatusBar {
        background-color: #f5f5f5;
        color: #555555;
    }
    QLabel {
        color: #555555;
    }
"""

class ImageResizeDialog(QDialog):
    def __init__(self, orig_w, orig_h, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Insert Image")
        self.orig_w = orig_w
        self.orig_h = orig_h
        layout = QFormLayout(self)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(50, 2000)
        self.width_spin.setValue(min(orig_w, 500))
        self.width_spin.setSuffix(" px")
        self.width_spin.valueChanged.connect(self._sync_height)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(50, 2000)
        self.height_spin.setValue(int(min(orig_w, 500) * orig_h / orig_w))
        self.height_spin.setSuffix(" px")
        self.lock_ratio = True
        layout.addRow("Width:", self.width_spin)
        layout.addRow("Height:", self.height_spin)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _sync_height(self, w):
        if self.lock_ratio and self.orig_w:
            self.height_spin.blockSignals(True)
            self.height_spin.setValue(int(w * self.orig_h / self.orig_w))
            self.height_spin.blockSignals(False)

    def values(self):
        return self.width_spin.value(), self.height_spin.value()

class NotesApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WriteNow")

        def resource_path(relative_path):
            import os
            base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
            return os.path.join(base_path, relative_path)
        
        self.setWindowIcon(QIcon("assets/logo.png"))
        self.setMinimumSize(700, 450)
        self.resize(900, 600)
        self.notes: dict[str, str] = {}
        self.current_note: str | None = None
        self._loading = False
        self._dark_mode = False
        self._build_toolbar()
        self._build_central_widget()
        self._build_status_bar()
        self._load_from_disk()
        self._refresh_list()
        QApplication.instance().setStyleSheet(LIGHT)

    def _build_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)
        toolbar.setContentsMargins(4, 4, 4, 4)
        self.addToolBar(toolbar)
        new_action = QAction("＋  New Note", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.setToolTip("New note  (Ctrl+N)")
        new_action.triggered.connect(self._new_note)
        toolbar.addAction(new_action)
        toolbar.addSeparator()
        delete_action = QAction("🗑  Delete", self)
        delete_action.setShortcut(QKeySequence("Ctrl+D"))
        delete_action.setToolTip("Delete selected note  (Ctrl+D)")
        delete_action.triggered.connect(self._delete_note)
        toolbar.addAction(delete_action)
        toolbar.addSeparator()
        clear_action = QAction("✕  Clear All", self)
        clear_action.setToolTip("Delete all notes")
        clear_action.triggered.connect(self._clear_all)
        toolbar.addAction(clear_action)
        toolbar.addSeparator()
        img_action = QAction("🖼  Add Image", self)
        img_action.setShortcut(QKeySequence("Ctrl+I"))
        img_action.setToolTip("Insert image into note  (Ctrl+I)")
        img_action.triggered.connect(self._insert_image)
        toolbar.addAction(img_action)
        toolbar.addSeparator()
        export_action = QAction("📤  Export", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.setToolTip("Export note  (Ctrl+E)")
        export_action.triggered.connect(self._export_note)
        toolbar.addAction(export_action)
        toolbar.addSeparator()
        self.theme_action = QAction("🌙  Dark", self)
        self.theme_action.setToolTip("Toggle dark/light mode")
        self.theme_action.triggered.connect(self._toggle_theme)
        toolbar.addAction(self.theme_action)

    def _build_central_widget(self):
        container = QWidget()
        self.setCentralWidget(container)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont("Segoe UI", 11))
        self.list_widget.setMinimumWidth(180)
        self.list_widget.setSpacing(2)
        self.list_widget.currentItemChanged.connect(self._on_note_selected)
        splitter.addWidget(self.list_widget)
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Segoe UI", 12))
        self.editor.setPlaceholderText("What's on your mind...")
        self.editor.setAcceptRichText(True)
        self.editor.textChanged.connect(self._on_text_changed)
        splitter.addWidget(self.editor)
        splitter.setSizes([200, 700])

    def _build_status_bar(self):
        self.word_count_label = QLabel("Words: 0")
        self.word_count_label.setFont(QFont("Segoe UI", 9))
        self.statusBar().addPermanentWidget(self.word_count_label)
        self.statusBar().showMessage("Ready")

    def _toggle_theme(self):
        self._dark_mode = not self._dark_mode
        if self._dark_mode:
            QApplication.instance().setStyleSheet(DARK)
            self.theme_action.setText("☀️  Light")
        else:
            QApplication.instance().setStyleSheet(LIGHT)
            self.theme_action.setText("🌙  Dark")

    def _pixmap_to_base64(self, pixmap: QPixmap) -> str:
        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QBuffer.WriteOnly)
        pixmap.save(buf, "PNG")
        buf.close()
        return base64.b64encode(ba.data()).decode("ascii")

    def _insert_image(self):
        if self.current_note is None:
            QMessageBox.information(self, "No Note", "Please select or create a note first.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)")
        if not path:
            return
        img = QImage(path)
        if img.isNull():
            QMessageBox.warning(self, "Error", "Could not load image.")
            return
        dialog = ImageResizeDialog(img.width(), img.height(), self)
        if dialog.exec_() != QDialog.Accepted:
            return
        w, h = dialog.values()
        pixmap = QPixmap.fromImage(img).scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        b64 = self._pixmap_to_base64(pixmap)
        data_uri = f"data:image/png;base64,{b64}"
        cursor = self.editor.textCursor()
        cursor.insertHtml(f'<img src="{data_uri}" width="{w}" height="{h}"/>')
        self.statusBar().showMessage("Image inserted", 3000)

    def _export_note(self):
        if self.current_note is None:
            QMessageBox.information(self, "No Note", "Please select a note to export.")
            return
        fmt_choice, ok = QInputDialog.getItem(self, "Export Format", "Choose format:", ["HTML (.html)", "Plain Text (.txt)", "PDF (.pdf)"], 0, False)
        if not ok:
            return
        if "HTML" in fmt_choice:
            self._export_html()
        elif "Plain Text" in fmt_choice:
            self._export_txt()
        elif "PDF" in fmt_choice:
            self._export_pdf()

    def _export_html(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export as HTML", f"{self.current_note}.html", "HTML Files (*.html)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.editor.toHtml())
        self._open_after_export(path)

    def _export_txt(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export as Text", f"{self.current_note}.txt", "Text Files (*.txt)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.editor.toPlainText())
        self._open_after_export(path)

    def _export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export as PDF", f"{self.current_note}.pdf", "PDF Files (*.pdf)")
        if not path:
            return
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        self.editor.document().print_(printer)
        self._open_after_export(path)

    def _open_after_export(self, path: str):
        reply = QMessageBox.question(self, "Exported", f'Saved to:\n{path}\n\nOpen it now?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _new_note(self):
        title, ok = QInputDialog.getText(self, "New Note", "Note title:")
        if not ok:
            return
        title = title.strip()
        if not title:
            return
        if title in self.notes:
            QMessageBox.warning(self, "Duplicate", f'A note called "{title}" already exists.')
            return
        self.notes[title] = ""
        self._save_to_disk()
        self._refresh_list()
        self._select_note(title)
        self.statusBar().showMessage(f'Created "{title}"', 3000)

    def _delete_note(self):
        if self.current_note is None:
            return
        reply = QMessageBox.question(self, "Delete Note", f'Delete "{self.current_note}"?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        del self.notes[self.current_note]
        self.current_note = None
        self._save_to_disk()
        self._refresh_list()
        self._loading = True
        self.editor.clear()
        self._loading = False
        self.statusBar().showMessage("Note deleted", 3000)

    def _clear_all(self):
        if not self.notes:
            return
        reply = QMessageBox.warning(self, "Clear All Notes", "This will permanently delete ALL notes. Are you sure?", QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
        if reply != QMessageBox.Yes:
            return
        self.notes.clear()
        self.current_note = None
        self._save_to_disk()
        self._refresh_list()
        self._loading = True
        self.editor.clear()
        self._loading = False
        self.statusBar().showMessage("All notes deleted", 3000)

    def _on_note_selected(self, current, _previous):
        if current is None:
            return
        self._select_note(current.text())

    def _select_note(self, title: str):
        self.current_note = title
        self._loading = True
        content = self.notes[title]
        if content.strip().startswith("<"):
            self.editor.setHtml(content)
        else:
            self.editor.setPlainText(content)
        self._loading = False
        self.editor.setFocus()
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).text() == title:
                self.list_widget.setCurrentRow(i)
                break
        self._update_word_count()

    def _on_text_changed(self):
        if self._loading or self.current_note is None:
            return
        self.notes[self.current_note] = self.editor.toHtml()
        self._save_to_disk()
        self._update_word_count()

    def _refresh_list(self):
        self.list_widget.clear()
        for title in self.notes:
            self.list_widget.addItem(title)

    def _update_word_count(self):
        text = self.editor.toPlainText()
        self.word_count_label.setText(f"Words: {len(text.split()) if text.strip() else 0}")

    def _save_to_disk(self):
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.notes, f, indent=2, ensure_ascii=False)

    def _load_from_disk(self):
        if not os.path.exists(SAVE_FILE):
            return
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    self.notes = {str(k): str(v) for k, v in data.items()}
            except json.JSONDecodeError:
                self.notes = {}

    def closeEvent(self, event):
        self._save_to_disk()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 11))
    window = NotesApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()