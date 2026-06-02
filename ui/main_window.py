from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QTabWidget,
    QLineEdit,
    QMessageBox
)

from PyQt6.QtCore import QTimer

from core.audio_engine import AudioEngine
from core.signal_analysis import SignalAnalyzer

from ui.widgets.metric_card import MetricCard
from ui.widgets.spectrum_widget import SpectrumWidget
from ui.calibration_page import CalibrationPage
from ui.report_page import ReportPage

from core.constants import APP_NAME, ORG_NAME


class MeasurementPage(QWidget):
    def __init__(self, calibration_engine=None, calibration_page=None):
        super().__init__()

        self.calibration_engine = calibration_engine
        self.calibration_page = calibration_page

        self.audio = AudioEngine()
        self.analyzer = SignalAnalyzer()

        self.timer = QTimer()
        self.timer.timeout.connect(self.live_measure)

        self.is_measuring = False

        self.current_result = None

        self.setup_ui()
        self.load_devices()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        title = QLabel("Measurement Module")
        title.setStyleSheet("""
            font-size: 26px;
            font-weight: 700;
            color: #f0f6ff;
        """)

        root.addWidget(title)

        device_row = QHBoxLayout()

        self.device_combo = QComboBox()

        self.refresh_button = QPushButton("Refresh Devices")
        self.refresh_button.clicked.connect(
            self.load_devices
        )

        device_row.addWidget(QLabel("Input Device"))
        device_row.addWidget(self.device_combo)
        device_row.addWidget(self.refresh_button)

        root.addLayout(device_row)

        metrics = QHBoxLayout()

        self.freq_card = MetricCard("Frequency")
        self.db_card = MetricCard("Level")
        self.thd_card = MetricCard("THD")
        # remove noise floor from measurement display per spec
        metrics.addWidget(self.freq_card)
        metrics.addWidget(self.db_card)
        metrics.addWidget(self.thd_card)

        root.addLayout(metrics)

        self.spectrum = SpectrumWidget()
        root.addWidget(self.spectrum)

        # Target inputs
        target_row = QHBoxLayout()
        target_row.setSpacing(12)

        self.target_freq = QComboBox()
        self.target_freq.addItems([
            "125",
            "250",
            "500",
            "1000",
            "2000",
            "4000",
            "8000"
        ])

        self.target_level = QLineEdit()
        self.target_level.setPlaceholderText("Target Level dB")
        self.target_level.setFixedWidth(120)

        target_row.addWidget(QLabel("Target Frequency"))
        target_row.addWidget(self.target_freq)
        target_row.addWidget(QLabel("Target Level dB"))
        target_row.addWidget(self.target_level)

        root.addLayout(target_row)

        self.pass_fail_label = QLabel("Status: --")
        self.pass_fail_label.setStyleSheet("font-size:12px; color:#cde6ff;")
        root.addWidget(self.pass_fail_label)

        button_row = QHBoxLayout()

        self.measure_button = QPushButton("Start Live")
        self.measure_button.setObjectName("primary")
        self.measure_button.clicked.connect(self.toggle_measurement)

        self.save_button = QPushButton("Save Measurement")
        self.save_button.setObjectName("primary")
        self.save_button.clicked.connect(self.save_measurement)

        button_row.addWidget(self.measure_button)
        button_row.addWidget(self.save_button)

        root.addLayout(button_row)


    def load_devices(self):
        self.device_combo.clear()

        devices = self.audio.get_devices()

        for idx, name in devices:
            self.device_combo.addItem(name, idx)

    def selected_device(self):
        return self.device_combo.currentData()

    def toggle_measurement(self):
        if not self.is_measuring:
            self.audio.set_device(
                self.selected_device()
            )

            self.timer.start(300)
            self.is_measuring = True
            self.measure_button.setText("Stop Live")

        else:
            self.timer.stop()
            self.is_measuring = False
            self.measure_button.setText("Start Live")

            if self.calibration_page is not None and self.current_result is not None:
                self.calibration_page.set_measured_value(self.current_result['db'])

    def live_measure(self):
        try:
            signal = self.audio.capture()

            result = self.analyzer.analyze(
                signal,
                self.audio.sample_rate
            )

            self.current_result = result

            self.freq_card.set_value(
                f"{result['frequency']:.2f} Hz"
            )

            self.db_card.set_value(
                f"{result['db']:.2f} dB"
            )

            self.thd_card.set_value(
                f"{result['thd']:.2f}%"
            )

            self.spectrum.update_plot(
                result["frequencies"],
                result["spectrum"]
            )

        except Exception:
            self.timer.stop()
            self.is_measuring = False
            self.measure_button.setText("Start Live")

    def get_current_measurement(self):
        if self.current_result is None:
            return None

        return {
            "frequency": int(
                min(
                    [125, 250, 500, 1000, 2000, 4000, 8000],
                    key=lambda x: abs(
                        x - self.current_result["frequency"]
                    )
                )
            ),
            "measured_db": self.current_result["db"],
            "thd": self.current_result["thd"]
        }

    def save_measurement(self):
        from database.db import CalibrationDatabase

        measurement = self.get_current_measurement()

        if measurement is None:
            QMessageBox.warning(self, "No Data", "No measurement available to save.")
            return

        try:
            target_freq = int(self.target_freq.currentText())
            target_level = float(self.target_level.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter a valid numeric target level.")
            return

        measured_db = measurement["measured_db"]
        thd = measurement.get("thd", 0.0)

        # apply last calibration offset if available
        offset = 0.0

        if self.calibration_engine is not None:
            profile = self.calibration_engine.get_profile()
            offset = float(profile.get(str(target_freq), 0.0))

        adjusted_db = measured_db + offset

        tolerance = self.calibration_engine.PASS_TOLERANCE_DB if self.calibration_engine else 3.0
        thd_tolerance = self.calibration_engine.PASS_THD_PERCENT if self.calibration_engine else 3.0

        level_pass = abs(adjusted_db - target_level) <= tolerance
        thd_pass = thd <= thd_tolerance
        status = "PASS" if level_pass and thd_pass else "FAIL"

        if self.calibration_page is not None:
            self.calibration_page.set_measured_value(measured_db)

        db = CalibrationDatabase()
        db.add_measurement_record(
            target_freq,
            target_level,
            measured_db,
            adjusted_db,
            thd,
            status
        )

        self.pass_fail_label.setText(f"Status: {status}")
        QMessageBox.information(self, "Saved", "Measurement saved to database.")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            f"{APP_NAME} - {ORG_NAME}"
        )

        self.resize(1500, 950)

        self.setup_ui()

    def setup_ui(self):
        tabs = QTabWidget()

        # create calibration first (leftmost), then measurement, then report
        self.calibration_page = CalibrationPage()

        self.measurement_page = MeasurementPage(
            calibration_engine=self.calibration_page.engine,
            calibration_page=self.calibration_page
        )

        tabs.addTab(self.calibration_page, "Calibration")
        tabs.addTab(self.measurement_page, "Measurement")

        self.report_page = ReportPage()
        tabs.addTab(self.report_page, "Report")

        # global styles for buttons and inputs to improve visibility
        self.setStyleSheet('''
            QPushButton { background: #14232b; color: #eaf6ff; padding:8px 12px; border-radius:6px; }
            QPushButton#primary { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #2b90ff, stop:1 #1b6fff); color: white; font-weight:600 }
            QPushButton#secondary { background: #2b3944; color:#dbeaf7 }
            QComboBox, QLineEdit { background: #081421; color:#eaf6ff; padding:6px; border-radius:6px }
        ''')

        self.setCentralWidget(tabs)

        