"""
Schema Pydantic untuk endpoint Collaborator pada proyek.
Digunakan untuk validasi request/response pada fitur manajemen kolaborator.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CollaboratorAddRequest(BaseModel):
    """Request body untuk menambahkan kolaborator ke proyek."""

    user_id: uuid.UUID = Field(
        ...,
        description="UUID dari user yang akan ditag sebagai kolaborator",
    )
    role: str = Field(
        default="viewer",
        description="Peran kolaborator: 'viewer' (lihat saja) atau 'contributor' (bisa tambah activity log)",
    )


class CollaboratorResponse(BaseModel):
    """Response data satu kolaborator."""

    id: uuid.UUID
    user_id: uuid.UUID
    user_name: str = Field(..., description="Nama lengkap kolaborator")
    user_email: str = Field(..., description="Email kolaborator")
    user_role: str = Field(..., description="Role sistem user (SA, Sales, Lead_SA, Admin)")
    role: str = Field(..., description="Peran kolaborator di proyek: viewer atau contributor")
    added_by_name: str = Field(..., description="Nama user yang menambahkan kolaborator")
    created_at: datetime


class CollaboratorListResponse(BaseModel):
    """Response daftar kolaborator suatu proyek."""

    items: list[CollaboratorResponse]
    total: int
