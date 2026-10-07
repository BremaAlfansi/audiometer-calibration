import os
import sqlite3
import struct
from datetime import datetime

import numpy as np

# Without these, sqlite3 stores NumPy scalars (audio is float32) as raw bytes.
for _numpy_type in (np.float16, np.float32, np.float64):
    sqlite3.register_adapter(_numpy_type, float)
for _numpy_type in (np.int8, np.int16, np.int32, np.int64):
    sqlite3.register_adapter(_numpy_type, int)

REAL_COLUMNS = {
    "calibration_points": ["measured_db", "reference_db", "gain_correction_db"],
    "verification_results": [
        "level_db", "measured_frequency", "measured_db",
        "gain_correction_db", "calibrated_db", "thd"
    ]
}


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def blob_to_float(blob):
    """Decode a NumPy float32/float64 that an older version stored as raw bytes."""
    return struct.unpack("<f" if len(blob) == 4 else "<d", blob)[0]


class CalibrationDatabase:
    DEVICE_FIELDS = [
        "brand",
        "model",
        "serial_number",
        "calibration_date",
        "technician",
        "notes",
        "report_date"
    ]

    def __init__(self, db_path="database/audicalpro.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.init_db()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.connect()
        cur = conn.cursor()

        # One calibration point per frequency; recalibrating replaces it.
        cur.execute("""
        CREATE TABLE IF NOT EXISTS calibration_points (
            frequency INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            measured_db REAL NOT NULL,
            reference_db REAL NOT NULL,
            gain_correction_db REAL NOT NULL,
            status TEXT NOT NULL
        )
        """)

        # One verification result per (frequency, level); retaking replaces it.
        cur.execute("""
        CREATE TABLE IF NOT EXISTS verification_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            frequency INTEGER NOT NULL,
            level_db REAL NOT NULL,
            measured_frequency REAL NOT NULL,
            frequency_status TEXT NOT NULL,
            measured_db REAL NOT NULL,
            gain_correction_db REAL NOT NULL,
            calibrated_db REAL NOT NULL,
            level_status TEXT NOT NULL,
            thd REAL NOT NULL,
            thd_status TEXT NOT NULL,
            overall_status TEXT NOT NULL,
            UNIQUE (frequency, level_db)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS device_info (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS frequency_response (
            frequency INTEGER PRIMARY KEY,
            correction_db REAL NOT NULL
        )
        """)

        self.repair_byte_values(cur)

        conn.commit()
        conn.close()

    @staticmethod
    def repair_byte_values(cur):
        """Turn numbers that were saved as raw float32/float64 bytes back into numbers."""
        for table, columns in REAL_COLUMNS.items():
            for column in columns:
                rows = cur.execute(
                    f"SELECT rowid, {column} FROM {table} WHERE typeof({column}) = 'blob'"
                ).fetchall()
                for rowid, blob in rows:
                    if len(blob) in (4, 8):
                        cur.execute(
                            f"UPDATE {table} SET {column} = ? WHERE rowid = ?",
                            (blob_to_float(blob), rowid)
                        )

    # Calibration points

    def upsert_calibration_point(self, point):
        conn = self.connect()
        conn.execute("""
        INSERT OR REPLACE INTO calibration_points
        (frequency, timestamp, measured_db, reference_db, gain_correction_db, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            point["frequency"],
            point.get("timestamp") or now_str(),
            point["measured_db"],
            point["reference_db"],
            point["gain_correction_db"],
            point["status"]
        ))
        conn.commit()
        conn.close()

    def get_calibration_points(self):
        conn = self.connect()
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
        SELECT * FROM calibration_points ORDER BY frequency
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_calibration_point(self, frequency):
        conn = self.connect()
        conn.execute(
            "DELETE FROM calibration_points WHERE frequency = ?",
            (frequency,)
        )
        conn.commit()
        conn.close()

    def clear_calibration_points(self):
        conn = self.connect()
        conn.execute("DELETE FROM calibration_points")
        conn.commit()
        conn.close()

    # Microphone frequency-response corrections (dB relative to the reference frequency)

    def get_response_corrections(self):
        conn = self.connect()
        rows = conn.execute("SELECT frequency, correction_db FROM frequency_response").fetchall()
        conn.close()
        return dict(rows)

    def set_response_correction(self, frequency, correction_db):
        conn = self.connect()
        conn.execute("""
        INSERT OR REPLACE INTO frequency_response (frequency, correction_db) VALUES (?, ?)
        """, (frequency, correction_db))
        conn.commit()
        conn.close()

    def clear_response_corrections(self):
        conn = self.connect()
        conn.execute("DELETE FROM frequency_response")
        conn.commit()
        conn.close()

    # Verification results

    def upsert_verification_result(self, result):
        conn = self.connect()
        conn.execute("""
        INSERT OR REPLACE INTO verification_results
        (
            timestamp, frequency, level_db,
            measured_frequency, frequency_status,
            measured_db, gain_correction_db, calibrated_db, level_status,
            thd, thd_status, overall_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.get("timestamp") or now_str(),
            result["frequency"],
            result["level_db"],
            result["measured_frequency"],
            result["frequency_status"],
            result["measured_db"],
            result["gain_correction_db"],
            result["calibrated_db"],
            result["level_status"],
            result["thd"],
            result["thd_status"],
            result["overall_status"]
        ))
        conn.commit()
        conn.close()

    def get_verification_results(self):
        conn = self.connect()
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
        SELECT * FROM verification_results ORDER BY frequency, level_db
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def has_verification_result(self, frequency, level_db):
        conn = self.connect()
        row = conn.execute("""
        SELECT 1 FROM verification_results
        WHERE frequency = ? AND level_db = ?
        """, (frequency, level_db)).fetchone()
        conn.close()
        return row is not None

    def delete_verification_result(self, frequency, level_db):
        conn = self.connect()
        conn.execute("""
        DELETE FROM verification_results
        WHERE frequency = ? AND level_db = ?
        """, (frequency, level_db))
        conn.commit()
        conn.close()

    def clear_verification_results(self):
        conn = self.connect()
        conn.execute("DELETE FROM verification_results")
        conn.commit()
        conn.close()

    # Device information

    def get_device_info(self):
        conn = self.connect()
        rows = conn.execute("SELECT key, value FROM device_info").fetchall()
        conn.close()

        info = {field: "" for field in self.DEVICE_FIELDS}
        info.update(dict(rows))
        return info

    def save_device_info(self, info):
        """Save the given fields; fields not in `info` keep their stored value."""
        conn = self.connect()
        conn.executemany("""
        INSERT OR REPLACE INTO device_info (key, value) VALUES (?, ?)
        """, [
            (field, str(info[field]))
            for field in self.DEVICE_FIELDS
            if field in info
        ])
        conn.commit()
        conn.close()
