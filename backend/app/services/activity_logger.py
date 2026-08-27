"""
Service ActivityLogger — Modul untuk mencatat dan memproses aktivitas harian SA.

Fitur utama:
- Membuat log aktivitas dengan validasi project
- AI note polishing via LLM Provider
- Retry polish untuk entry yang gagal
- Project story timeline dengan filter dan pagination
- Google Calendar sync dan event mapping
"""

import logging
import math
import random
import string
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.models.project import Project
from app.services.llm_provider import llm_factory, LLMResponse

logger = logging.getLogger(__name__)


# Schema output untuk AI polishing (dikirim ke LLM)
AI_POLISH_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "discussion_points": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Daftar poin-poin diskusi yang sudah dirapikan",
        },
        "action_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Deskripsi item aksi",
                    },
                    "pic": {
                        "type": "string",
                        "nullable": True,
                        "description": "Person in charge (jika disebutkan dalam notes)",
                    },
                },
                "required": ["description"],
            },
            "description": "Daftar item aksi yang harus ditindaklanjuti",
        },
    },
    "required": ["discussion_points", "action_items"],
}


def _generate_log_id() -> str:
    """
    Generate ID log aktivitas unik.
    Format: LOG-{YYYYMMDD}-{random 6 chars}
    """
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"LOG-{date_part}-{random_part}"


