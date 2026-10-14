"""
Unit tests untuk model NotificationLog.
Memverifikasi bahwa konstruktor menerima kwarg `notification_metadata`
(atribut Python yang di-map ke kolom DB `metadata`) dan menolak `metadata=`
yang reserved oleh SQLAlchemy Declarative.
"""

import uuid

from app.models import NotificationLog


def test_notification_log_accepts_notification_metadata():
    """Konstruktor menerima notification_metadata tanpa raise."""
    log = NotificationLog(
        id="notif-abc123",
        event_type="status_change",
        recipient_user_id=uuid.uuid4(),
        channel="in-app",
        status="sent",
        reference_id="PRJ-001",
        notification_metadata={"project_id": "PRJ-001", "bant_score": 80},
    )

    assert log.notification_metadata == {"project_id": "PRJ-001", "bant_score": 80}


def test_metadata_kwarg_tidak_mengisi_kolom():
    """
    Membuktikan bug B1: kwarg `metadata=` TIDAK mengisi kolom notification_metadata.
    `metadata` adalah atribut reserved SQLAlchemy (MetaData registry), sehingga
    nilai yang dikirim lewat `metadata=` hilang (tidak pernah dipersist ke kolom DB),
    dan `notification_metadata` tetap None. Inilah alasan konstruktor wajib memakai
    `notification_metadata=`.
    """
    log = NotificationLog(
        id="notif-def456",
        event_type="status_change",
        recipient_user_id=uuid.uuid4(),
        channel="in-app",
        status="sent",
        reference_id="PRJ-002",
        metadata={"project_id": "PRJ-002"},
    )

    assert log.notification_metadata is None
