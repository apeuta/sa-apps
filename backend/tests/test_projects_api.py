"""
Unit tests untuk API endpoint POST /api/v1/projects.
Memverifikasi validasi input, file upload, pembuatan record, dan trigger scoring.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app


# =============================================================================
# Fixtures & Helpers
# =============================================================================


def _mock_user():
    """Buat mock User object untuk dependency injection."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "sales@company.com"
    user.name = "Test Sales"
    user.role = "Sales"
    return user


def _create_fake_file(filename: str, content: bytes = b"fake content", content_type: str = "application/pdf"):
    """Buat tuple file upload untuk TestClient."""
    return ("files", (filename, BytesIO(content), content_type))


@pytest.fixture
def client():
    """TestClient untuk FastAPI tanpa database nyata."""
    return TestClient(app)


@pytest.fixture
def mock_auth_and_db():
    """Patch auth dependency dan database session."""
    mock_user = _mock_user()

    # Patch get_current_user dependency
    with patch("app.api.projects.get_current_user", return_value=mock_user) as auth_mock:
        # Patch database session
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        with patch("app.api.projects.get_db") as db_mock:
            # Override dependency
            async def override_get_db():
                yield mock_session

            app.dependency_overrides[
                __import__("app.core.database", fromlist=["get_db"]).get_db
            ] = override_get_db
            app.dependency_overrides[
                __import__("app.core.dependencies", fromlist=["get_current_user"]).get_current_user
            ] = lambda: mock_user

            yield mock_user, mock_session

    # Cleanup overrides
    app.dependency_overrides.clear()


# =============================================================================
# Test: Validasi Input Form
# =============================================================================


class TestProjectFormValidation:
    """Test validasi input form project submission."""

    def test_project_name_kosong_ditolak(self, mock_auth_and_db):
        """Project name kosong menghasilkan error validasi."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "   ",  # Hanya whitespace
                "customer_name": "PT Test",
                "target_submit": str(date.today() + timedelta(days=7)),
                "estimasi_nilai": "1000000",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        body = response.json()
        assert body["status"] == "error"

    def test_project_name_melebihi_150_chars_ditolak(self, mock_auth_and_db):
        """Project name > 150 karakter ditolak."""
        client = TestClient(app)
        long_name = "A" * 151
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": long_name,
                "customer_name": "PT Test",
                "target_submit": str(date.today() + timedelta(days=7)),
                "estimasi_nilai": "1000000",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_target_submit_masa_lalu_ditolak(self, mock_auth_and_db):
        """Target submit di masa lalu menghasilkan error."""
        client = TestClient(app)
        yesterday = date.today() - timedelta(days=1)
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "Proyek Valid",
                "customer_name": "PT Test",
                "target_submit": str(yesterday),
                "estimasi_nilai": "1000000",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        body = response.json()
        assert body["status"] == "error"
        # Cek bahwa error ada di field target_submit
        errors = body.get("data", [])
        field_names = [e["field"] for e in errors]
        assert "target_submit" in field_names

    def test_estimasi_nilai_terlalu_kecil_ditolak(self, mock_auth_and_db):
        """Estimasi nilai < 0.01 ditolak."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "Proyek Valid",
                "customer_name": "PT Test",
                "target_submit": str(date.today() + timedelta(days=7)),
                "estimasi_nilai": "0.001",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        body = response.json()
        errors = body.get("data", [])
        field_names = [e["field"] for e in errors]
        assert "estimasi_nilai" in field_names

    def test_estimasi_nilai_terlalu_besar_ditolak(self, mock_auth_and_db):
        """Estimasi nilai > 999,999,999,999.00 ditolak."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "Proyek Valid",
                "customer_name": "PT Test",
                "target_submit": str(date.today() + timedelta(days=7)),
                "estimasi_nilai": "9999999999999.00",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_estimasi_nilai_bukan_angka_ditolak(self, mock_auth_and_db):
        """Estimasi nilai non-numeric ditolak."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "Proyek Valid",
                "customer_name": "PT Test",
                "target_submit": str(date.today() + timedelta(days=7)),
                "estimasi_nilai": "bukan-angka",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_input_valid_tanpa_file_berhasil(self, mock_auth_and_db):
        """Input valid tanpa file menghasilkan 201 dengan message BANT manual."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "Proyek Valid",
                "customer_name": "PT Customer",
                "target_submit": str(date.today() + timedelta(days=30)),
                "estimasi_nilai": "500000000",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["status"] == "New"
        assert body["data"]["scoring_triggered"] is False
        assert body["data"]["message_bant"] is not None
        assert "BANT Manual" in body["data"]["message_bant"]


# =============================================================================
# Test: File Upload Validation
# =============================================================================


class TestFileUploadValidation:
    """Test validasi file upload."""

    def test_file_pdf_valid_diterima(self, mock_auth_and_db):
        """File PDF valid berhasil diupload."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "Proyek PDF",
                "customer_name": "PT Test",
                "target_submit": str(date.today() + timedelta(days=7)),
                "estimasi_nilai": "1000000",
            },
            files=[_create_fake_file("proposal.pdf")],
        )
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        files = body["data"]["files"]
        assert len(files) == 1
        assert files[0]["success"] is True
        assert body["data"]["scoring_triggered"] is True

    def test_file_docx_valid_diterima(self, mock_auth_and_db):
        """File DOCX valid berhasil diupload."""
        client = TestClient(app)
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "Proyek DOCX",
                "customer_name": "PT Test",
                "target_submit": str(date.today() + timedelta(days=7)),
                "estimasi_nilai": "1000000",
            },
            files=[("files", ("document.docx", BytesIO(b"docx content"), mime))],
        )
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        files = body["data"]["files"]
        assert len(files) == 1
        assert files[0]["success"] is True

    def test_file_format_invalid_ditolak(self, mock_auth_and_db):
        """File dengan format selain PDF/DOCX ditolak per-file."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "Proyek Invalid File",
                "customer_name": "PT Test",
                "target_submit": str(date.today() + timedelta(days=7)),
                "estimasi_nilai": "1000000",
            },
            files=[("files", ("image.png", BytesIO(b"png data"), "image/png"))],
        )
        # Proyek tetap dibuat (201), tapi file ditolak
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        files = body["data"]["files"]
        assert len(files) == 1
        assert files[0]["success"] is False
        assert "Format file tidak valid" in files[0]["error"]

    def test_partial_failure_file_valid_disimpan(self, mock_auth_and_db):
        """File valid tetap disimpan meskipun ada file yang gagal (partial failure)."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "Proyek Mixed Files",
                "customer_name": "PT Test",
                "target_submit": str(date.today() + timedelta(days=7)),
                "estimasi_nilai": "1000000",
            },
            files=[
                _create_fake_file("valid.pdf"),
                ("files", ("invalid.txt", BytesIO(b"text data"), "text/plain")),
                _create_fake_file("another_valid.pdf"),
            ],
        )
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        files = body["data"]["files"]
        assert len(files) == 3

        # File valid berhasil
        valid_files = [f for f in files if f["success"]]
        failed_files = [f for f in files if not f["success"]]
        assert len(valid_files) == 2
        assert len(failed_files) == 1
        # Scoring tetap di-trigger karena ada file valid
        assert body["data"]["scoring_triggered"] is True

    def test_maks_5_file_divalidasi(self, mock_auth_and_db):
        """Upload lebih dari 5 file ditolak."""
        client = TestClient(app)
        many_files = [_create_fake_file(f"file{i}.pdf") for i in range(6)]
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "Proyek Banyak File",
                "customer_name": "PT Test",
                "target_submit": str(date.today() + timedelta(days=7)),
                "estimasi_nilai": "1000000",
            },
            files=many_files,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        body = response.json()
        errors = body.get("data", [])
        field_names = [e["field"] for e in errors]
        assert "files" in field_names


