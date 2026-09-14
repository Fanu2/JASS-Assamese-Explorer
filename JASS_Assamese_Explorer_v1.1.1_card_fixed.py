import sys
import sqlite3
import random
import json
import urllib.parse
import urllib.request
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QRectF
from PySide6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QPixmap
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QTextEdit, QSplitter, QMessageBox, QGroupBox, QFormLayout,
    QComboBox, QSpinBox, QColorDialog, QDialog, QDialogButtonBox,
    QSlider, QFileDialog, QCheckBox
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "JASS_Assamese_Corpus.db"


THEMES = {
    "Rose Garden": {
        "bg": "#fff4f7", "panel": "#ffffff", "accent": "#b23a62",
        "text": "#351522", "secondary": "#7c4a5c"
    },
    "Midnight Love": {
        "bg": "#171522", "panel": "#272238", "accent": "#e9a8c0",
        "text": "#fff4f8", "secondary": "#d0b9c5"
    },
    "Golden Evening": {
        "bg": "#fff8e8", "panel": "#fffdf7", "accent": "#9a6a20",
        "text": "#3f2b12", "secondary": "#765c34"
    },
    "Lavender Dream": {
        "bg": "#f6f1ff", "panel": "#ffffff", "accent": "#7955a6",
        "text": "#30233d", "secondary": "#665676"
    },
    "Ocean Breeze": {
        "bg": "#edf8fb", "panel": "#ffffff", "accent": "#24778a",
        "text": "#17333a", "secondary": "#4e6e75"
    },
    "Classic Paper": {
        "bg": "#f7f1e3", "panel": "#fffdf7", "accent": "#684c35",
        "text": "#30261e", "secondary": "#756454"
    }
}


