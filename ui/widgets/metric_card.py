from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt

from ui import style
from ui.style import READING_BG, READING_FG, TEXT_MUTED, px, s


class MetricCard(QFrame):
    """Compact read-only readout: caption above, value below."""

    def __init__(self, title):
        super().__init__()

        self.setMinimumWidth(s(80))
        self.setStyleSheet(f"""
            QFrame {{
                background: {READING_BG};
                border: 1px dashed #3a8a83;
                border-radius: 8px;
            }}
            QLabel {{ border: none; background: transparent; }}
        """)

        compact = style.COMPACT
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6 if compact else 10, 6, 4 if compact else 10, 8)
        layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: {px(12 if compact else 13)}; color: {TEXT_MUTED};")

        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.value_label.setStyleSheet(
            f"font-size: {px(19)}; font-weight: 700; color: {READING_FG};"
            " font-family: Consolas, monospace;"
        )
        self.value_label.setTextFormat(Qt.TextFormat.PlainText)

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def set_value(self, text):
        self.value_label.setText(text)
