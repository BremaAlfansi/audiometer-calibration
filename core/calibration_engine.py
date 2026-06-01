import json
import os

from database.db import CalibrationDatabase


class CalibrationEngine:
    IEC_FREQUENCIES = [
        125,
        250,
        500,
        1000,
        2000,
        4000,
        8000
    ]

    PASS_TOLERANCE_DB = 3.0

    def __init__(self):
        self.profile_path = "config/calibration_profile.json"
        self.database = CalibrationDatabase()

        self.offsets = {
            str(freq): 0.0
            for freq in self.IEC_FREQUENCIES
        }

        self.session_results = []

        self.load_profile()

    def calculate_correction(
        self,
        frequency,
        measured_db,
        reference_db,
        tolerance_db=None
    ):
        correction = reference_db - measured_db

        tolerance = (
            tolerance_db
            if tolerance_db is not None
            else self.PASS_TOLERANCE_DB
        )

        status = (
            "PASS"
            if abs(correction) <= tolerance
            else "FAIL"
        )

        result = {
            "frequency": frequency,
            "measured_db": measured_db,
            "reference_db": reference_db,
            "correction_db": correction,
            "status": status
        }

        self.session_results.append(result)

        self.offsets[str(frequency)] = correction

        self.database.add_record(
            frequency,
            measured_db,
            reference_db,
            correction,
            status
        )

        return result

    def get_session_results(self):
        return self.session_results

    def clear_session(self):
        self.session_results = []

    def get_summary(self):
        total = len(self.session_results)

        passed = sum(
            1 for item in self.session_results
            if item["status"] == "PASS"
        )

        failed = total - passed

        overall = "PASS" if failed == 0 and total > 0 else "FAIL"

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "overall": overall
        }

    def save_profile(self):
        os.makedirs("config", exist_ok=True)

        with open(self.profile_path, "w") as f:
            json.dump(self.offsets, f, indent=4)

    def load_profile(self):
        if os.path.exists(self.profile_path):
            with open(self.profile_path, "r") as f:
                self.offsets.update(json.load(f))

    def get_profile(self):
        return self.offsets

    def get_history(self):
        return self.database.get_all_records()

    def clear_history(self):
        self.database.clear_history()