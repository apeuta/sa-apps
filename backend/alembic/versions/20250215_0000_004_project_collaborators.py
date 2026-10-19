"""Buat tabel project_collaborators

Revision ID: 004
Revises: 003
Create Date: 2025-02-15 00:00:00.000000

Membuat tabel project_collaborators untuk menyimpan peer/atasan yang di-tag
ke suatu proyek. Mirror persis model SQLAlchemy di
app/models/project_collaborator.py — sebelumnya tabel ini hanya tercipta via
Base.metadata.create_all saat startup, bukan lewat migration.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# Identifikasi revisi
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Buat tabel project_collaborators beserta constraint-nya."""
    op.create_table(
        "project_collaborators",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Primary key UUID",
        ),
        sa.Column(
            "id_project",
            sa.String(50),
            nullable=False,
            comment="FK ke proyek terkait",
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="FK ke user yang di-tag sebagai kolaborator",
        ),
        sa.Column(
            "role",
            sa.String(20),
            nullable=False,
            server_default="viewer",
            comment="Peran kolaborator: viewer atau contributor",
        ),
        sa.Column(
            "added_by",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="FK ke user yang menambahkan kolaborator",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="Waktu penambahan kolaborator",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["id_project"],
            ["projects.id_project"],
            name="fk_project_collaborators_project",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_project_collaborators_user",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["added_by"],
            ["users.id"],
            name="fk_project_collaborators_added_by",
        ),
        sa.UniqueConstraint(
            "id_project",
            "user_id",
            name="uq_project_collaborator",
        ),
        comment=(
            "Tabel kolaborator proyek — peer/atasan yang di-tag untuk melihat atau berkontribusi"
        ),
    )


def downgrade() -> None:
    """Hapus tabel project_collaborators."""
    op.drop_table("project_collaborators")
