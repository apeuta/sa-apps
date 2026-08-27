"""
API endpoints untuk Activity Log — pencatatan aktivitas harian SA.

Endpoints:
- POST /activity-logs — Buat activity log baru
- POST /activity-logs/{id}/polish — Re-trigger AI polishing
- GET /projects/{id}/story — Ambil project story timeline

Sesuai requirement 8.1–8.7.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.activity_log import (
    ActivityLogCreate,
    ActivityLogResponse,
    ProjectStoryResponse,
)
from app.schemas.response import error_response, success_response
from app.services.activity_logger import ActivityLogger

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Activity Logs"])


def _build_log_response(log) -> dict:
    """Helper untuk membangun response dict dari ActivityLog model."""
    return {
        "id_log": log.id_log,
        "id_project": log.id_project,
        "sa_id": str(log.sa_id),
        "subtask_category": log.subtask_category,
        "duration_hours": float(log.duration_hours),
        "raw_notes": log.raw_notes,
        "ai_polished_notes": log.ai_polished_notes,
        "gcal_event_id": log.gcal_event_id,
        "created_at": log.created_at.isoformat(),
        "needs_repolish": log.ai_polished_notes is None,
    }


@router.post(
    "/activity-logs",
    status_code=status.HTTP_201_CREATED,
    summary="Buat activity log baru",
    description=(
        "Endpoint untuk SA mencatat aktivitas harian pada proyek tertentu. "
        "Menerima project ID, subtask category, durasi, dan raw notes. "
        "AI akan otomatis memproses raw notes menjadi structured format."
    ),
)
async def create_activity_log(
    payload: ActivityLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Buat activity log baru.

    Flow:
    1. Validasi input (schema Pydantic)
    2. Validasi project_id ada di database
    3. Proses AI polishing untuk raw_notes
    4. Simpan record (dengan atau tanpa polished notes)
    5. Return 201 dengan data log

    Requirement: 8.1, 8.2, 8.3, 8.4, 8.6
    """
    try:
        activity_logger = ActivityLogger(db)

        # Buat log baru — service menangani validasi project dan AI polishing
        activity_log = await activity_logger.create_log(
            sa_id=current_user.id,
            id_project=payload.id_project,
            subtask_category=payload.subtask_category,
            duration_hours=payload.duration_hours,
            raw_notes=payload.raw_notes,
            gcal_event_id=payload.gcal_event_id,
        )

        # Build response
        response_data = _build_log_response(activity_log)

        # Tentukan pesan berdasarkan status polishing
        if activity_log.ai_polished_notes:
            message = "Activity log berhasil dibuat dan notes di-polish oleh AI."
        else:
            message = (
                "Activity log berhasil dibuat. AI polishing gagal — "
                "gunakan tombol 'Polish Ulang' untuk mencoba kembali."
            )

        return success_response(data=response_data, message=message)

    except ValueError as e:
        # Project tidak ditemukan atau validasi gagal
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response(message=str(e)),
        )
    except Exception as e:
        logger.error(f"Gagal membuat activity log: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(message="Gagal membuat activity log. Silakan coba lagi."),
        )


@router.post(
    "/activity-logs/{id_log}/polish",
    summary="Re-trigger AI polishing",
    description=(
        "Endpoint untuk SA memicu ulang proses AI polishing pada entry "
        "yang sebelumnya gagal. Menghasilkan structured notes dari raw_notes."
    ),
)
async def retry_polish_notes(
    id_log: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Re-trigger AI polishing untuk activity log tertentu.

    Digunakan saat polishing awal gagal dan SA ingin mencoba kembali.

    Requirement: 8.6
    """
    try:
        activity_logger = ActivityLogger(db)

        # Retry polish — service menangani validasi ownership
        activity_log = await activity_logger.retry_polish(
            id_log=id_log,
            sa_id=current_user.id,
        )

        response_data = _build_log_response(activity_log)

        if activity_log.ai_polished_notes:
            message = "AI polishing berhasil. Notes sudah diperbarui."
        else:
            message = "AI polishing masih gagal. Silakan coba lagi nanti."

        return success_response(data=response_data, message=message)

    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(message=str(e)),
        )
    except Exception as e:
        logger.error(f"Gagal retry polish log {id_log}: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(message="Gagal memproses ulang notes. Silakan coba lagi."),
        )


@router.get(
    "/projects/{id_project}/story",
    summary="Ambil project story timeline",
    description=(
        "Endpoint untuk menampilkan timeline aktivitas proyek. "
        "Mendukung filter berdasarkan subtask category dan rentang tanggal, "
        "dengan pagination maksimal 20 entry per halaman."
    ),
)
async def get_project_story(
    id_project: str,
    page: int = Query(default=1, ge=1, description="Halaman (1-based)"),
    page_size: int = Query(default=20, ge=1, le=20, description="Entry per halaman (max 20)"),
    category: Optional[str] = Query(
        default=None,
        description="Filter subtask category",
    ),
    date_from: Optional[datetime] = Query(
        default=None,
        description="Filter tanggal mulai (ISO 8601)",
    ),
    date_to: Optional[datetime] = Query(
        default=None,
        description="Filter tanggal akhir (ISO 8601)",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ambil project story sebagai timeline aktivitas.

    Menampilkan daftar activity log per proyek, diurutkan terbaru terlebih dahulu.
    Mendukung filter category dan rentang tanggal.

    Requirement: 8.5
    """
    try:
        activity_logger = ActivityLogger(db)

        # Ambil project story — service menangani validasi project
        result = await activity_logger.get_project_story(
            id_project=id_project,
            page=page,
            page_size=page_size,
            category=category,
            date_from=date_from,
            date_to=date_to,
        )

        # Build response items
        items = [_build_log_response(log) for log in result["items"]]

        response_data = {
            "items": items,
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
            "total_pages": result["total_pages"],
        }

        return success_response(
            data=response_data,
            message=f"Project story untuk {id_project} (halaman {page}/{result['total_pages']}).",
        )

    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(message=str(e)),
        )
    except Exception as e:
        logger.error(f"Gagal mengambil project story {id_project}: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(message="Gagal mengambil project story."),
        )
