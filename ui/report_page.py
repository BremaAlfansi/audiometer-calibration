from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox
)

import csv
import struct
from openpyxl import Workbook

from database.db import CalibrationDatabase


class ReportPage(QWidget):
    def __init__(self):
        super().__init__()

        self.db = CalibrationDatabase()

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        root = QVBoxLayout(self)

        title = QLabel("Saved Measurements")
        title.setStyleSheet("font-size:20px; font-weight:bold;")

        root.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Timestamp",
            "Frequency",
            "Target Level",
            "Measured dB",
            "Adjusted dB",
            "THD",
            "Status"
        ])

        # double click to clear a cell
        self.table.cellDoubleClicked.connect(self.clear_cell)

        # style table and headers for esthetic look
        from PyQt6.QtWidgets import QHeaderView
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet('''
            QTableWidget { background: #081018; color: #e9f0ff; border: none }
            QHeaderView::section { background: #0f1a2b; color:#dbe9ff; padding:8px; font-weight:700 }
            QTableWidget::item { padding:6px }
        ''')

        root.addWidget(self.table)

        btn_row = QHBoxLayout()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_data)
        self.refresh_btn.setObjectName("secondary")

        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_csv_btn.setObjectName("primary")

        self.export_xlsx_btn = QPushButton("Export Excel")
        self.export_xlsx_btn.clicked.connect(self.export_xlsx)
        self.export_xlsx_btn.setObjectName("primary")

        btn_row.addWidget(self.refresh_btn)
        btn_row.addWidget(self.export_csv_btn)
        btn_row.addWidget(self.export_xlsx_btn)

        root.addLayout(btn_row)

    def normalize_value(self, value, col_idx):
        if isinstance(value, bytes):
            if len(value) == 4:
                try:
                    value = struct.unpack('<f', value)[0]
                except struct.error:
                    pass
            elif len(value) == 8:
                try:
                    value = struct.unpack('<d', value)[0]
                except struct.error:
                    pass

            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8')
                except Exception:
                    value = repr(value)

        if isinstance(value, float):
            if col_idx == 5:
                return f"{value:.2f}%"
            return f"{value:.2f}"

        if isinstance(value, int):
            return str(value)

        return str(value)

    def load_data(self):
        rows = self.db.get_measurements()

        self.table.setRowCount(0)

        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            for col_idx, value in enumerate(row_data):
                normalized = self.normalize_value(value, col_idx)
                item = QTableWidgetItem(normalized)
                self.table.setItem(row, col_idx, item)

    def clear_cell(self, row, column):
        # clear the clicked cell
        item = self.table.item(row, column)
        if item:
            item.setText("")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "measurements.csv", "CSV Files (*.csv)")

        if not path:
            return

        rows = self.db.get_measurements()

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Frequency", "Target Level", "Measured dB", "Adjusted dB", "THD", "Status"])

                for r in rows:
                    normalized = [self.normalize_value(v, idx) for idx, v in enumerate(r)]
                    writer.writerow(normalized)

            QMessageBox.information(self, "Exported", "CSV exported successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export CSV: {e}")

    def export_xlsx(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Excel", "measurements.xlsx", "Excel Files (*.xlsx)")

        if not path:
            return

        rows = self.db.get_measurements()

        try:
            wb = Workbook()
            ws = wb.active
            ws.append(["Timestamp", "Frequency", "Target Level", "Measured dB", "Adjusted dB", "THD", "Status"])

            for r in rows:
                normalized = [self.normalize_value(v, idx) for idx, v in enumerate(r)]
                ws.append(normalized)

            wb.save(path)

            QMessageBox.information(self, "Exported", "Excel exported successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export Excel: {e}")
