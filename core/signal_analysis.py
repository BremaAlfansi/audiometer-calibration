import math
import numpy as np
from scipy.signal import windows
from scipy.fft import rfft, rfftfreq

from core.constants import MIN_TONE_FREQUENCY_HZ, IEC_FREQUENCIES

# The audiometric test frequencies are exactly the standard octave-band centres.
OCTAVE_BAND_CENTRES = IEC_FREQUENCIES


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
        octave_bands = self.octave_band_levels(spectrum, frequencies, window)

        # Plain Python floats: audio arrives as float32, and sqlite3 stores NumPy
        # scalars as raw bytes instead of numbers.
        return {
            "frequency": float(fundamental_freq),
            "db": float(db),
            "thd": float(thd),
            "noise": float(noise),
            "prominence_db": float(prominence_db),
            "octave_bands": octave_bands,
            "frequencies": frequencies,
            "spectrum": spectrum
        }

    @staticmethod
    def octave_band_levels(spectrum, frequencies, window):
        """Level per 1-octave band (dB, same scale as the raw level), centre -> dB.

        A band spans fc/sqrt(2) .. fc*sqrt(2). Band power comes from the windowed
        one-sided spectrum (Parseval), so a pure tone's band level equals its RMS level.
        """
        power_scale = 2.0 / (len(window) * np.sum(window ** 2))
        power = spectrum ** 2 * power_scale

        levels = {}
        for centre in OCTAVE_BAND_CENTRES:
            in_band = (frequencies >= centre / np.sqrt(2)) & (frequencies < centre * np.sqrt(2))
            band_power = float(np.sum(power[in_band]))
            levels[centre] = float(10 * np.log10(max(band_power, 1e-24)))
        return levels

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