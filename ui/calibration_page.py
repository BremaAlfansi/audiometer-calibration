from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QTableWidget,
    QMessageBox,
    QGroupBox,
    QHeaderView,
    QAbstractItemView
)

from core.calibration_engine import CalibrationEngine, gain_correction
from core.constants import IEC_FREQUENCIES, LEVEL_RESOLUTION_DB
from ui.i18n import tr
from ui.style import (
    banner, legend_label, status_item, NumericItem, db_validator, setup_table, info_icon, section_title,
    fit_table_height, two_line_header
)


class CalibrationPage(QWidget):
    calibration_changed = pyqtSignal()

    def __init__(self, engine: CalibrationEngine, live_panel):
        super().__init__()

        self.engine = engine
        self.live = live_panel

        self.setup_ui()
        self.refresh_table()

        self.live.reading_updated.connect(self.on_reading)
        self.live.live_state_changed.connect(lambda _: self.update_preview())

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel(tr("Calibration"))
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addWidget(info_icon(tr(
            "For each frequency: present a tone on the audiometer, read the true level on the "
            "reference sound level meter, type it as Reference, then press Calibrate."
        )))
        header.addStretch(1)
        header.addWidget(legend_label())
        root.addLayout(header)

        # Input form: Frequency | Reference | Measured | Gain correction, left to right.
        group = QGroupBox(tr("Calibrate one frequency"))
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)

        self.frequency_combo = QComboBox()
        for f in IEC_FREQUENCIES:
            self.frequency_combo.addItem(f"{f} Hz", f)
        self.frequency_combo.setCurrentIndex(IEC_FREQUENCIES.index(1000))
        self.frequency_combo.currentIndexChanged.connect(self.update_preview)

        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText(tr("from reference meter"))
        self.reference_input.setValidator(db_validator())
        self.reference_input.textChanged.connect(self.update_preview)

        self.measured_input = QLineEdit()
        self.measured_input.setReadOnly(True)
        self.measured_input.setPlaceholderText(tr("start live signal"))
        self.measured_input.setValidator(db_validator())
        self.measured_input.textChanged.connect(self.update_preview)

        self.manual_check = QCheckBox(tr("Enter manually"))
        self.manual_check.toggled.connect(self.on_manual_toggled)

        self.correction_value = QLabel("--")
        self.correction_value.setObjectName("reading")

        correction_header = QHBoxLayout()
        correction_header.addWidget(QLabel(tr("Gain correction (dB)")))
        correction_header.addWidget(info_icon(tr(
            "Gain correction = Reference − Measured.\n"
            "It is added to every later reading at this frequency:\n"
            "Corrected = Measured + Gain correction.\n"
            "PASS when Corrected equals Reference ({res} dB resolution)."
        ).format(res=LEVEL_RESOLUTION_DB)))
        correction_header.addStretch(1)

        grid.addWidget(QLabel(tr("Frequency")), 0, 0)
        grid.addWidget(QLabel(tr("Reference (dB)")), 0, 1)
        grid.addWidget(QLabel(tr("Measured (dB)")), 0, 2)
        grid.addLayout(correction_header, 0, 3)

        grid.addWidget(self.frequency_combo, 1, 0)
        grid.addWidget(self.reference_input, 1, 1)
        grid.addWidget(self.measured_input, 1, 2)
        grid.addWidget(self.correction_value, 1, 3)

        self.calibrate_button = QPushButton(tr("Calibrate"))
        self.calibrate_button.setObjectName("primary")
        self.calibrate_button.clicked.connect(self.calibrate)
        grid.addWidget(self.calibrate_button, 2, 0)
        grid.addWidget(self.manual_check, 2, 2)

        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 1)
        root.addWidget(group)

        self.form_banner = QLabel()
        self.form_banner.setVisible(False)
        root.addWidget(self.form_banner)

        # Calibration table: one row per frequency, including missing ones.
        root.addWidget(section_title(tr("Calibration points")))

        self.coverage_banner = QLabel()
        self.coverage_banner.setVisible(False)
        root.addWidget(self.coverage_banner)

        columns = [
            tr("Frequency (Hz)"),
            tr("Measured (dB)"),
            tr("Reference (dB)"),
            tr("Gain Correction (dB)"),
            tr("Corrected (dB)"),
            tr("Status")
        ]
        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels([two_line_header(c) for c in columns])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self.recalibrate_selected)
        setup_table(self.table)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        root.addWidget(self.table)

        table_buttons = QHBoxLayout()
        self.recalibrate_button = QPushButton(tr("Recalibrate"))
        self.recalibrate_button.clicked.connect(self.recalibrate_selected)
        self.delete_button = QPushButton(tr("Delete"))
        self.delete_button.setObjectName("danger")
        self.delete_button.clicked.connect(self.delete_selected)
        table_buttons.addWidget(self.recalibrate_button)
        table_buttons.addWidget(self.delete_button)
        table_buttons.addStretch(1)
        root.addLayout(table_buttons)
        root.addStretch(1)

    # Live / preview

    def on_reading(self, reading):
        if not self.manual_check.isChecked():
            self.measured_input.setText(f"{reading['db']:.2f}")

    def on_manual_toggled(self, manual):
        self.measured_input.setReadOnly(not manual)
        self.measured_input.clear()
        self.measured_input.setPlaceholderText(tr("type measured dB") if manual else tr("start live signal"))
        # re-polish so the :read-only style (reading vs input look) updates
        self.measured_input.style().unpolish(self.measured_input)
        self.measured_input.style().polish(self.measured_input)
        self.update_preview()

    def selected_frequency(self):
        return self.frequency_combo.currentData()

    def parse(self, line_edit):
        try:
            return float(line_edit.text().replace(",", "."))
        except ValueError:
            return None

    def update_preview(self):
        measured = self.parse(self.measured_input)
        reference = self.parse(self.reference_input)

        if measured is None or reference is None:
            self.correction_value.setText("--")
        else:
            self.correction_value.setText(f"{gain_correction(measured, reference):+.2f}")

        if not self.manual_check.isChecked() and not self.live.is_live():
            banner(self.form_banner, "warn", tr("Live is off: press Start Live, or tick “Enter manually”."))
        else:
            banner(self.form_banner, "warn", "")

    # Actions

    def calibrate(self):
        frequency = self.selected_frequency()
        reference = self.parse(self.reference_input)
        measured = self.parse(self.measured_input)

        if reference is None:
            QMessageBox.warning(self, tr("Reference missing"),
                                tr("Enter the level read from the reference sound level meter."))
            self.reference_input.setFocus()
            return

        if measured is None:
            QMessageBox.warning(self, tr("Measured level missing"),
                                tr("Start Live (left panel), or tick “Enter manually” and type it."))
            return

        if not self.manual_check.isChecked():
            reading = self.live.reading()
            if reading is None or not self.live.has_signal():
                QMessageBox.warning(self, tr("No signal"),
                                    tr("No tone detected. Check the audiometer output and the microphone."))
                return

            if not self.engine.frequency_ok(frequency, reading["frequency"]):
                answer = QMessageBox.question(
                    self, tr("Frequency mismatch"),
                    tr("Selected {selected} Hz, but the detected tone is {detected:.1f} Hz.\n\n"
                       "Continue anyway?").format(selected=frequency, detected=reading["frequency"])
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return

        if frequency in self.engine.get_calibration_points():
            answer = QMessageBox.question(
                self, tr("Replace calibration"),
                tr("{freq} Hz is already calibrated. Replace it?").format(freq=frequency)
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.engine.calibrate(frequency, measured, reference)
        self.reference_input.clear()
        if self.manual_check.isChecked():
            self.measured_input.clear()

        self.refresh_table()
        self.select_next_uncalibrated()
        self.calibration_changed.emit()

    def select_next_uncalibrated(self):
        remaining = self.engine.uncalibrated_frequencies()
        if remaining:
            self.frequency_combo.setCurrentIndex(IEC_FREQUENCIES.index(remaining[0]))

    def selected_table_frequency(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).sort_value

    def recalibrate_selected(self, *_):
        frequency = self.selected_table_frequency()
        if frequency is None:
            QMessageBox.information(self, tr("Select a row"), tr("Select a row in the table first."))
            return
        self.frequency_combo.setCurrentIndex(IEC_FREQUENCIES.index(frequency))
        self.reference_input.setFocus()

    def delete_selected(self):
        frequency = self.selected_table_frequency()
        if frequency is None:
            QMessageBox.information(self, tr("Select a row"), tr("Select a row in the table first."))
            return

        if frequency not in self.engine.get_calibration_points():
            return

        answer = QMessageBox.question(
            self, tr("Delete calibration"),
            tr("Delete the calibration for {freq} Hz?").format(freq=frequency)
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.engine.delete_calibration_point(frequency)
        self.refresh_table()
        self.calibration_changed.emit()

    def refresh_table(self):
        points = self.engine.get_calibration_points()

        self.table.setRowCount(0)
        for frequency in IEC_FREQUENCIES:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, NumericItem(frequency, str(frequency)))

            point = points.get(frequency)
            if point is None:
                for col in range(1, 5):
                    self.table.setItem(row, col, status_item(None, "—"))
                self.table.setItem(row, 5, status_item(None, tr("NOT CALIBRATED")))
                continue

            self.table.setItem(row, 1, NumericItem(point["measured_db"], f"{point['measured_db']:.2f}"))
            self.table.setItem(row, 2, NumericItem(point["reference_db"], f"{point['reference_db']:.2f}"))
            self.table.setItem(row, 3, NumericItem(point["gain_correction_db"],
                                                   f"{point['gain_correction_db']:+.2f}"))
            self.table.setItem(row, 4, NumericItem(point["corrected_db"], f"{point['corrected_db']:.2f}"))
            status = status_item(point["status"])
            status.setToolTip(tr("Calibrated at {time}").format(time=point["timestamp"]))
            self.table.setItem(row, 5, status)

        fit_table_height(self.table)

        missing = [f for f in IEC_FREQUENCIES if f not in points]
        if missing:
            banner(self.coverage_banner, "warn",
                   tr("Not calibrated yet: {list}").format(list=", ".join(f"{f} Hz" for f in missing)))
        else:
            banner(self.coverage_banner, "ok", tr("All frequencies calibrated."))
