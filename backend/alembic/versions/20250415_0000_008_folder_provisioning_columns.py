"""Tambah kolom folder provisioning ke tabel projects

Revision ID: 008
Revises: 007
Create Date: 2025-04-15 00:00:00.000000

Menambahkan kolom nullable gdrive_solutions_folder_id (ID subfolder Solutions,
ADR 0005) dan folder_provisioning_status (pending/provisioned/failed) beserta
CheckConstraint-nya. Kedua kolom nullable, tanpa backfill — proyek lama tetap
valid dengan nilai NULL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# Identifikasi revisi
revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Tambah kolom folder provisioning + CheckConstraint status."""
    op.add_column(
        "projects",
        sa.Column("gdrive_solutions_folder_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column("folder_provisioning_status", sa.String(20), nullable=True),
    )
    op.create_check_constraint(
        "chk_projects_folder_provisioning_status",
        "projects",
        "folder_provisioning_status IS NULL OR "
        "folder_provisioning_status IN ('pending','provisioned','failed')",
    )


def downgrade() -> None:
    """Hapus CheckConstraint lalu kedua kolom folder provisioning."""
    op.drop_constraint(
        "chk_projects_folder_provisioning_status",
        "projects",
        type_="check",
    )
    op.drop_column("projects", "folder_provisioning_status")
    op.drop_column("projects", "gdrive_solutions_folder_id")
