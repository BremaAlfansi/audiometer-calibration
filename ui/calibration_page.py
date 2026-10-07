from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QGroupBox,
    QHeaderView,
    QAbstractItemView
)

from core.calibration_engine import CalibrationEngine, gain_correction
from core.constants import IEC_FREQUENCIES, REFERENCE_FREQUENCY, CALIBRATOR_LEVELS_DB, LEVEL_RESOLUTION_DB
from ui.i18n import tr
from ui.style import (
    banner, legend_label, status_item, NumericItem, db_validator, setup_table, info_icon, section_title,
    fit_table_height, two_line_header, style_status_label, INPUT_BORDER, READING_FG
)

RESPONSE_COLUMN = 1


class CalibrationPage(QWidget):
    calibration_changed = pyqtSignal()

    def __init__(self, engine: CalibrationEngine, live_panel):
        super().__init__()

        self.engine = engine
        self.live = live_panel
        self.filling_table = False

        self.setup_ui()
        self.refresh()

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
            "1. Put the acoustic calibrator on the microphone (1 kHz).\n"
            "2. Enter the calibrator level (usually 94 dB or 114 dB) and press Calibrate.\n"
            "3. If the microphone response is not flat, enter its correction per frequency "
            "in the Calibration points table."
        )))
        header.addStretch(1)
        header.addWidget(legend_label())
        root.addLayout(header)

        # Reference calibration at 1 kHz: Frequency | Calibrator | Measured | Gain correction
        group = QGroupBox(tr("Reference calibration"))
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)

        frequency_value = QLabel(f"{REFERENCE_FREQUENCY} Hz")
        frequency_value.setObjectName("reading")
        frequency_value.setToolTip(tr("Fixed: acoustic calibrators work at 1 kHz."))

        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText(tr("e.g. 94 or 114"))
        self.reference_input.setValidator(db_validator())
        self.reference_input.textChanged.connect(self.update_preview)

        presets = QHBoxLayout()
        presets.setSpacing(6)
        for level in CALIBRATOR_LEVELS_DB:
            button = QPushButton(f"{level:g} dB")
            button.setToolTip(tr("Use {level:g} dB").format(level=level))
            button.clicked.connect(lambda _, v=level: self.reference_input.setText(f"{v:g}"))
            presets.addWidget(button)
        presets.addStretch(1)

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
            "Gain correction = Calibrator level − Measured.\n"
            "PASS when Measured + Gain correction equals the calibrator level ({res} dB resolution)."
        ).format(res=LEVEL_RESOLUTION_DB)))
        correction_header.addStretch(1)

        grid.addWidget(QLabel(tr("Frequency")), 0, 0)
        grid.addWidget(QLabel(tr("Calibrator level (dB)")), 0, 1)
        grid.addWidget(QLabel(tr("Measured (dB)")), 0, 2)
        grid.addLayout(correction_header, 0, 3)

        grid.addWidget(frequency_value, 1, 0)
        grid.addWidget(self.reference_input, 1, 1)
        grid.addWidget(self.measured_input, 1, 2)
        grid.addWidget(self.correction_value, 1, 3)

        self.calibrate_button = QPushButton(tr("Calibrate"))
        self.calibrate_button.setObjectName("primary")
        self.calibrate_button.clicked.connect(self.calibrate)
        grid.addWidget(self.calibrate_button, 2, 0)
        grid.addLayout(presets, 2, 1)
        grid.addWidget(self.manual_check, 2, 2)

        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 1)
        root.addWidget(group)

        self.form_banner = QLabel()
        self.form_banner.setVisible(False)
        root.addWidget(self.form_banner)

        # Current calibration result
        status_row = QHBoxLayout()
        self.status_chip = QLabel()
        self.status_text = QLabel()
        self.status_text.setObjectName("caption")
        self.delete_button = QPushButton(tr("Delete"))
        self.delete_button.setObjectName("danger")
        self.delete_button.clicked.connect(self.delete_calibration)
        status_row.addWidget(self.status_chip)
        status_row.addWidget(self.status_text, 1)
        status_row.addWidget(self.delete_button)
        root.addLayout(status_row)

        # Calibration points: microphone response correction per frequency (editable)
        points_header = QHBoxLayout()
        points_header.addWidget(section_title(tr("Calibration points")))
        points_header.addWidget(info_icon(tr(
            "Microphone frequency-response correction, in dB relative to 1 kHz.\n"
            "Take it from the microphone's calibration certificate. Leave 0.00 if the response is flat.\n"
            "Example: the microphone reads 1.5 dB too low at 8000 Hz → enter +1.5.\n"
            "Total correction = Gain correction + Response correction."
        )))
        points_header.addStretch(1)
        hint = QLabel(tr("Double-click a value to edit it."))
        hint.setObjectName("caption")
        points_header.addWidget(hint)
        root.addLayout(points_header)

        columns = [tr("Frequency (Hz)"), tr("Response correction (dB)"), tr("Total correction (dB)")]
        self.table = QTableWidget(len(IEC_FREQUENCIES), len(columns))
        self.table.setHorizontalHeaderLabels([two_line_header(c) for c in columns])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.AnyKeyPressed
        )
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemChanged.connect(self.on_response_edited)
        setup_table(self.table)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        root.addWidget(self.table)

        root.addStretch(1)

    def showEvent(self, event):
        # The two-line header only has its real height once the page is on screen.
        super().showEvent(event)
        fit_table_height(self.table)

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

    @staticmethod
    def parse(text):
        try:
            return float(text.strip().replace(",", "."))
        except ValueError:
            return None

    def update_preview(self):
        measured = self.parse(self.measured_input.text())
        reference = self.parse(self.reference_input.text())

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
        reference = self.parse(self.reference_input.text())
        measured = self.parse(self.measured_input.text())

        if reference is None:
            QMessageBox.warning(self, tr("Calibrator level missing"),
                                tr("Enter the calibrator level, e.g. 94 dB or 114 dB."))
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

            if not self.engine.frequency_ok(REFERENCE_FREQUENCY, reading["frequency"]):
                answer = QMessageBox.question(
                    self, tr("Frequency mismatch"),
                    tr("Selected {selected} Hz, but the detected tone is {detected:.1f} Hz.\n\n"
                       "Continue anyway?").format(selected=REFERENCE_FREQUENCY, detected=reading["frequency"])
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return

        if self.engine.is_calibrated():
            answer = QMessageBox.question(
                self, tr("Replace calibration"),
                tr("{freq} Hz is already calibrated. Replace it?").format(freq=REFERENCE_FREQUENCY)
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.engine.calibrate(measured, reference)
        if self.manual_check.isChecked():
            self.measured_input.clear()

        self.refresh()
        self.calibration_changed.emit()

    def delete_calibration(self):
        if not self.engine.is_calibrated():
            return

        answer = QMessageBox.question(
            self, tr("Delete calibration"),
            tr("Delete the calibration for {freq} Hz?").format(freq=REFERENCE_FREQUENCY)
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.engine.delete_reference_point()
        self.refresh()
        self.calibration_changed.emit()

    def on_response_edited(self, item):
        if self.filling_table or item.column() != RESPONSE_COLUMN:
            return

        frequency = IEC_FREQUENCIES[item.row()]
        value = self.parse(item.text())
        if value is None or abs(value) > 30:
            QMessageBox.warning(self, tr("Invalid value"),
                                tr("Enter a number in dB between −30 and +30, e.g. 1.5 or -0.8."))
        else:
            self.engine.set_response_correction(frequency, value)
            self.calibration_changed.emit()

        self.refresh()

    # Display

    def refresh(self):
        point = self.engine.get_reference_point()

        if point is None:
            style_status_label(self.status_chip, None, tr("NOT CALIBRATED"))
            self.status_text.setText(tr("Not calibrated yet. Calibrate at 1 kHz with the calibrator."))
            self.delete_button.setVisible(False)
        else:
            style_status_label(self.status_chip, point["status"])
            self.status_text.setText(tr(
                "{ref:.2f} dB calibrator · measured {meas:.2f} dB · gain correction {gain:+.2f} dB · {time}"
            ).format(ref=point["reference_db"], meas=point["measured_db"],
                     gain=point["gain_correction_db"], time=point["timestamp"]))
            self.delete_button.setVisible(True)

        self.fill_table(point)

    def fill_table(self, point):
        self.filling_table = True
        corrections = self.engine.get_response_corrections()

        for row, frequency in enumerate(IEC_FREQUENCIES):
            freq_item = NumericItem(frequency, str(frequency))
            freq_item.setFlags(freq_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, freq_item)

            correction = corrections[frequency]
            if frequency == REFERENCE_FREQUENCY:
                response = QTableWidgetItem("0.00  (" + tr("reference") + ")")
                response.setFlags(response.flags() & ~Qt.ItemFlag.ItemIsEditable)
                response.setForeground(QColor(READING_FG))
            else:
                response = QTableWidgetItem(f"{correction:+.2f}")
                response.setForeground(QColor(INPUT_BORDER))
                response.setToolTip(tr("Double-click to edit"))
            response.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, RESPONSE_COLUMN, response)

            if point is None:
                total = status_item(None, "—")
            else:
                total = NumericItem(None, f"{point['gain_correction_db'] + correction:+.2f}")
                total.setForeground(QColor(READING_FG))
            total.setFlags(total.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, total)

        fit_table_height(self.table)
        self.filling_table = False
