"""PostgreSQL embebido para correr AllpaShift en una PC SIN Docker (pgserver). Deja un servidor corriendo y carga el esquema y los seeds del equipo.

    python deploy/local/pg_local.py            # arranca (o reutiliza) el servidor y carga 00-schema + seeds si falta
    python deploy/local/pg_local.py --recrear  # borra los esquemas agro/nasa/ref y los vuelve a cargar
    python deploy/local/pg_local.py --parar    # detiene el servidor

Escribe en la última línea  PUERTO=<n>  (la usa levantar-todo.ps1). Usuario postgres, base postgres, sin contraseña, solo 127.0.0.1.
Requiere:  pip install pgserver "psycopg[binary]"   (están en climate-service/requirements-dev.txt)

Por qué se copia la base de zonas horarias: el PostgreSQL de pgserver para Windows NO trae la carpeta `timezone`, y el driver JDBC pide la
zona del equipo ('America/Lima', 'UTC'…) al conectar: sin ella la API Java falla con  FATAL: invalid value for parameter "TimeZone".
Python ya trae esos mismos archivos en el paquete `tzdata`; se copian dentro de pgserver una sola vez.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pgserver

REPO = Path(__file__).resolve().parents[2]
DDL = REPO / "04. base de datos" / "ddl"
SEEDS = [DDL / "00-schema.sql", DDL / "seed" / "01-catalogo-norte.sql", DDL / "seed" / "02-datos-nasa.sql", DDL / "seed" / "03-salud-suelo.sql"]
DATOS = Path(__file__).resolve().parent / ".pgdata"
PG = Path(pgserver.__file__).resolve().parent / "pginstall"
PSQL = PG / "bin" / ("psql.exe" if sys.platform == "win32" else "psql")


def zonas_horarias() -> None:
    destino = PG / "share" / "postgresql" / "timezone"
    if destino.exists():
        return
    try:
        import tzdata
    except ImportError:
        print("Falta tzdata:  pip install tzdata   (sin él, la API Java no podrá conectarse)", file=sys.stderr)
        return
    shutil.copytree(Path(tzdata.__file__).resolve().parent / "zoneinfo", destino)
    print(f"zonas horarias copiadas a {destino}")


def psql(uri: str, *, archivo: Path | None = None, sql: str | None = None) -> str:
    # las opciones van ANTES de la URI: en Windows psql no reordena los argumentos
    args = [str(PSQL), "-v", "ON_ERROR_STOP=1", "-q", "-t", "-A"] + (["-c", sql] if sql else []) + [uri]
    r = subprocess.run(args, stdin=archivo.open("rb") if archivo else None, capture_output=True, timeout=600, check=False)
    if r.returncode != 0:
        raise SystemExit(f"psql falló ({archivo.name if archivo else sql}): {r.stderr.decode('utf-8', 'replace')[:400]}")
    return r.stdout.decode("utf-8", "replace").strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--recrear", action="store_true")
    ap.add_argument("--parar", action="store_true")
    a = ap.parse_args()

    zonas_horarias()
    DATOS.parent.mkdir(parents=True, exist_ok=True)
    if a.parar:
        subprocess.run([str(PG / "bin" / "pg_ctl.exe"), "stop", "-D", str(DATOS), "-m", "fast"], check=False)
        return 0

    srv = pgserver.get_server(DATOS, cleanup_mode=None)  # None = se queda corriendo cuando este script termina
    uri = srv.get_uri()
    puerto = int(re.search(r":(\d+)/", uri).group(1))
    if a.recrear:
        psql(uri, sql="DROP SCHEMA IF EXISTS agro CASCADE; DROP SCHEMA IF EXISTS nasa CASCADE; DROP SCHEMA IF EXISTS ref CASCADE;")
    if psql(uri, sql="SELECT to_regclass('agro.zonas')") in ("", "None"):
        for f in SEEDS:
            psql(uri, archivo=f)
            print(f"cargado {f.name}")
    filas = psql(uri, sql="SELECT (SELECT count(*) FROM agro.zonas) || ' zonas, ' || (SELECT count(*) FROM agro.cultivos) || ' cultivos, ' || (SELECT count(*) FROM nasa.datos_nasa) || ' datos NASA'")
    print(f"PostgreSQL {puerto}: {filas}")
    print(f"PUERTO={puerto}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
