"""Exporta los datos de David AL ESQUEMA DEL EQUIPO (Jhonny): `agro`, `nasa` y `ref` de `04. base de datos/ddl/00-schema.sql`.

    python -m db.export_allpashift      # escribe  04. base de datos/ddl/seed/02-datos-nasa.sql

Por qué existe: `db/postgres/01_schema.sql` (modelo en estrella de David) y `00-schema.sql` (modelo de Jhonny, el que lee y graba Java)
son dos esquemas distintos. Lo que Java ve es el de Jhonny. Este archivo lleva los datos reales a SUS tablas:

  nasa.datasets    suma VNP13A1 (VIIRS NDVI): es el NDVI que sí se pudo leer (MODIS MOD13Q1 es HDF4 y no se usa)
  nasa.normales    normal mensual por valle: POWER 1991-2020 (lluvia, humedad, Tmax, Tmin) e IMERG 2001-2020
  nasa.datos_nasa  datos reales por punto y fecha: POWER (2017 y los últimos 60 días), SMAP, NDVI VIIRS, MUR SST, IMERG

El SQL es autocontenido (COPY ... FROM STDIN) y se puede ejecutar varias veces sin duplicar, igual que `01-catalogo-norte.sql`:
    database-deploy.bat seed         (o: psql -d allpashift -v ON_ERROR_STOP=1 < 02-datos-nasa.sql)
Convención de `variable` (la del contrato): 'NOMBRE_NASA:campoContrato' + sufijo de escala si no es diaria (':mensual', ':16d').
"""

from __future__ import annotations

import csv
import io
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

from etl.config import RAIZ

from .build import RUTA_DB

SALIDA = RAIZ.parents[2] / "04. base de datos" / "ddl" / "seed" / "02-datos-nasa.sql"
ZONAS_EQUIPO = range(1, 19)  # agro.zonas del seed de Jhonny: 1-16 (mismos ids que los valles de David), 17 Huarmaca, 18 Ayabaca

# código en la base de David -> (variable del contrato, fuente, versión)
VARIABLES = {
    "PRECTOTCORR": ("PRECTOTCORR:lluviaMm", "NASA POWER", None),
    "GWETTOP": ("GWETTOP:humedadSuelo", "NASA POWER", None),
    "T2M_MAX": ("T2M_MAX:tempMaxC", "NASA POWER", None),
    "T2M_MIN": ("T2M_MIN:tempMinC", "NASA POWER", None),
    "SMAP_SM": ("soil_moisture_am:humedadSuelo", "SMAP", "006"),
    "VNP13A1_NDVI": ("NDVI:ndvi", "VIIRS NDVI", "002"),  # honesto: NO es MODIS
    "MUR_SST": ("analysed_sst:sstC", "MUR SST", "4.1"),
    "MUR_SST_ANOM": ("sstAnom:sstAnomaliaC", "MUR SST", "4.1"),
    "IMERG_PRECIP": ("precipitation:lluviaMm", "GPM IMERG", "07"),
    "IMERG_PRECIP_M": ("precipitation:lluviaMm", "GPM IMERG", "07"),
}
POWER_CONTRATO = ("PRECTOTCORR", "GWETTOP", "T2M_MAX", "T2M_MIN")
SUFIJO = {"diaria": "", "mensual": ":mensual", "compuesta16d": ":16d"}
NORMALES = POWER_CONTRATO + ("IMERG_PRECIP_M",)


def _csv(filas: list[list]) -> str:
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(filas)  # None -> vacío = NULL en COPY ... FORMAT csv
    return buf.getvalue()


def datos_nasa(con: sqlite3.Connection) -> list[list]:
    ultimo = date.fromisoformat(con.execute("SELECT MAX(fecha) FROM observacion WHERE escala = 'diaria'").fetchone()[0])
    desde_dia = (ultimo - timedelta(days=60)).isoformat()
    desde_mes = ultimo.replace(year=ultimo.year - 1, day=1).isoformat()
    p = ",".join(f"'{c}'" for c in POWER_CONTRATO)
    s = ",".join(f"'{c}'" for c in VARIABLES if c not in POWER_CONTRATO)
    consulta = f"""
        SELECT z.lat, z.lon, o.fecha, v.codigo, o.escala, o.valor, o.zona_id
        FROM observacion o JOIN zona z ON z.id = o.zona_id JOIN variable v ON v.id = o.variable_id
        WHERE v.codigo IN ({s})
           OR (v.codigo IN ({p}) AND (
                (o.escala = 'diaria'  AND (o.fecha BETWEEN '2017-01-01' AND '2017-04-30' OR o.fecha >= '{desde_dia}'))
             OR (o.escala = 'mensual' AND (o.fecha BETWEEN '2016-12-01' AND '2017-06-01' OR o.fecha >= '{desde_mes}'))))
        ORDER BY v.codigo, o.zona_id, o.fecha"""  # noqa: S608 - constantes del propio módulo
    filas = []
    for lat, lon, fecha, codigo, escala, valor, zona_id in con.execute(consulta):
        variable, fuente, version = VARIABLES[codigo]
        filas.append([lat, lon, fecha, fuente, variable + SUFIJO[escala], round(valor, 4), version, zona_id if zona_id in ZONAS_EQUIPO else None])
    return filas


