"""
API endpoints untuk Notification — manajemen notifikasi pengguna.

Endpoints:
- GET /notifications — Ambil daftar notifikasi user (paginated, terbaru dulu)
- PATCH /notifications/{id}/read — Tandai notifikasi sebagai dibaca
- GET /notifications/unread-count — Ambil jumlah notifikasi belum dibaca

Sesuai requirement 14.7, 14.8.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.response import error_response, success_response
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _build_notification_response(notification) -> dict:
    """Helper untuk membangun response dict dari NotificationLog model."""
    return {
        "id": notification.id,
        "event_type": notification.event_type,
        "channel": notification.channel,
        "status": notification.status,
        "reference_id": notification.reference_id,
        "metadata": notification.notification_metadata,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
        "read_at": notification.read_at.isoformat() if notification.read_at else None,
    }


@router.get(
    "",
    summary="Ambil daftar notifikasi user",
    description=(
        "Endpoint untuk mengambil riwayat notifikasi in-app pengguna. "
        "Diurutkan terbaru terlebih dahulu, dengan pagination (default 20/page)."
    ),
)
async def get_notifications(
    page: int = Query(default=1, ge=1, description="Halaman (1-based)"),
    per_page: int = Query(default=20, ge=1, le=20, description="Item per halaman (max 20)"),
    current_user: User = Depends(get_current_user),
):
    """
    Ambil daftar notifikasi in-app untuk user yang sedang login.

    Menampilkan notifikasi terbaru terlebih dahulu.
    Pagination: default 20 item per halaman.

    Requirement: 14.7
    """
    try:
        result = await notification_service.get_user_notifications(
            user_id=current_user.id,
            page=page,
            per_page=per_page,
        )

        # Build response items
        items = [_build_notification_response(n) for n in result["items"]]

        response_data = {
            "items": items,
            "total": result["total"],
            "page": result["page"],
            "per_page": result["per_page"],
        }

        return success_response(
            data=response_data,
            message=f"Notifikasi (halaman {page}, total: {result['total']}).",
        )

    except Exception as e:
        logger.error(f"Gagal mengambil notifikasi: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(message="Gagal mengambil notifikasi."),
        )


@router.patch(
    "/{notification_id}/read",
    summary="Tandai notifikasi sebagai dibaca",
    description=(
        "Endpoint untuk menandai notifikasi tertentu sebagai sudah dibaca. "
        "Hanya bisa dilakukan oleh pemilik notifikasi."
    ),
)
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Tandai notifikasi sebagai dibaca.

    Update status ke 'read' dan set read_at timestamp.
    Hanya bisa dilakukan oleh penerima notifikasi.

    Requirement: 14.8
    """
    try:
        await notification_service.mark_as_read(
            notification_id=notification_id,
            user_id=current_user.id,
        )

        return success_response(
            data={"id": notification_id, "status": "read"},
            message="Notifikasi berhasil ditandai sebagai dibaca.",
        )

    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(message=str(e)),
        )
    except Exception as e:
        logger.error(f"Gagal mark as read notifikasi {notification_id}: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(message="Gagal memperbarui notifikasi."),
        )


@router.get(
    "/unread-count",
    summary="Ambil jumlah notifikasi belum dibaca",
    description="Endpoint untuk mendapatkan jumlah notifikasi yang belum dibaca oleh user.",
)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
):
    """
    Ambil jumlah notifikasi in-app yang belum dibaca.

    Digunakan untuk badge counter di frontend.

    Requirement: 14.7
    """
    try:
        count = await notification_service.get_unread_count(user_id=current_user.id)

        return success_response(
            data={"unread_count": count},
            message=f"Anda memiliki {count} notifikasi belum dibaca.",
        )

    except Exception as e:
        logger.error(f"Gagal mengambil unread count: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(message="Gagal mengambil jumlah notifikasi."),
        )
