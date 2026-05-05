"""
api/routes/analytics.py — Monthly summary and progress-ring endpoints
"""

from fastapi import APIRouter, HTTPException

from schemas.models import MonthlySummary, ProgressRing
from services.analytics_service import build_monthly_summary, build_progress_ring
from store.memory_store import store

router = APIRouter()


def _require_settings():
    s = store.get_settings()
    if not s:
        raise HTTPException(status_code=400, detail="Save your settings first via POST /api/v1/settings")
    return s


@router.get("/summary", response_model=MonthlySummary, summary="Full monthly analytics")
def monthly_summary():
    """
    Returns a complete month-to-date breakdown including:
    - Total hours worked / on break
    - Ahead / Behind delta
    - Estimated PKR earnings
    - Per-day summaries (including paid holiday fill-ins)
    """
    s       = _require_settings()
    summary = build_monthly_summary(
        cycle_start     = s["cycle_start_date"],
        monthly_salary  = s["monthly_salary_pkr"],
        log_entries     = store.all_logs(),
        holidays        = store.all_holidays(),
    )
    return summary


@router.get("/progress-ring", response_model=ProgressRing, summary="Progress ring data for the dashboard")
def progress_ring():
    """
    Returns percent complete, Ahead/Behind/On-Track status, and the colour
    to render in the SVG progress ring.
    """
    s       = _require_settings()
    summary = build_monthly_summary(
        cycle_start     = s["cycle_start_date"],
        monthly_salary  = s["monthly_salary_pkr"],
        log_entries     = store.all_logs(),
        holidays        = store.all_holidays(),
    )
    return build_progress_ring(summary)
