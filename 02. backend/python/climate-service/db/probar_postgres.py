"""Prueba el SQL de PostgreSQL contra un servidor REAL embebido (pgserver; no necesita Docker ni instalar nada).

    pip install pgserver "psycopg[binary]"        # solo para esta prueba
    python -m db.probar_postgres                  # crea el esquema, carga las semillas y compara con SQLite

Comprueba: 01_schema.sql se ejecuta, las semillas CSV cargan (JSONB, booleanos, fechas), los conteos coinciden con
data/agroshift.sqlite, las claves foráneas se cumplen y las vistas devuelven datos.
"""

import csv
import gzip
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

from .build import RUTA_DB
from .export_postgres import SALIDA, SEMILLAS


def main() -> int:
    try:
        import pgserver
        import psycopg
    except ImportError:
        print('Falta: pip install pgserver "psycopg[binary]"')
        return 2
    if not (SALIDA / "01_schema.sql").exists() or not RUTA_DB.exists():
        print("Corre antes: python -m db.build && python -m db.export_postgres")
        return 2

    pgdata = Path(tempfile.mkdtemp(prefix="agroshift_pg_"))
    srv = pgserver.get_server(pgdata, cleanup_mode="delete")
    fallos: list[str] = []
    try:
        with psycopg.connect(srv.get_uri(), autocommit=True) as con:
            version = con.execute("SELECT version()").fetchone()[0]
            print("PostgreSQL real:", version.split(",")[0])
            con.execute((SALIDA / "01_schema.sql").read_text(encoding="utf-8"))
            print("✓ 01_schema.sql ejecutado")

            lite = sqlite3.connect(RUTA_DB)
            for tabla in SEMILLAS:
                ruta = SALIDA / "seed" / (f"{tabla}.csv.gz" if tabla == "observacion" else f"{tabla}.csv")
                abrir = (lambda p: gzip.open(p, "rt", encoding="utf-8", newline="")) if ruta.suffix == ".gz" else (lambda p: open(p, encoding="utf-8", newline=""))
                with abrir(ruta) as f:
                    columnas = next(csv.reader(f))
                    f.seek(0)
                    with con.cursor() as cur, cur.copy(f"COPY {tabla} ({', '.join(columnas)}) FROM STDIN WITH (FORMAT csv, HEADER true)") as cp:
                        while bloque := f.read(1 << 20):
                            cp.write(bloque)
                pg = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
                sq = lite.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
                marca = "✓" if pg == sq else "✗"
                print(f"{marca} {tabla:<22} PostgreSQL {pg:>7} · SQLite {sq:>7}")
                if pg != sq:
                    fallos.append(f"{tabla}: {pg} != {sq}")

            # claves foráneas: se agregaron tras el COPY, así que se revisan con una consulta
            huerfanas = con.execute(
                "SELECT COUNT(*) FROM observacion o LEFT JOIN zona z ON z.id = o.zona_id LEFT JOIN variable v ON v.id = o.variable_id WHERE z.id IS NULL OR v.id IS NULL"
            ).fetchone()[0]
            print(("✓" if huerfanas == 0 else "✗"), "observaciones huérfanas:", huerfanas)
            if huerfanas:
                fallos.append("observaciones huérfanas")

            for vista, sql in (
                ("v_datos_nasa", "SELECT COUNT(*) FROM v_datos_nasa"),
                ("v_anomalia_mensual", "SELECT COUNT(*), ROUND(MAX(z)::numeric, 1) FROM v_anomalia_mensual"),
                ("v_ultimo_dato", "SELECT COUNT(*) FROM v_ultimo_dato"),
                ("v_validacion_resumen", "SELECT COUNT(*) FROM v_validacion_resumen WHERE nivel_maximo = 'alto'"),
            ):
                fila = con.execute(sql).fetchone()
                print("✓ vista", vista, "->", fila)
            j = con.execute("SELECT indicadores->'lluvia'->>'nivel' FROM validacion_quincena LIMIT 1").fetchone()[0]
            print("✓ JSONB consultable:", j)
    except Exception as e:  # noqa: BLE001
        print("✗ ERROR:", type(e).__name__, str(e)[:400])
        fallos.append(str(e)[:200])
    finally:
        srv.cleanup()
        shutil.rmtree(pgdata, ignore_errors=True)
    print("\nRESULTADO:", "TODO COINCIDE" if not fallos else f"{len(fallos)} problemas: {fallos}")
    return 0 if not fallos else 1


if __name__ == "__main__":
    sys.exit(main())
