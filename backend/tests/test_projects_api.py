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


def _create_fake_file(
    filename: str, content: bytes = b"fake content", content_type: str = "application/pdf"
):
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


# =============================================================================
# Test: Persistensi estimasi_nilai (regresi B4)
# =============================================================================


class TestEstimasiNilaiPersist:
    """
    Test regresi: estimasi_nilai harus ikut dipersist ke record Project saat
    create, bukan sekadar muncul di response (fix B4).
    """

    def test_create_mempersist_estimasi_nilai_ke_record(self, mock_auth_and_db):
        """
        Nilai estimasi_nilai yang dikirim harus di-set pada object Project yang
        di-add ke session (yang akan di-commit ke DB), bukan hanya di response.
        """
        mock_user, mock_session = mock_auth_and_db
        client = TestClient(app)
        response = client.post(
            "/api/v1/projects",
            data={
                "project_name": "Proyek Estimasi",
                "customer_name": "PT Estimasi",
                "target_submit": str(date.today() + timedelta(days=7)),
                "estimasi_nilai": "750000000.50",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

        # Ambil object Project yang di-add ke session (akan di-commit ke DB)
        assert mock_session.add.call_count == 1
        added_project = mock_session.add.call_args.args[0]
        assert added_project.estimasi_nilai == Decimal("750000000.50")

        # Nilai juga tercermin di response
        body = response.json()
        assert Decimal(str(body["data"]["estimasi_nilai"])) == Decimal("750000000.50")


# =============================================================================
# Test: PATCH /projects/{id} benar-benar mempersist (regresi bant_detail & estimasi_nilai)
# =============================================================================


def _real_project(**overrides):
    """Buat object Project nyata (bukan mock) untuk test readback persistensi."""
    from app.models.project import Project

    defaults = dict(
        id_project="PRJ-20250101-ABC123",
        project_name="Proyek Lama",
        customer_name="PT Lama",
        status="New",
        target_submit=date.today() + timedelta(days=7),
        sales_pic=uuid.uuid4(),
        bant_detail=None,
        estimasi_nilai=None,
    )
    defaults.update(overrides)
    return Project(**defaults)


@pytest.fixture
def mock_patch_db():
    """
    Patch auth (role Lead_SA agar lolos ensure_project_access) + session untuk
    endpoint PATCH /projects/{id}. db.execute mengembalikan project pada panggilan
    pertama (lookup), lalu None (cek collaborator di ensure_project_access).
    """
    mock_user = _mock_user()
    mock_user.role = "Lead_SA"

    project = _real_project()

    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()

    def _make_result(value):
        result = MagicMock()
        result.scalar_one_or_none = MagicMock(return_value=value)
        return result

    # Panggilan 1: lookup Project. Panggilan 2: cek collaborator (None).
    mock_session.execute = AsyncMock(side_effect=[_make_result(project), _make_result(None)])

    async def override_get_db():
        yield mock_session

    import app.core.database as database_module
    import app.core.dependencies as dependencies_module

    app.dependency_overrides[database_module.get_db] = override_get_db
    app.dependency_overrides[dependencies_module.get_current_user] = lambda: mock_user

    yield mock_user, mock_session, project

    app.dependency_overrides.clear()


class TestUpdateProjectPersist:
    """
    Test regresi: PATCH harus benar-benar mengubah object yang di-commit
    (bukan sekadar mengembalikan 200). bant_detail sebelumnya gagal persist
    karena JSONB tanpa MutableDict.
    """

    def test_patch_bant_detail_tersimpan(self, mock_patch_db):
        """
        PATCH bant_detail harus ter-set pada object Project (readback), bukan
        hanya 200. Ini test yang gagal sebelum fix MutableDict.
        """
        mock_user, mock_session, project = mock_patch_db
        client = TestClient(app)
        response = client.patch(
            "/api/v1/projects/PRJ-20250101-ABC123",
            json={"bant_detail": {"budget": 8, "authority": 5}},
        )
        assert response.status_code == status.HTTP_200_OK
        # commit dipanggil
        mock_session.commit.assert_awaited()
        # Readback dari object yang di-commit
        assert project.bant_detail == {"budget": 8, "authority": 5}

    def test_patch_bant_detail_merge_dengan_existing(self, mock_patch_db):
        """PATCH bant_detail melakukan merge terhadap nilai existing."""
        mock_user, mock_session, project = mock_patch_db
        project.bant_detail = {"budget": 2}
        client = TestClient(app)
        response = client.patch(
            "/api/v1/projects/PRJ-20250101-ABC123",
            json={"bant_detail": {"authority": 9}},
        )
        assert response.status_code == status.HTTP_200_OK
        assert project.bant_detail == {"budget": 2, "authority": 9}

    def test_patch_estimasi_nilai_valid_tersimpan(self, mock_patch_db):
        """PATCH estimasi_nilai valid ter-set pada object (readback)."""
        mock_user, mock_session, project = mock_patch_db
        client = TestClient(app)
        response = client.patch(
            "/api/v1/projects/PRJ-20250101-ABC123",
            json={"estimasi_nilai": "123456.78"},
        )
        assert response.status_code == status.HTTP_200_OK
        mock_session.commit.assert_awaited()
        assert project.estimasi_nilai == Decimal("123456.78")

    def test_patch_estimasi_nilai_di_luar_range_ditolak(self, mock_patch_db):
        """PATCH estimasi_nilai di luar range (terlalu besar) ditolak 422."""
        mock_user, mock_session, project = mock_patch_db
        client = TestClient(app)
        response = client.patch(
            "/api/v1/projects/PRJ-20250101-ABC123",
            json={"estimasi_nilai": "9999999999999.00"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # Nilai tidak berubah
        assert project.estimasi_nilai is None

    def test_patch_estimasi_nilai_terlalu_kecil_ditolak(self, mock_patch_db):
        """PATCH estimasi_nilai < 0.01 ditolak 422."""
        mock_user, mock_session, project = mock_patch_db
        client = TestClient(app)
        response = client.patch(
            "/api/v1/projects/PRJ-20250101-ABC123",
            json={"estimasi_nilai": "0.001"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert project.estimasi_nilai is None
