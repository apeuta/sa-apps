"""
API endpoints untuk Document Tracking.
Menangani CRUD dokumen proyek dan state machine transisi status.

State Machine:
- Draft → Reviewed: SA, Lead_SA
- Reviewed → Final: SA, Lead_SA
- Final → Reviewed (mundur): HANYA Lead_SA
- Reviewed → Draft (mundur): HANYA Lead_SA
- Draft → Final (loncat): DITOLAK untuk semua role
"""

import random
import string
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.document import Document
from app.models.project import Project
from app.models.user import User
from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentStatusUpdate,
)
from app.schemas.response import error_response, success_response

router = APIRouter(tags=["Documents"])


def _generate_doc_id() -> str:
    """Generate ID dokumen unik dengan format DOC-{YYYYMMDD}-{random6}."""
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"DOC-{date_part}-{random_part}"


# Definisi transisi yang valid dalam state machine
VALID_TRANSITIONS = {
    "Draft": ["Reviewed"],       # Draft hanya bisa maju ke Reviewed
    "Reviewed": ["Final"],       # Reviewed hanya bisa maju ke Final
    "Final": [],                 # Final tidak bisa maju (terminal state untuk forward)
}

# Transisi mundur — hanya bisa dilakukan oleh Lead_SA
BACKWARD_TRANSITIONS = {
    "Final": ["Reviewed"],       # Final bisa mundur ke Reviewed (Lead_SA only)
    "Reviewed": ["Draft"],       # Reviewed bisa mundur ke Draft (Lead_SA only)
    "Draft": [],                 # Draft tidak bisa mundur
}