def normales(con: sqlite3.Connection) -> list[list]:
    q = ",".join(f"'{c}'" for c in NORMALES)
    filas = []
    for zona_id, codigo, mes, media, a0, a1 in con.execute(
        f"""SELECT n.zona_id, v.codigo, n.mes, n.media, n.anio_ini, n.anio_fin FROM normal_mensual n JOIN variable v ON v.id = n.variable_id
            WHERE v.codigo IN ({q}) AND n.zona_id < 100 ORDER BY v.codigo, n.zona_id, n.mes"""  # noqa: S608
    ):
        variable, fuente, _ = VARIABLES[codigo]
        filas.append([zona_id, variable, mes, round(media, 4), f"{a0}-{a1}", fuente])
    return filas


def generar(ruta_db: Path = RUTA_DB) -> tuple[str, dict[str, int]]:
    con = sqlite3.connect(ruta_db)
    dn, nr = datos_nasa(con), normales(con)
    con.close()
    sql = f"""-- ============================================================================
-- AllpaShift - datos NASA reales para el esquema del equipo (generado por db/export_allpashift.py; no editar a mano)
-- Requiere 00-schema.sql y seed/01-catalogo-norte.sql (agro.zonas). Se puede ejecutar varias veces sin duplicar.
--   database-deploy.bat seed
-- Contenido: {len(nr)} normales y {len(dn)} datos NASA de los valles del norte (ver la cabecera de db/export_allpashift.py).
-- Fuentes: NASA POWER, SMAP SPL3SMP_E v006, VIIRS VNP13A1 v002, MUR SST v4.1, GPM IMERG V07 (IMERG y la caja Nino 1+2 los bajo Sheila).
-- ============================================================================
SET client_min_messages = warning;
BEGIN;

INSERT INTO nasa.datasets (codigo, nombre, fuente, version, doi, proveedor, resolucion, requiere_login, uso) VALUES
 ('VNP13A1', 'VIIRS NDVI 16 dias (500 m)', 'VIIRS NDVI', '002', NULL, 'LP DAAC', '500 m', TRUE, 'Vigor de cultivo: continuidad de MODIS; es el NDVI que usa AllpaShift')
ON CONFLICT (codigo) DO NOTHING;

CREATE TEMP TABLE _normales (zona_id integer, variable text, mes smallint, valor double precision, periodo varchar(9), fuente text) ON COMMIT DROP;
COPY _normales (zona_id, variable, mes, valor, periodo, fuente) FROM STDIN WITH (FORMAT csv);
{_csv(nr)}\\.

INSERT INTO nasa.normales (zona_id, variable, mes, valor, periodo, fuente)
SELECT n.zona_id, n.variable, n.mes, n.valor, n.periodo, n.fuente FROM _normales n
WHERE EXISTS (SELECT 1 FROM agro.zonas z WHERE z.id = n.zona_id)
ON CONFLICT (zona_id, variable, mes, periodo) DO NOTHING;

CREATE TEMP TABLE _datos (lat double precision, lon double precision, fecha date, fuente text, variable text, valor double precision, version varchar(10), zona_id integer) ON COMMIT DROP;
COPY _datos (lat, lon, fecha, fuente, variable, valor, version, zona_id) FROM STDIN WITH (FORMAT csv);
{_csv(dn)}\\.

INSERT INTO nasa.datos_nasa (lat, lon, fecha, fuente, variable, valor, version, zona_id)
SELECT d.lat, d.lon, d.fecha, d.fuente, d.variable, d.valor, d.version,
       CASE WHEN EXISTS (SELECT 1 FROM agro.zonas z WHERE z.id = d.zona_id) THEN d.zona_id END
FROM _datos d
WHERE NOT EXISTS (SELECT 1 FROM nasa.datos_nasa t
                  WHERE t.lat = d.lat AND t.lon = d.lon AND t.fecha = d.fecha AND t.fuente = d.fuente AND t.variable = d.variable);

COMMIT;
SELECT fuente, count(*) AS filas, min(fecha) AS desde, max(fecha) AS hasta FROM nasa.datos_nasa GROUP BY fuente ORDER BY fuente;
"""
    return sql, {"normales": len(nr), "datos_nasa": len(dn)}


def main() -> int:
    if not RUTA_DB.exists():
        print("Corre antes: python -m db.build")
        return 2
    sql, n = generar()
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(sql, encoding="utf-8", newline="\n")
    print(f"{SALIDA}\n  {n['normales']} normales · {n['datos_nasa']} datos NASA · {SALIDA.stat().st_size / 1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
