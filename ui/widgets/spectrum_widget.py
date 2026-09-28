import numpy as np
import pyqtgraph as pg

from ui.style import s


class SpectrumWidget(pg.PlotWidget):
    """Small FFT preview - only meant to confirm that a tone is coming in."""

    def __init__(self):
        super().__init__()

        self.setFixedHeight(s(150))
        self.setMenuEnabled(False)
        self.setMouseEnabled(x=False, y=False)
        self.hideButtons()
        self.setLogMode(x=True, y=False)
        self.setXRange(np.log10(50), np.log10(12000), padding=0)
        self.showGrid(x=True, y=True, alpha=0.15)

        # Fixed decade ticks: pyqtgraph's automatic log ticks crowd into unreadable text.
        self.getAxis("bottom").setTicks([[
            (np.log10(100), "100"), (np.log10(1000), "1k"), (np.log10(10000), "10k")
        ], []])
        self.getAxis("left").setTicks([[(v, str(v)) for v in (0, -50, -100, -150)], []])

        self.curve = self.plot(pen=pg.mkPen("#7ee0d6", width=1))

    def update_plot(self, x, y):
        # Skip the DC bin: log x-axis cannot show 0 Hz.
        magnitude_db = 20 * np.log10(np.maximum(y[1:], 1e-12))
        self.curve.setData(x[1:], magnitude_db)

    def clear_plot(self):
        self.curve.setData([], [])
