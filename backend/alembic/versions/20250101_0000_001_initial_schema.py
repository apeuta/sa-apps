"""Initial schema - buat semua tabel Portal SA MVP

Revision ID: 001
Revises: None
Create Date: 2025-01-01 00:00:00.000000

Membuat tabel: users, projects, documents, activity_logs,
notification_logs, audit_logs, sla_tracking
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Identifikasi revisi
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Buat semua tabel initial schema."""

    # === Tabel Users ===
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="SA"),
        sa.Column("google_id", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("google_id", name="uq_users_google_id"),
        sa.CheckConstraint(
            "role IN ('Sales', 'SA', 'Lead_SA', 'Admin')",
            name="chk_users_role",
        ),
        comment="Tabel pengguna sistem Portal SA",
    )

    # === Tabel Projects ===
    op.create_table(
        "projects",
        sa.Column("id_project", sa.String(50), nullable=False),
        sa.Column("project_name", sa.String(150), nullable=False),
        sa.Column("customer_name", sa.String(150), nullable=False),
        sa.Column("dq_number", sa.String(20), nullable=True),
        sa.Column("sales_pic", sa.UUID(), nullable=False),
        sa.Column("assigned_sa", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="New"),
        sa.Column("target_submit", sa.Date(), nullable=False),
        sa.Column("bant_score", sa.Integer(), nullable=True),
        sa.Column("bant_detail", postgresql.JSONB(), nullable=True),
        sa.Column("use_case_tags", postgresql.JSONB(), nullable=True, server_default=sa.text("'[]'::jsonb")),
        sa.Column("gdrive_folder_id", sa.String(255), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id_project"),
        sa.ForeignKeyConstraint(["sales_pic"], ["users.id"], name="fk_projects_sales_pic"),
        sa.ForeignKeyConstraint(["assigned_sa"], ["users.id"], name="fk_projects_assigned_sa"),
        sa.CheckConstraint(
            "status IN ('New', 'Pending Assignment', 'Assigned', 'Ready', "
            "'Closed-Win', 'Handover Complete', 'Lost', 'Need Clarification', "
            "'Scoring Pending', 'Manual Review Required')",
            name="chk_projects_status",
        ),
        sa.CheckConstraint(
            "bant_score IS NULL OR (bant_score BETWEEN 0 AND 100)",
            name="chk_projects_bant_score",
        ),
        sa.CheckConstraint(
            "dq_number IS NULL OR dq_number ~ '^[A-Za-z0-9\\-]{5,20}$'",
            name="chk_dq_number_format",
        ),
        comment="Tabel proyek presales Portal SA",
    )

    # === Tabel Documents ===
    op.create_table(
        "documents",
        sa.Column("id_doc", sa.String(50), nullable=False),
        sa.Column("id_project", sa.String(50), nullable=False),
        sa.Column("doc_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="Draft"),
        sa.Column("gdrive_link", sa.Text(), nullable=False),
        sa.Column("folder_type", sa.String(20), nullable=False),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id_doc"),
        sa.ForeignKeyConstraint(["id_project"], ["projects.id_project"], name="fk_documents_project"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_documents_created_by"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], name="fk_documents_updated_by"),
        sa.CheckConstraint(
            "doc_type IN ('PropTek', 'BOQ', 'Mandays', 'MoM', 'RFP', 'HLD')",
            name="chk_documents_doc_type",
        ),
        sa.CheckConstraint(
            "status IN ('Draft', 'Reviewed', 'Final')",
            name="chk_documents_status",
        ),
        sa.CheckConstraint(
            "folder_type IN ('Inventory', 'Diagram', 'Solutions')",
            name="chk_documents_folder_type",
        ),
        comment="Tabel metadata dokumen proyek",
    )

    # === Tabel ActivityLogs ===
    op.create_table(
        "activity_logs",
        sa.Column("id_log", sa.String(50), nullable=False),
        sa.Column("id_project", sa.String(50), nullable=False),
        sa.Column("sa_id", sa.UUID(), nullable=False),
        sa.Column("subtask_category", sa.String(50), nullable=False),
        sa.Column("gcal_event_id", sa.String(255), nullable=True),
        sa.Column("duration_hours", sa.Numeric(5, 2), nullable=False),
        sa.Column("raw_notes", sa.Text(), nullable=False),
        sa.Column("ai_polished_notes", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id_log"),
        sa.ForeignKeyConstraint(["id_project"], ["projects.id_project"], name="fk_activity_logs_project"),
        sa.ForeignKeyConstraint(["sa_id"], ["users.id"], name="fk_activity_logs_sa"),
        sa.CheckConstraint(
            "subtask_category IN ('Meeting Pre-Sales', 'Create PropTek', "
            "'Create BOQ', 'Peer Review', 'Internal Discussion', "
            "'Customer Workshop')",
            name="chk_activity_logs_subtask_category",
        ),
        sa.CheckConstraint(
            "duration_hours BETWEEN 0.25 AND 24.00",
            name="chk_activity_logs_duration_hours",
        ),
        comment="Tabel catatan aktivitas harian SA",
    )

    # Partial unique index untuk gcal_event_id (hanya jika tidak NULL)
    op.create_index(
        "idx_unique_gcal_mapping",
        "activity_logs",
        ["gcal_event_id"],
        unique=True,
        postgresql_where=sa.text("gcal_event_id IS NOT NULL"),
    )

    # === Tabel NotificationLogs ===
    op.create_table(
        "notification_logs",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("recipient_user_id", sa.UUID(), nullable=False),
        sa.Column("channel", sa.String(10), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="pending"),
        sa.Column("reference_id", sa.String(50), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"], name="fk_notification_logs_recipient"),
        sa.CheckConstraint(
            "event_type IN ('assignment', 'status_change', 'sla_reminder', "
            "'sla_escalation', 'handover', 'doc_ready')",
            name="chk_notification_logs_event_type",
        ),
        sa.CheckConstraint(
            "channel IN ('in-app', 'email')",
            name="chk_notification_logs_channel",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'sent', 'failed', 'read')",
            name="chk_notification_logs_status",
        ),
        comment="Tabel riwayat notifikasi pengguna",
    )

    # === Tabel AuditLogs ===
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.String(50), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("performed_by", sa.UUID(), nullable=False),
        sa.Column("old_value", postgresql.JSONB(), nullable=True),
        sa.Column("new_value", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["performed_by"], ["users.id"], name="fk_audit_logs_performed_by"),
        comment="Tabel jejak audit perubahan data sistem",
    )

    # === Tabel SLATracking ===
    op.create_table(
        "sla_tracking",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column("project_id", sa.String(50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stopped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("days_elapsed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("current_status", sa.String(10), nullable=False, server_default="green"),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id_project"], name="fk_sla_tracking_project"),
        sa.UniqueConstraint("project_id", name="uq_sla_tracking_project_id"),
        sa.CheckConstraint(
            "current_status IN ('green', 'yellow', 'red')",
            name="chk_sla_tracking_current_status",
        ),
        comment="Tabel tracking SLA countdown DQ Number",
    )


def downgrade() -> None:
    """Hapus semua tabel (urutan terbalik karena foreign key)."""
    op.drop_table("sla_tracking")
    op.drop_table("audit_logs")
    op.drop_table("notification_logs")
    op.drop_index("idx_unique_gcal_mapping", table_name="activity_logs")
    op.drop_table("activity_logs")
    op.drop_table("documents")
    op.drop_table("projects")
    op.drop_table("users")
