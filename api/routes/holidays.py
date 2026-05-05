"""
api/routes/holidays.py — Paid-holiday management endpoints
"""

from datetime import date

from fastapi import APIRouter, HTTPException, Path

from schemas.models import HolidayRequest, HolidayResponse
from services.analytics_service import hourly_rate
from store.memory_store import store

router = APIRouter()


def _historical_avg() -> float:
    logs = store.all_logs()
    holiday_dates = {h["holiday_date"] for h in store.all_holidays()}
    nets = [e["net_decimal"] for e in logs if e["log_date"] not in holiday_dates]
    return round(sum(nets) / len(nets), 2) if nets else 8.0


@router.post("/", response_model=HolidayResponse, summary="Mark a date as a paid holiday")
def add_holiday(payload: HolidayRequest):
    """
    Mark a date as a paid holiday.
    The historical average hours from logged days will be used to credit
    earnings for this holiday.
    """
    # Remove any existing log for this day so the holiday becomes the authoritative record.
    store.delete_log(payload.holiday_date)

    avg = _historical_avg()
    data = {
        "holiday_date": payload.holiday_date,
        "label": payload.label,
        "historical_avg_hours": avg,
    }
    store.add_holiday(payload.holiday_date, data)
    return data


@router.get("/", response_model=list[HolidayResponse], summary="List all marked holidays")
def list_holidays():
    return store.all_holidays()


@router.delete("/{holiday_date}", summary="Remove a paid holiday mark")
def remove_holiday(holiday_date: date = Path(..., description="Date in YYYY-MM-DD format")):
    if not store.remove_holiday(holiday_date):
        raise HTTPException(status_code=404, detail=f"{holiday_date} is not marked as a holiday.")
    return {"detail": f"Holiday on {holiday_date} removed."}
