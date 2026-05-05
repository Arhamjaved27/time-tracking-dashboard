# ShiftGlass Pro — FastAPI Project

> High-performance work analytics dashboard for freelancers & contract employees.

---

## Project Structure

```
shiftglass_pro/
│
├── main.py                          # FastAPI app entry-point
├── requirements.txt
│
├── core/
│   └── config.py                    # App-wide settings (Pydantic BaseSettings)
│
├── schemas/
│   └── models.py                    # All Pydantic request/response models
│
├── services/
│   └── analytics_service.py         # Pure business logic (no FastAPI deps)
│
├── store/
│   └── memory_store.py              # Thread-safe in-memory state (single session)
│
├── api/
│   └── routes/
│       ├── settings.py              # POST/GET  /api/v1/settings
│       ├── logs.py                  # CRUD      /api/v1/logs
│       ├── analytics.py             # GET       /api/v1/analytics/summary | progress-ring
│       └── holidays.py              # CRUD      /api/v1/holidays
│
└── static/
    └── index.html                   # Glass-morphism dashboard (HTML + Vanilla JS)
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** for the dashboard.
Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## API Reference

### Settings
| Method | Endpoint              | Description                        |
|--------|-----------------------|------------------------------------|
| POST   | /api/v1/settings/     | Save salary + cycle start date     |
| GET    | /api/v1/settings/     | Retrieve current settings          |

### Work Logs
| Method | Endpoint              | Description                        |
|--------|-----------------------|------------------------------------|
| POST   | /api/v1/logs/         | Add / update a day's log           |
| GET    | /api/v1/logs/         | List all logged days               |
| GET    | /api/v1/logs/{date}   | Get a single day's log             |
| DELETE | /api/v1/logs/{date}   | Delete a day's log                 |

### Analytics
| Method | Endpoint                         | Description                     |
|--------|----------------------------------|---------------------------------|
| GET    | /api/v1/analytics/summary        | Full monthly summary            |
| GET    | /api/v1/analytics/progress-ring  | Progress ring data (SVG-ready)  |

### Holidays
| Method | Endpoint                  | Description                      |
|--------|---------------------------|----------------------------------|
| POST   | /api/v1/holidays/         | Mark a date as paid holiday      |
| GET    | /api/v1/holidays/         | List all holidays                |
| DELETE | /api/v1/holidays/{date}   | Remove a holiday                 |

---

## Key Design Decisions

| Concern              | Decision                                                                 |
|----------------------|--------------------------------------------------------------------------|
| **Day detection**    | Auto-detected from calendar weekday (Fri=7h, Sun=OT, else=8h)           |
| **Decimal time**     | `h + m/60`, rounded to 2 dp (e.g. 2h 15m → 2.25)                       |
| **Hourly rate**      | `monthly_salary / (26 days × 8 hrs)`                                    |
| **Holiday credit**   | Historical average net hours from all logged days                        |
| **State layer**      | In-memory `MemoryStore` singleton — swap for SQLite/PostgreSQL in prod   |
| **Frontend storage** | `localStorage` for persistence across refreshes without a DB            |
| **UI**               | Glass-morphism with Tailwind CSS + FontAwesome + Google Fonts            |

---

## Environment Variables (`.env`)

```env
WORK_DAYS_PER_MONTH=26
REGULAR_DAY_HOURS=8.0
FRIDAY_HOURS=7.0
CURRENCY=PKR
```

All variables have sensible defaults defined in `core/config.py`.
