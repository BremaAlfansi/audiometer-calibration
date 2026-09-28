import os
import sqlite3
from datetime import datetime


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class CalibrationDatabase:
    DEVICE_FIELDS = [
        "brand",
        "model",
        "serial_number",
        "calibration_date",
        "technician",
        "notes"
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

        conn.commit()
        conn.close()

    # Calibration points

    def upsert_calibration_point(self, point):
        conn = self.connect()
        conn.execute("""
        INSERT OR REPLACE INTO calibration_points
        (frequency, timestamp, measured_db, reference_db, gain_correction_db, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            point["frequency"],
            now_str(),
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
            now_str(),
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
        conn = self.connect()
        conn.executemany("""
        INSERT OR REPLACE INTO device_info (key, value) VALUES (?, ?)
        """, [
            (field, str(info.get(field, "")))
            for field in self.DEVICE_FIELDS
        ])
        conn.commit()
        conn.close()
