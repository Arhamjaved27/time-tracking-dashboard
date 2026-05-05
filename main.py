"""
ShiftGlass Pro — FastAPI Backend
Work Analytics Dashboard for Freelancers & Contract Employees
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from api.routes import settings, logs, analytics, holidays
from core.config import settings as app_settings

app = FastAPI(
    title="ShiftGlass Pro",
    description="High-performance single-session work analytics dashboard for freelancers.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(settings.router,  prefix="/api/v1/settings",  tags=["Settings"])
app.include_router(logs.router,      prefix="/api/v1/logs",      tags=["Work Logs"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(holidays.router,  prefix="/api/v1/holidays",  tags=["Holidays"])

# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_dashboard():
    """Serve the ShiftGlass Pro glass-morphism dashboard."""
    from pathlib import Path
    html_path = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "app": "ShiftGlass Pro", "version": "1.0.0"}
