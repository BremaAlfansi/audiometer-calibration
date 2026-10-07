import pyqtgraph as pg
from PyQt6.QtCore import Qt

from core.signal_analysis import OCTAVE_BAND_CENTRES
from ui.style import s, READING_FG, INPUT_BORDER

BAR_COLOR = "#2f5f5b"
# Bright red: readable on the black plot, unlike the darker FAIL table colour.
MISMATCH_COLOR = "#ff6b6b"

# Y axis per scale: (floor, top, ticks). Raw readings are dBFS (<= 0); calibrated
# readings are dB on the calibrator's scale (audiometer outputs up to ~120 dB).
SCALES = {
    "raw": (-110.0, 0.0, (0, -30, -60, -90)),
    "calibrated": (0.0, 130.0, (0, 40, 80, 120)),
}


def band_label(centre):
    return f"{centre // 1000}k" if centre >= 1000 else str(centre)


class OctaveBandWidget(pg.PlotWidget):
    """1-octave band levels, 125 Hz - 8 kHz.

    The strongest band (the tone) is highlighted. A dashed frame marks the band of
    the selected test frequency; if the strongest band is elsewhere it turns red.
    """

    def __init__(self):
        super().__init__()

        self.count = len(OCTAVE_BAND_CENTRES)
        self.target_index = None
        self.levels = None

        self.setFixedHeight(s(170))
        self.setMenuEnabled(False)
        self.setMouseEnabled(x=False, y=False)
        self.hideButtons()
        self.showGrid(x=False, y=True, alpha=0.15)
        self.setXRange(-0.6, self.count - 0.4, padding=0)
        self.getAxis("bottom").setTicks([[(i, band_label(c)) for i, c in enumerate(OCTAVE_BAND_CENTRES)], []])

        self.target_frame = pg.BarGraphItem(
            x=[0], height=[0], y0=0, width=0.86,
            brush=pg.mkBrush(0, 0, 0, 0),
            pen=pg.mkPen(INPUT_BORDER, width=2, style=Qt.PenStyle.DashLine)
        )
        self.target_frame.setVisible(False)
        self.addItem(self.target_frame)

        self.bars = pg.BarGraphItem(x=list(range(self.count)), height=[0] * self.count, y0=0, width=0.7,
                                    brush=BAR_COLOR, pen=None)
        self.addItem(self.bars)

        self.peak_label = pg.TextItem(color=READING_FG, anchor=(0.5, 1.0))
        self.addItem(self.peak_label)

        self.set_scale("raw")

    def set_scale(self, scale):
        self.floor, self.top, ticks = SCALES[scale]
        self.setYRange(self.floor, self.top, padding=0)
        self.getAxis("left").setTicks([[(v, str(v)) for v in ticks], []])
        self.target_frame.setOpts(y0=self.floor, height=[self.top - self.floor])
        self.redraw()

    def set_target(self, frequency):
        """Frame the band of the test frequency; None hides the frame."""
        self.target_index = OCTAVE_BAND_CENTRES.index(frequency) if frequency in OCTAVE_BAND_CENTRES else None
        if self.target_index is not None:
            self.target_frame.setOpts(x=[self.target_index])
        self.target_frame.setVisible(self.target_index is not None)
        self.redraw()

    def update_bands(self, levels):
        """`levels`: band centre -> dB, already on the current scale."""
        self.levels = levels
        self.redraw()

    def clear_bands(self):
        self.levels = None
        self.redraw()

    def redraw(self):
        if self.levels is None:
            self.bars.setOpts(y0=self.floor, height=[0] * self.count, brushes=[pg.mkBrush(BAR_COLOR)] * self.count)
            self.peak_label.setText("")
            return

        values = [min(max(self.levels[c], self.floor), self.top) for c in OCTAVE_BAND_CENTRES]
        peak = max(range(self.count), key=values.__getitem__)
        mismatch = self.target_index is not None and peak != self.target_index
        peak_color = MISMATCH_COLOR if mismatch else READING_FG

        brushes = [pg.mkBrush(peak_color if i == peak else BAR_COLOR) for i in range(self.count)]
        self.bars.setOpts(y0=self.floor, height=[v - self.floor for v in values], brushes=brushes)

        self.peak_label.setColor(peak_color)
        self.peak_label.setText(f"{self.levels[OCTAVE_BAND_CENTRES[peak]]:.1f}")
        self.peak_label.setPos(peak, min(values[peak] + 2, self.top - 2))
