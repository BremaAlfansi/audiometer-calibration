import math
import numpy as np
from scipy.signal import windows
from scipy.fft import rfft, rfftfreq

from core.constants import MIN_TONE_FREQUENCY_HZ


class SignalAnalyzer:
    def analyze(self, signal, sample_rate):
        signal = signal - np.mean(signal)

        window = windows.hann(len(signal))
        windowed = signal * window

        spectrum = np.abs(rfft(windowed))
        frequencies = rfftfreq(len(signal), 1 / sample_rate)

        # Ignore DC / sub-audio bins: room rumble there is not a test tone.
        first_idx = int(np.searchsorted(frequencies, MIN_TONE_FREQUENCY_HZ))
        peak_idx = int(np.argmax(spectrum[first_idx:])) + first_idx
        fundamental_freq = self.interpolated_peak(spectrum, frequencies, peak_idx)

        # A pure tone stands far above the median of the spectrum; broadband noise does not.
        median = max(float(np.median(spectrum[first_idx:])), 1e-12)
        prominence_db = 20 * np.log10(max(spectrum[peak_idx], 1e-12) / median)

        rms = np.sqrt(np.mean(signal ** 2))
        db = 20 * np.log10(max(rms, 1e-12))

        thd = self.calculate_thd(spectrum, peak_idx)
        noise = self.noise_floor(spectrum)

        return {
            "frequency": fundamental_freq,
            "db": db,
            "thd": thd,
            "noise": noise,
            "prominence_db": prominence_db,
            "frequencies": frequencies,
            "spectrum": spectrum
        }

    @staticmethod
    def interpolated_peak(spectrum, frequencies, idx):
        """Refine the peak between FFT bins (parabola on log magnitude).

        The bins are 2 Hz apart, but 125 Hz +/-1 % only allows +/-1.25 Hz.
        """
        if idx <= 0 or idx >= len(spectrum) - 1:
            return frequencies[idx]

        a, b, c = np.log(np.maximum(spectrum[idx - 1:idx + 2], 1e-12))
        denominator = a - 2 * b + c
        offset = 0.5 * (a - c) / denominator if denominator != 0 else 0.0
        bin_width = frequencies[1] - frequencies[0]
        return frequencies[idx] + offset * bin_width

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