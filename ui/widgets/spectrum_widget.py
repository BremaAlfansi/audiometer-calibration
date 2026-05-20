import pyqtgraph as pg


class SpectrumWidget(pg.PlotWidget):
    def __init__(self):
        super().__init__()

        self.curve = self.plot()
        self.setTitle("FFT Spectrum")
        self.setLabel("left", "Magnitude")
        self.setLabel("bottom", "Frequency (Hz)")

    def update_plot(self, x, y):
        self.curve.setData(x, y)