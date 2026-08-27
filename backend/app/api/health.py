"""
Health check endpoint untuk monitoring status service.
Mengecek koneksi database dan status API.
Response time harus < 5 detik (sesuai requirement 10.5).
"""

from fastapi import APIRouter

from app.core.database import check_database_health

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    Mengecek status database (asyncpg) dan API.
    Return format sesuai standar: {"status": "success", "data": {...}, "message": "..."}
    """
    # Cek koneksi database
    db_healthy = await check_database_health()
    db_status = "healthy" if db_healthy else "unhealthy"

    # API selalu healthy jika endpoint ini bisa merespons
    api_status = "healthy"

    return {
        "status": "success",
        "data": {
            "database": db_status,
            "api": api_status,
        },
        "message": "Health check berhasil",
    }
