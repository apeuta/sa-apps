"""
Portal SA MVP — Backend FastAPI Application
Entry point utama untuk API backend.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.core.exceptions import register_exception_handlers
from app.core.rate_limiter import RateLimiterMiddleware
from app.schemas.response import success_response
from app.services.gemini_adapter import GeminiAdapter
from app.services.llm_provider import llm_factory

# Import semua model agar terdaftar di Base.metadata
from app.models import (  # noqa: F401
    User, Project, Document, ActivityLog,
    NotificationLog, AuditLog, SLATracking,
)
from app.api.auth import router as auth_router
from app.api.scoring import router as scoring_router
from app.api.projects import router as projects_router
from app.api.assignment import router as assignment_router
from app.api.workflow import router as workflow_router
from app.api.documents import router as documents_router
from app.api.dq_number import router as dq_number_router
from app.api.activity_logs import router as activity_logs_router
from app.api.calendar import router as calendar_router
from app.api.sla import router as sla_router
from app.api.notifications import router as notifications_router
from app.api.handover import router as handover_router
from app.api.admin import router as admin_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API untuk Portal SA MVP — Manajemen Proyek Pre-Sales & Activity Log",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Konfigurasi CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter middleware (100 req/min/user, sliding window)
app.add_middleware(RateLimiterMiddleware)

# Daftarkan custom exception handlers agar semua response pakai format standar
register_exception_handlers(app)

# Register API routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(scoring_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(assignment_router, prefix="/api/v1")
app.include_router(workflow_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(dq_number_router, prefix="/api/v1")
app.include_router(activity_logs_router, prefix="/api/v1")
app.include_router(calendar_router, prefix="/api/v1")
app.include_router(sla_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(handover_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_create_tables():
    """
    Buat semua tabel database jika belum ada.
    Ini memastikan tabel selalu tersedia bahkan jika Alembic migration
    belum dijalankan secara manual (misalnya di deployment baru).
    create_all() bersifat idempotent — hanya membuat tabel yang belum ada.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables checked/created successfully.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}", exc_info=True)

    # Register LLM adapter agar scoring engine dan summarize bisa berfungsi
    try:
        llm_factory.register_adapter("gemini", GeminiAdapter)
        logger.info("GeminiAdapter registered in LLM factory.")
    except Exception as e:
        logger.error(f"Failed to register GeminiAdapter: {e}", exc_info=True)


@app.get("/health")
async def health_check():
    """
    Health check endpoint untuk Docker dan monitoring.
    Tidak memerlukan autentikasi.
    """
    return success_response(
        data={"api": "healthy", "database": "healthy"},
        message="Service berjalan normal.",
    )
