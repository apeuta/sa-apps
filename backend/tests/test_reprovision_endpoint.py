"""
Tests untuk endpoint re-provision folder (FEAT-002 / T5).

POST /projects/{project_id}/provision-folder (ADR 0006: idempotency guard
sederhana). Memvalidasi:
- Role-guard: SA / Sales -> 403 (hanya Lead_SA/Admin).
- Sukses: `gdrive_folder_id` null -> 200, status 'pending', task provisioning
  dijadwalkan dengan email SA assigned + Lead_SA + Sales.
- Idempotency: `gdrive_folder_id` non-null -> 409 Conflict (tidak menjadwalkan).

Test terisolasi: session DB di-mock, background task di-patch agar tidak
membuka DB nyata saat dieksekusi.
"""

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.main import app

PROJECT_ID = "PRJ-20250101-ABC123"


# =============================================================================
# Helpers & fixtures
# =============================================================================


def _make_user(role: str, user_id: uuid.UUID | None = None):
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.email = f"{role.lower()}@company.com"
    user.name = f"Test {role}"
    user.role = role
    return user


def _make_project(gdrive_folder_id=None, assigned_sa=None):
    project = MagicMock()
    project.id_project = PROJECT_ID
    project.project_name = "Proyek Uji"
    project.customer_name = "Customer A"
    project.status = "Assigned"
    project.sales_pic = uuid.uuid4()
    project.assigned_sa = assigned_sa or uuid.uuid4()
    project.target_submit = date(2026, 12, 31)
    project.gdrive_folder_id = gdrive_folder_id
    project.gdrive_solutions_folder_id = None
    project.folder_provisioning_status = None
    return project


def _execute_result_scalar(value):
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=value)
    result.scalar = MagicMock(return_value=value)
    return result


def _override_current_user(user):
    app.dependency_overrides[get_current_user] = lambda: user


def _override_db(session):
    async def _override():
        yield session

    app.dependency_overrides[get_db] = _override


@pytest.fixture(autouse=True)
def _cleanup_overrides():
    yield
    app.dependency_overrides.clear()


# =============================================================================
# Role-guard
# =============================================================================


class TestRoleGuard:
    """Hanya Lead_SA/Admin yang boleh re-provision."""

    @pytest.mark.parametrize("role", ["SA", "Sales"])
    def test_role_non_privileged_403(self, role):
        user = _make_user(role)
        mock_session = AsyncMock()
        _override_db(mock_session)
        _override_current_user(user)

        client = TestClient(app)
        response = client.post(f"/api/v1/projects/{PROJECT_ID}/provision-folder")

        assert response.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# Sukses: folder belum ada -> jadwalkan provisioning
# =============================================================================


class TestReprovisionSukses:
    def test_gdrive_null_menjadwalkan_task_dan_pending(self):
        lead = _make_user("Lead_SA")
        sa = _make_user("SA")
        sales = _make_user("Sales")
        project = _make_project(gdrive_folder_id=None, assigned_sa=sa.id)

        mock_session = AsyncMock()
        # execute: 1) project, 2) SA assigned, 3) Sales (sales_pic).
        mock_session.execute = AsyncMock(
            side_effect=[
                _execute_result_scalar(project),
                _execute_result_scalar(sa),
                _execute_result_scalar(sales),
            ]
        )
        mock_session.commit = AsyncMock()

        _override_db(mock_session)
        _override_current_user(lead)

        client = TestClient(app)
        with patch(
            "app.api.assignment._trigger_folder_provisioner",
            new_callable=AsyncMock,
        ) as mock_task:
            response = client.post(f"/api/v1/projects/{PROJECT_ID}/provision-folder")

        assert response.status_code == status.HTTP_200_OK
        body = response.json()["data"]
        assert body["folder_provisioning_triggered"] is True
        assert body["folder_provisioning_status"] == "pending"
        assert project.folder_provisioning_status == "pending"
        # Task dijadwalkan dengan email SA assigned, Lead_SA, Sales.
        mock_task.assert_awaited_once()
        args = mock_task.await_args.args
        assert args[0] == PROJECT_ID
        assert args[1] == sa.email
        assert args[2] == lead.email
        assert args[3] == sales.email


# =============================================================================
# Idempotency: folder sudah ada -> 409
# =============================================================================


class TestReprovisionIdempotency:
    def test_gdrive_non_null_409(self):
        lead = _make_user("Lead_SA")
        project = _make_project(gdrive_folder_id="master_existing")

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(
            side_effect=[_execute_result_scalar(project)]
        )
        mock_session.commit = AsyncMock()

        _override_db(mock_session)
        _override_current_user(lead)

        client = TestClient(app)
        with patch(
            "app.api.assignment._trigger_folder_provisioner",
            new_callable=AsyncMock,
        ) as mock_task:
            response = client.post(f"/api/v1/projects/{PROJECT_ID}/provision-folder")

        assert response.status_code == status.HTTP_409_CONFLICT
        mock_task.assert_not_awaited()

    def test_project_tidak_ditemukan_404(self):
        lead = _make_user("Lead_SA")

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(
            side_effect=[_execute_result_scalar(None)]
        )

        _override_db(mock_session)
        _override_current_user(lead)

        client = TestClient(app)
        response = client.post(f"/api/v1/projects/{PROJECT_ID}/provision-folder")

        assert response.status_code == status.HTTP_404_NOT_FOUND
