"""Tambah kolom pmo_lead_email dan delivery_lead_email ke tabel projects

Revision ID: 002
Revises: 001
Create Date: 2025-01-15 00:00:00.000000

Kolom baru untuk menyimpan konfigurasi email PMO Lead dan Delivery Lead
per-proyek, digunakan oleh fitur PMO Handover automation (requirement 17.6).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# Identifikasi revisi
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Tambah kolom handover config ke tabel projects."""
    op.add_column(
        "projects",
        sa.Column(
            "pmo_lead_email",
            sa.String(255),
            nullable=True,
            comment="Email PMO Lead untuk handover proyek",
        ),
    )
    op.add_column(
        "projects",
        sa.Column(
            "delivery_lead_email",
            sa.String(255),
            nullable=True,
            comment="Email Delivery Lead untuk handover proyek",
        ),
    )


def downgrade() -> None:
    """Hapus kolom handover config dari tabel projects."""
    op.drop_column("projects", "delivery_lead_email")
    op.drop_column("projects", "pmo_lead_email")
