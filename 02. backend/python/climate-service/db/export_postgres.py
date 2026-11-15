"""Genera el SQL de PostgreSQL (esquema, vistas y semillas) a partir del MISMO esquema que usa SQLite.

    python -m db.export_postgres

Salida en db/postgres/:
  01_schema.sql   tablas, índices y vistas (sintaxis comprobada con sqlglot; no hay PostgreSQL en la PC de David)
  seed/*.csv(.gz) datos listos para \\copy       02_seed.sql   los comandos \\copy en el orden correcto
Para Jhonny:  psql -d agroshift -f db/postgres/01_schema.sql  &&  psql -d agroshift -f db/postgres/02_seed.sql
"""

import gzip
import json
from pathlib import Path

import pandas as pd
import sqlglot
from sqlalchemy import create_engine, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from . import schema
from .build import RUTA_DB

SALIDA = Path(__file__).resolve().parent / "postgres"
# Orden respetando las claves foráneas. cultivo/rotacion NO se exportan: el catálogo real es de Alejandro.
SEMILLAS = ["region", "fuente_dato", "variable", "zona", "normal_mensual", "indice_climatico", "episodio_calido", "sst_clima", "tendencia", "composite_nino", "contraste_fuentes", "observacion", "validacion_quincena", "recomendacion_cache"]
GRANDES = {"observacion"}  # se comprimen


def ddl() -> str:
    d = postgresql.dialect()
    partes = ["-- AgroShift · esquema PostgreSQL (generado por db/export_postgres.py; no editar a mano)\n"]
    for t in schema.metadata.sorted_tables:
        partes.append(str(CreateTable(t).compile(dialect=d)).strip() + ";\n")
        partes += [str(CreateIndex(i).compile(dialect=d)).strip() + ";\n" for i in sorted(t.indexes, key=lambda i: i.name)]
    for nombre, sql in schema.VISTAS.items():
        cuerpo = " ".join(sql.split())
        partes.append(f"CREATE OR REPLACE VIEW {nombre} AS {cuerpo};\n")
    return "\n".join(partes)


def validar(sql: str) -> int:
    """Parsea cada sentencia con la gramática de PostgreSQL. Lanza ParseError si algo no es válido."""
    sentencias = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
    return len(sentencias)


def exportar_semillas(ruta_db: Path) -> list[str]:
    (SALIDA / "seed").mkdir(parents=True, exist_ok=True)
    eng = create_engine(f"sqlite:///{ruta_db}")
    comandos = ["-- Semillas (generado por db/export_postgres.py). Ejecutar desde db/postgres/ con psql.", "-- observacion.csv.gz: descomprimir antes (gunzip -k seed/observacion.csv.gz).\n"]
    with eng.connect() as con:
        for nombre in SEMILLAS:
            df = pd.read_sql(text(f"SELECT * FROM {nombre}"), con)
            if nombre == "observacion":
                df = df.drop(columns=["id"])  # lo asigna la secuencia
            for c in df.columns:  # un id con NULL llega como float (1.0): PostgreSQL no lo acepta como entero
                if c.endswith("_id") and str(df[c].dtype) == "float64":
                    df[c] = df[c].astype("Int64")
            for c in df.columns:
                if c in {"entrada", "indicadores", "rotaciones", "que_hacer", "advertencias", "payload"}:
                    df[c] = df[c].map(lambda v: v if v is None else (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)))
            ext = "csv.gz" if nombre in GRANDES else "csv"
            ruta = SALIDA / "seed" / f"{nombre}.{ext}"
            if nombre in GRANDES:
                with gzip.open(ruta, "wt", encoding="utf-8", newline="") as f:
                    df.to_csv(f, index=False)
            else:
                df.to_csv(ruta, index=False, encoding="utf-8")
            columnas = ", ".join(df.columns)
            comandos.append(f"\\copy {nombre} ({columnas}) FROM 'seed/{nombre}.csv' WITH (FORMAT csv, HEADER true)")
    comandos.append("")
    for t in ("observacion", "episodio_calido", "validacion_quincena", "recomendacion_cache", "contraste_fuentes"):  # tablas con id automático
        comandos.append(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), COALESCE((SELECT MAX(id) FROM {t}), 1));")
    (SALIDA / "02_seed.sql").write_text("\n".join(comandos) + "\n", encoding="utf-8")
    return SEMILLAS


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    sql = ddl()
    n = validar(sql)
    (SALIDA / "01_schema.sql").write_text(sql, encoding="utf-8")
    print(f"01_schema.sql: {n} sentencias válidas para PostgreSQL")
    if RUTA_DB.exists():
        print(f"semillas: {len(exportar_semillas(RUTA_DB))} tablas -> {SALIDA / 'seed'}")
    else:
        print("sin data/agroshift.sqlite: corre primero `python -m db.build` para generar las semillas")


if __name__ == "__main__":
    main()
