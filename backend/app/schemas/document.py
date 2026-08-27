"""
Schema Pydantic untuk endpoint Document Tracking.
Digunakan untuk validasi request/response pada fitur CRUD dan state machine dokumen.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

from pydantic import BaseModel, Field


class DocTypeEnum(str, Enum):
    """Tipe dokumen yang tersedia di sistem."""
    PropTek = "PropTek"
    BOQ = "BOQ"
    Mandays = "Mandays"
    MoM = "MoM"
    RFP = "RFP"
    HLD = "HLD"


class FolderTypeEnum(str, Enum):
    """Tipe folder penyimpanan dokumen di Google Drive."""
    Inventory = "Inventory"
    Diagram = "Diagram"
    Solutions = "Solutions"


class DocStatusEnum(str, Enum):
    """Status dokumen dalam state machine."""
    Draft = "Draft"
    Reviewed = "Reviewed"
    Final = "Final"


class DocumentCreate(BaseModel):
    """Request body untuk membuat dokumen baru."""

    doc_type: DocTypeEnum = Field(
        ...,
        description="Tipe dokumen: PropTek, BOQ, Mandays, MoM, RFP, HLD",
    )
    gdrive_link: str = Field(
        ...,
        min_length=1,
        description="Link Google Drive dokumen (wajib diisi)",
    )
    folder_type: FolderTypeEnum = Field(
        ...,
        description="Tipe folder penyimpanan: Inventory, Diagram, Solutions",
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Catatan tambahan untuk dokumen (maks 500 karakter)",
    )


class DocumentStatusUpdate(BaseModel):
    """Request body untuk mengubah status dokumen."""

    new_status: DocStatusEnum = Field(
        ...,
        description="Status baru dokumen: Draft, Reviewed, Final",
    )


class DocumentResponse(BaseModel):
    """Response data lengkap dokumen."""

    id_doc: str = Field(..., description="ID dokumen unik")
    id_project: str = Field(..., description="ID proyek pemilik dokumen")
    doc_type: str = Field(..., description="Tipe dokumen")
    status: str = Field(..., description="Status dokumen saat ini")
    gdrive_link: str = Field(..., description="Link Google Drive")
    folder_type: str = Field(..., description="Tipe folder penyimpanan")
    notes: Optional[str] = Field(None, description="Catatan tambahan")
    created_by: uuid.UUID = Field(..., description="User yang membuat dokumen")
    updated_by: Optional[uuid.UUID] = Field(None, description="User yang terakhir update")
    created_at: datetime = Field(..., description="Waktu pembuatan")
    updated_at: datetime = Field(..., description="Waktu update terakhir")
