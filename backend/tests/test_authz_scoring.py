"""
Unit tests untuk authorization Fase 0.6 (B8 & B9).

Memvalidasi:
- B8 scoring reads (GET bant-result & recommendations): butuh authentication saja,
  terbuka untuk user terautentikasi manapun.
- B8 score-manual (POST): write-set ketat — hanya Sales PIC, assigned SA, atau
  Lead_SA/Admin. Collaborator sengaja DITOLAK (boundary halus).
- B9 PATCH /projects/{id}: general access set — privileged, Sales PIC, assigned SA,
  atau collaborator. User tak terkait ditolak.

Semua test terisolasi: DB session dan scoring_engine di-override/mock, tidak
membutuhkan Postgres live.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.main import app
from app.models.project_collaborator import ProjectCollaborator
from app.schemas.scoring import BANTResult, BANTSubScores

# =============================================================================
# Fixtures & Helpers
# =============================================================================


def _make_user(role: str = "SA", user_id: uuid.UUID | None = None):
    """Buat mock User untuk dependency override."""
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.email = f"{role.lower()}@company.com"
    user.name = f"Test {role}"
    user.role = role
    return user


def _make_project(sales_pic=None, assigned_sa=None):
    """Buat mock Project dengan field access yang relevan."""
    project = MagicMock()
    project.id_project = "PRJ-20250101-ABC123"
    project.sales_pic = sales_pic
    project.assigned_sa = assigned_sa
    project.bant_score = 80
    project.bant_detail = {"budget": 20, "authority": 20, "need": 20, "timeline": 20}
    project.use_case_tags = ["etl"]
    project.status = "Pending Assignment"
    return project


def _execute_result_scalar(value):
    """Mock hasil db.execute() untuk .scalar_one_or_none()."""
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=value)
    return result


def _override_current_user(user):
    """Override dependency get_current_user agar mengembalikan user tertentu."""
    app.dependency_overrides[get_current_user] = lambda: user


def _override_db(mock_session):
    """Override dependency get_db agar menyuplai mock session."""

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override


@pytest.fixture(autouse=True)
def _cleanup_overrides():
    """Bersihkan dependency override setelah tiap test."""
    yield
    app.dependency_overrides.clear()


BANT_RESULT = BANTResult(
    total_score=80,
    sub_scores=BANTSubScores(budget=20, authority=20, need=20, timeline=20),
    use_case_tags=["etl"],
    status="Pending Assignment",
    feedback=None,
)


# =============================================================================
# B8 — Scoring reads (bant-result & recommendations): auth saja, terbuka
# =============================================================================


class TestScoringReadsAuth:
    """GET bant-result & recommendations hanya butuh authentication."""

    def test_bant_result_unauthenticated_401(self):
        """Request tanpa token → 401."""
        mock_session = AsyncMock()
        _override_db(mock_session)
        client = TestClient(app)
        response = client.get("/api/v1/projects/PRJ-20250101-ABC123/bant-result")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_bant_result_authed_unrelated_user_200(self):
        """User terautentikasi tak terkait tetap boleh membaca → 200."""
        project = _make_project()  # user tak terkait sama sekali
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_execute_result_scalar(project))
        _override_db(mock_session)
        _override_current_user(_make_user(role="SA"))

        client = TestClient(app)
        response = client.get("/api/v1/projects/PRJ-20250101-ABC123/bant-result")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

    def test_recommendations_unauthenticated_401(self):
        """Request tanpa token → 401."""
        mock_session = AsyncMock()
        _override_db(mock_session)
        client = TestClient(app)
        response = client.get("/api/v1/projects/PRJ-20250101-ABC123/recommendations")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_recommendations_authed_unrelated_user_200(self):
        """User terautentikasi tak terkait tetap boleh membaca → 200."""
        project = _make_project()
        project.use_case_tags = []  # jalur cepat: tanpa panggil scoring_engine
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_execute_result_scalar(project))
        _override_db(mock_session)
        _override_current_user(_make_user(role="SA"))

        client = TestClient(app)
        response = client.get("/api/v1/projects/PRJ-20250101-ABC123/recommendations")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"


# =============================================================================
# B8 — score-manual (POST): write-set ketat (collaborator DITOLAK)
# =============================================================================


SCORE_BODY = {"budget": 20, "authority": 20, "need": 20, "timeline": 20}


class TestScoreManualAuthz:
    """POST score-manual: hanya Sales PIC, assigned SA, atau Lead_SA/Admin."""

    def test_unauthenticated_401(self):
        mock_session = AsyncMock()
        _override_db(mock_session)
        client = TestClient(app)
        response = client.post(
            "/api/v1/projects/PRJ-20250101-ABC123/score-manual", json=SCORE_BODY
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unrelated_sa_forbidden_403(self):
        """SA tak terkait (bukan PIC/assigned/privileged) → 403."""
        project = _make_project(sales_pic=uuid.uuid4(), assigned_sa=uuid.uuid4())
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_execute_result_scalar(project))
        _override_db(mock_session)
        _override_current_user(_make_user(role="SA"))

        client = TestClient(app)
        response = client.post(
            "/api/v1/projects/PRJ-20250101-ABC123/score-manual", json=SCORE_BODY
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_collaborator_forbidden_403(self):
        """Collaborator sengaja DITOLAK dari write-set score-manual → 403."""
        collaborator = _make_user(role="SA")
        project = _make_project(sales_pic=uuid.uuid4(), assigned_sa=uuid.uuid4())

        mock_session = AsyncMock()
        # Project di-load dulu; andai pun ada query lanjutan, user tetap collaborator
        # yang tidak masuk write-set, jadi harus 403 tanpa pernah menjalankan scoring.
        mock_session.execute = AsyncMock(return_value=_execute_result_scalar(project))
        _override_db(mock_session)
        _override_current_user(collaborator)

        client = TestClient(app)
        response = client.post(
            "/api/v1/projects/PRJ-20250101-ABC123/score-manual", json=SCORE_BODY
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch("app.api.scoring.scoring_engine")
    def test_sales_pic_allowed(self, mock_engine):
        """Sales PIC project → diizinkan."""
        pic = _make_user(role="Sales")
        project = _make_project(sales_pic=pic.id, assigned_sa=uuid.uuid4())
        project.bant_detail = None  # hindari merge metadata agar jalur sederhana

        mock_engine.score_manual = AsyncMock(return_value=BANT_RESULT)
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_execute_result_scalar(project))
        _override_db(mock_session)
        _override_current_user(pic)

        client = TestClient(app)
        response = client.post(
            "/api/v1/projects/PRJ-20250101-ABC123/score-manual", json=SCORE_BODY
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

    @patch("app.api.scoring.scoring_engine")
    def test_assigned_sa_allowed(self, mock_engine):
        """Assigned SA → diizinkan."""
        sa = _make_user(role="SA")
        project = _make_project(sales_pic=uuid.uuid4(), assigned_sa=sa.id)
        project.bant_detail = None

        mock_engine.score_manual = AsyncMock(return_value=BANT_RESULT)
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_execute_result_scalar(project))
        _override_db(mock_session)
        _override_current_user(sa)

        client = TestClient(app)
        response = client.post(
            "/api/v1/projects/PRJ-20250101-ABC123/score-manual", json=SCORE_BODY
        )
        assert response.status_code == status.HTTP_200_OK

    @patch("app.api.scoring.scoring_engine")
    def test_lead_sa_allowed(self, mock_engine):
        """Lead_SA (privileged) → diizinkan meski bukan PIC/assigned."""
        lead = _make_user(role="Lead_SA")
        project = _make_project(sales_pic=uuid.uuid4(), assigned_sa=uuid.uuid4())
        project.bant_detail = None

        mock_engine.score_manual = AsyncMock(return_value=BANT_RESULT)
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_execute_result_scalar(project))
        _override_db(mock_session)
        _override_current_user(lead)

        client = TestClient(app)
        response = client.post(
            "/api/v1/projects/PRJ-20250101-ABC123/score-manual", json=SCORE_BODY
        )
        assert response.status_code == status.HTTP_200_OK

    @patch("app.api.scoring.scoring_engine")
    def test_admin_allowed(self, mock_engine):
        """Admin (privileged) → diizinkan."""
        admin = _make_user(role="Admin")
        project = _make_project(sales_pic=uuid.uuid4(), assigned_sa=uuid.uuid4())
        project.bant_detail = None

        mock_engine.score_manual = AsyncMock(return_value=BANT_RESULT)
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_execute_result_scalar(project))
        _override_db(mock_session)
        _override_current_user(admin)

        client = TestClient(app)
        response = client.post(
            "/api/v1/projects/PRJ-20250101-ABC123/score-manual", json=SCORE_BODY
        )
        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# B9 — PATCH /projects/{id}: general access set
# =============================================================================


class TestUpdateProjectAuthz:
    """PATCH /projects/{id}: user tak terkait ditolak, authorized diizinkan."""

    def test_unrelated_user_forbidden_403(self):
        """User terautentikasi tanpa akses (bukan collaborator) → 403."""
        project = _make_project(sales_pic=uuid.uuid4(), assigned_sa=uuid.uuid4())
        mock_session = AsyncMock()
        # Pertama: load project. Kedua: cek collaborator → None (bukan collaborator).
        mock_session.execute = AsyncMock(
            side_effect=[
                _execute_result_scalar(project),
                _execute_result_scalar(None),
            ]
        )
        _override_db(mock_session)
        _override_current_user(_make_user(role="SA"))

        client = TestClient(app)
        response = client.patch(
            "/api/v1/projects/PRJ-20250101-ABC123",
            json={"project_name": "Nama Baru"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sales_pic_allowed(self):
        """Sales PIC project → diizinkan update."""
        pic = _make_user(role="Sales")
        project = _make_project(sales_pic=pic.id, assigned_sa=uuid.uuid4())
        mock_session = AsyncMock()
        # Hanya butuh load project; privileged check pakai field, tanpa query collaborator
        # tetapi ensure_project_access selalu query collaborator setelah cek field gagal.
        # Karena is_sales_pic True, query collaborator tidak dieksekusi — cukup 1 execute.
        mock_session.execute = AsyncMock(return_value=_execute_result_scalar(project))
        mock_session.commit = AsyncMock()
        _override_db(mock_session)
        _override_current_user(pic)

        client = TestClient(app)
        response = client.patch(
            "/api/v1/projects/PRJ-20250101-ABC123",
            json={"project_name": "Nama Baru"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

    def test_lead_sa_allowed(self):
        """Lead_SA (privileged) → diizinkan update."""
        lead = _make_user(role="Lead_SA")
        project = _make_project(sales_pic=uuid.uuid4(), assigned_sa=uuid.uuid4())
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_execute_result_scalar(project))
        mock_session.commit = AsyncMock()
        _override_db(mock_session)
        _override_current_user(lead)

        client = TestClient(app)
        response = client.patch(
            "/api/v1/projects/PRJ-20250101-ABC123",
            json={"project_name": "Nama Baru"},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_collaborator_allowed(self):
        """Collaborator termasuk general access set → diizinkan update."""
        collaborator = _make_user(role="SA")
        project = _make_project(sales_pic=uuid.uuid4(), assigned_sa=uuid.uuid4())
        collab_row = MagicMock(spec=ProjectCollaborator)
        mock_session = AsyncMock()
        # load project, lalu cek collaborator → ketemu row.
        mock_session.execute = AsyncMock(
            side_effect=[
                _execute_result_scalar(project),
                _execute_result_scalar(collab_row),
            ]
        )
        mock_session.commit = AsyncMock()
        _override_db(mock_session)
        _override_current_user(collaborator)

        client = TestClient(app)
        response = client.patch(
            "/api/v1/projects/PRJ-20250101-ABC123",
            json={"project_name": "Nama Baru"},
        )
        assert response.status_code == status.HTTP_200_OK
