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


class CalibrationPage(QWidget):
    def __init__(self):
        super().__init__()

        self.engine = CalibrationEngine()

        self.setup_ui()

    def setup_ui(self):
        root = QVBoxLayout(self)

        title = QLabel("Calibration Module")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
        """)
        root.addWidget(title)

        input_group = QGroupBox("Calibration Input")
        input_layout = QVBoxLayout()

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

        freq_row.addWidget(QLabel("Frequency (Hz)"))
        freq_row.addWidget(self.frequency_combo)

        input_layout.addLayout(freq_row)

        # Measured
        measured_row = QHBoxLayout()

        self.measured_input = QLineEdit()
        self.measured_input.setPlaceholderText("Measured dB")

        measured_row.addWidget(QLabel("Measured dB"))
        measured_row.addWidget(self.measured_input)

        input_layout.addLayout(measured_row)

        # Reference
        reference_row = QHBoxLayout()

        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Reference dB")

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
        self.calculate_button.clicked.connect(
            self.calculate_calibration
        )

        self.save_button = QPushButton("Save Profile")
        self.save_button.clicked.connect(
            self.save_profile
        )

        self.clear_button = QPushButton("Clear Session")
        self.clear_button.clicked.connect(
            self.clear_session
        )

        self.history_button = QPushButton("Load History")
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

            self.measured_input.clear()
            self.reference_input.clear()

        except ValueError:
            QMessageBox.warning(
                self,
                "Input Error",
                "Enter valid numeric values."
            )

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