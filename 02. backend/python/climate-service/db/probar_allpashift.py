"""Prueba el seed de datos NASA contra el esquema REAL del equipo, en un PostgreSQL de verdad (pgserver, sin Docker).

    pip install pgserver "psycopg[binary]"
    python -m db.build && python -m db.export_allpashift
    python -m db.probar_allpashift

Hace lo mismo que `database-deploy.bat`: ejecuta con psql, por la entrada estándar y con ON_ERROR_STOP=1,
  04. base de datos/ddl/00-schema.sql  ->  seed/01-catalogo-norte.sql  ->  seed/02-datos-nasa.sql
y comprueba: conteos, claves foráneas, que correrlo dos veces NO duplica, y que los datos coinciden con la base de David.
"""

from __future__ import annotations

import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

from .build import RUTA_DB
from .export_allpashift import SALIDA, generar

DDL = SALIDA.parent.parent  # 04. base de datos/ddl


def _psql(psql: Path, uri: str, archivo: Path) -> subprocess.CompletedProcess:
    with archivo.open("rb") as f:
        # las opciones van ANTES de la URI: en Windows psql no reordena y se perdería ON_ERROR_STOP
        return subprocess.run([str(psql), "-v", "ON_ERROR_STOP=1", "-q", uri], stdin=f, capture_output=True, timeout=300, check=False)


def main() -> int:
    try:
        import pgserver
        import psycopg
    except ImportError:
        print('Falta: pip install pgserver "psycopg[binary]"')
        return 2
    if not RUTA_DB.exists() or not SALIDA.exists():
        print("Corre antes: python -m db.build && python -m db.export_allpashift")
        return 2

    esperado = generar()[1]
    psql = Path(pgserver.__file__).parent / "pginstall" / "bin" / ("psql.exe" if sys.platform == "win32" else "psql")
    pgdata = Path(tempfile.mkdtemp(prefix="allpashift_pg_"))
    srv = pgserver.get_server(pgdata, cleanup_mode="delete")
    fallos: list[str] = []

    def comprobar(ok: bool, texto: str) -> None:
        print(("✓ " if ok else "✗ ") + texto)
        if not ok:
            fallos.append(texto)

    try:
        uri = srv.get_uri()
        with psycopg.connect(uri, autocommit=True) as con:
            print("PostgreSQL real:", con.execute("SELECT version()").fetchone()[0].split(",")[0])
        for archivo in (DDL / "00-schema.sql", DDL / "seed" / "01-catalogo-norte.sql", SALIDA):
            r = _psql(psql, uri, archivo)
            comprobar(r.returncode == 0, f"{archivo.name} ejecutado (psql por stdin, ON_ERROR_STOP)" + ("" if r.returncode == 0 else f": {r.stderr.decode('utf-8', 'replace')[:300]}"))

        with psycopg.connect(uri, autocommit=True) as con:
            def n(sql: str) -> int:
                return con.execute(sql).fetchone()[0]

            comprobar(n("SELECT count(*) FROM nasa.datos_nasa") == esperado["datos_nasa"], f"nasa.datos_nasa = {n('SELECT count(*) FROM nasa.datos_nasa')} (esperado {esperado['datos_nasa']})")
            comprobar(n("SELECT count(*) FROM nasa.normales") == esperado["normales"], f"nasa.normales = {n('SELECT count(*) FROM nasa.normales')} (esperado {esperado['normales']})")
            comprobar(n("SELECT count(*) FROM nasa.datasets WHERE codigo = 'VNP13A1'") == 1, "nasa.datasets tiene VNP13A1")

            # idempotente: una segunda ejecución no duplica
            antes = n("SELECT count(*) FROM nasa.datos_nasa"), n("SELECT count(*) FROM nasa.normales")
            r = _psql(psql, uri, SALIDA)
            despues = n("SELECT count(*) FROM nasa.datos_nasa"), n("SELECT count(*) FROM nasa.normales")
            comprobar(r.returncode == 0 and antes == despues, f"segunda ejecución sin duplicar ({antes} -> {despues})")

            comprobar(n("SELECT count(*) FROM nasa.datos_nasa d LEFT JOIN agro.zonas z ON z.id = d.zona_id WHERE d.zona_id IS NOT NULL AND z.id IS NULL") == 0, "sin datos huérfanos de zona")
            fuentes = {r[0] for r in con.execute("SELECT DISTINCT fuente FROM nasa.datos_nasa")}
            comprobar(fuentes == {"NASA POWER", "SMAP", "VIIRS NDVI", "MUR SST", "GPM IMERG"}, f"fuentes cargadas: {sorted(fuentes)}")
            comprobar("MODIS NDVI" not in fuentes, "ningún dato se rotula MODIS (el NDVI es de VIIRS)")
            comprobar(n("SELECT count(*) FROM nasa.datos_nasa WHERE variable NOT LIKE '%:%'") == 0, "toda variable es NOMBRE_NASA:campoContrato")

            # el mismo dato que en la base de David: marzo-2017 en Bajo Piura (POWER diario, lluvia promedio) y la normal de marzo
            lite = sqlite3.connect(RUTA_DB)
            sq = lite.execute("SELECT AVG(o.valor) FROM observacion o JOIN variable v ON v.id=o.variable_id WHERE o.zona_id=1 AND o.escala='diaria' AND v.codigo='PRECTOTCORR' AND o.fecha BETWEEN '2017-03-01' AND '2017-03-31'").fetchone()[0]
            pg = con.execute("SELECT AVG(valor) FROM nasa.datos_nasa WHERE zona_id = 1 AND variable = 'PRECTOTCORR:lluviaMm' AND fecha BETWEEN '2017-03-01' AND '2017-03-31'").fetchone()[0]
            comprobar(abs(sq - pg) < 1e-3, f"lluvia de marzo 2017 en Bajo Piura: SQLite {sq:.3f} = PostgreSQL {pg:.3f} mm/día")
            nor = con.execute("SELECT valor FROM nasa.normales WHERE zona_id = 1 AND variable = 'PRECTOTCORR:lluviaMm' AND mes = 3").fetchone()[0]
            comprobar(1.0 < nor < 3.0, f"normal de marzo (POWER 1991-2020) en Bajo Piura = {nor:.2f} mm/día")
            im = con.execute("SELECT valor FROM nasa.datos_nasa WHERE zona_id = 1 AND variable = 'precipitation:lluviaMm:mensual' AND fecha = '2017-03-01'").fetchone()
            comprobar(im is not None and 15 < im[0] < 22, f"IMERG marzo 2017 en Bajo Piura = {im[0] if im else None} mm/día (Sheila: 577 mm/mes)")
            # lo que Java hace: dato más reciente de un punto
            ult = con.execute("SELECT fuente, max(fecha) FROM nasa.datos_nasa WHERE zona_id = 1 GROUP BY fuente ORDER BY fuente").fetchall()
            print("  último dato en Bajo Piura por fuente:", [(f, str(d)) for f, d in ult])
    except Exception as e:  # noqa: BLE001
        print("✗ ERROR:", type(e).__name__, str(e)[:400])
        fallos.append(str(e)[:200])
    finally:
        srv.cleanup()
        shutil.rmtree(pgdata, ignore_errors=True)
    print("\nRESULTADO:", "TODO BIEN" if not fallos else f"{len(fallos)} problemas")
    return 0 if not fallos else 1


if __name__ == "__main__":
    sys.exit(main())