@router.post(
    "/projects/{project_id}/documents",
    summary="Buat dokumen baru untuk proyek",
    description=(
        "Membuat entry dokumen baru dengan status awal 'Draft'. "
        "Memvalidasi bahwa proyek ada sebelum membuat dokumen."
    ),
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    project_id: str,
    body: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Buat dokumen baru untuk proyek tertentu.

    Flow:
    1. Validasi proyek ada di database
    2. Generate id_doc unik
    3. Set status awal "Draft"
    4. Simpan ke database
    """
    # Validasi proyek ada
    project_result = await db.execute(
        select(Project).where(Project.id_project == project_id)
    )
    project = project_result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proyek dengan ID '{project_id}' tidak ditemukan.",
        )

    # Generate ID dokumen dan timestamp
    now = datetime.now(timezone.utc)
    doc_id = _generate_doc_id()

    # Buat record dokumen baru
    new_document = Document(
        id_doc=doc_id,
        id_project=project_id,
        doc_type=body.doc_type.value,
        status="Draft",
        gdrive_link=body.gdrive_link,
        folder_type=body.folder_type.value,
        notes=body.notes,
        created_by=current_user.id,
        updated_by=None,
        created_at=now,
        updated_at=now,
    )
    db.add(new_document)
    await db.commit()
    await db.refresh(new_document)

    # Format response
    response_data = DocumentResponse(
        id_doc=new_document.id_doc,
        id_project=new_document.id_project,
        doc_type=new_document.doc_type,
        status=new_document.status,
        gdrive_link=new_document.gdrive_link,
        folder_type=new_document.folder_type,
        notes=new_document.notes,
        created_by=new_document.created_by,
        updated_by=new_document.updated_by,
        created_at=new_document.created_at,
        updated_at=new_document.updated_at,
    ).model_dump(mode="json")

    return success_response(
        data=response_data,
        message=f"Dokumen '{body.doc_type.value}' berhasil dibuat untuk proyek '{project_id}'.",
    )


@router.get(
    "/projects/{project_id}/documents",
    summary="Daftar dokumen proyek",
    description="Menampilkan semua dokumen yang terkait dengan proyek tertentu.",
)
async def list_project_documents(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ambil daftar semua dokumen untuk proyek tertentu.
    Diurutkan berdasarkan waktu pembuatan (terbaru di atas).
    """
    # Validasi proyek ada
    project_result = await db.execute(
        select(Project).where(Project.id_project == project_id)
    )
    project = project_result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proyek dengan ID '{project_id}' tidak ditemukan.",
        )

    # Query semua dokumen untuk proyek ini
    result = await db.execute(
        select(Document)
        .where(Document.id_project == project_id)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()

    # Format response
    documents_data = [
        DocumentResponse(
            id_doc=doc.id_doc,
            id_project=doc.id_project,
            doc_type=doc.doc_type,
            status=doc.status,
            gdrive_link=doc.gdrive_link,
            folder_type=doc.folder_type,
            notes=doc.notes,
            created_by=doc.created_by,
            updated_by=doc.updated_by,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        ).model_dump(mode="json")
        for doc in documents
    ]

    return success_response(
        data={"documents": documents_data, "total": len(documents_data)},
        message=f"Ditemukan {len(documents_data)} dokumen untuk proyek '{project_id}'.",
    )


@router.patch(
    "/documents/{doc_id}/status",
    summary="Update status dokumen (state machine)",
    description=(
        "Mengubah status dokumen mengikuti aturan state machine. "
        "Transisi maju: Draft → Reviewed → Final (SA & Lead_SA). "
        "Transisi mundur: hanya Lead_SA. "
        "Loncat (Draft → Final): ditolak."
    ),
)
async def update_document_status(
    doc_id: str,
    body: DocumentStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update status dokumen dengan enforcement state machine.

    Rules:
    - Transisi maju (Draft→Reviewed, Reviewed→Final): SA dan Lead_SA
    - Transisi mundur (Final→Reviewed, Reviewed→Draft): hanya Lead_SA
    - Loncat (Draft→Final): ditolak untuk semua role
    - Status "Final" hanya bisa diubah oleh Lead_SA
    - Catat timestamp dan user pada setiap transisi
    """
    # Cari dokumen
    doc_result = await db.execute(
        select(Document).where(Document.id_doc == doc_id)
    )
    document = doc_result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dokumen dengan ID '{doc_id}' tidak ditemukan.",
        )

    current_status = document.status
    new_status = body.new_status.value

    # Cek jika status sama — tidak perlu transisi
    if current_status == new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dokumen sudah berstatus '{current_status}'. Tidak ada perubahan.",
        )

    # Cek proteksi: status "Final" hanya bisa diubah oleh Lead_SA
    if current_status == "Final" and current_user.role != "Lead_SA":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Hanya Lead_SA yang dapat mengubah status dokumen yang sudah 'Final'."
            ),
        )

    # Cek apakah transisi maju yang valid
    is_forward = new_status in VALID_TRANSITIONS.get(current_status, [])

    # Cek apakah transisi mundur yang valid (hanya Lead_SA)
    is_backward = new_status in BACKWARD_TRANSITIONS.get(current_status, [])

    if is_forward:
        # Transisi maju — SA dan Lead_SA boleh
        pass
    elif is_backward:
        # Transisi mundur — hanya Lead_SA
        if current_user.role != "Lead_SA":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Hanya Lead_SA yang dapat melakukan transisi mundur. "
                    f"Transisi '{current_status}' → '{new_status}' memerlukan role Lead_SA."
                ),
            )
    else:
        # Transisi tidak valid (loncat atau arah yang tidak dikenali)
        valid_forward = VALID_TRANSITIONS.get(current_status, [])
        valid_backward = BACKWARD_TRANSITIONS.get(current_status, [])
        all_valid = valid_forward + valid_backward

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Transisi status tidak valid: '{current_status}' → '{new_status}'. "
                f"Dari status '{current_status}', transisi yang diizinkan: "
                f"{all_valid if all_valid else 'tidak ada (terminal state)'}."
            ),
        )

    # Update status, timestamp, dan user
    now = datetime.now(timezone.utc)
    document.status = new_status
    document.updated_at = now
    document.updated_by = current_user.id

    await db.commit()
    await db.refresh(document)

    # Format response
    response_data = DocumentResponse(
        id_doc=document.id_doc,
        id_project=document.id_project,
        doc_type=document.doc_type,
        status=document.status,
        gdrive_link=document.gdrive_link,
        folder_type=document.folder_type,
        notes=document.notes,
        created_by=document.created_by,
        updated_by=document.updated_by,
        created_at=document.created_at,
        updated_at=document.updated_at,
    ).model_dump(mode="json")

    return success_response(
        data=response_data,
        message=(
            f"Status dokumen '{doc_id}' berhasil diubah: "
            f"'{current_status}' → '{new_status}'."
        ),
    )
