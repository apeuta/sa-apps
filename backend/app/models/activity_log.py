"""
Model SQLAlchemy untuk tabel ActivityLogs.
Menyimpan catatan aktivitas harian SA per proyek.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    String,
    Text,
    Numeric,
    ForeignKey,
    CheckConstraint,
    Index,
    DateTime,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ActivityLog(Base):
    """Model untuk tabel activity_logs - catatan aktivitas SA."""

    __tablename__ = "activity_logs"

    # Kolom utama
    id_log: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        comment="ID log aktivitas (format custom)",
    )
    id_project: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("projects.id_project"),
        nullable=False,
        comment="FK ke proyek terkait",
    )
    sa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="FK ke user SA yang melakukan aktivitas",
    )
    subtask_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Kategori aktivitas SA",
    )
    gcal_event_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="ID event Google Calendar (opsional)",
    )
    duration_hours: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Durasi aktivitas dalam jam (0.25 - 24.00)",
    )
    raw_notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Catatan mentah dari SA",
    )
    ai_polished_notes: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Catatan yang sudah di-polish oleh AI (JSON terstruktur)",
    )

    # Timestamp (timezone-aware)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Waktu pembuatan record",
    )

    # Constraints dan Indexes
    __table_args__ = (
        CheckConstraint(
            "subtask_category IN ('Meeting Pre-Sales', 'Create PropTek', "
            "'Create BOQ', 'Peer Review', 'Internal Discussion', "
            "'Customer Workshop')",
            name="chk_activity_logs_subtask_category",
        ),
        CheckConstraint(
            "duration_hours BETWEEN 0.25 AND 24.00",
            name="chk_activity_logs_duration_hours",
        ),
        # Partial unique index: gcal_event_id harus unik jika tidak NULL
        Index(
            "idx_unique_gcal_mapping",
            "gcal_event_id",
            unique=True,
            postgresql_where=text("gcal_event_id IS NOT NULL"),
        ),
        {"comment": "Tabel catatan aktivitas harian SA"},
    )

    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id_log}, category={self.subtask_category})>"
