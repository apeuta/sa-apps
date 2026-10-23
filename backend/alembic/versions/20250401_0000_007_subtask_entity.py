"""Tambah entity Subtask dan kolom link activity_logs.id_subtask

Revision ID: 007
Revises: 006
Create Date: 2025-04-01 00:00:00.000000

Membuat tabel subtasks (work item assignable per proyek) dan menambahkan
kolom link opsional activity_logs.id_subtask dengan FK ON DELETE SET NULL.
Kolom subtask_category dan constraint chk_activity_logs_subtask_category tidak
diubah — Subtask adalah konsep work item yang berbeda dari ActivityCategory.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Identifikasi revisi
revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Buat tabel subtasks dan kolom link activity_logs.id_subtask."""
    op.create_table(
        "subtasks",
        sa.Column("id_subtask", sa.String(50), primary_key=True),
        sa.Column(
            "id_project",
            sa.String(50),
            sa.ForeignKey("projects.id_project", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assigned_sa",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('open', 'in_progress', 'done')",
            name="chk_subtasks_status",
        ),
        sa.UniqueConstraint(
            "id_project", "title", name="uq_subtask_project_title"
        ),
        comment="Tabel subtask — work item assignable per proyek",
    )
    op.add_column(
        "activity_logs",
        sa.Column("id_subtask", sa.String(50), nullable=True),
    )
    op.create_foreign_key(
        "fk_activity_logs_id_subtask",
        "activity_logs",
        "subtasks",
        ["id_subtask"],
        ["id_subtask"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Hapus kolom link activity_logs.id_subtask dan tabel subtasks."""
    op.drop_constraint(
        "fk_activity_logs_id_subtask",
        "activity_logs",
        type_="foreignkey",
    )
    op.drop_column("activity_logs", "id_subtask")
    op.drop_table("subtasks")
