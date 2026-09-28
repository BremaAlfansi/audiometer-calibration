from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QStyle
)

from core.audio_engine import AudioEngine
from core.signal_analysis import SignalAnalyzer
from core.constants import MIN_SIGNAL_DB, MIN_TONE_PROMINENCE_DB
from ui.i18n import tr
from ui import style
from ui.style import banner, info_icon, s
from ui.widgets.metric_card import MetricCard
from ui.widgets.spectrum_widget import SpectrumWidget


class LivePanel(QWidget):
    """Input device + live readings. Shared by the Calibration and Measurement tabs."""

    reading_updated = pyqtSignal(object)
    live_state_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        self.audio = AudioEngine()
        self.analyzer = SignalAnalyzer()

        self.timer = QTimer()
        self.timer.timeout.connect(self.live_measure)

        self.current_reading = None

        self.setup_ui()
        self.load_devices()

    def setup_ui(self):
        self.setFixedWidth(300 if style.COMPACT else s(370))

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        title = QLabel(tr("Live Signal"))
        title.setObjectName("pageTitle")
        root.addWidget(title)

        device_row = QHBoxLayout()
        self.device_combo = QComboBox()
        self.device_combo.setToolTip(tr("Input device (measurement microphone / coupler)"))
        self.refresh_button = QPushButton()
        self.refresh_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.refresh_button.setToolTip(tr("Refresh device list"))
        self.refresh_button.setFixedWidth(s(42))
        self.refresh_button.clicked.connect(self.load_devices)
        device_row.addWidget(self.device_combo, 1)
        device_row.addWidget(self.refresh_button)
        root.addLayout(device_row)

        self.live_button = QPushButton(tr("Start Live"))
        self.live_button.setObjectName("primary")
        self.live_button.clicked.connect(self.toggle_live)
        root.addWidget(self.live_button)

        # Frequency left, level middle, THD right - same order as every table.
        cards = QHBoxLayout()
        cards.setSpacing(6)
        self.freq_card = MetricCard(tr("Frequency"))
        self.db_card = MetricCard(tr("Level (raw)"))
        self.db_card.setToolTip(tr("Uncorrected input level (dBFS)."))
        self.thd_card = MetricCard("THD")
        cards.addWidget(self.freq_card)
        cards.addWidget(self.db_card)
        cards.addWidget(self.thd_card)
        root.addLayout(cards)

        self.signal_banner = QLabel()
        banner(self.signal_banner, "warn", tr("Live is off"))
        root.addWidget(self.signal_banner)

        spectrum_row = QHBoxLayout()
        spectrum_row.addWidget(QLabel(tr("Spectrum")))
        spectrum_row.addStretch(1)
        spectrum_row.addWidget(info_icon(tr("Only confirms that a tone is coming in.")))
        root.addLayout(spectrum_row)
        self.spectrum = SpectrumWidget()
        root.addWidget(self.spectrum)

        root.addStretch(1)

    def load_devices(self):
        self.device_combo.clear()

        try:
            devices = self.audio.get_devices()
        except Exception as e:
            banner(self.signal_banner, "error", tr("Could not list audio devices: {error}").format(error=e))
            return

        for idx, name in devices:
            self.device_combo.addItem(name, idx)

        if not devices:
            banner(self.signal_banner, "error", tr("No input device found. Connect a microphone and press ↻."))

    def is_live(self):
        return self.timer.isActive()

    def toggle_live(self):
        if self.is_live():
            self.stop_live()
            return

        if self.device_combo.currentData() is None:
            banner(self.signal_banner, "error", tr("Select an input device first."))
            return

        self.audio.set_device(self.device_combo.currentData())
        self.timer.start(300)
        self.live_button.setText(tr("Stop Live"))
        banner(self.signal_banner, "warn", tr("Waiting for signal…"))
        self.live_state_changed.emit(True)

    def stop_live(self, message=None):
        self.timer.stop()
        self.live_button.setText(tr("Start Live"))
        banner(self.signal_banner, "warn", message or tr("Live is off"))
        self.live_state_changed.emit(False)

    def live_measure(self):
        try:
            signal = self.audio.capture()
            result = self.analyzer.analyze(signal, self.audio.sample_rate)
        except Exception as e:
            self.current_reading = None
            self.stop_live(tr("Live stopped: {error}").format(error=e))
            return

        self.current_reading = result

        self.freq_card.set_value(f"{result['frequency']:.1f} Hz")
        self.db_card.set_value(f"{result['db']:.1f} dB")
        self.thd_card.set_value(f"{result['thd']:.2f} %")
        self.spectrum.update_plot(result["frequencies"], result["spectrum"])

        if self.has_signal():
            banner(self.signal_banner, "ok", tr("Signal detected"))
        else:
            banner(self.signal_banner, "warn", tr("No tone detected. Check the audiometer output."))

        self.reading_updated.emit(result)

    def has_signal(self):
        r = self.current_reading
        return (
            r is not None
            and r["db"] >= MIN_SIGNAL_DB
            and r.get("prominence_db", 0.0) >= MIN_TONE_PROMINENCE_DB
        )

    def reading(self):
        """Latest reading while live, else None."""
        return self.current_reading if self.is_live() else None
