from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QHeaderView,
    QAbstractItemView
)

import csv
import os
import sqlite3
import struct
from openpyxl import Workbook

import database.db as db_module
from database.db import CalibrationDatabase


class ReportPage(QWidget):
    def __init__(self):
        super().__init__()

        self.db = CalibrationDatabase()
        self.raw_rows = []

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        title = QLabel("Saved Measurements")
        title.setStyleSheet("font-size:16px; font-weight:bold;")

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

        # pilih satu baris penuh, bisa banyak baris (Ctrl / Shift)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        # double click to clear a cell
        self.table.cellDoubleClicked.connect(self.clear_cell)

        # style table and headers for esthetic look
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

        self.delete_btn = QPushButton("Hapus Data")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setObjectName("danger")

        self.delete_all_btn = QPushButton("Hapus Semua")
        self.delete_all_btn.clicked.connect(self.delete_all)
        self.delete_all_btn.setObjectName("danger")

        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_csv_btn.setObjectName("primary")

        self.export_xlsx_btn = QPushButton("Export Excel")
        self.export_xlsx_btn.clicked.connect(self.export_xlsx)
        self.export_xlsx_btn.setObjectName("primary")

        btn_row.addWidget(self.refresh_btn)
        btn_row.addWidget(self.delete_btn)
        btn_row.addWidget(self.delete_all_btn)
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

        # simpan data mentah supaya baris yang dipilih bisa dihapus dari database
        self.raw_rows = list(rows)

        self.table.setRowCount(0)

        for row_data in self.raw_rows:
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

    # ---------- Hapus data ----------

    def _open_connection(self):
        """Cari koneksi SQLite dari CalibrationDatabase (tanpa perlu ubah db.py)."""
        for value in vars(self.db).values():
            if isinstance(value, sqlite3.Connection):
                return value, False

        candidates = list(vars(self.db).values()) + list(vars(db_module).values())
        for value in candidates:
            if isinstance(value, (str, os.PathLike)):
                path = str(value)
                if path.lower().endswith((".db", ".sqlite", ".sqlite3")):
                    return sqlite3.connect(path), True

        raise RuntimeError("File database SQLite tidak ditemukan di database/db.py.")

    def _delete_from_db(self, rows=None):
        """Hapus baris yang dipilih (rows) atau semua baris (rows=None)."""
        # Pakai method milik db.py kalau sudah ada
        if rows is None and hasattr(self.db, "delete_all_measurements"):
            self.db.delete_all_measurements()
            return

        if rows is not None and hasattr(self.db, "delete_measurement"):
            for row in rows:
                self.db.delete_measurement(row)
            return

        # Fallback: deteksi tabel dan kolom waktu secara otomatis
        conn, opened_here = self._open_connection()

        try:
            tables = [
                r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            ]

            table = next((t for t in tables if "measurement" in t.lower()), None)
            if table is None:
                raise RuntimeError(
                    f"Tabel pengukuran tidak ditemukan. Tabel yang ada: {tables}"
                )

            if rows is None:
                conn.execute(f'DELETE FROM "{table}"')
            else:
                columns = [
                    r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')
                ]
                time_col = next(
                    (c for c in columns
                     if "time" in c.lower() or "date" in c.lower()),
                    None
                )
                if time_col is None:
                    raise RuntimeError(
                        f"Kolom waktu tidak ditemukan. Kolom yang ada: {columns}"
                    )

                for row in rows:
                    conn.execute(
                        f'DELETE FROM "{table}" WHERE rowid = ('
                        f'SELECT rowid FROM "{table}" WHERE "{time_col}" = ? LIMIT 1)',
                        (row[0],)
                    )

            conn.commit()
        finally:
            if opened_here:
                conn.close()

    def delete_selected(self):
        rows = sorted(
            {index.row() for index in self.table.selectedIndexes()},
            reverse=True
        )

        if not rows:
            QMessageBox.information(
                self,
                "Hapus Data",
                "Pilih dulu baris yang mau dihapus."
            )
            return

        answer = QMessageBox.question(
            self,
            "Hapus Data",
            f"Hapus {len(rows)} baris terpilih?"
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self._delete_from_db([self.raw_rows[r] for r in rows])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Gagal menghapus data: {e}")

        self.load_data()

    def delete_all(self):
        if not self.raw_rows:
            return

        answer = QMessageBox.question(
            self,
            "Hapus Semua",
            "Hapus SEMUA data pengukuran? Tindakan ini tidak bisa dibatalkan."
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self._delete_from_db(None)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Gagal menghapus data: {e}")

        self.load_data()

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
