from core.constants import (
    IEC_FREQUENCIES,
    TEST_LEVELS_DB,
    REFERENCE_FREQUENCY,
    LEVEL_RESOLUTION_DB,
    LEVEL_TOLERANCE_DB,
    FREQUENCY_TOLERANCE_PCT,
    THD_MAX_PCT,
    PASS,
    FAIL
)
from database.db import CalibrationDatabase


def levels_match(a, b):
    """True when two levels are identical at the displayed resolution."""
    return round(a / LEVEL_RESOLUTION_DB) == round(b / LEVEL_RESOLUTION_DB)


def gain_correction(measured_db, reference_db):
    """Gain correction = Reference - Measured.

    Adding it to a measured reading gives the reference-scale level:
    calibrated = measured + correction.
    """
    return reference_db - measured_db


class CalibrationEngine:
    IEC_FREQUENCIES = IEC_FREQUENCIES
    TEST_LEVELS_DB = TEST_LEVELS_DB

    def __init__(self, database=None):
        self.database = database or CalibrationDatabase()

    # Step 2: calibration
    #   Gain at 1 kHz from the calibrator, plus a per-frequency microphone
    #   response correction (dB relative to 1 kHz, entered manually).
    #   Total correction(f) = gain correction + response correction(f).

    @staticmethod
    def with_corrected_level(point):
        """Add the corrected level and judge it: PASS when Measured + Correction equals Reference."""
        point["corrected_db"] = point["measured_db"] + point["gain_correction_db"]
        point["status"] = PASS if levels_match(point["corrected_db"], point["reference_db"]) else FAIL
        return point

    def calibrate(self, measured_db, reference_db):
        point = self.with_corrected_level({
            "frequency": REFERENCE_FREQUENCY,
            "measured_db": measured_db,
            "reference_db": reference_db,
            "gain_correction_db": gain_correction(measured_db, reference_db)
        })
        self.database.upsert_calibration_point(point)
        return point

    def get_reference_point(self):
        """The 1 kHz calibrator measurement, or None if not calibrated yet."""
        for p in self.database.get_calibration_points():
            if p["frequency"] == REFERENCE_FREQUENCY:
                # Status is recomputed on read so points saved under an older rule are judged the same way.
                return self.with_corrected_level(p)
        return None

    def is_calibrated(self):
        return self.get_reference_point() is not None

    def delete_reference_point(self):
        self.database.delete_calibration_point(REFERENCE_FREQUENCY)

    def get_response_corrections(self):
        """Correction per frequency in dB relative to 1 kHz; 0.0 where none was entered."""
        stored = self.database.get_response_corrections()
        return {
            f: 0.0 if f == REFERENCE_FREQUENCY else float(stored.get(f, 0.0))
            for f in IEC_FREQUENCIES
        }

    def set_response_correction(self, frequency, correction_db):
        if frequency != REFERENCE_FREQUENCY:
            self.database.set_response_correction(frequency, float(correction_db))

    def get_correction(self, frequency):
        """Total correction added to raw readings at this frequency, or None if not calibrated."""
        point = self.get_reference_point()
        if point is None:
            return None
        return point["gain_correction_db"] + self.get_response_corrections()[frequency]

    # Step 3: verification (per-parameter pass/fail)

    @staticmethod
    def frequency_ok(target_hz, measured_hz):
        return abs(measured_hz - target_hz) <= target_hz * FREQUENCY_TOLERANCE_PCT / 100

    @staticmethod
    def level_ok(frequency, target_db, calibrated_db):
        # Round the deviation to the display resolution so 3.04 dB off reads as 3.0 and passes.
        deviation = round(abs(calibrated_db - target_db) / LEVEL_RESOLUTION_DB) * LEVEL_RESOLUTION_DB
        return deviation <= LEVEL_TOLERANCE_DB[frequency] + 1e-9

    def evaluate(self, frequency, level_db, reading, correction_db):
        reading = {key: float(reading[key]) for key in ("frequency", "db", "thd")}
        calibrated_db = reading["db"] + correction_db

        frequency_status = PASS if self.frequency_ok(frequency, reading["frequency"]) else FAIL
        level_status = PASS if self.level_ok(frequency, level_db, calibrated_db) else FAIL
        thd_status = PASS if reading["thd"] <= THD_MAX_PCT else FAIL

        statuses = (frequency_status, level_status, thd_status)

        return {
            "frequency": frequency,
            "level_db": level_db,
            "measured_frequency": reading["frequency"],
            "frequency_status": frequency_status,
            "measured_db": reading["db"],
            "gain_correction_db": correction_db,
            "calibrated_db": calibrated_db,
            "level_status": level_status,
            "thd": reading["thd"],
            "thd_status": thd_status,
            "overall_status": PASS if all(s == PASS for s in statuses) else FAIL
        }

    def save_result(self, result):
        self.database.upsert_verification_result(result)

    def has_result(self, frequency, level_db):
        return self.database.has_verification_result(frequency, level_db)

    def delete_result(self, frequency, level_db):
        self.database.delete_verification_result(frequency, level_db)

    def get_results(self):
        return self.database.get_verification_results()

    def coverage(self):
        """Map every planned (frequency, level) pair to its result, or None."""
        grid = {
            (f, float(l)): None
            for f in IEC_FREQUENCIES
            for l in TEST_LEVELS_DB
        }
        for r in self.get_results():
            grid[(r["frequency"], float(r["level_db"]))] = r
        return grid

    def missing_points(self):
        return [key for key, r in self.coverage().items() if r is None]

    def summary(self):
        results = self.get_results()
        passed = sum(1 for r in results if r["overall_status"] == PASS)
        planned = len(IEC_FREQUENCIES) * len(TEST_LEVELS_DB)
        missing = len(self.missing_points())
        failed = len(results) - passed

        return {
            "planned": planned,
            "measured": len(results),
            "passed": passed,
            "failed": failed,
            "missing": missing,
            "overall": PASS if failed == 0 and missing == 0 and results else FAIL
        }

    def clear_all(self):
        """Start over. Microphone response corrections are kept: they belong to the microphone."""
        self.database.clear_calibration_points()
        self.database.clear_verification_results()