class RomanticCardDialog(QDialog):
    def __init__(self, assamese, english="", source_line=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JASS Assamese Romantic Card Studio")
        self.resize(1050, 760)

        self.assamese = assamese
        self.source_line = source_line
        self.dragging = False
        self.drag_start = QPoint()
        self.offset = QPoint(0, 0)

        root = QVBoxLayout(self)

        controls = QHBoxLayout()
        self.theme = QComboBox()
        self.theme.addItems(THEMES.keys())
        self.theme.currentIndexChanged.connect(self.update_preview)

        self.size = QSpinBox()
        self.size.setRange(12, 80)
        self.size.setValue(30)
        self.size.valueChanged.connect(self.update_preview)

        self.color_btn = QPushButton("Text colour")
        self.color = "#351522"
        self.color_btn.clicked.connect(self.choose_color)

        self.bold = QCheckBox("Bold")
        self.bold.stateChanged.connect(self.update_preview)

        controls.addWidget(QLabel("Theme"))
        controls.addWidget(self.theme)
        controls.addWidget(QLabel("Font"))
        controls.addWidget(self.size)
        controls.addWidget(self.color_btn)
        controls.addWidget(self.bold)
        controls.addStretch()
        root.addLayout(controls)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter, 1)

        editor = QWidget()
        editor_layout = QVBoxLayout(editor)

        editor_layout.addWidget(QLabel("Assamese text — editable"))
        self.assamese_edit = QTextEdit()
        self.assamese_edit.setPlainText(assamese)
        self.assamese_edit.setFont(QFont("Noto Sans", 15))
        self.assamese_edit.textChanged.connect(self.update_preview)
        editor_layout.addWidget(self.assamese_edit)

        editor_layout.addWidget(QLabel("English translation / additional words — editable"))
        self.english_edit = QTextEdit()
        self.english_edit.setPlainText(english)
        self.english_edit.setFont(QFont("Segoe UI", 13))
        self.english_edit.textChanged.connect(self.update_preview)
        editor_layout.addWidget(self.english_edit)

        editor_layout.addWidget(QLabel(
            "Tip: edit either text box, add your own romantic words, "
            "then drag the text on the preview."
        ))

        splitter.addWidget(editor)

        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.addWidget(QLabel("Card preview — drag text to reposition"))

        self.preview = QLabel()
        self.preview.setMinimumSize(520, 520)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet("background: #d9d9d9;")
        self.preview.mousePressEvent = self.preview_press
        self.preview.mouseMoveEvent = self.preview_move
        self.preview.mouseReleaseEvent = self.preview_release
        preview_layout.addWidget(self.preview, 1)

        splitter.addWidget(preview_panel)
        splitter.setSizes([430, 600])

        buttons = QDialogButtonBox()
        save_btn = buttons.addButton(
            "Create / Save Romantic Card",
            QDialogButtonBox.ButtonRole.AcceptRole
        )
        cancel_btn = buttons.addButton(
            "Cancel", QDialogButtonBox.ButtonRole.RejectRole
        )
        save_btn.clicked.connect(self.save_card)
        cancel_btn.clicked.connect(self.reject)
        root.addWidget(buttons)

        self.update_preview()

    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.color), self, "Choose text colour")
        if color.isValid():
            self.color = color.name()
            self.update_preview()

    def make_card(self, save_size=(1200, 1200)):
        theme = THEMES[self.theme.currentText()]
        pix = QPixmap(*save_size)
        pix.fill(QColor(theme["bg"]))

        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Decorative frame
        p.setPen(QPen(QColor(theme["accent"]), 5))
        p.drawRoundedRect(QRectF(35, 35, save_size[0]-70, save_size[1]-70), 35, 35)

        # Small decorative hearts
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(theme["accent"])))
        for x, y, r in [(95, 95, 18), (save_size[0]-95, 95, 18),
                        (95, save_size[1]-95, 18),
                        (save_size[0]-95, save_size[1]-95, 18)]:
            p.drawEllipse(QPoint(x, y), r, r)

        assamese = self.assamese_edit.toPlainText().strip()
        english = self.english_edit.toPlainText().strip()

        # Keep the main Assamese message in the center area.
        main_font = QFont("Noto Sans", self.size.value())
        main_font.setBold(self.bold.isChecked())
        main_font.setItalic(True)
        p.setFont(main_font)
        p.setPen(QColor(self.color))

        main_rect = QRectF(
            100 + self.offset.x(), 230 + self.offset.y(),
            save_size[0] - 200, 430
        )
        p.drawText(
            main_rect,
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            assamese
        )

        if english:
            eng_font = QFont("Segoe UI", max(16, self.size.value() - 8))
            eng_font.setItalic(True)
            p.setFont(eng_font)
            p.setPen(QColor(theme["secondary"]))
            eng_rect = QRectF(
                120 + self.offset.x(), 700 + self.offset.y(),
                save_size[0] - 240, 270
            )
            p.drawText(
                eng_rect,
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                english
            )

        p.setFont(QFont("Segoe UI", 15))
        p.setPen(QColor(theme["accent"]))
        footer = "JASS Assamese Explorer"
        if self.source_line:
            try:
                source_line_display = f"{int(str(self.source_line).replace(',', '')):,}"
            except (TypeError, ValueError):
                source_line_display = str(self.source_line)
            footer += f"  •  Source line {source_line_display}"
        p.drawText(
            QRectF(80, save_size[1]-85, save_size[0]-160, 35),
            Qt.AlignmentFlag.AlignCenter, footer
        )

        p.end()
        return pix

    def update_preview(self):
        pix = self.make_card((800, 800))
        self.preview.setPixmap(
            pix.scaled(
                self.preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

    def preview_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start = event.position().toPoint()
            event.accept()

    def preview_move(self, event):
        if self.dragging:
            current = event.position().toPoint()
            delta = current - self.drag_start
            # Preview is scaled, so use a modest multiplier.
            self.offset += QPoint(delta.x() * 2, delta.y() * 2)
            self.drag_start = current
            self.update_preview()
            event.accept()

    def preview_release(self, event):
        self.dragging = False
        event.accept()

    def save_card(self):
        default = BASE_DIR / "Assamese_Romantic_Card.png"
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Romantic Card", str(default),
            "PNG Image (*.png);;JPEG Image (*.jpg)"
        )
        if not filename:
            return

        pix = self.make_card((1200, 1200))
        if not pix.save(filename):
            QMessageBox.warning(self, "Save failed", "Could not save the card.")
            return

        QMessageBox.information(
            self, "Card created",
            f"Beautiful romantic card saved to:\n{filename}"
        )
        self.accept()


class AssameseExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JASS Assamese Explorer v1.1 • Discovery Studio")
        self.resize(1450, 900)

        if not DB_PATH.exists():
            QMessageBox.critical(
                self, "Database not found",
                f"Could not find:\n{DB_PATH}\n\n"
                "Place this application beside JASS_Assamese_Corpus.db."
            )
            raise SystemExit(1)

        self.conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        self.conn.row_factory = sqlite3.Row
        self.build_ui()
        self.load_stats()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        title = QLabel("JASS Assamese Explorer")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        root.addWidget(title)

        subtitle = QLabel(
            "Discovery Studio • 1,613,879 verified Assamese records • DATABASE READ-ONLY"
        )
        root.addWidget(subtitle)

        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search an Assamese word or phrase…")
        self.search.returnPressed.connect(self.search_corpus)

        self.mode = QComboBox()
        self.mode.addItems(["Phrase", "Contains"])

        self.limit = QComboBox()
        self.limit.addItems(["50", "100", "250", "500"])
        self.limit.setCurrentText("100")

        for button, slot in [
            ("🔎 Search", self.search_corpus),
            ("🎲 Random", self.random_record),
            ("📊 Statistics", self.load_stats),
        ]:
            b = QPushButton(button)
            b.clicked.connect(slot)
            search_row.addWidget(b)

        search_row.insertWidget(0, self.search, 1)
        search_row.insertWidget(1, self.mode)
        search_row.insertWidget(2, self.limit)
        root.addLayout(search_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter, 1)

        left = QWidget()
        ll = QVBoxLayout(left)
        self.results_label = QLabel("Results")
        ll.addWidget(self.results_label)

        self.results = QListWidget()
        self.results.currentItemChanged.connect(self.result_selected)
        ll.addWidget(self.results)

        nav = QHBoxLayout()
        prev = QPushButton("← Previous")
        nxt = QPushButton("Next →")
        prev.clicked.connect(lambda: self.move_result(-1))
        nxt.clicked.connect(lambda: self.move_result(1))
        nav.addWidget(prev)
        nav.addWidget(nxt)
        ll.addLayout(nav)

        splitter.addWidget(left)

        right = QWidget()
        rl = QVBoxLayout(right)

        info = QGroupBox("Selected Record")
        form = QFormLayout(info)
        self.source_line = QLabel("—")
        self.record_id = QLabel("—")
        self.char_count = QLabel("—")
        self.word_count = QLabel("—")
        form.addRow("Source line:", self.source_line)
        form.addRow("Record ID:", self.record_id)
        form.addRow("Characters:", self.char_count)
        form.addRow("Words:", self.word_count)
        rl.addWidget(info)

        rl.addWidget(QLabel("Assamese"))
        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)
        self.reader_size = QSlider(Qt.Orientation.Horizontal)
        self.reader_size.setRange(12, 34)
        self.reader_size.setValue(18)
        self.reader_size.valueChanged.connect(self.resize_reader)
        rl.addWidget(self.reader_size)
        rl.addWidget(self.text_view, 3)

        tr_row = QHBoxLayout()
        self.translate_btn = QPushButton("🌐 Translate to English")
        self.translate_btn.clicked.connect(self.translate_current)
        self.status_translate = QLabel("")
        tr_row.addWidget(self.translate_btn)
        tr_row.addWidget(self.status_translate, 1)
        rl.addLayout(tr_row)

        rl.addWidget(QLabel("English translation / editable additions"))
        self.english_view = QTextEdit()
        self.english_view.setPlaceholderText(
            "Translation will appear here. You can edit it, add words, "
            "or turn it into a romantic message."
        )
        rl.addWidget(self.english_view, 2)

        action_row = QHBoxLayout()
        copy_a = QPushButton("Copy Assamese")
        copy_e = QPushButton("Copy English")
        card = QPushButton("❤️ Create Romantic Card")
        copy_a.clicked.connect(lambda: QApplication.clipboard().setText(
            self.text_view.toPlainText()
        ))
        copy_e.clicked.connect(lambda: QApplication.clipboard().setText(
            self.english_view.toPlainText()
        ))
        card.clicked.connect(self.create_card)
        action_row.addWidget(copy_a)
        action_row.addWidget(copy_e)
        action_row.addWidget(card)
        rl.addLayout(action_row)

        splitter.addWidget(right)
        splitter.setSizes([450, 950])

        self.status = QLabel("Ready")
        root.addWidget(self.status)

    def load_stats(self):
        count = self.conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        min_line, max_line = self.conn.execute(
            "SELECT MIN(source_line), MAX(source_line) FROM records"
        ).fetchone()
        self.status.setText(
            f"Corpus: {count:,} records • "
            f"Source lines {min_line:,}–{max_line:,} • READ-ONLY"
        )

    def search_corpus(self):
        query = self.search.text().strip()
        if not query:
            return

        self.results.clear()
        self.text_view.clear()
        self.english_view.clear()

        limit = int(self.limit.currentText())

        try:
            if self.mode.currentText() == "Phrase":
                rows = self.conn.execute(
                    """
                    SELECT r.id, r.source_line, r.text
                    FROM assamese_fts f
                    JOIN records r ON r.id = f.rowid
                    WHERE assamese_fts MATCH ?
                    LIMIT ?
                    """,
                    (f'"{query}"', limit)
                ).fetchall()
            else:
                rows = self.conn.execute(
                    """
                    SELECT id, source_line, text
                    FROM records
                    WHERE text LIKE ?
                    LIMIT ?
                    """,
                    (f"%{query}%", limit)
                ).fetchall()
        except sqlite3.Error as exc:
            self.status.setText(f"Search error: {exc}")
            return

        for row in rows:
            preview = row["text"].replace("\n", " ")
            if len(preview) > 220:
                preview = preview[:220] + "…"
            item = QListWidgetItem(
                f"Line {row['source_line']:,}  |  {preview}"
            )
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            self.results.addItem(item)

        self.results_label.setText(f"Results: {len(rows):,}")
        self.status.setText(
            f"Search complete: {len(rows):,} result(s) for “{query}”"
        )
        if rows:
            self.results.setCurrentRow(0)

    def result_selected(self, current, previous):
        if current is None:
            return

        record_id = current.data(Qt.ItemDataRole.UserRole)
        row = self.conn.execute(
            "SELECT id, source_line, text FROM records WHERE id = ?",
            (record_id,)
        ).fetchone()
        if row is None:
            return

        text = row["text"]
        self.record_id.setText(f"{row['id']:,}")
        self.source_line.setText(f"{row['source_line']:,}")
        self.char_count.setText(f"{len(text):,}")
        self.word_count.setText(f"{len(text.split()):,}")
        self.text_view.setPlainText(text)
        self.english_view.clear()
        self.status_translate.setText("")

    def resize_reader(self, value):
        self.text_view.setFont(QFont("Noto Sans", value))

    def move_result(self, delta):
        row = self.results.currentRow()
        new_row = row + delta
        if 0 <= new_row < self.results.count():
            self.results.setCurrentRow(new_row)

    def random_record(self):
        total = self.conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        if total == 0:
            return

        record_id = random.randint(1, total)
        row = self.conn.execute(
            "SELECT id, source_line, text FROM records WHERE id = ?",
            (record_id,)
        ).fetchone()
        if row is None:
            return

        self.results.clear()
        item = QListWidgetItem(
            f"Line {row['source_line']:,}  |  "
            f"{row['text'][:220].replace(chr(10), ' ')}"
        )
        item.setData(Qt.ItemDataRole.UserRole, row["id"])
        self.results.addItem(item)
        self.results.setCurrentItem(item)
        self.results_label.setText("Random discovery")
        self.status.setText(
            f"Random record selected: source line {row['source_line']:,}"
        )

    def translate_current(self):
        text = self.text_view.toPlainText().strip()
        if not text:
            return

        self.translate_btn.setEnabled(False)
        self.status_translate.setText("Translating online…")
        QApplication.processEvents()

        try:
            # Google Translate's public web endpoint is used only as a
            # convenience. The corpus/database remains completely local.
            params = urllib.parse.urlencode({
                "client": "gtx",
                "sl": "as",
                "tl": "en",
                "dt": "t",
                "q": text[:4500]
            })
            url = "https://translate.googleapis.com/translate_a/single?" + params
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))

            translated = "".join(
                part[0] for part in data[0] if part and part[0]
            )
            self.english_view.setPlainText(translated)
            self.status_translate.setText("Translation complete.")
        except Exception as exc:
            self.status_translate.setText(
                "Online translation unavailable — edit English manually."
            )
            QMessageBox.information(
                self, "Translation unavailable",
                "The online Assamese → English service could not complete "
                "the request.\n\n"
                f"Details: {exc}\n\n"
                "You can still edit the English box and create a card."
            )
        finally:
            self.translate_btn.setEnabled(True)

    def create_card(self):
        text = self.text_view.toPlainText().strip()
        if not text:
            QMessageBox.information(
                self, "No passage selected",
                "Select an Assamese passage first."
            )
            return

        dlg = RomanticCardDialog(
            text,
            self.english_view.toPlainText(),
            self.source_line.text().replace(",", "")
            if self.source_line.text() != "—" else None,
            self
        )
        dlg.exec()

    def closeEvent(self, event):
        self.conn.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("JASS Assamese Explorer")
    window = AssameseExplorer()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