# =============================================================================
# Test: Project Record Creation
# =============================================================================


class TestProjectRecordCreation:
    """Test pembuatan record project."""

    def test_project_dibuat_dengan_status_new(self, mock_auth_and_db):
        """Proyek baru selalu memiliki status 'New'."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "Proyek Baru",
                "customer_name": "PT Baru",
                "target_submit": str(date.today() + timedelta(days=14)),
                "estimasi_nilai": "250000000",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["data"]["status"] == "New"

    def test_project_id_format_prj(self, mock_auth_and_db):
        """ID proyek mengikuti format PRJ-{date}-{random}."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "Proyek ID Test",
                "customer_name": "PT ID",
                "target_submit": str(date.today() + timedelta(days=7)),
                "estimasi_nilai": "100000",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        project_id = body["data"]["id_project"]
        assert project_id.startswith("PRJ-")
        # Format: PRJ-YYYYMMDD-XXXXXX (total panjang = 4+8+6+2 separators = 20)
        parts = project_id.split("-")
        assert len(parts) == 3
        assert parts[0] == "PRJ"
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 6  # Random

    def test_project_memiliki_timestamp(self, mock_auth_and_db):
        """Proyek baru memiliki created_at yang tidak null."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "Proyek Timestamp",
                "customer_name": "PT Timestamp",
                "target_submit": str(date.today() + timedelta(days=7)),
                "estimasi_nilai": "100000",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["data"]["created_at"] is not None

    def test_project_memiliki_sales_pic(self, mock_auth_and_db):
        """Proyek baru memiliki sales_pic yang sesuai user login."""
        mock_user, _ = mock_auth_and_db
        client = TestClient(app)
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "Proyek Sales PIC",
                "customer_name": "PT Sales",
                "target_submit": str(date.today() + timedelta(days=7)),
                "estimasi_nilai": "100000",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["data"]["sales_pic"] == str(mock_user.id)


# =============================================================================
# Test: Response Format
# =============================================================================


class TestResponseFormat:
    """Test format response API standar."""

    def test_response_sukses_format_standar(self, mock_auth_and_db):
        """Response sukses mengikuti format standar."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "Proyek Format",
                "customer_name": "PT Format",
                "target_submit": str(date.today() + timedelta(days=7)),
                "estimasi_nilai": "100000",
            },
        )
        body = response.json()
        # Format standar: status, data, message
        assert "status" in body
        assert "data" in body
        assert "message" in body
        assert body["status"] == "success"

    def test_response_error_format_standar(self, mock_auth_and_db):
        """Response error validasi mengikuti format standar."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "",
                "customer_name": "PT Test",
                "target_submit": str(date.today() - timedelta(days=1)),
                "estimasi_nilai": "abc",
            },
        )
        body = response.json()
        assert "status" in body
        assert body["status"] == "error"
        assert "message" in body
