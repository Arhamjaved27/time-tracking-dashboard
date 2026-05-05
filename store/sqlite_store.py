"""
store/sqlite_store.py — SQLite-based persistent store for ShiftGlass Pro
Replaces in-memory store with database persistence.
"""

import sqlite3
from datetime import date
from typing import Optional


class SQLiteStore:
    """SQLite-backed store shared across all requests."""

    def __init__(self, db_path: str = "shiftglass.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    monthly_salary_pkr REAL,
                    cycle_start_date TEXT,
                    hourly_rate_pkr REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    log_date TEXT PRIMARY KEY,
                    day_type TEXT,
                    work_decimal REAL,
                    break_decimal REAL,
                    net_decimal REAL,
                    target_hours REAL,
                    delta_hours REAL,
                    earnings_pkr REAL,
                    notes TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS holidays (
                    holiday_date TEXT PRIMARY KEY,
                    label TEXT,
                    historical_avg_hours REAL
                )
            """)
            conn.commit()

    # ── Settings ──────────────────────────────────────────────────────────────

    def save_settings(self, data: dict) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO settings (id, monthly_salary_pkr, cycle_start_date, hourly_rate_pkr)
                VALUES (1, ?, ?, ?)
            """, (data["monthly_salary_pkr"], data["cycle_start_date"], data["hourly_rate_pkr"]))
            conn.commit()

    def get_settings(self) -> Optional[dict]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
            if row:
                return {
                    "monthly_salary_pkr": row[1],
                    "cycle_start_date": row[2],
                    "hourly_rate_pkr": row[3],
                }
        return None

    # ── Logs ──────────────────────────────────────────────────────────────────

    def upsert_log(self, log_date: date, data: dict) -> None:
        date_str = log_date.isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO logs (log_date, day_type, work_decimal, break_decimal, net_decimal, target_hours, delta_hours, earnings_pkr, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (date_str, data["day_type"], data["work_decimal"], data["break_decimal"], data["net_decimal"], data["target_hours"], data["delta_hours"], data["earnings_pkr"], data.get("notes")))
            conn.commit()

    def get_log(self, log_date: date) -> Optional[dict]:
        date_str = log_date.isoformat()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM logs WHERE log_date = ?", (date_str,)).fetchone()
            if row:
                return {
                    "log_date": date.fromisoformat(row[0]),
                    "day_type": row[1],
                    "work_decimal": row[2],
                    "break_decimal": row[3],
                    "net_decimal": row[4],
                    "target_hours": row[5],
                    "delta_hours": row[6],
                    "earnings_pkr": row[7],
                    "notes": row[8],
                }
        return None

    def delete_log(self, log_date: date) -> bool:
        date_str = log_date.isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM logs WHERE log_date = ?", (date_str,))
            conn.commit()
            return cursor.rowcount > 0

    def all_logs(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM logs").fetchall()
            return [{
                "log_date": date.fromisoformat(row[0]),
                "day_type": row[1],
                "work_decimal": row[2],
                "break_decimal": row[3],
                "net_decimal": row[4],
                "target_hours": row[5],
                "delta_hours": row[6],
                "earnings_pkr": row[7],
                "notes": row[8],
            } for row in rows]

    # ── Holidays ──────────────────────────────────────────────────────────────

    def add_holiday(self, holiday_date: date, data: dict) -> None:
        date_str = holiday_date.isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO holidays (holiday_date, label, historical_avg_hours)
                VALUES (?, ?, ?)
            """, (date_str, data["label"], data["historical_avg_hours"]))
            conn.commit()

    def remove_holiday(self, holiday_date: date) -> bool:
        date_str = holiday_date.isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM holidays WHERE holiday_date = ?", (date_str,))
            conn.commit()
            return cursor.rowcount > 0

    def all_holidays(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM holidays").fetchall()
            return [{
                "holiday_date": date.fromisoformat(row[0]),
                "label": row[1],
                "historical_avg_hours": row[2],
            } for row in rows]

    def is_holiday(self, d: date) -> bool:
        date_str = d.isoformat()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT 1 FROM holidays WHERE holiday_date = ?", (date_str,)).fetchone()
            return row is not None


# Global singleton
store = SQLiteStore()