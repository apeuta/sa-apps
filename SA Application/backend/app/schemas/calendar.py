"""
Pydantic schemas untuk Google Calendar sync dan event mapping.
Digunakan oleh endpoint /api/v1/calendar/sync dan /api/v1/calendar/map.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# === Request Schemas ===


class CalendarSyncRequest(BaseModel):
    """Request body untuk sync Google Calendar events."""

    access_token: str = Field(
        ...,
        description="Google OAuth access token untuk akses Calendar API",
    )


class CalendarMapRequest(BaseModel):
    """Request body untuk memetakan event Google Calendar ke proyek."""

    gcal_event_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="ID event dari Google Calendar",
    )
    project_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="ID proyek tujuan mapping",
    )
    subtask_category: str = Field(
        ...,
        description="Kategori aktivitas SA",
    )
    duration_hours: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0.25"),
        le=Decimal("24.00"),
        description="Override durasi (jam). Jika kosong, dihitung otomatis dari event.",
    )
    raw_notes: Optional[str] = Field(
        default=None,
        description="Catatan mentah. Jika kosong, auto-generate dari event title + description.",
    )
    event_title: str = Field(
        ...,
        description="Judul event untuk auto-generate notes jika raw_notes kosong",
    )
    event_description: Optional[str] = Field(
        default=None,
        description="Deskripsi event untuk auto-generate notes",
    )
    is_all_day: bool = Field(
        default=False,
        description="Apakah event all-day (durasi default 8 jam)",
    )
    event_start: Optional[datetime] = Field(
        default=None,
        description="Waktu mulai event (untuk kalkulasi durasi)",
    )
    event_end: Optional[datetime] = Field(
        default=None,
        description="Waktu selesai event (untuk kalkulasi durasi)",
    )


# === Response Schemas ===


class CalendarEventResponse(BaseModel):
    """Representasi satu event Google Calendar setelah sync."""

    gcal_event_id: str
    title: str
    start: Optional[str] = None
    end: Optional[str] = None
    duration_hours: Decimal
    is_all_day: bool
    description: Optional[str] = None


class CalendarSyncResponse(BaseModel):
    """Response dari endpoint sync — daftar events."""

    events: list[CalendarEventResponse]
    total_events: int


class CalendarMapResponse(BaseModel):
    """Response dari endpoint map — detail activity log yang dibuat."""

    id_log: str
    id_project: str
    gcal_event_id: str
    subtask_category: str
    duration_hours: Decimal
    raw_notes: str
    created_at: datetime
