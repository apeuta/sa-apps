"""
Schema Pydantic untuk entity Subtask (work item assignable per proyek).
Digunakan untuk validasi request/response pada fitur manajemen subtask.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SubtaskCreateRequest(BaseModel):
    """Request body untuk membuat subtask baru."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Deskripsi work item subtask",
    )


class SubtaskUpdateStatusRequest(BaseModel):
    """Request body untuk mengubah status subtask."""

    status: str = Field(
        ...,
        description="Status subtask; nilai valid: 'open', 'in_progress', 'done'",
    )


class SubtaskAssignRequest(BaseModel):
    """Request body untuk menugaskan (assign) subtask ke seorang SA."""

    assigned_sa: Optional[uuid.UUID] = Field(
        default=None,
        description="UUID SA yang ditugaskan; NULL untuk melepas penugasan",
    )


class SubtaskResponse(BaseModel):
    """Response data satu subtask."""

    id_subtask: str
    id_project: str
    title: str
    status: str
    assigned_sa: Optional[uuid.UUID] = None
    assigned_sa_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SubtaskListResponse(BaseModel):
    """Response daftar subtask suatu proyek."""

    items: list[SubtaskResponse]
    total: int
