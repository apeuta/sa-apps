"""
API endpoints untuk manajemen proyek pre-sales.
Menangani submission request baru oleh Sales termasuk file upload.
"""

import logging
import random
import string
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.project import Project
from app.models.user import User
from app.schemas.project import FileUploadResult, ProjectResponse
from app.schemas.response import error_response, success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])

# Konstanta file upload
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20MB
MAX_FILES = 5
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def _generate_project_id() -> str:
    """
    Generate ID proyek unik dengan format PRJ-{YYYYMMDD}-{random 6 chars}.
    Contoh: PRJ-20250101-A3X9K2
    """
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"PRJ-{date_part}-{random_part}"


def _validate_file_extension(filename: str) -> bool:
    """Cek apakah ekstensi file termasuk yang diizinkan."""
    if not filename:
        return False
    lower_name = filename.lower()
    return any(lower_name.endswith(ext) for ext in ALLOWED_EXTENSIONS)


async def _process_file_upload(file: UploadFile) -> tuple[FileUploadResult, Optional[bytes]]:
    """
    Proses satu file upload: validasi format dan ukuran.
    Return tuple (hasil validasi, konten file jika valid).
    """
    filename = file.filename or "unknown"

    # Validasi ekstensi file
    if not _validate_file_extension(filename):
        return FileUploadResult(
            filename=filename,
            success=False,
            error=f"Format file tidak valid. Hanya PDF dan DOCX yang diterima.",
        ), None

    # Validasi MIME type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        # Fallback: cek ekstensi saja (beberapa client tidak kirim MIME type yang benar)
        if not _validate_file_extension(filename):
            return FileUploadResult(
                filename=filename,
                success=False,
                error=f"MIME type '{content_type}' tidak didukung.",
            ), None

    # Baca konten file dan validasi ukuran
    try:
        content = await file.read()
        size_bytes = len(content)

        if size_bytes > MAX_FILE_SIZE_BYTES:
            size_mb = size_bytes / (1024 * 1024)
            return FileUploadResult(
                filename=filename,
                success=False,
                error=f"Ukuran file {size_mb:.1f}MB melebihi batas 20MB.",
                size_bytes=size_bytes,
            ), None

        if size_bytes == 0:
            return FileUploadResult(
                filename=filename,
                success=False,
                error="File kosong (0 bytes).",
                size_bytes=0,
            ), None

        return FileUploadResult(
            filename=filename,
            success=True,
            size_bytes=size_bytes,
        ), content

    except Exception as e:
        logger.error(f"Gagal membaca file '{filename}': {e}")
        return FileUploadResult(
            filename=filename,
            success=False,
            error=f"Gagal membaca file: {str(e)}",
        ), None


