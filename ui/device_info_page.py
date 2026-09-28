from PyQt6.QtCore import QDate, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QDateEdit,
    QPlainTextEdit,
    QPushButton,
    QGroupBox
)

from reports.report_data import missing_device_fields
from ui.i18n import tr
from ui.style import banner, s


class DeviceInfoPage(QWidget):
    info_saved = pyqtSignal()

    def __init__(self, database):
        super().__init__()

        self.db = database

        self.setup_ui()
        self.load()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel(tr("Device Information"))
        title.setObjectName("pageTitle")
        root.addWidget(title)

        group = QGroupBox(tr("Audiometer under test"))
        group.setMaximumWidth(s(820))
        form = QFormLayout(group)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)

        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("Interacoustics")
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("AD629")
        self.serial_input = QLineEdit()

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setDate(QDate.currentDate())

        self.technician_input = QLineEdit()

        self.notes_input = QPlainTextEdit()
        self.notes_input.setPlaceholderText(tr("Room conditions, coupler / transducer, remarks"))
        self.notes_input.setFixedHeight(100)

        form.addRow(tr("Brand") + " *", self.brand_input)
        form.addRow(tr("Model / Type") + " *", self.model_input)
        form.addRow(tr("Serial number") + " *", self.serial_input)
        form.addRow(tr("Calibration date"), self.date_input)
        form.addRow(tr("Technician") + " *", self.technician_input)
        form.addRow(tr("Notes"), self.notes_input)

        root.addWidget(group)

        required = QLabel("* " + tr("required for the report"))
        required.setObjectName("caption")
        root.addWidget(required)

        self.status_banner = QLabel()
        self.status_banner.setVisible(False)
        self.status_banner.setMaximumWidth(s(820))
        root.addWidget(self.status_banner)

        button_row = QHBoxLayout()
        self.save_button = QPushButton(tr("Save"))
        self.save_button.setObjectName("primary")
        self.save_button.clicked.connect(self.save)
        button_row.addWidget(self.save_button)
        button_row.addStretch(1)
        root.addLayout(button_row)

        root.addStretch(1)

    def values(self):
        return {
            "brand": self.brand_input.text().strip(),
            "model": self.model_input.text().strip(),
            "serial_number": self.serial_input.text().strip(),
            "calibration_date": self.date_input.date().toString("yyyy-MM-dd"),
            "technician": self.technician_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip()
        }

    def load(self):
        info = self.db.get_device_info()

        self.brand_input.setText(info["brand"])
        self.model_input.setText(info["model"])
        self.serial_input.setText(info["serial_number"])
        self.technician_input.setText(info["technician"])
        self.notes_input.setPlainText(info["notes"])

        if info["calibration_date"]:
            self.date_input.setDate(QDate.fromString(info["calibration_date"], "yyyy-MM-dd"))

    def save(self):
        info = self.values()
        self.db.save_device_info(info)

        missing = missing_device_fields(info)
        if missing:
            banner(self.status_banner, "warn",
                   tr("Saved, but still missing: {fields}").format(fields=", ".join(tr(m) for m in missing)))
        else:
            banner(self.status_banner, "ok", tr("Device information saved."))

        self.info_saved.emit()
