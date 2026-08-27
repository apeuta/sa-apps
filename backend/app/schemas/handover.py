"""
Schema Pydantic untuk fitur PMO Handover.
Validasi input/output untuk endpoint handover proyek ke tim PMO dan Delivery.

Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7
"""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# Regex sederhana untuk validasi format email
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class HandoverConfigInput(BaseModel):
    """
    Input untuk konfigurasi email PMO Lead dan Delivery Lead.
    Digunakan saat Lead_SA perlu mengisi email sebelum handover bisa diproses.
    (Requirement 17.6)
    """

    pmo_email: str = Field(
        ...,
        description="Email PMO Lead yang akan menerima handover",
    )
    delivery_email: str = Field(
        ...,
        description="Email Delivery Lead yang akan menerima handover",
    )

    @field_validator("pmo_email", "delivery_email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Validasi format email menggunakan regex."""
        if not EMAIL_REGEX.match(v):
            raise ValueError(f"Format email tidak valid: '{v}'")
        return v.lower().strip()


class HandoverReadiness(BaseModel):
    """
    Response pengecekan kesiapan handover.
    Menampilkan status apakah semua prasyarat handover terpenuhi.
    """

    ready: bool = Field(
        ...,
        description="Apakah handover siap diproses",
    )
    missing_items: list[str] = Field(
        default_factory=list,
        description="Daftar item yang belum terpenuhi untuk handover",
    )
    pmo_email: Optional[str] = Field(
        None,
        description="Email PMO Lead yang dikonfigurasi (None jika belum)",
    )
    delivery_email: Optional[str] = Field(
        None,
        description="Email Delivery Lead yang dikonfigurasi (None jika belum)",
    )
    project_status: Optional[str] = Field(
        None,
        description="Status proyek saat ini",
    )
    hld_status: Optional[str] = Field(
        None,
        description="Status dokumen HLD (None jika belum ada HLD)",
    )


class HandoverResponse(BaseModel):
    """
    Response setelah handover berhasil diproses.
    Berisi data proyek dan detail handover yang dilakukan.
    """

    id_project: str
    project_name: str
    customer_name: str
    old_status: str
    new_status: str
    pmo_email: str
    delivery_email: str
    final_deliverables_folder_id: Optional[str] = None
    documents_handed_over: list[str] = Field(
        default_factory=list,
        description="Daftar tipe dokumen berstatus Final yang di-handover",
    )
    handover_at: datetime
