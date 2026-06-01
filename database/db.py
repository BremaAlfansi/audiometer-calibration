import sqlite3
from datetime import datetime


class CalibrationDatabase:
    def __init__(self, db_path="database/audicalpro.db"):
        self.db_path = db_path
        self.init_db()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS calibration_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            frequency INTEGER NOT NULL,
            measured_db REAL NOT NULL,
            reference_db REAL NOT NULL,
            correction_db REAL NOT NULL,
            status TEXT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            target_frequency INTEGER NOT NULL,
            target_level REAL NOT NULL,
            measured_db REAL NOT NULL,
            adjusted_db REAL NOT NULL,
            thd REAL NOT NULL,
            status TEXT NOT NULL
        )
        """)

        conn.commit()
        conn.close()

    def add_record(
        self,
        frequency,
        measured_db,
        reference_db,
        correction_db,
        status
    ):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO calibration_history
        (
            timestamp,
            frequency,
            measured_db,
            reference_db,
            correction_db,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            frequency,
            measured_db,
            reference_db,
            correction_db,
            status
        ))

        conn.commit()
        conn.close()

    def add_measurement_record(
        self,
        target_frequency,
        target_level,
        measured_db,
        adjusted_db,
        thd,
        status
    ):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO measurements
        (
            timestamp,
            target_frequency,
            target_level,
            measured_db,
            adjusted_db,
            thd,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            target_frequency,
            target_level,
            measured_db,
            adjusted_db,
            thd,
            status
        ))

        conn.commit()
        conn.close()

    def get_all_records(self):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
        SELECT
            timestamp,
            frequency,
            measured_db,
            reference_db,
            correction_db,
            status
        FROM calibration_history
        ORDER BY id DESC
        """)

        rows = cur.fetchall()
        conn.close()

        return rows

    def clear_history(self):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("DELETE FROM calibration_history")

        conn.commit()
        conn.close()

    def get_measurements(self):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
        SELECT
            timestamp,
            target_frequency,
            target_level,
            measured_db,
            adjusted_db,
            thd,
            status
        FROM measurements
        ORDER BY id DESC
        """)

        rows = cur.fetchall()
        conn.close()

        return rows

    def clear_measurements(self):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("DELETE FROM measurements")

        conn.commit()
        conn.close()