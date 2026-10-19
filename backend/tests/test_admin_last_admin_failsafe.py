"""
Unit tests untuk failsafe last-Admin pada endpoint PATCH /admin/users/{user_id}/role.

Memverifikasi invariant: sistem harus selalu punya minimal satu Admin.
- Men-demote Admin satu-satunya ditolak (409 Conflict).
- Men-demote Admin ketika masih ada Admin lain diperbolehkan.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.main import app


def _mock_admin():
    """Buat mock User dengan role Admin untuk current_user."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "admin@company.com"
    user.name = "Admin Utama"
    user.role = "Admin"
    return user


def _mock_target_admin():
    """Buat mock User target yang berperan sebagai Admin."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "target@company.com"
    user.name = "Target Admin"
    user.role = "Admin"
    return user


@pytest.fixture
def admin_env():
    """Setup current_user Admin + mock DB session, dengan override dependency."""
    current_admin = _mock_admin()
    target_admin = _mock_target_admin()

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    # db.execute(...).scalar_one_or_none() -> target user
    execute_result = MagicMock()
    execute_result.scalar_one_or_none = MagicMock(return_value=target_admin)
    mock_session.execute = AsyncMock(return_value=execute_result)

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: current_admin

    with patch("app.api.admin.get_current_user", return_value=current_admin):
        yield current_admin, target_admin, mock_session

    app.dependency_overrides.clear()


def test_demote_admin_terakhir_ditolak(admin_env):
    """Men-demote Admin satu-satunya ditolak dengan 409 Conflict."""
    current_admin, target_admin, mock_session = admin_env
    # Hanya ada 1 Admin di sistem.
    mock_session.scalar = AsyncMock(return_value=1)

    client = TestClient(app)
    response = client.patch(
        f"/api/v1/admin/users/{target_admin.id}/role",
        json={"role": "SA"},
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    body = response.json()
    assert "Admin terakhir" in body["message"]
    # Perubahan role tidak di-commit.
    mock_session.commit.assert_not_awaited()


def test_demote_admin_dengan_admin_lain_diperbolehkan(admin_env):
    """Men-demote Admin ketika masih ada Admin lain diperbolehkan."""
    current_admin, target_admin, mock_session = admin_env
    # Ada lebih dari 1 Admin di sistem.
    mock_session.scalar = AsyncMock(return_value=2)

    client = TestClient(app)
    response = client.patch(
        f"/api/v1/admin/users/{target_admin.id}/role",
        json={"role": "SA"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["role"] == "SA"
    assert body["data"]["old_role"] == "Admin"
    mock_session.commit.assert_awaited()