async def _trigger_scoring_engine(
    project_id: str,
    valid_files: list[tuple[str, bytes, str]],
) -> None:
    """
    Background task: trigger Scoring_Engine untuk analisis BANT.
    Dipanggil async setelah record proyek tersimpan (< 5 detik).

    Args:
        project_id: ID proyek yang baru dibuat.
        valid_files: List tuple (filename, content_bytes, mime_type).
    """
    logger.info(
        f"[ScoringEngine] Trigger scoring untuk proyek {project_id} "
        f"dengan {len(valid_files)} file."
    )
    # TODO: Implementasi lengkap di task 5.3 (Scoring_Engine)
    # Saat ini hanya log — scoring engine akan diimplementasikan terpisah
    try:
        # Placeholder: akan memanggil ScoringEngine.score_documents()
        # dari app.services.scoring_engine setelah task 5.3 selesai
        pass
    except Exception as e:
        logger.error(f"[ScoringEngine] Gagal memproses proyek {project_id}: {e}")


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Submit request proyek pre-sales baru",
    description=(
        "Endpoint untuk Sales mengajukan request proyek baru. "
        "Menerima form data + file attachment (PDF/DOCX, max 20MB/file, max 5 files). "
        "Membuat record project dengan status 'New' dan trigger scoring engine async."
    ),
)
async def create_project(
    background_tasks: BackgroundTasks,
    project_name: str = Form(
        ...,
        min_length=1,
        max_length=150,
        description="Nama proyek (wajib, max 150 karakter)",
    ),
    customer_name: str = Form(
        ...,
        min_length=1,
        max_length=150,
        description="Nama customer (wajib, max 150 karakter)",
    ),
    target_submit: date = Form(
        ...,
        description="Target tanggal submit (format: YYYY-MM-DD, tidak boleh masa lalu)",
    ),
    estimasi_nilai: str = Form(
        ...,
        description="Estimasi nilai proyek IDR (0.01 - 999,999,999,999.00)",
    ),
    files: list[UploadFile] = File(
        default=[],
        description="File attachment (PDF/DOCX, max 20MB/file, max 5 files)",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit request proyek pre-sales baru.

    Flow:
    1. Validasi input form (project_name, customer_name, target_submit, estimasi_nilai)
    2. Validasi file upload (format, ukuran, jumlah)
    3. Buat record Project dengan status "New"
    4. Trigger Scoring_Engine async jika ada file valid
    5. Return 201 dengan data proyek + hasil upload per file
    """
    # === Validasi manual untuk field yang diterima sebagai Form ===

    # Trim whitespace
    project_name = project_name.strip()
    customer_name = customer_name.strip()

    # Validasi field kosong setelah trim
    validation_errors = []

    if not project_name:
        validation_errors.append({"field": "project_name", "reason": "Nama proyek wajib diisi."})

    if not customer_name:
        validation_errors.append({"field": "customer_name", "reason": "Nama customer wajib diisi."})

    # Validasi target_submit tidak boleh masa lalu
    if target_submit < date.today():
        validation_errors.append({
            "field": "target_submit",
            "reason": "Target submit tidak boleh tanggal di masa lalu.",
        })

    # Validasi estimasi_nilai — parse Decimal dari string
    estimasi_decimal: Optional[Decimal] = None
    try:
        estimasi_decimal = Decimal(estimasi_nilai)
        if estimasi_decimal < Decimal("0.01"):
            validation_errors.append({
                "field": "estimasi_nilai",
                "reason": "Estimasi nilai minimum adalah 0.01.",
            })
        elif estimasi_decimal > Decimal("999999999999.00"):
            validation_errors.append({
                "field": "estimasi_nilai",
                "reason": "Estimasi nilai maksimum adalah 999,999,999,999.00.",
            })
    except (InvalidOperation, ValueError):
        validation_errors.append({
            "field": "estimasi_nilai",
            "reason": "Format estimasi nilai tidak valid. Gunakan angka desimal.",
        })

    # Validasi jumlah file
    if len(files) > MAX_FILES:
        validation_errors.append({
            "field": "files",
            "reason": f"Maksimal {MAX_FILES} file per request.",
        })

    # Return 422 jika ada error validasi
    if validation_errors:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response(
                message="Validasi gagal. Periksa data yang dikirim.",
                data=validation_errors,
            ),
        )

    # === Proses file upload (partial failure handling) ===
    file_results: list[FileUploadResult] = []
    valid_files_data: list[tuple[str, bytes, str]] = []  # (filename, content, mime_type)

    for file in files:
        result, content = await _process_file_upload(file)
        file_results.append(result)
        if result.success and content is not None:
            mime_type = file.content_type or "application/octet-stream"
            valid_files_data.append((file.filename or "unknown", content, mime_type))

    # === Buat record Project ===
    project_id = _generate_project_id()
    now = datetime.now(timezone.utc)

    new_project = Project(
        id_project=project_id,
        project_name=project_name,
        customer_name=customer_name,
        target_submit=target_submit,
        status="New",
        sales_pic=current_user.id,
        created_at=now,
        updated_at=now,
    )

    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    logger.info(
        f"Proyek baru dibuat: {project_id} oleh {current_user.email} "
        f"({len(valid_files_data)} file valid dari {len(files)} total)"
    )

    # === Trigger Scoring Engine async (< 5 detik setelah record tersimpan) ===
    scoring_triggered = False
    message_bant: Optional[str] = None

    if valid_files_data:
        # Ada file valid — trigger scoring engine di background
        background_tasks.add_task(
            _trigger_scoring_engine,
            project_id,
            valid_files_data,
        )
        scoring_triggered = True
    else:
        # Tidak ada file valid — arahkan ke BANT manual (requirement 2.7)
        message_bant = (
            "Tidak ada file attachment valid. "
            "Silakan gunakan opsi 'Isi BANT Manual' untuk melanjutkan scoring."
        )

    # === Build response ===
    response_data = ProjectResponse(
        id_project=project_id,
        project_name=project_name,
        customer_name=customer_name,
        target_submit=target_submit,
        estimasi_nilai=estimasi_decimal,
        status="New",
        sales_pic=current_user.id,
        created_at=now,
        files=file_results,
        scoring_triggered=scoring_triggered,
        message_bant=message_bant,
    )

    return success_response(
        data=response_data.model_dump(mode="json"),
        message="Request proyek berhasil dibuat.",
    )
