"""
api/routes/settings.py — User settings endpoints
"""

from fastapi import APIRouter, HTTPException

from core.config import settings as cfg
from schemas.models import UserSettings, UserSettingsResponse
from services.analytics_service import hourly_rate
from store.sqlite_store import store

router = APIRouter()


@router.post("/", response_model=UserSettingsResponse, summary="Save user settings")
def save_settings(payload: UserSettings):
    """
    Store the monthly salary and cycle start date.
    Returns the derived hourly rate in PKR.
    """
    data = payload.model_dump()
    data["hourly_rate_pkr"] = hourly_rate(payload.monthly_salary_pkr)
    store.save_settings(data)
    return data


@router.get("/", response_model=UserSettingsResponse, summary="Get current settings")
def get_settings():
    """Retrieve the currently saved user settings."""
    s = store.get_settings()
    if not s:
        raise HTTPException(status_code=404, detail="No settings saved yet. POST /api/v1/settings first.")
    return s
