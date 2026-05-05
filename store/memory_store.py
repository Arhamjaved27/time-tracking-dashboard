"""
store/memory_store.py — Thread-safe in-memory state for a single session.
In production, swap this out for a database layer (SQLite / PostgreSQL).
"""

from __future__ import annotations

import threading
from datetime import date
from typing import Optional


class MemoryStore:
    """Singleton in-memory store shared across all requests in one process."""

    _lock = threading.Lock()

    def __init__(self):
        self._settings: dict = {}
        self._logs: dict[date, dict] = {}       # date → log entry dict
        self._holidays: dict[date, dict] = {}   # date → holiday dict

    # ── Settings ──────────────────────────────────────────────────────────────

    def save_settings(self, data: dict) -> None:
        with self._lock:
            self._settings = data.copy()

    def get_settings(self) -> Optional[dict]:
        return self._settings.copy() if self._settings else None

    # ── Logs ──────────────────────────────────────────────────────────────────

    def upsert_log(self, log_date: date, data: dict) -> None:
        with self._lock:
            self._logs[log_date] = data.copy()

    def get_log(self, log_date: date) -> Optional[dict]:
        return self._logs.get(log_date)

    def delete_log(self, log_date: date) -> bool:
        with self._lock:
            if log_date in self._logs:
                del self._logs[log_date]
                return True
            return False

    def all_logs(self) -> list[dict]:
        return list(self._logs.values())

    # ── Holidays ──────────────────────────────────────────────────────────────

    def add_holiday(self, holiday_date: date, data: dict) -> None:
        with self._lock:
            self._holidays[holiday_date] = data.copy()

    def remove_holiday(self, holiday_date: date) -> bool:
        with self._lock:
            if holiday_date in self._holidays:
                del self._holidays[holiday_date]
                return True
            return False

    def all_holidays(self) -> list[dict]:
        return list(self._holidays.values())

    def is_holiday(self, d: date) -> bool:
        return d in self._holidays


# Global singleton
store = MemoryStore()
