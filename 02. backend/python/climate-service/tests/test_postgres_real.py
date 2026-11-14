"""Prueba opcional contra un PostgreSQL REAL embebido. Lenta (~25 s) y necesita la base generada:

    pip install pgserver "psycopg[binary]"
    python -m db.build && python -m db.export_postgres
    pytest -m postgres
"""

import pytest

from db.build import RUTA_DB
from db.export_postgres import SALIDA


@pytest.mark.postgres
def test_esquema_y_semillas_en_postgres_real():
    pytest.importorskip("pgserver")
    pytest.importorskip("psycopg")
    if not RUTA_DB.exists() or not (SALIDA / "01_schema.sql").exists():
        pytest.skip("falta `python -m db.build` y `python -m db.export_postgres`")
    from db.probar_postgres import main

    assert main() == 0
