"""
Custom exception handlers untuk FastAPI.
Memastikan SEMUA response (termasuk error) mengikuti format standar:
{"status": "error", "data": ..., "message": "..."}
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.response import error_response


def register_exception_handlers(app: FastAPI) -> None:
    """
    Daftarkan semua custom exception handler ke aplikasi FastAPI.
    Dipanggil dari main.py saat inisialisasi app.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """
        Handler untuk semua HTTPException (termasuk 401, 403, 404, dll).
        Mengubah response ke format standar.
        """
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                message=str(exc.detail),
            ),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handler untuk error validasi Pydantic (422).
        Mengembalikan detail error per-field dalam format standar.
        """
        # Konversi error Pydantic ke format per-field
        field_errors = []
        for error in exc.errors():
            # Ambil lokasi field (bisa nested, ambil element terakhir)
            loc = error.get("loc", [])
            # Skip "body" prefix dari lokasi
            field_parts = [str(part) for part in loc if part != "body"]
            field_name = ".".join(field_parts) if field_parts else "unknown"

            field_errors.append({
                "field": field_name,
                "reason": error.get("msg", "Validation error"),
            })

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response(
                message="Validasi gagal. Periksa data yang dikirim.",
                data=field_errors,
            ),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Catch-all handler untuk error yang tidak tertangkap.
        Mengembalikan 500 Internal Server Error dalam format standar.
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                message="Terjadi kesalahan internal server.",
            ),
        )
