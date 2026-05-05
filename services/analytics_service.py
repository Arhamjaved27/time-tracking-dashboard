"""
services/analytics_service.py — Pure business logic for ShiftGlass Pro
No FastAPI imports; fully testable in isolation.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Optional

from core.config import settings
from schemas.models import DayType, LogEntryResponse, MonthlySummary, ProgressRing


# ── Helpers ───────────────────────────────────────────────────────────────────

def to_decimal(hours: int, minutes: int) -> float:
    """Convert h + m → decimal hours, rounded to 2 dp."""
    return round(hours + minutes / 60, 2)


def get_day_type(d: date) -> DayType:
    """0=Mon … 6=Sun"""
    wd = d.weekday()
    if wd == 4:
        return DayType.FRIDAY
    if wd == 6:
        return DayType.SUNDAY
    return DayType.REGULAR


def target_hours_for_type(day_type: DayType) -> float:
    if day_type == DayType.FRIDAY:
        return settings.FRIDAY_HOURS
    if day_type == DayType.SUNDAY:
        return 0.0          # OT — no mandatory target
    return settings.REGULAR_DAY_HOURS


def hourly_rate(monthly_salary: float) -> float:
    """PKR per hour based on 26-day, 8-hour standard."""
    return round(monthly_salary / (settings.WORK_DAYS_PER_MONTH * settings.REGULAR_DAY_HOURS), 4)


# ── Log computation ───────────────────────────────────────────────────────────

def compute_log_entry(
    log_date: date,
    work_hours: int,
    work_minutes: int,
    break_hours: int,
    break_minutes: int,
    monthly_salary: float,
    notes: Optional[str] = None,
) -> LogEntryResponse:
    day_type      = get_day_type(log_date)
    work_dec      = to_decimal(work_hours, work_minutes)
    break_dec     = to_decimal(break_hours, break_minutes)
    net_dec       = round(max(work_dec - break_dec, 0.0), 2)
    target        = target_hours_for_type(day_type)
    delta         = round(net_dec - target, 2)
    rate          = hourly_rate(monthly_salary)
    earnings      = round(net_dec * rate, 2)

    return LogEntryResponse(
        log_date      = log_date,
        day_type      = day_type,
        work_decimal  = work_dec,
        break_decimal = break_dec,
        net_decimal   = net_dec,
        target_hours  = target,
        delta_hours   = delta,
        earnings_pkr  = earnings,
        notes         = notes,
    )


# ── Monthly analytics ─────────────────────────────────────────────────────────

def build_monthly_summary(
    cycle_start: date,
    monthly_salary: float,
    log_entries: list[dict],      # raw dicts from in-memory store
    holidays: list[dict],         # raw dicts from in-memory store
) -> MonthlySummary:
    rate          = hourly_rate(monthly_salary)
    cycle_end     = _last_day_of_cycle(cycle_start)  # For reference, not used
    today         = date.today()
    cutoff        = today  # Always up to today

    # Build a date → log map
    log_map: dict[date, dict] = {e["log_date"]: e for e in log_entries}
    holiday_dates: set[date]  = {h["holiday_date"] for h in holidays}

    # Historical avg from logged days (for holiday fill-in)
    logged_nets   = [e["net_decimal"] for e in log_entries if e["log_date"] not in holiday_dates]
    hist_avg      = round(sum(logged_nets) / len(logged_nets), 2) if logged_nets else settings.REGULAR_DAY_HOURS

    total_worked  = 0.0
    total_break   = 0.0
    total_target  = 0.0
    total_earn    = 0.0
    ot_days       = 0
    daily_list    = []

    d = cycle_start
    while d <= cutoff:
        day_type = DayType.HOLIDAY if d in holiday_dates else get_day_type(d)
        target   = target_hours_for_type(day_type) if day_type != DayType.HOLIDAY else 0.0

        if day_type == DayType.HOLIDAY:
            net_dec  = hist_avg
            earnings = round(net_dec * rate, 2)
            delta    = 0.0
            break_dec = 0.0
        elif d in log_map:
            e         = log_map[d]
            net_dec   = e["net_decimal"]
            break_dec = e["break_decimal"]
            earnings  = round(net_dec * rate, 2)
            delta     = round(net_dec - target, 2)
        else:
            total_target += target
            d += timedelta(days=1)
            continue  # unlogged workday / future day still contributes to monthly target

        if day_type == DayType.SUNDAY:
            ot_days += 1

        total_worked += net_dec
        total_break  += break_dec if day_type != DayType.HOLIDAY else 0.0
        total_target += target
        total_earn   += earnings

        from schemas.models import DailySummary
        daily_list.append(DailySummary(
            log_date    = d,
            day_type    = day_type,
            net_decimal = net_dec,
            target_hours= target,
            delta_hours = delta,
            earnings_pkr= earnings,
        ))
        d += timedelta(days=1)

    progress = round((total_worked / total_target * 100) if total_target else 0.0, 1)

    return MonthlySummary(
        cycle_start           = cycle_start,
        cycle_end             = cycle_end,
        total_worked_hours    = round(total_worked, 2),
        total_break_hours     = round(total_break, 2),
        total_target_hours    = round(total_target, 2),
        total_delta_hours     = round(total_worked - total_target, 2),
        days_logged           = len(daily_list),
        paid_holidays         = len(holiday_dates),
        overtime_days         = ot_days,
        estimated_earnings_pkr= round(total_earn, 2),
        monthly_salary_pkr    = monthly_salary,
        progress_percent      = progress,
        daily_summaries       = daily_list,
    )


def build_progress_ring(summary: MonthlySummary) -> ProgressRing:
    delta = summary.total_delta_hours
    if delta >= 0:
        status = "Ahead" if delta > 0 else "On Track"
        color  = "#22c55e"   # green
    else:
        status = "Behind"
        color  = "#ef4444" if delta < -2 else "#f59e0b"  # red or amber

    return ProgressRing(
        percent           = summary.progress_percent,
        status            = status,
        color_hex         = color,
        hours_ahead_behind= round(abs(delta), 2),
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _last_day_of_cycle(start: date) -> date:
    """Return the last calendar day of the month that contains `start`."""
    if start.month == 12:
        return date(start.year + 1, 1, 1) - timedelta(days=1)
    return date(start.year, start.month + 1, 1) - timedelta(days=1)
