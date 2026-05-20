import math
import numpy as np
from scipy.signal import windows
from scipy.fft import rfft, rfftfreq


class SignalAnalyzer:
    def analyze(self, signal, sample_rate):
        signal = signal - np.mean(signal)

        window = windows.hann(len(signal))
        windowed = signal * window

        spectrum = np.abs(rfft(windowed))
        frequencies = rfftfreq(len(signal), 1 / sample_rate)

        peak_idx = np.argmax(spectrum[1:]) + 1
        fundamental_freq = frequencies[peak_idx]

        rms = np.sqrt(np.mean(signal ** 2))
        db = 20 * np.log10(max(rms, 1e-12))

        thd = self.calculate_thd(spectrum, peak_idx)
        noise = self.noise_floor(spectrum)

        return {
            "frequency": fundamental_freq,
            "db": db,
            "thd": thd,
            "noise": noise,
            "frequencies": frequencies,
            "spectrum": spectrum
        }

    def calculate_thd(self, spectrum, fundamental_idx):
        fundamental = spectrum[fundamental_idx]

        if fundamental <= 0:
            return 0.0

        harmonic_power = 0

        for harmonic in range(2, 6):
            idx = fundamental_idx * harmonic
            if idx < len(spectrum):
                harmonic_power += spectrum[idx] ** 2

        return math.sqrt(harmonic_power) / fundamental * 100

    def noise_floor(self, spectrum):
        return np.mean(spectrum)