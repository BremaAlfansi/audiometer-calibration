from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout


class MetricCard(QFrame):
    def __init__(self, title):
        super().__init__()

        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 12px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px;")

        self.value_label = QLabel("--")
        self.value_label.setStyleSheet(
            "font-size: 28px; font-weight: bold;"
        )

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def set_value(self, text):
        self.value_label.setText(text)