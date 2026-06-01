from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class MetricCard(QFrame):
    def __init__(self, title):
        super().__init__()

        self.setFixedHeight(110)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #232323, stop:1 #1b2430);
                color: #e6e6e6;
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 10px;
                padding: 8px;
            }
            QLabel { color: #d7d7d7 }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_label.setStyleSheet("font-size: 12px; color: #aeb6c1;")

        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Segoe UI", 26)
        font.setWeight(QFont.Weight.DemiBold)
        self.value_label.setFont(font)
        self.value_label.setStyleSheet("color: #ffffff;")
        self.value_label.setTextFormat(Qt.TextFormat.PlainText)

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def set_value(self, text):
        self.value_label.setText(text)