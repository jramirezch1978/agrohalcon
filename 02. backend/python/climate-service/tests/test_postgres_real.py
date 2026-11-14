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


@pytest.mark.postgres
def test_seed_de_datos_nasa_en_el_esquema_del_equipo():
    """00-schema.sql + 01-catalogo-norte.sql + 02-datos-nasa.sql en un PostgreSQL real, como database-deploy.bat."""
    pytest.importorskip("pgserver")
    pytest.importorskip("psycopg")
    from db.export_allpashift import SALIDA as seed

    if not RUTA_DB.exists() or not seed.exists():
        pytest.skip("falta `python -m db.build` y `python -m db.export_allpashift`")
    from db.probar_allpashift import main

    assert main() == 0
