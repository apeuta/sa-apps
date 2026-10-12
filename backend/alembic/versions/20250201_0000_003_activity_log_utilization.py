"""Tambah work_type & project_phase ke activity_logs + restrukturisasi subtask

Revision ID: 003
Revises: 002
Create Date: 2025-02-01 00:00:00.000000

Mendukung pemetaan utilisasi dua dimensi (Project vs Non-Project, dan fase
Pre/Implementation/Post). Perubahan:
- id_project menjadi nullable (Non-Project tidak terkait proyek).
- Kolom baru: work_type (Project/Non-Project), project_phase.
- CheckConstraint subtask_category lama diganti dengan daftar baru (union
  Project + Non-Project).
- CheckConstraint baru: work_type, project_phase, dan konsistensi antar-field.

Catatan: data activity log existing di-reset via seed (seed_demo_data.py),
jadi migration ini hanya mengubah struktur. Baris lama (bila ada) di-set
work_type='Project' lewat server_default.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# Identifikasi revisi
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_SUBTASK_CHECK = "chk_activity_logs_subtask_category"
NEW_SUBTASK_VALUES = (
    "'Assessment', 'Internal Meeting', 'Customer Meeting', "
    "'Principal Meeting', 'Commercial Document', 'Technical Document', "
    "'Document Review', 'Training', 'Self-Lab', 'Self-Learning', "
    "'Exam', 'Internal Presentation', 'External Presentation'"
)
OLD_SUBTASK_VALUES = (
    "'Meeting Pre-Sales', 'Create PropTek', 'Create BOQ', "
    "'Peer Review', 'Internal Discussion', 'Customer Workshop'"
)


def upgrade() -> None:
    # 1. Tambah kolom work_type (server_default 'Project' agar baris lama valid)
    op.add_column(
        "activity_logs",
        sa.Column(
            "work_type",
            sa.String(20),
            nullable=False,
            server_default="Project",
            comment="Jenis aktivitas: Project atau Non-Project",
        ),
    )
    # 2. Tambah kolom project_phase (nullable)
    op.add_column(
        "activity_logs",
        sa.Column(
            "project_phase",
            sa.String(30),
            nullable=True,
            comment="Fase proyek; NULL untuk Non-Project",
        ),
    )
    # Baris lama berstatus Project → beri default fase Pre-Implementation agar
    # lolos constraint konsistensi.
    op.execute(
        "UPDATE activity_logs SET project_phase = 'Pre-Implementation' "
        "WHERE work_type = 'Project' AND project_phase IS NULL"
    )

    # 3. id_project menjadi nullable
    op.alter_column(
        "activity_logs",
        "id_project",
        existing_type=sa.String(50),
        nullable=True,
    )

    # 4. Ganti CheckConstraint subtask_category
    op.drop_constraint(OLD_SUBTASK_CHECK, "activity_logs", type_="check")
    op.create_check_constraint(
        OLD_SUBTASK_CHECK,
        "activity_logs",
        f"subtask_category IN ({NEW_SUBTASK_VALUES})",
    )

    # 5. Constraint baru
    op.create_check_constraint(
        "chk_activity_logs_work_type",
        "activity_logs",
        "work_type IN ('Project', 'Non-Project')",
    )
    op.create_check_constraint(
        "chk_activity_logs_project_phase",
        "activity_logs",
        "project_phase IS NULL OR project_phase IN "
        "('Pre-Implementation', 'Implementation', 'Post-Implementation')",
    )
    op.create_check_constraint(
        "chk_activity_logs_worktype_consistency",
        "activity_logs",
        "(work_type = 'Project' AND id_project IS NOT NULL AND project_phase IS NOT NULL) "
        "OR (work_type = 'Non-Project' AND id_project IS NULL AND project_phase IS NULL)",
    )

    # Lepas server_default setelah kolom terisi (default aplikasi via model)
    op.alter_column("activity_logs", "work_type", server_default=None)


def downgrade() -> None:
    # Hapus constraint baru
    op.drop_constraint("chk_activity_logs_worktype_consistency", "activity_logs", type_="check")
    op.drop_constraint("chk_activity_logs_project_phase", "activity_logs", type_="check")
    op.drop_constraint("chk_activity_logs_work_type", "activity_logs", type_="check")

    # Kembalikan CheckConstraint subtask lama
    op.drop_constraint(OLD_SUBTASK_CHECK, "activity_logs", type_="check")
    op.create_check_constraint(
        OLD_SUBTASK_CHECK,
        "activity_logs",
        f"subtask_category IN ({OLD_SUBTASK_VALUES})",
    )

    # id_project kembali NOT NULL (asumsikan tidak ada baris Non-Project)
    op.alter_column(
        "activity_logs",
        "id_project",
        existing_type=sa.String(50),
        nullable=False,
    )

    # Hapus kolom baru
    op.drop_column("activity_logs", "project_phase")
    op.drop_column("activity_logs", "work_type")
