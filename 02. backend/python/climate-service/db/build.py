"""Construye la base de datos desde las descargas en caché (etl/jobs.py).

    python -m db.build                              # data/agroshift.sqlite (se recrea cada vez)
    python -m db.build --catalogo ruta/cultivos.json  # catálogo REAL de Alejandro (si falta, usa el de prueba marcado es_prueba)

Orden: catálogos -> zonas (SRTM, suelos) -> POWER -> normales 1991-2020 -> índices Niño/ONI -> satélites
(SMAP, MUR, NDVI, IMERG) -> cultivos y rotaciones -> tendencias y años Niño -> validación 2017 -> estado de hoy.
"""

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, event, insert, text

from app.crops import cargar_catalogo, generar_candidatas
from app.indicators import calcular_indicadores
from app.que_hacer import construir_que_hacer
from app.rotations import rotaciones_para
from app.schemas import IndicadoresRequest
from etl import cache, mur_opendap
from etl.config import DATA
from etl.inputs import BASE_NORMAL, construir_entrada
from etl.zonas import PUNTOS_MAR, ZONAS

from . import analisis, catalogos, schema

RUTA_DB = DATA / "agroshift.sqlite"
SAMPLE_CATALOGO = DATA.parent / "samples" / "catalogo_cultivos_ejemplo.json"
MES_ONI = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6, "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}
RANGO = {"bajo": 0, "medio": 1, "alto": 2}


def motor(ruta: Path):
    eng = create_engine(f"sqlite:///{ruta}")

    @event.listens_for(eng, "connect")
    def _fk(dbapi_con, _):  # SQLite no exige claves foráneas salvo que se pida
        dbapi_con.execute("PRAGMA foreign_keys=ON")

    return eng


def _f(texto: str) -> date:
    return date.fromisoformat(texto[:10])


# ------------------------------------------------------------------ catálogos y zonas
def sembrar_catalogos(con) -> None:
    estados = {
        "SMAP": "en_uso" if cache.leer("smap") else "probado",
        "MUR_SST": "en_uso" if cache.leer("mur") else "probado",
        "SRTM": "en_uso" if cache.leer("srtm") else "probado",
        "VNP13A1": "en_uso" if cache.leer("ndvi") else "probado",
        "IMERG_DL": "en_uso" if cache.leer("imerg") else "bloqueado",
    }
    con.execute(insert(schema.region), [{"id": i, "codigo": c, "nombre": n} for i, c, n in catalogos.REGIONES])
    columnas = ("id", "codigo", "nombre", "institucion", "producto", "version", "doi", "resolucion", "cobertura", "url", "acceso", "estado", "nota")
    filas = [dict(zip(columnas, f, strict=True)) for f in catalogos.FUENTES]
    for f in filas:
        f["estado"] = estados.get(f["codigo"], f["estado"])
    con.execute(insert(schema.fuente_dato), filas)
    variables = [*catalogos.VARIABLES, (15, "MUR_SST_ANOM", "Anomalía de MUR SST vs 2003-2022", "°C", 7, "Calculada aquí: SST del día menos la climatología del mismo día del año")]
    con.execute(insert(schema.variable), [dict(zip(("id", "codigo", "nombre", "unidad", "fuente_id", "descripcion"), v, strict=True)) for v in variables])


def sembrar_zonas(con) -> dict[str, int]:
    regiones = {c: i for i, c, _ in catalogos.REGIONES}
    srtm = {z["zona"]: z for z in (cache.leer("srtm") or {}).get("zonas", [])}
    suelos = {z["zona"]: z for z in (cache.leer("suelos") or {}).get("zonas", [])}
    filas = []
    for z in [*ZONAS, *PUNTOS_MAR]:
        s, g = srtm.get(z.nombre, {}), suelos.get(z.nombre, {})
        filas.append(
            {
                "id": z.id, "nombre": z.nombre, "region_id": regiones[z.region], "tipo": "mar" if z.id >= 100 else "agricola",
                "lat": z.lat, "lon": z.lon, "aproximada": z.id < 100,
                "elevacion_m": s.get("elevacion_m"), "pendiente_pct": s.get("pendiente_pct"),
                "suelo_ph": g.get("ph"), "suelo_carbono_g_kg": g.get("carbono_organico_g_kg"),
                "suelo_arcilla_pct": g.get("arcilla_pct"), "suelo_arena_pct": g.get("arena_pct"),
            }
        )  # fmt: skip
    con.execute(insert(schema.zona), filas)
    return {z.nombre: z.id for z in [*ZONAS, *PUNTOS_MAR]}


