"""
api/routes/logs.py — Work-log CRUD endpoints
"""

from datetime import date

from fastapi import APIRouter, HTTPException, Path

from schemas.models import LogEntryRequest, LogEntryResponse
from services.analytics_service import compute_log_entry
from store.memory_store import store

router = APIRouter()


def _require_settings():
    s = store.get_settings()
    if not s:
        raise HTTPException(status_code=400, detail="Save your settings first via POST /api/v1/settings")
    return s


@router.post("/", response_model=LogEntryResponse, summary="Add or update a work log")
def upsert_log(payload: LogEntryRequest):
    """
    Log hours + minutes for a given date. The system:
    - Converts h/m → decimal
    - Detects day type (Regular / Friday / Sunday OT / Holiday)
    - Calculates earnings and delta vs target
    """
    s         = _require_settings()
    response  = compute_log_entry(
        log_date        = payload.log_date,
        work_hours      = payload.work_hours,
        work_minutes    = payload.work_minutes,
        break_hours     = payload.break_hours,
        break_minutes   = payload.break_minutes,
        monthly_salary  = s["monthly_salary_pkr"],
        notes           = payload.notes,
    )
    store.upsert_log(payload.log_date, response.model_dump())
    return response


@router.get("/{log_date}", response_model=LogEntryResponse, summary="Get a single day's log")
def get_log(log_date: date = Path(..., description="Date in YYYY-MM-DD format")):
    entry = store.get_log(log_date)
    if not entry:
        raise HTTPException(status_code=404, detail=f"No log found for {log_date}")
    return entry


@router.get("/", response_model=list[LogEntryResponse], summary="List all logged days")
def list_logs():
    return store.all_logs()


@router.delete("/{log_date}", summary="Delete a work log")
def delete_log(log_date: date = Path(..., description="Date in YYYY-MM-DD format")):
    if not store.delete_log(log_date):
        raise HTTPException(status_code=404, detail=f"No log found for {log_date}")
    return {"detail": f"Log for {log_date} deleted."}
