# app/ui/contrast_defs_dialog.py
from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QPlainTextEdit, QLabel
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class ContrastDefinitionsDialog(QDialog):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Contrast definitions")
        self.resize(700, 520)

        layout = QVBoxLayout(self)

        title = QLabel("Contrast definitions (used by the app)")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title.setStyleSheet("color: white; font-weight: 600;")

        edit = QPlainTextEdit()
        edit.setReadOnly(True)
        edit.setPlainText(text)

        font = QFont("Courier New")
        font.setStyleHint(QFont.StyleHint.Monospace)
        edit.setFont(font)

        # local styling (independent from app global stylesheet)
        self.setStyleSheet(
            """
            QDialog { background-color: #1e1e1e; }
            QPlainTextEdit {
                background-color: #111111;
                color: #ffffff;
                border: 1px solid #444444;
            }
            QPushButton {
                background-color: #6c2bd1;
                color: white;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QPushButton:hover { background-color: #8e44ff; }
            """
        )

        btns = QHBoxLayout()
        btns.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btns.addWidget(close_btn)

        layout.addWidget(title)
        layout.addWidget(edit, 1)
        layout.addLayout(btns)