# ------------------------------------------------------------------ observaciones
def _insertar_obs(con, filas: list[dict]) -> int:
    if not filas:
        return 0
    df = pd.DataFrame(filas).drop_duplicates(["zona_id", "fecha", "escala", "variable_id"])
    registros = df.to_dict("records")
    for i in range(0, len(registros), 20000):
        con.execute(insert(schema.observacion), registros[i : i + 20000])
    return len(registros)


def cargar_power(con, zid: dict[str, int]) -> int:
    datos = cache.leer("power")
    if not datos:
        print("  ⚠ sin caché de POWER (python -m etl.jobs power)")
        return 0
    vid = catalogos.CODIGO_VARIABLE
    filas = []
    for z in datos["zonas"]:
        for param, serie in z["mensual"].items():
            if param in vid:
                filas += [{"zona_id": zid[z["zona"]], "fecha": date(int(k[:4]), int(k[4:6]), 1), "escala": "mensual", "variable_id": vid[param], "valor": v, "calidad": None} for k, v in serie.items()]
        for clave in ("diario_2017", "diario_reciente"):
            for param, serie in z[clave].items():
                if param in vid:
                    filas += [{"zona_id": zid[z["zona"]], "fecha": date(int(k[:4]), int(k[4:6]), int(k[6:])), "escala": "diaria", "variable_id": vid[param], "valor": v, "calidad": None} for k, v in serie.items()]
    return _insertar_obs(con, filas)


def calcular_normales(con) -> int:
    df = pd.read_sql(
        text("SELECT o.zona_id, o.variable_id, o.fecha, o.valor FROM observacion o WHERE o.escala = 'mensual'"), con
    )
    df["fecha"] = pd.to_datetime(df["fecha"])
    base = df[df["fecha"].dt.year.between(*BASE_NORMAL)].copy()
    base["mes"] = base["fecha"].dt.month
    g = base.groupby(["zona_id", "variable_id", "mes"])["valor"].agg(media="mean", desviacion="std", n_anios="size").reset_index()
    g["anio_ini"], g["anio_fin"] = BASE_NORMAL
    con.execute(insert(schema.normal_mensual), g.to_dict("records"))
    return len(g)


def cargar_indices(con) -> tuple[int, int]:
    d = cache.leer("nino")
    if not d:
        print("  ⚠ sin caché de índices (python -m etl.jobs nino)")
        return 0, 0
    fuente_cpc, fuente_oni = catalogos.CODIGO_FUENTE["CPC_NINO"], catalogos.CODIGO_FUENTE["ONI"]
    filas = []
    for f in d["nino"]:
        for k, v in f.items():
            if k != "fecha":
                filas.append({"codigo": k.upper(), "fecha": _f(f["fecha"]), "valor": v, "fuente_id": fuente_cpc})
    for f in d["oni"]:
        filas.append({"codigo": "ONI", "fecha": date(f["anio"], MES_ONI[f["trimestre"]], 1), "valor": f["oni"], "fuente_id": fuente_oni})
    con.execute(insert(schema.indice_climatico), filas)
    eps = [
        {"indice": "NINO12_ANOM", "inicio": _f(e["inicio"]), "fin": _f(e["fin"]), "meses": e["meses"], "pico_anomalia_c": e["pico_anom"], "pico_fecha": _f(e["pico_fecha"]), "media_anomalia_c": e["media_anom"]}
        for e in d["episodios_nino12"]
    ]
    if eps:
        con.execute(insert(schema.episodio_calido), eps)
    return len(filas), len(eps)


