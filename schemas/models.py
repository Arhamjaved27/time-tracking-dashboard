"""
schemas/models.py — All Pydantic request / response models for ShiftGlass Pro
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ── Enums ─────────────────────────────────────────────────────────────────────

class DayType(str, Enum):
    REGULAR  = "regular"   # Mon–Thu, Sat  → 8 h target
    FRIDAY   = "friday"    # Fri           → 7 h target
    SUNDAY   = "sunday"    # Sun           → Overtime (OT)
    HOLIDAY  = "holiday"   # Paid holiday  → historical-avg contribution


# ── Settings ──────────────────────────────────────────────────────────────────

class UserSettings(BaseModel):
    monthly_salary_pkr: float = Field(..., gt=0, description="Gross monthly salary in PKR")
    cycle_start_date: date      = Field(..., description="First day of the pay cycle (YYYY-MM-DD)")

    @field_validator("monthly_salary_pkr")
    @classmethod
    def salary_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("monthly_salary_pkr must be positive")
        return v

class UserSettingsResponse(UserSettings):
    hourly_rate_pkr: float = Field(..., description="Derived hourly rate (salary / 26 / 8)")


# ── Work Log ──────────────────────────────────────────────────────────────────

class LogEntryRequest(BaseModel):
    log_date: date           = Field(..., description="Date being logged (YYYY-MM-DD)")
    work_hours: int          = Field(..., ge=0, le=23, description="Whole hours worked")
    work_minutes: int        = Field(0,   ge=0, le=59, description="Additional minutes worked")
    break_hours: int         = Field(0,   ge=0, le=23, description="Whole hours on break")
    break_minutes: int       = Field(0,   ge=0, le=59, description="Additional minutes on break")
    notes: Optional[str]     = Field(None, max_length=500)

class LogEntryResponse(BaseModel):
    log_date: date
    day_type: DayType
    work_decimal: float      = Field(..., description="Total work time in decimal hours (e.g. 2.25)")
    break_decimal: float     = Field(..., description="Break time in decimal hours")
    net_decimal: float       = Field(..., description="work_decimal − break_decimal")
    target_hours: float      = Field(..., description="Daily target (8 / 7 / OT)")
    delta_hours: float       = Field(..., description="net_decimal − target_hours  (+ ahead / − behind)")
    earnings_pkr: float      = Field(..., description="Estimated earnings for this day")
    notes: Optional[str]


# ── Holiday ───────────────────────────────────────────────────────────────────

class HolidayRequest(BaseModel):
    holiday_date: date       = Field(..., description="Date to mark as paid holiday")
    label: Optional[str]     = Field(None, max_length=100, description="Holiday name/label")

class HolidayResponse(HolidayRequest):
    historical_avg_hours: float = Field(..., description="Avg daily hours used for this holiday's contribution")


# ── Analytics ─────────────────────────────────────────────────────────────────

class DailySummary(BaseModel):
    log_date: date
    day_type: DayType
    net_decimal: float
    target_hours: float
    delta_hours: float
    earnings_pkr: float

class MonthlySummary(BaseModel):
    cycle_start: date
    cycle_end: date
    total_worked_hours: float
    total_break_hours: float
    total_target_hours: float
    total_delta_hours: float       # positive = ahead, negative = behind
    days_logged: int
    paid_holidays: int
    overtime_days: int
    estimated_earnings_pkr: float
    monthly_salary_pkr: float
    progress_percent: float        # (total_worked / total_target) * 100
    daily_summaries: list[DailySummary]

class ProgressRing(BaseModel):
    percent: float
    status: str                    # "Ahead", "On Track", "Behind"
    color_hex: str                 # green / amber / red
    hours_ahead_behind: float
