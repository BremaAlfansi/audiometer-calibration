from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QTabWidget
)

from PyQt6.QtCore import QTimer

from core.audio_engine import AudioEngine
from core.signal_analysis import SignalAnalyzer

from ui.widgets.metric_card import MetricCard
from ui.widgets.spectrum_widget import SpectrumWidget
from ui.calibration_page import CalibrationPage

from core.constants import APP_NAME, ORG_NAME


class MeasurementPage(QWidget):
    def __init__(self):
        super().__init__()

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

        title = QLabel("Measurement Module")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
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
        self.noise_card = MetricCard("Noise Floor")

        metrics.addWidget(self.freq_card)
        metrics.addWidget(self.db_card)
        metrics.addWidget(self.thd_card)
        metrics.addWidget(self.noise_card)

        root.addLayout(metrics)

        self.spectrum = SpectrumWidget()
        root.addWidget(self.spectrum)

        self.measure_button = QPushButton("Start Live")
        self.measure_button.clicked.connect(
            self.toggle_measurement
        )

        root.addWidget(self.measure_button)

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

            self.noise_card.set_value(
                f"{result['noise']:.2f}"
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
            "measured_db": self.current_result["db"]
        }


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

        self.measurement_page = MeasurementPage()

        self.calibration_page = CalibrationPage()
        tabs.addTab(
            self.measurement_page,
            "Measurement"
        )

        tabs.addTab(
            self.calibration_page,
            "Calibration"
        )

        self.setCentralWidget(tabs)