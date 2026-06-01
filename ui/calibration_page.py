from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QGroupBox
)

from core.calibration_engine import CalibrationEngine
from ui.widgets.spectrum_widget import SpectrumWidget
from PyQt6.QtWidgets import QHeaderView


class CalibrationPage(QWidget):
    def __init__(self):
        super().__init__()

        self.engine = CalibrationEngine()
        self.auto_fill_measured = True

        self.setup_ui()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        title = QLabel("Calibration Module")
        title.setStyleSheet("""
            font-size: 26px;
            font-weight: 700;
            color: #f0f6ff;
        """)
        root.addWidget(title)

        input_group = QGroupBox("Calibration Input")
        input_layout = QVBoxLayout()

        input_group.setLayout(input_layout)
        input_group.setStyleSheet('''
            QGroupBox { padding: 10px; border: 1px solid rgba(255,255,255,0.06); border-radius:8px; }
            QLabel { color: #d0d7de }
            QLineEdit { background: #0f1720; color: #e6eef8; padding:6px; border-radius:6px }
            QComboBox { background: #0f1720; color: #e6eef8; padding:4px; border-radius:6px }
            QPushButton { padding:6px 10px; border-radius:6px }
            QPushButton#primary { background-color: #2b90ff; color: white }
        ''')

        # Frequency
        freq_row = QHBoxLayout()

        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems([
            "125",
            "250",
            "500",
            "1000",
            "2000",
            "4000",
            "8000"
        ])

        # default to 1 kHz
        self.frequency_combo.setCurrentText("1000")

        freq_row.addWidget(QLabel("Frequency (Hz)"))
        freq_row.addWidget(self.frequency_combo)

        input_layout.addLayout(freq_row)

        # Measured
        measured_row = QHBoxLayout()

        self.measured_input = QLineEdit()
        self.measured_input.setPlaceholderText("Measured dB")
        self.measured_input.textChanged.connect(self.on_manual_measured_edit)

        measured_row.addWidget(QLabel("Measured dB"))
        measured_row.addWidget(self.measured_input)

        input_layout.addLayout(measured_row)

        # Reference
        reference_row = QHBoxLayout()

        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Reference dB")
        self.reference_input.textChanged.connect(self.on_reference_changed)

        reference_row.addWidget(QLabel("Reference dB"))
        reference_row.addWidget(self.reference_input)

        input_layout.addLayout(reference_row)

        # Tolerance
        tolerance_row = QHBoxLayout()

        self.tolerance_input = QLineEdit()
        self.tolerance_input.setText("3.0")
        self.tolerance_input.setPlaceholderText("Tolerance dB")

        tolerance_row.addWidget(QLabel("Tolerance (± dB)"))
        tolerance_row.addWidget(self.tolerance_input)

        input_layout.addLayout(tolerance_row)

        # Buttons
        button_row = QHBoxLayout()

        self.calculate_button = QPushButton("Calculate Calibration")
        self.calculate_button.setObjectName("primary")
        self.calculate_button.clicked.connect(
            self.calculate_calibration
        )

        self.save_button = QPushButton("Save Profile")
        self.save_button.setObjectName("primary")
        self.save_button.clicked.connect(
            self.save_profile
        )

        self.clear_button = QPushButton("Clear Session")
        self.clear_button.setObjectName("secondary")
        self.clear_button.clicked.connect(
            self.clear_session
        )

        self.history_button = QPushButton("Load History")
        self.history_button.setObjectName("secondary")
        self.history_button.clicked.connect(
            self.load_history
        )

        button_row.addWidget(self.calculate_button)
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.clear_button)
        button_row.addWidget(self.history_button)

        input_layout.addLayout(button_row)

        input_group.setLayout(input_layout)
        root.addWidget(input_group)

        # Summary
        self.summary_label = QLabel(
            "Total: 0 | PASS: 0 | FAIL: 0 | Overall: FAIL"
        )

        self.summary_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
        """)

        root.addWidget(self.summary_label)

        self.gain_preview_label = QLabel("Gain Correction: -- dB")
        self.gain_preview_label.setStyleSheet("font-size: 14px; color: #a8c9ff;")
        root.addWidget(self.gain_preview_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)

        self.table.setHorizontalHeaderLabels([
            "Frequency",
            "Measured dB",
            "Reference dB",
            "Correction dB",
            "Status"
        ])

        root.addWidget(self.table)

        # small status labels
        status_row = QHBoxLayout()
        self.last_measured_label = QLabel("Last Measured: -- dB")
        self.cal_level_label = QLabel("Calibration Level: -- dB")

        status_row.addWidget(self.last_measured_label)
        status_row.addWidget(self.cal_level_label)

        root.addLayout(status_row)

        # table header style
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet('''
            QTableWidget { background: #0b1220; color: #e6eef8; border: none }
            QHeaderView::section { background: #121826; color:#d7e1ff; padding:8px; font-weight:700 }
            QTableWidget::item { padding:6px }
        ''')

    def calculate_calibration(self):
        try:
            frequency = int(
                self.frequency_combo.currentText()
            )

            measured = float(
                self.measured_input.text()
            )

            reference = float(
                self.reference_input.text()
            )

            tolerance = float(
                self.tolerance_input.text()
            )

            result = self.engine.calculate_correction(
                frequency,
                measured,
                reference,
                tolerance
            )

            self.add_result_to_table(result)
            self.update_summary()

            # update small status labels
            self.last_measured_label.setText(f"Last Measured: {result['measured_db']:.2f} dB")
            self.cal_level_label.setText(f"Calibration Level: {result['reference_db']:.2f} dB")

            self.measured_input.clear()
            self.reference_input.clear()

        except ValueError:
            QMessageBox.warning(
                self,
                "Input Error",
                "Enter valid numeric values."
            )

    def on_manual_measured_edit(self, text):
        if self.measured_input.hasFocus():
            self.auto_fill_measured = False
        self.update_correction_preview()

    def on_reference_changed(self, text):
        self.update_correction_preview()

    def set_measured_value(self, value):
        if not self.auto_fill_measured:
            return

        self.measured_input.blockSignals(True)
        self.measured_input.setText(f"{value:.2f}")
        self.measured_input.blockSignals(False)
        self.update_correction_preview()

    def update_correction_preview(self):
        try:
            measured = float(self.measured_input.text())
            reference = float(self.reference_input.text())
            correction = reference - measured
            self.gain_preview_label.setText(
                f"Gain Correction: {correction:.2f} dB"
            )
        except ValueError:
            self.gain_preview_label.setText("Gain Correction: -- dB")

    def add_result_to_table(self, result):
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(
            row,
            0,
            QTableWidgetItem(str(result["frequency"]))
        )

        self.table.setItem(
            row,
            1,
            QTableWidgetItem(
                f"{result['measured_db']:.2f}"
            )
        )

        self.table.setItem(
            row,
            2,
            QTableWidgetItem(
                f"{result['reference_db']:.2f}"
            )
        )

        self.table.setItem(
            row,
            3,
            QTableWidgetItem(
                f"{result['correction_db']:.2f}"
            )
        )

        self.table.setItem(
            row,
            4,
            QTableWidgetItem(result["status"])
        )

    def update_summary(self):
        summary = self.engine.get_summary()

        self.summary_label.setText(
            f"Total: {summary['total']} | "
            f"PASS: {summary['passed']} | "
            f"FAIL: {summary['failed']} | "
            f"Overall: {summary['overall']}"
        )

    def save_profile(self):
        self.engine.save_profile()

        QMessageBox.information(
            self,
            "Saved",
            "Calibration profile saved."
        )

    def clear_session(self):
        self.engine.clear_session()
        self.table.setRowCount(0)
        self.update_summary()

    def load_history(self):
        rows = self.engine.get_history()

        self.table.setRowCount(0)

        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            frequency = row_data[1]
            measured = row_data[2]
            reference = row_data[3]
            correction = row_data[4]
            status = row_data[5]

            self.table.setItem(
                row,
                0,
                QTableWidgetItem(str(frequency))
            )

            self.table.setItem(
                row,
                1,
                QTableWidgetItem(f"{measured:.2f}")
            )

            self.table.setItem(
                row,
                2,
                QTableWidgetItem(f"{reference:.2f}")
            )

            self.table.setItem(
                row,
                3,
                QTableWidgetItem(f"{correction:.2f}")
            )

            self.table.setItem(
                row,
                4,
                QTableWidgetItem(status)
            )

        # update small labels with most recent if available
        if rows:
            latest = rows[0]
            self.last_measured_label.setText(f"Last Measured: {latest[2]:.2f} dB")
            self.cal_level_label.setText(f"Calibration Level: {latest[3]:.2f} dB")