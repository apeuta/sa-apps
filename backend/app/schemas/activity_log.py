"""
Pydantic schemas untuk Activity Log.
Validasi input dan format response sesuai requirement 8.x.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# Daftar subtask category yang valid (requirement 8.7)
VALID_SUBTASK_CATEGORIES = [
    "Meeting Pre-Sales",
    "Create PropTek",
    "Create BOQ",
    "Peer Review",
    "Internal Discussion",
    "Customer Workshop",
]


class ActionItem(BaseModel):
    """Item aksi hasil AI polishing."""

    description: str
    pic: Optional[str] = None


class AiPolishedNotes(BaseModel):
    """Format output AI polishing (requirement 8.3)."""

    discussion_points: list[str] = Field(
        default_factory=list,
        description="Daftar poin diskusi yang sudah di-polish",
    )
    action_items: list[ActionItem] = Field(
        default_factory=list,
        description="Daftar item aksi dengan deskripsi dan PIC",
    )


class ActivityLogCreate(BaseModel):
    """
    Schema validasi untuk pembuatan activity log baru (requirement 8.1, 8.2).

    Validasi:
    - id_project: wajib, string (FK ke projects)
    - subtask_category: wajib, harus dari daftar yang valid
    - duration_hours: 0.25–24.00, kelipatan 0.25
    - raw_notes: wajib, maksimal 5000 karakter
    - gcal_event_id: opsional, untuk mapping dari Google Calendar
    """

    id_project: str = Field(
        ...,
        min_length=1,
        description="ID proyek terkait (FK ke tabel projects)",
    )
    subtask_category: str = Field(
        ...,
        description="Kategori subtask aktivitas",
    )
    duration_hours: Decimal = Field(
        ...,
        ge=Decimal("0.25"),
        le=Decimal("24.00"),
        description="Durasi aktivitas dalam jam (0.25–24.00, kelipatan 0.25)",
    )
    raw_notes: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Catatan mentah aktivitas (maks 5000 karakter)",
    )
    gcal_event_id: Optional[str] = Field(
        None,
        max_length=255,
        description="ID event Google Calendar (opsional)",
    )

    @field_validator("subtask_category")
    @classmethod
    def validate_subtask_category(cls, v: str) -> str:
        """Validasi subtask_category dari daftar yang diizinkan."""
        if v not in VALID_SUBTASK_CATEGORIES:
            raise ValueError(
                f"Subtask category tidak valid. "
                f"Pilihan: {', '.join(VALID_SUBTASK_CATEGORIES)}"
            )
        return v

    @field_validator("duration_hours")
    @classmethod
    def validate_duration_multiple(cls, v: Decimal) -> Decimal:
        """Validasi durasi harus kelipatan 0.25."""
        remainder = v % Decimal("0.25")
        if remainder != 0:
            raise ValueError("Durasi harus kelipatan 0.25 jam.")
        return v

    @field_validator("raw_notes")
    @classmethod
    def strip_notes(cls, v: str) -> str:
        """Trim whitespace di awal/akhir."""
        return v.strip()


class ActivityLogResponse(BaseModel):
    """Schema response untuk satu activity log entry."""

    id_log: str
    id_project: str
    sa_id: UUID
    subtask_category: str
    duration_hours: Decimal
    raw_notes: str
    ai_polished_notes: Optional[dict] = None
    gcal_event_id: Optional[str] = None
    created_at: datetime
    needs_repolish: bool = Field(
        default=False,
        description="True jika AI polishing gagal dan perlu di-trigger ulang",
    )

    class Config:
        from_attributes = True


class ProjectStoryResponse(BaseModel):
    """Schema response untuk project story (paginated)."""

    items: list[ActivityLogResponse]
    total: int = Field(..., description="Total jumlah entry")
    page: int = Field(..., description="Halaman saat ini (1-based)")
    page_size: int = Field(default=20, description="Jumlah entry per halaman")
    total_pages: int = Field(..., description="Total halaman")
