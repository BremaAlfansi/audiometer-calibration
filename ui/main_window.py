from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QMainWindow,
    QScrollArea,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QTabWidget,
    QFrame,
    QComboBox
)

from core.calibration_engine import CalibrationEngine
from core.constants import APP_NAME, ORG_NAME, IEC_FREQUENCIES
from reports.report_data import missing_device_fields
from ui.i18n import tr, LANGUAGES, get_language, set_language
from ui.style import app_stylesheet
from ui.widgets.live_panel import LivePanel
from ui.device_info_page import DeviceInfoPage
from ui.calibration_page import CalibrationPage
from ui.measurement_page import MeasurementPage
from ui.report_page import ReportPage


def scrollable(page):
    """Wrap a tab page so short screens scroll it instead of clipping the window."""
    area = QScrollArea()
    area.setWidget(page)
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    return area


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"{APP_NAME} - {ORG_NAME}")
        self.resize(1400, 880)
        self.setStyleSheet(app_stylesheet())

        self.engine = CalibrationEngine()
        self.live_panel = None

        self.build()

    def build(self, tab_index=0):
        """(Re)create every widget, e.g. after the language changes."""
        if self.live_panel is not None:
            self.live_panel.timer.stop()

        self.setup_ui()
        self.connect_signals()
        self.tabs.setCurrentIndex(tab_index)
        self.update_progress()

    def setup_ui(self):
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left: live readings, visible from every step.
        self.live_panel = LivePanel()
        root.addWidget(self.live_panel)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setStyleSheet("color: rgba(255,255,255,0.12);")
        root.addWidget(divider)

        # Right: workflow progress + language + one tab per step.
        right = QVBoxLayout()
        right.setContentsMargins(10, 10, 10, 10)
        right.setSpacing(8)

        top_row = QHBoxLayout()
        self.progress_label = QLabel()
        self.progress_label.setObjectName("caption")
        self.language_combo = QComboBox()
        for code, name in LANGUAGES.items():
            self.language_combo.addItem(name, code)
        self.language_combo.setCurrentIndex(list(LANGUAGES).index(get_language()))
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        top_row.addWidget(self.progress_label)
        top_row.addStretch(1)
        top_row.addWidget(QLabel("🌐"))
        top_row.addWidget(self.language_combo)
        right.addLayout(top_row)

        self.tabs = QTabWidget()
        self.device_page = DeviceInfoPage(self.engine.database)
        self.calibration_page = CalibrationPage(self.engine, self.live_panel)
        self.measurement_page = MeasurementPage(self.engine, self.live_panel)
        self.report_page = ReportPage(self.engine)

        self.pages = [self.device_page, self.calibration_page, self.measurement_page, self.report_page]
        titles = [tr("Device Info"), tr("Calibration"), tr("Measurement"), tr("Report")]
        for number, (page, title) in enumerate(zip(self.pages, titles), start=1):
            self.tabs.addTab(scrollable(page), f"{number}  {title}")
        right.addWidget(self.tabs, 1)

        root.addLayout(right, 1)
        self.setCentralWidget(central)  # deletes the previous central widget, if any

    def connect_signals(self):
        self.device_page.info_saved.connect(self.on_data_changed)

        self.calibration_page.calibration_changed.connect(self.measurement_page.update_correction_info)
        self.calibration_page.calibration_changed.connect(self.on_data_changed)

        self.measurement_page.results_changed.connect(self.on_data_changed)
        self.measurement_page.go_to_calibration.connect(self.show_calibration)

        self.report_page.retake_requested.connect(self.show_measurement)
        self.report_page.data_cleared.connect(self.on_report_cleared)

        self.tabs.currentChanged.connect(self.on_tab_changed)

    def on_language_changed(self):
        set_language(self.language_combo.currentData())
        # Defer: the combo emitting this signal is destroyed by the rebuild.
        tab_index = self.tabs.currentIndex()
        QTimer.singleShot(0, lambda: self.build(tab_index))

    def on_data_changed(self):
        self.report_page.refresh()
        self.update_progress()

    def on_report_cleared(self):
        self.calibration_page.refresh_table()
        self.measurement_page.refresh_table()
        self.measurement_page.update_correction_info()
        self.update_progress()

    def show_page(self, page):
        self.tabs.setCurrentIndex(self.pages.index(page))

    def on_tab_changed(self, index):
        if self.pages[index] is self.report_page:
            self.report_page.refresh()

    def show_calibration(self, frequency):
        self.show_page(self.calibration_page)
        self.calibration_page.frequency_combo.setCurrentIndex(IEC_FREQUENCIES.index(frequency))

    def show_measurement(self, frequency, level_db):
        self.show_page(self.measurement_page)
        self.measurement_page.set_point(frequency, level_db)

    def update_progress(self):
        info_missing = missing_device_fields(self.engine.database.get_device_info())
        calibrated = len(IEC_FREQUENCIES) - len(self.engine.uncalibrated_frequencies())
        summary = self.engine.summary()

        def mark(done):
            return "✔" if done else "○"

        self.progress_label.setText(
            f"{mark(not info_missing)} {tr('Device Info')}   ›   "
            f"{mark(calibrated == len(IEC_FREQUENCIES))} {tr('Calibration')} {calibrated}/{len(IEC_FREQUENCIES)}   ›   "
            f"{mark(summary['missing'] == 0)} {tr('Measurement')} {summary['measured']}/{summary['planned']}"
        )

    def closeEvent(self, event):
        self.live_panel.timer.stop()
        super().closeEvent(event)
