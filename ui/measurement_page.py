from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTableWidget,
    QMessageBox,
    QGroupBox,
    QHeaderView,
    QAbstractItemView
)

from core.calibration_engine import CalibrationEngine
from core.constants import IEC_FREQUENCIES, TEST_LEVELS_DB
from ui.i18n import tr
from ui.style import s
from ui.style import (
    banner, legend_label, status_item, style_status_label, NumericItem, setup_table, info_icon, section_title,
    two_line_header
)
from ui.result_dialog import ResultDetailDialog, make_parameter_table, fill_parameter_table


def status_value_item(value, text, status):
    """Measured value, colored green/red by its own status."""
    item = status_item(status, text)
    item.sort_value = value
    item.setToolTip(status)
    return item


class MeasurementPage(QWidget):
    results_changed = pyqtSignal()
    go_to_calibration = pyqtSignal(int)

    SORT_KEYS = [
        lambda r: (r["frequency"], r["level_db"]),
        lambda r: (r["level_db"], r["frequency"]),
        lambda r: (r["overall_status"] != "FAIL", r["frequency"], r["level_db"]),
        lambda r: r["timestamp"],
    ]
    NEWEST_FIRST = 3

    def __init__(self, engine: CalibrationEngine, live_panel):
        super().__init__()

        self.engine = engine
        self.live = live_panel
        self.preview = None

        self.setup_ui()
        self.refresh_table()
        self.update_correction_info()

        self.live.reading_updated.connect(self.on_reading)
        self.live.live_state_changed.connect(self.on_live_state)

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel(tr("Measurement"))
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addWidget(info_icon(tr(
            "Set the audiometer to the chosen frequency and level, present the tone, "
            "check the result per parameter, then press Save Result.\n"
            "Saving the same frequency + level again replaces the old result."
        )))
        header.addStretch(1)
        header.addWidget(legend_label())
        root.addLayout(header)

        # Test point inputs
        group = QGroupBox(tr("Test point"))
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)

        self.frequency_combo = QComboBox()
        for f in IEC_FREQUENCIES:
            self.frequency_combo.addItem(f"{f} Hz", f)
        self.frequency_combo.setCurrentIndex(IEC_FREQUENCIES.index(1000))
        self.frequency_combo.currentIndexChanged.connect(self.on_point_changed)

        self.level_combo = QComboBox()
        for level in TEST_LEVELS_DB:
            self.level_combo.addItem(f"{level} dB", float(level))
        self.level_combo.currentIndexChanged.connect(self.on_point_changed)

        self.correction_value = QLabel("--")
        self.correction_value.setObjectName("reading")

        self.save_button = QPushButton(tr("Save Result"))
        self.save_button.setObjectName("primary")
        self.save_button.clicked.connect(self.save_result)

        grid.addWidget(QLabel(tr("Frequency")), 0, 0)
        grid.addWidget(QLabel(tr("Level")), 0, 1)
        grid.addWidget(QLabel(tr("Gain correction")), 0, 2)
        grid.addWidget(self.frequency_combo, 1, 0)
        grid.addWidget(self.level_combo, 1, 1)
        grid.addWidget(self.correction_value, 1, 2)
        grid.addWidget(self.save_button, 1, 3)
        for col in range(3):
            grid.setColumnStretch(col, 1)
        root.addWidget(group)

        self.point_banner = QLabel()
        self.point_banner.setVisible(False)
        root.addWidget(self.point_banner)

        # Live per-parameter result
        result_header = QHBoxLayout()
        result_header.addWidget(section_title(tr("Live result")))
        result_header.addStretch(1)
        self.overall_label = QLabel()
        style_status_label(self.overall_label, None)
        result_header.addWidget(self.overall_label)
        root.addLayout(result_header)

        self.parameter_table = make_parameter_table()
        fill_parameter_table(self.parameter_table, None)
        root.addWidget(self.parameter_table)

        # Saved results
        saved_header = QHBoxLayout()
        saved_header.addWidget(section_title(tr("Saved results")))
        saved_header.addStretch(1)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            tr("Frequency, then Level"),
            tr("Level, then Frequency"),
            tr("Failures first"),
            tr("Newest first"),
        ])
        self.sort_combo.currentIndexChanged.connect(self.refresh_table)
        saved_header.addWidget(QLabel(tr("Sort")))
        saved_header.addWidget(self.sort_combo)
        root.addLayout(saved_header)

        # Frequency | Level | THD, left to right; measured values carry their own color.
        columns = [
            tr("Frequency (Hz)"),
            tr("Level (dB)"),
            tr("Measured freq (Hz)"),
            tr("Corrected level (dB)"),
            "THD (%)",
            tr("Overall")
        ]
        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels([two_line_header(c) for c in columns])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self.show_details)
        setup_table(self.table)
        # Keep a few rows visible even on short screens; the tab scrolls instead.
        self.table.setMinimumHeight(s(230))
        root.addWidget(self.table, 1)

        table_buttons = QHBoxLayout()
        details = QPushButton(tr("Details"))
        details.clicked.connect(self.show_details)
        retake = QPushButton(tr("Retake"))
        retake.clicked.connect(self.retake_selected)
        delete = QPushButton(tr("Delete"))
        delete.setObjectName("danger")
        delete.clicked.connect(self.delete_selected)
        table_buttons.addWidget(details)
        table_buttons.addWidget(retake)
        table_buttons.addWidget(delete)
        table_buttons.addStretch(1)
        root.addLayout(table_buttons)

    # Test point

    def selected_point(self):
        return self.frequency_combo.currentData(), self.level_combo.currentData()

    def set_point(self, frequency, level_db):
        self.frequency_combo.setCurrentIndex(IEC_FREQUENCIES.index(frequency))
        level_index = self.level_combo.findData(float(level_db))
        if level_index >= 0:
            self.level_combo.setCurrentIndex(level_index)

    def on_point_changed(self):
        self.update_correction_info()
        self.update_preview()

    def update_correction_info(self):
        frequency, level_db = self.selected_point()
        correction = self.engine.get_correction(frequency)

        if correction is None:
            self.correction_value.setText("—")
            banner(self.point_banner, "error",
                   tr("{freq} Hz is not calibrated yet. Calibrate it first.").format(freq=frequency))
        else:
            self.correction_value.setText(f"{correction:+.2f} dB")
            if self.engine.has_result(frequency, level_db):
                banner(self.point_banner, "warn",
                       tr("Already saved. Saving again replaces it."))
            elif not self.live.is_live():
                banner(self.point_banner, "warn", tr("Live is off: press Start Live."))
            else:
                banner(self.point_banner, "warn", "")

    # Live preview

    def on_live_state(self, _):
        self.update_correction_info()
        if not self.live.is_live():
            self.preview = None
            fill_parameter_table(self.parameter_table, None)
            style_status_label(self.overall_label, None)

    def on_reading(self, _):
        self.update_preview()

    def update_preview(self):
        reading = self.live.reading()
        frequency, level_db = self.selected_point()
        correction = self.engine.get_correction(frequency)

        if reading is None or correction is None:
            self.preview = None
            fill_parameter_table(self.parameter_table, None)
            style_status_label(self.overall_label, None)
            return

        self.preview = self.engine.evaluate(frequency, level_db, reading, correction)
        fill_parameter_table(self.parameter_table, self.preview)
        style_status_label(self.overall_label, self.preview["overall_status"])

    # Actions

    def save_result(self):
        frequency, level_db = self.selected_point()

        if self.engine.get_correction(frequency) is None:
            answer = QMessageBox.question(
                self, tr("Not calibrated"),
                tr("{freq} Hz is not calibrated yet. Go to Calibration now?").format(freq=frequency)
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.go_to_calibration.emit(frequency)
            return

        if not self.live.is_live() or self.preview is None:
            QMessageBox.warning(self, tr("No live reading"),
                                tr("Start Live (left panel) and present the tone before saving."))
            return

        if not self.live.has_signal():
            QMessageBox.warning(self, tr("No signal"),
                                tr("No tone detected. Check the audiometer output and the microphone."))
            return

        if self.preview["frequency_status"] == "FAIL":
            answer = QMessageBox.question(
                self, tr("Frequency mismatch"),
                tr("Selected {selected} Hz, but the detected tone is {detected:.1f} Hz.\n\n"
                   "Continue anyway?").format(selected=frequency, detected=self.preview["measured_frequency"])
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        if self.engine.has_result(frequency, level_db):
            answer = QMessageBox.question(
                self, tr("Replace result"),
                tr("{freq} Hz / {level:.0f} dB is already saved. Replace it?").format(freq=frequency, level=level_db)
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.engine.save_result(dict(self.preview))
        self.refresh_table()
        self.select_next_missing()
        self.results_changed.emit()

    def select_next_missing(self):
        missing = self.engine.missing_points()
        if missing:
            self.set_point(*missing[0])
        else:
            self.update_correction_info()

    def selected_rows(self):
        rows = sorted({index.row() for index in self.table.selectionModel().selectedRows()})
        return [self.table.item(r, 0).data(Qt.ItemDataRole.UserRole) for r in rows]

    def show_details(self, *_):
        selected = self.selected_rows()
        if not selected:
            QMessageBox.information(self, tr("Select a row"), tr("Select a row in the table first."))
            return
        self.open_detail(selected[0])

    def open_detail(self, result):
        action = ResultDetailDialog(result, self).exec()
        if action == ResultDetailDialog.RETAKE:
            self.set_point(result["frequency"], result["level_db"])
        elif action == ResultDetailDialog.DELETE:
            self.delete_results([result])

    def retake_selected(self):
        selected = self.selected_rows()
        if not selected:
            QMessageBox.information(self, tr("Select a row"), tr("Select a row in the table first."))
            return
        self.set_point(selected[0]["frequency"], selected[0]["level_db"])

    def delete_selected(self):
        selected = self.selected_rows()
        if not selected:
            QMessageBox.information(self, tr("Select a row"), tr("Select a row in the table first."))
            return
        self.delete_results(selected)

    def delete_results(self, results):
        names = ", ".join(f"{r['frequency']} Hz/{r['level_db']:.0f} dB" for r in results[:6])
        if len(results) > 6:
            names += " …"

        answer = QMessageBox.question(
            self, tr("Delete results"),
            tr("Delete {n} result(s)?").format(n=len(results)) + "\n" + names
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        for r in results:
            self.engine.delete_result(r["frequency"], r["level_db"])

        self.refresh_table()
        self.update_correction_info()
        self.results_changed.emit()

    def refresh_table(self):
        index = self.sort_combo.currentIndex()
        results = sorted(self.engine.get_results(), key=self.SORT_KEYS[index],
                         reverse=index == self.NEWEST_FIRST)

        self.table.setRowCount(0)
        for r in results:
            row = self.table.rowCount()
            self.table.insertRow(row)

            first = NumericItem(r["frequency"], str(r["frequency"]))
            first.setData(Qt.ItemDataRole.UserRole, r)
            first.setToolTip(tr("Saved at {time}").format(time=r["timestamp"]))
            cells = [
                first,
                NumericItem(r["level_db"], f"{r['level_db']:.0f}"),
                status_value_item(r["measured_frequency"], f"{r['measured_frequency']:.1f}", r["frequency_status"]),
                status_value_item(r["calibrated_db"], f"{r['calibrated_db']:.1f}", r["level_status"]),
                status_value_item(r["thd"], f"{r['thd']:.2f}", r["thd_status"]),
                status_item(r["overall_status"])
            ]
            for col, item in enumerate(cells):
                self.table.setItem(row, col, item)
