from PyQt6.QtCore import QDate, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QDateEdit,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QFileDialog,
    QMessageBox,
    QHeaderView,
    QAbstractItemView
)

from core.calibration_engine import CalibrationEngine
from core.constants import IEC_FREQUENCIES, TEST_LEVELS_DB
from reports.report_data import collect_report_data, report_warnings, report_file_name
from reports.pdf_report import PDFReport
from reports.csv_report import export_csv, export_xlsx
from ui.i18n import tr
from ui.style import banner, status_item, style_status_label, setup_table, info_icon, section_title
from ui.result_dialog import ResultDetailDialog


class ReportPage(QWidget):
    retake_requested = pyqtSignal(int, float)
    data_cleared = pyqtSignal()

    def __init__(self, engine: CalibrationEngine):
        super().__init__()

        self.engine = engine

        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel(tr("Report"))
        title.setObjectName("pageTitle")
        root.addWidget(title)

        self.device_label = QLabel()
        self.device_label.setObjectName("caption")
        self.device_label.setWordWrap(True)
        root.addWidget(self.device_label)

        # Summary chips
        chips = QHBoxLayout()
        chips.setSpacing(8)
        self.chips = {key: QLabel() for key in ["measured", "passed", "failed", "missing", "overall"]}
        for label in self.chips.values():
            chips.addWidget(label)
        chips.addStretch(1)
        root.addLayout(chips)

        self.warning_banner = QLabel()
        self.warning_banner.setVisible(False)
        root.addWidget(self.warning_banner)

        grid_header = QHBoxLayout()
        grid_header.addWidget(section_title(tr("Data completeness")))
        grid_header.addWidget(info_icon(tr(
            "Each cell is one test point (frequency × level).\n"
            "— = not measured yet. Double-click a cell to see details, retake or delete it."
        )))
        grid_header.addStretch(1)
        root.addLayout(grid_header)

        self.grid = QTableWidget(len(IEC_FREQUENCIES), len(TEST_LEVELS_DB))
        self.grid.setVerticalHeaderLabels([f"{f} Hz" for f in IEC_FREQUENCIES])
        self.grid.setHorizontalHeaderLabels([f"{l} dB" for l in TEST_LEVELS_DB])
        self.grid.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.grid.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.grid.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.grid.cellDoubleClicked.connect(self.open_cell)
        setup_table(self.grid)
        root.addWidget(self.grid, 1)

        buttons = QHBoxLayout()
        pdf_button = QPushButton(tr("Export PDF"))
        pdf_button.setObjectName("primary")
        pdf_button.clicked.connect(self.export_pdf)
        csv_button = QPushButton(tr("Export CSV"))
        csv_button.setObjectName("primary")
        csv_button.clicked.connect(self.export_csv)
        xlsx_button = QPushButton(tr("Export Excel"))
        xlsx_button.clicked.connect(self.export_xlsx)
        clear = QPushButton(tr("New Calibration"))
        clear.setObjectName("danger")
        clear.setToolTip(tr("Delete the calibration and all measurement results"))
        clear.clicked.connect(self.clear_all)

        self.report_date = QDateEdit()
        self.report_date.setCalendarPopup(True)
        self.report_date.setDisplayFormat("yyyy-MM-dd")
        self.report_date.setToolTip(tr("Date printed at the signature and used in the file name"))
        self.report_date.dateChanged.connect(self.on_report_date_changed)

        buttons.addWidget(QLabel(tr("Report date")))
        buttons.addWidget(self.report_date)
        buttons.addSpacing(12)
        buttons.addWidget(pdf_button)
        buttons.addWidget(csv_button)
        buttons.addWidget(xlsx_button)
        buttons.addStretch(1)
        buttons.addWidget(clear)
        root.addLayout(buttons)

    def on_report_date_changed(self, value):
        self.engine.database.save_device_info({"report_date": value.toString("yyyy-MM-dd")})

    def refresh(self):
        data = collect_report_data(self.engine)
        info = data["device_info"]

        self.report_date.blockSignals(True)
        self.report_date.setDate(QDate.fromString(data["report_date"], "yyyy-MM-dd"))
        self.report_date.blockSignals(False)

        device = " ".join(v for v in [info["brand"], info["model"]] if v) or "—"
        self.device_label.setText(
            f"{device}   ·   S/N {info['serial_number'] or '—'}   ·   "
            f"{info['technician'] or '—'}   ·   {info['calibration_date'] or '—'}"
        )

        s = data["summary"]
        style_status_label(self.chips["measured"], None, f"{tr('Measured')} {s['measured']}/{s['planned']}")
        style_status_label(self.chips["passed"], "PASS", f"PASS {s['passed']}")
        style_status_label(self.chips["failed"], "FAIL" if s["failed"] else None, f"FAIL {s['failed']}")
        style_status_label(self.chips["missing"], "FAIL" if s["missing"] else None,
                           f"{tr('Missing')} {s['missing']}")
        style_status_label(self.chips["overall"], s["overall"], f"{tr('Overall')}: {s['overall']}")

        warnings = report_warnings(data, tr)
        if warnings:
            banner(self.warning_banner, "warn", "⚠ " + "<br>⚠ ".join(warnings))
        else:
            banner(self.warning_banner, "ok", tr("Data complete. Ready to export."))

        coverage = data["coverage"]
        for row, f in enumerate(IEC_FREQUENCIES):
            for col, level in enumerate(TEST_LEVELS_DB):
                result = coverage[(f, float(level))]
                if result is None:
                    self.grid.setItem(row, col, status_item(None, "—"))
                else:
                    item = status_item(result["overall_status"])
                    item.setToolTip(f"{result['calibrated_db']:.1f} dB")
                    self.grid.setItem(row, col, item)

    def open_cell(self, row, col):
        frequency = IEC_FREQUENCIES[row]
        level_db = float(TEST_LEVELS_DB[col])
        result = self.engine.coverage()[(frequency, level_db)]

        if result is None:
            answer = QMessageBox.question(
                self, tr("Not measured"),
                tr("{freq} Hz / {level:.0f} dB has no result yet. Measure it now?").format(
                    freq=frequency, level=level_db)
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.retake_requested.emit(frequency, level_db)
            return

        action = ResultDetailDialog(result, self).exec()
        if action == ResultDetailDialog.RETAKE:
            self.retake_requested.emit(frequency, level_db)
        elif action == ResultDetailDialog.DELETE:
            answer = QMessageBox.question(
                self, tr("Delete results"),
                tr("Delete {n} result(s)?").format(n=1) + f"\n{frequency} Hz/{level_db:.0f} dB"
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.engine.delete_result(frequency, level_db)
                self.refresh()
                self.data_cleared.emit()

    # Export

    def confirm_export(self, data):
        warnings = report_warnings(data, tr)
        if not warnings:
            return True

        answer = QMessageBox.question(
            self, tr("Report is incomplete"),
            "• " + "\n• ".join(warnings) + "\n\n" + tr("Export anyway? The issues will be listed in the report.")
        )
        return answer == QMessageBox.StandardButton.Yes

    def export_file(self, default_name, file_filter, writer):
        data = collect_report_data(self.engine)
        if not data["results"] and data["reference_point"] is None:
            QMessageBox.warning(self, tr("Nothing to export"), tr("There is no calibration or measurement data yet."))
            return

        if not self.confirm_export(data):
            return

        path, _ = QFileDialog.getSaveFileName(self, tr("Save report"), default_name, file_filter)
        if not path:
            return

        try:
            writer(path, data)
        except Exception as e:
            QMessageBox.warning(self, tr("Export failed"), tr("Could not write the file:") + f"\n{e}")
            return

        QMessageBox.information(self, tr("Exported"), tr("Saved to:") + f"\n{path}")

    def default_name(self, ext):
        return report_file_name(self.engine, ext)

    def export_pdf(self):
        self.export_file(self.default_name(".pdf"), "PDF (*.pdf)", PDFReport.export_calibration_report)

    def export_csv(self):
        self.export_file(self.default_name(".csv"), "CSV (*.csv)", export_csv)

    def export_xlsx(self):
        self.export_file(self.default_name(".xlsx"), "Excel (*.xlsx)", export_xlsx)

    def clear_all(self):
        answer = QMessageBox.warning(
            self, tr("New Calibration"),
            tr("This deletes the calibration and ALL measurement results.\n"
               "Device information and microphone response corrections are kept.\n"
               "Export the report or save the session first if you need it.\n\nContinue?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.engine.clear_all()
        self.refresh()
        self.data_cleared.emit()
