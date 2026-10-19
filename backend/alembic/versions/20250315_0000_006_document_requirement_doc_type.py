"""Tambah tipe dokumen Requirement ke constraint doc_type

Revision ID: 006
Revises: 005
Create Date: 2025-03-15 00:00:00.000000

Menambahkan nilai 'Requirement' ke CHECK constraint chk_documents_doc_type
agar dokumen bertipe Requirement bisa disimpan (fix roadmap 1.2 / fitur 7).
CHECK constraint di Postgres tidak bisa di-alter in-place, jadi constraint
lama di-drop lalu dibuat ulang dengan daftar nilai yang diperluas.
"""
from typing import Sequence, Union

from alembic import op

# Identifikasi revisi
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Perluas constraint doc_type agar mengizinkan 'Requirement'."""
    op.drop_constraint(
        "chk_documents_doc_type",
        "documents",
        type_="check",
    )
    op.create_check_constraint(
        "chk_documents_doc_type",
        "documents",
        "doc_type IN ('Requirement', 'PropTek', 'BOQ', 'Mandays', 'MoM', 'RFP', 'HLD')",
    )


def downgrade() -> None:
    """Kembalikan constraint doc_type ke daftar tanpa 'Requirement'."""
    op.drop_constraint(
        "chk_documents_doc_type",
        "documents",
        type_="check",
    )
    op.create_check_constraint(
        "chk_documents_doc_type",
        "documents",
        "doc_type IN ('PropTek', 'BOQ', 'Mandays', 'MoM', 'RFP', 'HLD')",
    )