class ActivityLogger:
    """
    Service class untuk manajemen activity log SA.

    Menangani:
    - Pembuatan log dengan validasi project
    - AI polishing catatan via LLM
    - Retry polishing untuk entry yang gagal
    - Query project story dengan filter dan pagination
    """

    def __init__(self, db: AsyncSession):
        """Inisialisasi service dengan database session."""
        self.db = db

    async def create_log(
        self,
        sa_id: uuid.UUID,
        id_project: str,
        subtask_category: str,
        duration_hours: Decimal,
        raw_notes: str,
        gcal_event_id: Optional[str] = None,
    ) -> ActivityLog:
        """
        Buat activity log baru.

        Flow:
        1. Validasi project_id ada di database
        2. Generate ID log unik
        3. Coba polish notes via AI
        4. Simpan record ke database (dengan atau tanpa polished notes)

        Args:
            sa_id: UUID user SA yang membuat log.
            id_project: ID proyek terkait.
            subtask_category: Kategori subtask.
            duration_hours: Durasi dalam jam.
            raw_notes: Catatan mentah dari SA.
            gcal_event_id: ID event Google Calendar (opsional).

        Returns:
            Instance ActivityLog yang sudah tersimpan.

        Raises:
            ValueError: Jika project_id tidak ditemukan.
        """
        # Validasi project exists
        await self._validate_project(id_project)

        # Generate ID unik
        id_log = _generate_log_id()

        # Coba polish notes via AI (requirement 8.3)
        ai_polished_notes = await self.polish_notes(raw_notes)

        # Buat record activity log
        activity_log = ActivityLog(
            id_log=id_log,
            id_project=id_project,
            sa_id=sa_id,
            subtask_category=subtask_category,
            duration_hours=duration_hours,
            raw_notes=raw_notes,
            ai_polished_notes=ai_polished_notes,
            gcal_event_id=gcal_event_id,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(activity_log)
        await self.db.commit()
        await self.db.refresh(activity_log)

        logger.info(
            f"Activity log dibuat: {id_log} untuk proyek {id_project} "
            f"(polished: {'ya' if ai_polished_notes else 'tidak'})"
        )

        return activity_log

    async def polish_notes(self, raw_notes: str) -> Optional[dict]:
        """
        Polish raw notes menggunakan LLM Provider (requirement 8.3).

        Mengirim raw notes ke LLM untuk diubah menjadi format terstruktur:
        - discussion_points: daftar poin diskusi
        - action_items: daftar item aksi dengan deskripsi dan PIC

        Args:
            raw_notes: Teks catatan mentah dari SA.

        Returns:
            Dict berisi discussion_points dan action_items, atau None jika LLM gagal.
        """
        try:
            provider = llm_factory.get_provider()

            # Kirim ke LLM untuk structuring
            response: LLMResponse = await provider.structure_text(
                text=raw_notes,
                output_schema=AI_POLISH_OUTPUT_SCHEMA,
            )

            # Cek apakah response berhasil
            if response.status == "success" and response.content is not None:
                # Validasi format response
                content = response.content
                if isinstance(content, dict) and "discussion_points" in content:
                    logger.info(
                        f"AI polishing berhasil. "
                        f"Points: {len(content.get('discussion_points', []))}, "
                        f"Actions: {len(content.get('action_items', []))}"
                    )
                    return content
                else:
                    logger.warning(
                        f"AI polishing: format response tidak sesuai schema. "
                        f"Content type: {type(content)}"
                    )
                    return None
            else:
                # LLM gagal — log error dan return None (requirement 8.6)
                logger.warning(
                    f"AI polishing gagal: {response.error_type} - "
                    f"{response.error_message}"
                )
                return None

        except Exception as e:
            # Tangkap semua error agar tidak menggagalkan penyimpanan (requirement 8.6)
            logger.error(f"AI polishing exception: {e}")
            return None

    async def retry_polish(self, id_log: str, sa_id: uuid.UUID) -> ActivityLog:
        """
        Re-trigger AI polishing untuk entry yang gagal (requirement 8.6).

        Dipanggil saat SA mengklik tombol "Polish Ulang".

        Args:
            id_log: ID log yang akan di-polish ulang.
            sa_id: UUID SA yang meminta retry (untuk validasi ownership).

        Returns:
            ActivityLog yang sudah di-update.

        Raises:
            ValueError: Jika log tidak ditemukan atau bukan milik SA.
        """
        # Cari activity log berdasarkan ID
        result = await self.db.execute(
            select(ActivityLog).where(ActivityLog.id_log == id_log)
        )
        activity_log = result.scalar_one_or_none()

        if activity_log is None:
            raise ValueError(f"Activity log '{id_log}' tidak ditemukan.")

        # Validasi ownership — hanya SA yang membuat bisa retry
        if activity_log.sa_id != sa_id:
            raise ValueError("Anda tidak memiliki akses ke activity log ini.")

        # Re-trigger polishing
        ai_polished_notes = await self.polish_notes(activity_log.raw_notes)

        # Update record
        activity_log.ai_polished_notes = ai_polished_notes
        await self.db.commit()
        await self.db.refresh(activity_log)

        logger.info(
            f"Retry polish untuk log {id_log}: "
            f"{'berhasil' if ai_polished_notes else 'gagal lagi'}"
        )

        return activity_log

    async def get_project_story(
        self,
        id_project: str,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Ambil project story — timeline aktivitas per proyek (requirement 8.5).

        Mendukung filter berdasarkan subtask category dan rentang tanggal,
        dengan pagination maksimal 20 entry per halaman.

        Args:
            id_project: ID proyek yang ingin dilihat story-nya.
            page: Halaman yang diminta (1-based).
            page_size: Jumlah entry per halaman (max 20).
            category: Filter berdasarkan subtask category (opsional).
            date_from: Filter tanggal mulai (opsional).
            date_to: Filter tanggal akhir (opsional).

        Returns:
            Dict berisi items, total, page, page_size, total_pages.
        """
        # Validasi project exists
        await self._validate_project(id_project)

        # Batasi page_size maksimal 20
        page_size = min(page_size, 20)

        # Bangun query base
        conditions = [ActivityLog.id_project == id_project]

        # Filter category
        if category:
            conditions.append(ActivityLog.subtask_category == category)

        # Filter rentang tanggal
        if date_from:
            conditions.append(ActivityLog.created_at >= date_from)
        if date_to:
            conditions.append(ActivityLog.created_at <= date_to)

        where_clause = and_(*conditions)

        # Hitung total
        count_query = select(func.count()).select_from(ActivityLog).where(where_clause)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Hitung total pages
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        # Query data dengan pagination
        offset = (page - 1) * page_size
        data_query = (
            select(ActivityLog)
            .where(where_clause)
            .order_by(ActivityLog.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(data_query)
        items = result.scalars().all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def sync_calendar(self, sa_id: uuid.UUID) -> list[dict]:
        """
        Sync events dari Google Calendar (placeholder untuk MVP).

        Di MVP ini hanya menyiapkan interface — implementasi lengkap
        akan dilakukan di task terpisah (Google Calendar integration).

        Args:
            sa_id: UUID SA yang meminta sync.

        Returns:
            List event yang berhasil di-sync (empty list untuk saat ini).
        """
        # TODO: Implementasi Google Calendar sync di iterasi berikutnya
        logger.info(f"Calendar sync diminta oleh SA {sa_id} (placeholder)")
        return []

    async def map_event_to_project(
        self,
        sa_id: uuid.UUID,
        gcal_event_id: str,
        id_project: str,
        duration_hours: Decimal,
        subtask_category: str,
        raw_notes: str = "",
    ) -> ActivityLog:
        """
        Map event Google Calendar ke proyek sebagai activity log (requirement 9.3).

        Args:
            sa_id: UUID SA yang melakukan mapping.
            gcal_event_id: ID event Google Calendar.
            id_project: ID proyek tujuan.
            duration_hours: Durasi dari event calendar.
            subtask_category: Kategori subtask.
            raw_notes: Catatan (opsional, default kosong).

        Returns:
            ActivityLog yang dibuat dari mapping event.

        Raises:
            ValueError: Jika event sudah dimapping atau project tidak valid.
        """
        # Cek apakah event sudah dimapping (unique constraint)
        existing = await self.db.execute(
            select(ActivityLog).where(ActivityLog.gcal_event_id == gcal_event_id)
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError(
                f"Event '{gcal_event_id}' sudah dipetakan ke proyek lain."
            )

        # Buat log dari event calendar
        return await self.create_log(
            sa_id=sa_id,
            id_project=id_project,
            subtask_category=subtask_category,
            duration_hours=duration_hours,
            raw_notes=raw_notes or f"[Mapped dari Google Calendar event]",
            gcal_event_id=gcal_event_id,
        )

    async def _validate_project(self, id_project: str) -> Project:
        """
        Validasi bahwa project ID ada di database.

        Args:
            id_project: ID proyek yang akan divalidasi.

        Returns:
            Instance Project jika ditemukan.

        Raises:
            ValueError: Jika proyek tidak ditemukan.
        """
        result = await self.db.execute(
            select(Project).where(Project.id_project == id_project)
        )
        project = result.scalar_one_or_none()

        if project is None:
            raise ValueError(f"Proyek dengan ID '{id_project}' tidak ditemukan.")

        return project
