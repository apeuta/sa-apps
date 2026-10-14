"""
Unit tests untuk endpoint GET /health.
Memverifikasi bahwa status database mencerminkan hasil check_database_health()
sebenarnya dan HTTP status code sesuai (200 saat sehat, 503 saat database down).
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """TestClient untuk FastAPI tanpa database nyata."""
    return TestClient(app)


def test_health_database_healthy(client):
    """Saat database sehat: HTTP 200 dan database='healthy'."""
    with patch("app.main.check_database_health", new=AsyncMock(return_value=True)):
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["api"] == "healthy"
    assert body["data"]["database"] == "healthy"


def test_health_database_unhealthy(client):
    """Saat database down: HTTP 503 dan database='unhealthy'."""
    with patch("app.main.check_database_health", new=AsyncMock(return_value=False)):
        response = client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["data"]["api"] == "healthy"
    assert body["data"]["database"] == "unhealthy"
