"""SECCIÓN: TEST HEALTH — Verifica el endpoint básico sin acceder a la base."""

import os

# SECCIÓN: TEST ENV — Variable mínima antes de importar la aplicación.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://masterquiz:masterquiz@localhost:5432/masterquiz",
)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health() -> None:
    """SECCIÓN: TEST CASE — Confirma estado 200 y contenido esperado."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