def cargar_satelites(con, zid: dict[str, int]) -> dict[str, int]:
    vid = catalogos.CODIGO_VARIABLE
    n: dict[str, int] = {}
    filas = []
    smap = cache.leer("smap")
    if smap:
        for k in ("reciente", "ene_may_2017"):
            filas += [{"zona_id": zid[d["zona"]], "fecha": _f(d["fecha"]), "escala": "diaria", "variable_id": vid["SMAP_SM"], "valor": d["valor"], "calidad": "recomendada"} for d in smap[k]["datos"]]
    clima = cache.leer("smap_clima")
    if clima:
        filas += [{"zona_id": zid[d["zona"]], "fecha": _f(d["fecha"]), "escala": "diaria", "variable_id": vid["SMAP_SM"], "valor": d["valor"], "calidad": "recomendada"} for d in clima["datos"]]
    n["SMAP"] = _insertar_obs(con, filas)

    filas = []
    mur, mclima = cache.leer("mur"), cache.leer("mur_clima")
    if mur:
        for nombre, p in mur["puntos"].items():
            z = zid[nombre]
            c = (mclima or {}).get("puntos", {}).get(nombre, [])
            for dia, v in p["sst_c"].items():
                filas.append({"zona_id": z, "fecha": _f(dia), "escala": "diaria", "variable_id": vid["MUR_SST"], "valor": v, "calidad": None})
                a = mur_opendap.anomalia(c, _f(dia), v) if c else None
                if a is not None:
                    filas.append({"zona_id": z, "fecha": _f(dia), "escala": "diaria", "variable_id": 15, "valor": a, "calidad": None})
    if mclima:
        con.execute(insert(schema.sst_clima), [{"zona_id": zid[nombre], "doy": c["doy"], "media_c": c["media_c"], "n": c["n"]} for nombre, cs in mclima["puntos"].items() for c in cs])
    n["MUR"] = _insertar_obs(con, filas)

    filas = []
    ndvi = cache.leer("ndvi")
    if ndvi:
        for k in ("dic2016_jul2017", "reciente"):
            filas += [{"zona_id": zid[d["zona"]], "fecha": _f(d["fecha"]), "escala": "compuesta16d", "variable_id": vid["VNP13A1_NDVI"], "valor": d["ndvi"], "calidad": f"confiabilidad={d['confiabilidad']}"} for d in ndvi[k]["datos"]]
    n["NDVI"] = _insertar_obs(con, filas)

    imerg = cache.leer("imerg")
    n["IMERG"] = _insertar_obs(con, [{"zona_id": zid[d["zona"]], "fecha": _f(d["fecha"]), "escala": "diaria", "variable_id": vid["IMERG_PRECIP"], "valor": d["valor"], "calidad": None} for d in imerg["datos"]]) if imerg else 0
    return n


# ------------------------------------------------------------------ cultivos y rotaciones
def cargar_cultivos(con, ruta: Path | None) -> bool:
    es_prueba = ruta is None
    cultivos = cargar_catalogo(ruta or SAMPLE_CATALOGO)
    con.execute(
        insert(schema.cultivo),
        [
            {"id": int(c.id), "nombre": c.nombre, "tipo": "anual", "temp_min_c": c.tempMinC, "temp_max_c": c.tempMaxC, "agua_necesaria": c.aguaNecesaria,
             "meses_siembra": c.mesesSiembra, "meses_cosecha": c.mesesCosecha, "acciones_por_etapa": c.accionesPorEtapa, "es_prueba": es_prueba,
             "fuente": "DATOS DE PRUEBA (samples/): no validados" if es_prueba else str(ruta)}
            for c in cultivos
        ],
    )  # fmt: skip
    con.execute(insert(schema.rotacion), [{"id": r.id, "nombre": r.nombre, "cultivo1_id": int(r.cultivo1Id), "cultivo2_id": int(r.cultivo2Id)} for r in generar_candidatas(cultivos)])
    return es_prueba


# ------------------------------------------------------------------ análisis
def cargar_analisis(con) -> dict:
    mensual = pd.read_sql(
        text("SELECT o.zona_id, v.codigo AS variable, v.id AS variable_id, o.fecha, o.valor FROM observacion o JOIN variable v ON v.id = o.variable_id WHERE o.escala = 'mensual'"), con
    )
    mensual["fecha"] = pd.to_datetime(mensual["fecha"])
    vid = catalogos.CODIGO_VARIABLE
    t = analisis.tendencias(mensual)
    if len(t):
        t["variable_id"] = t["variable"].map(vid)
        con.execute(insert(schema.tendencia), t.drop(columns="variable").to_dict("records"))
    nino = pd.read_sql(text("SELECT fecha, valor AS nino12_anom FROM indice_climatico WHERE codigo = 'NINO12_ANOM'"), con)
    nino["fecha"] = pd.to_datetime(nino["fecha"])
    años = analisis.anios_nino_costero(nino) if len(nino) else []
    c = analisis.composite_nino(mensual, años, variables=("PRECTOTCORR",)) if años else pd.DataFrame()
    if len(c):
        c["variable_id"] = c["variable"].map(vid)
        con.execute(insert(schema.composite_nino), c.drop(columns="variable").to_dict("records"))
    return {"tendencias": len(t), "anios_nino_costero": años, "composite": len(c)}


