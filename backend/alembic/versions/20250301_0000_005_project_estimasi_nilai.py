"""Tambah kolom estimasi_nilai ke tabel projects

Revision ID: 005
Revises: 004
Create Date: 2025-03-01 00:00:00.000000

Kolom baru untuk menyimpan estimasi nilai proyek (IDR) yang sebelumnya hanya
divalidasi di create_project namun tidak pernah dipersist (fix B4 / roadmap 1.1).
Nullable karena data proyek lama belum memiliki nilai estimasi.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# Identifikasi revisi
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Tambah kolom estimasi_nilai ke tabel projects."""
    op.add_column(
        "projects",
        sa.Column(
            "estimasi_nilai",
            sa.Numeric(14, 2),
            nullable=True,
            comment="Estimasi nilai proyek dalam IDR (0.01 - 999,999,999,999.00)",
        ),
    )


def downgrade() -> None:
    """Hapus kolom estimasi_nilai dari tabel projects."""
    op.drop_column("projects", "estimasi_nilai")
