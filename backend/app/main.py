"""
Haven Pet — FastAPI application entry point.
Sets up CORS, lifespan events, and registers all API routers.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # For SQLite dev: create tables directly (Alembic handles prod migrations)
    if settings.DATABASE_URL.startswith("sqlite"):
        async with engine.begin() as conn:
            # Import all models so they're registered with Base
            from app.models import (  # noqa: F401
                user, pet, vaccination, medication,
                behavior_log, recommendation, chat_message, notification,
            )
            await conn.run_sync(Base.metadata.create_all)
            # Migration check: add phone column if missing in existing table
            from sqlalchemy import text
            try:
                await conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(30)"))
            except Exception:
                pass




    # Start the APScheduler for proactive reminders
    from app.agents.reminder_agent import start_scheduler
    start_scheduler()

    yield

    # Shutdown: stop scheduler
    from app.agents.reminder_agent import stop_scheduler
    stop_scheduler()

    await engine.dispose()


app = FastAPI(
    title="Haven Pet API",
    description="AI-powered pet care assistant — REST API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend origins (local dev on any port & configured domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists before mounting static files
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ── Register API routers ──────────────────────────────────────────────
from app.api.v1 import auth, pets, vaccinations, medications  # noqa: E402
from app.api.v1 import behavior_logs, chat, recommendations  # noqa: E402
from app.api.v1 import notifications, reports, ml  # noqa: E402

API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX, tags=["Auth"])
app.include_router(pets.router, prefix=API_PREFIX, tags=["Pets"])
app.include_router(vaccinations.router, prefix=API_PREFIX, tags=["Vaccinations"])
app.include_router(medications.router, prefix=API_PREFIX, tags=["Medications"])
app.include_router(behavior_logs.router, prefix=API_PREFIX, tags=["Behavior Logs"])
app.include_router(chat.router, prefix=API_PREFIX, tags=["AI Chat"])
app.include_router(recommendations.router, prefix=API_PREFIX, tags=["Recommendations"])
app.include_router(notifications.router, prefix=API_PREFIX, tags=["Notifications"])
app.include_router(reports.router, prefix=API_PREFIX, tags=["Reports"])
app.include_router(ml.router, prefix=API_PREFIX, tags=["ML"])


@app.api_route("/", methods=["GET", "HEAD"], tags=["Health"])
async def root():
    """Health check endpoint."""
    return {"status": "ok", "app": "Haven Pet", "version": "1.0.0"}