# ------------------------------------------------------------------ validación 2017 y estado de hoy
def _serie_diaria(con, zona_id: int, desde: date, hasta: date) -> dict[str, dict[str, float]]:
    df = pd.read_sql(
        text("SELECT v.codigo AS variable, o.fecha, o.valor FROM observacion o JOIN variable v ON v.id = o.variable_id WHERE o.zona_id = :z AND o.escala = 'diaria' AND o.fecha BETWEEN :d AND :h"),
        con, params={"z": zona_id, "d": desde.isoformat(), "h": hasta.isoformat()},
    )  # fmt: skip
    out: dict[str, dict[str, float]] = {}
    for var, f, v in df.itertuples(index=False):
        out.setdefault(var, {})[f.replace("-", "")[:8]] = v
    return out


def _normales(con, zona_id: int) -> dict[int, dict[str, float]]:
    df = pd.read_sql(text("SELECT v.codigo AS variable, n.mes, n.media FROM normal_mensual n JOIN variable v ON v.id = n.variable_id WHERE n.zona_id = :z"), con, params={"z": zona_id})
    out: dict[int, dict[str, float]] = {m: {} for m in range(1, 13)}
    for var, mes, media in df.itertuples(index=False):
        out[int(mes)][var] = media
    return out


def _nino_mes(con, dia: date) -> float | None:
    r = con.execute(text("SELECT valor FROM indice_climatico WHERE codigo = 'NINO12_ANOM' AND fecha <= :d ORDER BY fecha DESC LIMIT 1"), {"d": dia.replace(day=1).isoformat()}).fetchone()
    return None if r is None else float(r[0])


def _smap_ventana(con, zona_id: int, hasta: date, dias: int = 14) -> tuple[float, float] | None:
    """(valor actual, normal del mes) de SMAP, o None si no hay datos suficientes (≥2 en la ventana, ≥8 en la climatología)."""
    act = con.execute(text("SELECT AVG(o.valor), COUNT(*) FROM observacion o JOIN variable v ON v.id = o.variable_id WHERE v.codigo = 'SMAP_SM' AND o.zona_id = :z AND o.fecha BETWEEN :d AND :h"),
                      {"z": zona_id, "d": (hasta - timedelta(days=dias - 1)).isoformat(), "h": hasta.isoformat()}).fetchone()  # fmt: skip
    nor = con.execute(text("SELECT AVG(o.valor), COUNT(*) FROM observacion o JOIN variable v ON v.id = o.variable_id WHERE v.codigo = 'SMAP_SM' AND o.zona_id = :z AND o.fecha BETWEEN '2016-01-01' AND '2025-12-31' AND CAST(SUBSTR(CAST(o.fecha AS VARCHAR(10)), 6, 2) AS INTEGER) = :m"),
                      {"z": zona_id, "m": hasta.month}).fetchone()  # fmt: skip
    if act and act[1] and act[1] >= 2 and nor and nor[1] and nor[1] >= 8:
        return float(act[0]), float(nor[0])
    return None


def _evaluar(entrada: dict, fecha: date, catalogo) -> dict:
    ind = calcular_indicadores(IndicadoresRequest.model_validate(entrada))
    out = {"indicadores": ind.model_dump(), "nivel_maximo": max((i["nivel"] for i in ind.model_dump().values()), key=RANGO.get)}
    if catalogo:
        elegidas, todas = rotaciones_para(ind, catalogo, None, fecha, 3, None)
        out["rotaciones"] = [e.resultado.model_dump() for e in elegidas]
        out["que_hacer"] = construir_que_hacer(ind, elegidas, todas).model_dump()
    return out


