import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.crops import cargar_catalogo
from app.main import app

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def leer(nombre: str):
    return json.loads((SAMPLES / nombre).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def req_contrato() -> dict:
    """El ejemplo de entrada del PDF 'Contrato del backend' (Piura, sequía + calor)."""
    return leer("indicadores_request.json")


@pytest.fixture
def indicadores_contrato() -> dict:
    return leer("indicadores_response.json")


@pytest.fixture(scope="session")
def catalogo():
    return cargar_catalogo(SAMPLES / "catalogo_cultivos_ejemplo.json")


@pytest.fixture
def catalogo_json() -> list[dict]:
    return leer("catalogo_cultivos_ejemplo.json")["cultivos"]