def validar_2017(con, zid: dict[str, int], catalogo) -> int:
    filas = []
    for z in ZONAS:
        zona_id = zid[z.nombre]
        diario = _serie_diaria(con, zona_id, date(2016, 12, 1), date(2017, 6, 30))
        if "PRECTOTCORR" not in diario:
            continue
        normales = _normales(con, zona_id)
        for mes in range(1, 5):
            siguiente = date(2017, mes + 1, 1)
            for ini, fin in ((date(2017, mes, 1), date(2017, mes, 15)), (date(2017, mes, 16), siguiente - timedelta(days=1))):
                entrada, traza = construir_entrada(z.lat, z.lon, fin, diario, normales, _nino_mes(con, fin), fuente_sst="NOAA CPC Niño 1+2 (OISST)", humedad_smap=_smap_ventana(con, zona_id, fin))
                ev = _evaluar(entrada, fin, catalogo)
                filas.append({"zona_id": zona_id, "evento": "nino_costero_2017", "desde": ini, "hasta": fin, "entrada": entrada, "indicadores": ev["indicadores"], "rotaciones": ev.get("rotaciones"), "que_hacer": ev.get("que_hacer"), "nivel_maximo": ev["nivel_maximo"], "advertencias": traza["advertencias"]})  # fmt: skip
    con.execute(insert(schema.validacion_quincena), filas)
    return len(filas)


def estado_de_hoy(con, zid: dict[str, int], catalogo, hoy: date) -> int:
    filas = []
    for z in ZONAS:
        zona_id = zid[z.nombre]
        diario = _serie_diaria(con, zona_id, hoy - timedelta(days=60), hoy)
        if "PRECTOTCORR" not in diario:
            continue
        ultimo = max(date(int(k[:4]), int(k[4:6]), int(k[6:])) for k in diario["PRECTOTCORR"])
        entrada, traza = construir_entrada(z.lat, z.lon, ultimo, diario, _normales(con, zona_id), _nino_mes(con, ultimo), fuente_sst="NOAA CPC Niño 1+2 (OISST)", humedad_smap=_smap_ventana(con, zona_id, ultimo))
        ev = _evaluar(entrada, ultimo, catalogo)
        payload = {"lat": z.lat, "lon": z.lon, "fecha": ultimo.isoformat(), "entrada": entrada, "trazabilidad": traza, **{k: v for k, v in ev.items() if k != "nivel_maximo"}, "nivelMaximo": ev["nivel_maximo"]}
        filas.append({"zona_id": zona_id, "fecha": ultimo, "payload": payload, "creado": datetime.now()})
    con.execute(insert(schema.recomendacion_cache), filas)
    return len(filas)


# ------------------------------------------------------------------ orquestación
def construir(ruta: Path = RUTA_DB, catalogo_ruta: Path | None = None) -> dict:
    if ruta.exists():
        ruta.unlink()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    eng = motor(ruta)
    schema.metadata.create_all(eng)
    resumen: dict = {}
    with eng.begin() as con:
        for nombre, sql in schema.VISTAS.items():
            con.execute(text(f"CREATE VIEW {nombre} AS {sql}"))
        sembrar_catalogos(con)
        zid = sembrar_zonas(con)
        resumen["observaciones_power"] = cargar_power(con, zid)
        resumen["normales"] = calcular_normales(con)
        resumen["indices"], resumen["episodios"] = cargar_indices(con)
        resumen["satelites"] = cargar_satelites(con, zid)
        es_prueba = cargar_cultivos(con, catalogo_ruta)
        catalogo = None if es_prueba else cargar_catalogo(catalogo_ruta)  # recomendaciones solo con catálogo real
        resumen["analisis"] = cargar_analisis(con)
        resumen["validacion_2017"] = validar_2017(con, zid, catalogo)
        resumen["estado_hoy"] = estado_de_hoy(con, zid, catalogo, date.today())
        resumen["catalogo_de_prueba"] = es_prueba
    with eng.connect() as con:
        resumen["violaciones_fk"] = len(con.execute(text("PRAGMA foreign_key_check")).fetchall())
        resumen["tablas"] = {t: con.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar() for t in schema.metadata.tables}
    return resumen


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalogo", type=Path)
    ap.add_argument("--salida", type=Path, default=RUTA_DB)
    a = ap.parse_args()
    r = construir(a.salida, a.catalogo)
    print(json.dumps(r, ensure_ascii=False, indent=1, default=str))
    print(f"\nBase de datos lista: {a.salida}")


if __name__ == "__main__":
    main()
