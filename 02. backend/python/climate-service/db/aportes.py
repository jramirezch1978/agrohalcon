"""Aportes del equipo a la base de datos: datos NASA que bajó Sheila (rama feature/calculos-sheila).

Su carpeta `calculos/data/precalculado/` trae dos archivos reales de la NASA que David no pudo bajar solo:

  imerg_piura.json     GPM IMERG V07 de 12 puntos de Piura: mensual Final 2001-01..2025-09 (mm/mes), diario Late de los últimos
                       45 días (mm/día) y climatología 2001-2020. David tiene bloqueado IMERG por el acuerdo de GES DISC.
  mur_sst_nino12.json  MUR SST v4.1: promedio SEMANAL de la caja Niño 1+2 (0-10°S, 90-80°O), 2016-05..2026-11.

Aquí se cargan al MISMO esquema que el resto de los datos (zonas, observaciones, normales, índices) y se contrastan con
las otras fuentes (POWER y NOAA CPC): si dos fuentes independientes dicen lo mismo, el dato es más confiable.

Dónde busca los archivos (en este orden): variable CALCULOS_PRECALCULADO · <repo>/02. backend/python/calculos/data/precalculado
(feature/integracion-sheila) · <repo>/calculos/data/precalculado (feature/calculos-sheila) · data/backup/sheila/ (copia con el
commit f1143f6 de su rama; su contenido es idéntico al de integracion-sheila).
"""

from __future__ import annotations

import calendar
import json
import math
import os
from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy import insert, text

from etl.config import BACKUP, RAIZ

from . import catalogos, schema

ARCHIVO_IMERG = "imerg_piura.json"
ARCHIVO_MUR = "mur_sst_nino12.json"
REPO = RAIZ.parents[2]  # climate-service -> python -> "02. backend" -> raíz del repositorio
DISTANCIA_MAX_KM = 5.0  # un punto de Sheila se asigna a un valle si está a menos de esto; si no, es zona "referencia"
ID_REFERENCIA = 201  # ids 201+ = puntos de referencia (los valles usan 1-99 y el mar 100+)
REGION_PIURA = 1


def candidatos() -> list[Path]:
    env = os.getenv("CALCULOS_PRECALCULADO")
    nueva = REPO / "02. backend" / "python" / "calculos" / "data" / "precalculado"  # feature/integracion-sheila
    return ([Path(env)] if env else []) + [nueva, REPO / "calculos" / "data" / "precalculado", BACKUP / "sheila"]


def localizar() -> Path | None:
    """Primera carpeta que tiene los dos archivos; None si no hay (la base se arma igual, sin estos aportes)."""
    return next((c for c in candidatos() if (c / ARCHIVO_IMERG).is_file() and (c / ARCHIVO_MUR).is_file()), None)


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def asignar_zonas(zonas: list[tuple[int, float, float]], puntos: list[dict]) -> dict[str, tuple[int | None, float]]:
    """Punto de Sheila -> (id de valle más cercano a menos de DISTANCIA_MAX_KM, distancia). Un valle recibe UN solo punto
    (el más cercano); los demás quedan como None (= zona de referencia nueva)."""
    mejor: dict[int, tuple[str, float]] = {}
    for p in puntos:
        zid, km = min(((z, distancia_km(p["lat"], p["lon"], la, lo)) for z, la, lo in zonas), key=lambda t: t[1])
        if km <= DISTANCIA_MAX_KM and (zid not in mejor or km < mejor[zid][1]):
            mejor[zid] = (p["id"], km)
    por_punto = {pid: (zid, km) for zid, (pid, km) in mejor.items()}
    return {p["id"]: ((por_punto[p["id"]][0], por_punto[p["id"]][1]) if p["id"] in por_punto else (None, 0.0)) for p in puntos}


def _leer(carpeta: Path, nombre: str) -> dict:
    return json.loads((carpeta / nombre).read_text(encoding="utf-8"))


def _filas_imerg(im: dict, zona_de: dict[str, int]) -> tuple[list[dict], list[dict]]:
    mensual, diario = [], []
    meses = im["mensual"]["meses"]
    for pid, serie in im["mensual"]["mm_mes"].items():
        for ym, mm in zip(meses, serie, strict=True):
            if mm is None:
                continue
            a, m = int(ym[:4]), int(ym[5:7])
            mensual.append({"zona_id": zona_de[pid], "fecha": date(a, m, 1), "escala": "mensual", "variable_id": catalogos.CODIGO_VARIABLE["IMERG_PRECIP_M"],
                            "valor": round(mm / calendar.monthrange(a, m)[1], 4), "calidad": "final"})  # fmt: skip
    for pid, serie in im["diario"]["mm_dia"].items():
        for dia, mm in zip(im["diario"]["fechas"], serie, strict=True):
            if mm is not None:
                diario.append({"zona_id": zona_de[pid], "fecha": date.fromisoformat(dia), "escala": "diaria", "variable_id": catalogos.CODIGO_VARIABLE["IMERG_PRECIP"],
                               "valor": mm, "calidad": "late"})  # fmt: skip
    return mensual, diario


def _normales_imerg(im: dict, mensual: list[dict], zona_de: dict[str, int]) -> list[dict]:
    """Normal 2001-2020 de IMERG Final (el valor que calculó Sheila) y su desviación (de la serie mensual, en mm/día)."""
    df = pd.DataFrame(mensual)
    df["mes"] = pd.to_datetime(df["fecha"]).dt.month
    df["anio"] = pd.to_datetime(df["fecha"]).dt.year
    a0, a1 = (int(x) for x in im["climatologia"]["periodo"].split("-"))
    base = df[df["anio"].between(a0, a1)]
    desv = base.groupby(["zona_id", "mes"])["valor"].std()
    filas = []
    for pid, valores in im["climatologia"]["mm_dia"].items():
        for mes, media in enumerate(valores, start=1):
            d = desv.get((zona_de[pid], mes))
            filas.append({"zona_id": zona_de[pid], "variable_id": catalogos.CODIGO_VARIABLE["IMERG_PRECIP_M"], "mes": mes, "media": media,
                          "desviacion": None if d is None or d != d else round(float(d), 4), "n_anios": im["climatologia"]["anios_con_dato"][pid][mes - 1],
                          "anio_ini": a0, "anio_fin": a1})  # fmt: skip
    return filas


def _filas_mur(mur: dict) -> list[dict]:
    f = catalogos.CODIGO_FUENTE["MUR_NINO12"]
    filas = []
    for s in mur["semanas"]:
        dia = date.fromisoformat(s["semana"])
        if s.get("sst") is not None:
            filas.append({"codigo": "MUR_NINO12", "fecha": dia, "valor": s["sst"], "fuente_id": f})
        if s.get("anomalia") is not None:
            filas.append({"codigo": "MUR_NINO12_ANOM", "fecha": dia, "valor": s["anomalia"], "fuente_id": f})
    return filas


def _estadisticas(a: pd.Series, b: pd.Series) -> dict | None:
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1, sort=True).dropna()
    if len(j) < 6:
        return None
    return {
        "n": len(j), "periodo_ini": j.index.min().date(), "periodo_fin": j.index.max().date(),
        "correlacion": round(float(j["a"].corr(j["b"])), 4), "sesgo_medio": round(float((j["a"] - j["b"]).mean()), 4),
        "rmse": round(float(((j["a"] - j["b"]) ** 2).mean() ** 0.5), 4),
    }  # fmt: skip


def contrastes(con) -> list[dict]:
    """Mide cuánto coinciden las fuentes independientes. Se guardan en `contraste_fuentes` (también salen en el panel)."""
    filas: list[dict] = []
    vid = catalogos.CODIGO_VARIABLE

    # 1) lluvia mensual: IMERG Final (satélite) vs POWER PRECTOTCORR (reanálisis) en los valles que tienen las dos
    obs = pd.read_sql(
        text("SELECT zona_id, variable_id, fecha, valor FROM observacion WHERE escala = 'mensual' AND variable_id IN (:a, :b)"),
        con, params={"a": vid["IMERG_PRECIP_M"], "b": vid["PRECTOTCORR"]},
    )  # fmt: skip
    obs["fecha"] = pd.to_datetime(obs["fecha"])
    for zid, g in obs.groupby("zona_id"):
        im = g[g["variable_id"] == vid["IMERG_PRECIP_M"]].set_index("fecha")["valor"]
        po = g[g["variable_id"] == vid["PRECTOTCORR"]].set_index("fecha")["valor"]
        e = _estadisticas(im, po) if len(im) and len(po) else None
        if e:
            filas.append({"par": "IMERG_vs_POWER", "zona_id": int(zid), "variable": "lluvia mm/día", "escala": "mensual", **e,
                          "nota": "A = IMERG Final (satélite, 0,1°) · B = POWER PRECTOTCORR (reanálisis, 0,5°). Sesgo = A - B."})  # fmt: skip

    # 2) Niño 1+2: MUR SST semanal (NASA, caja) vs NOAA CPC mensual (OISST), promediando MUR por mes
    ind = pd.read_sql(text("SELECT codigo, fecha, valor FROM indice_climatico WHERE codigo IN ('MUR_NINO12','MUR_NINO12_ANOM','NINO12','NINO12_ANOM')"), con)
    ind["fecha"] = pd.to_datetime(ind["fecha"])
    for mur_c, cpc_c, etiqueta in (("MUR_NINO12_ANOM", "NINO12_ANOM", "anomalía °C"), ("MUR_NINO12", "NINO12", "temperatura del mar °C")):
        m = ind[ind["codigo"] == mur_c].set_index("fecha")["valor"].resample("MS").mean()
        c = ind[ind["codigo"] == cpc_c].set_index("fecha")["valor"]
        e = _estadisticas(m, c) if len(m) and len(c) else None
        if e:
            filas.append({"par": "MURnino12_vs_CPCnino12", "zona_id": None, "variable": etiqueta, "escala": "mensual", **e,
                          "nota": "A = MUR SST (NASA, promedio de la caja Niño 1+2) · B = NOAA CPC Niño 1+2. Las anomalías usan bases distintas (MUR 2003-2014, CPC 1991-2020): el sesgo es esperable."})  # fmt: skip
    return filas


def cargar(con, zid: dict[str, int]) -> dict:
    """Carga los aportes de Sheila. Devuelve un resumen (vacío si no hay archivos)."""
    carpeta = localizar()
    if carpeta is None:
        return {}
    im, mur = _leer(carpeta, ARCHIVO_IMERG), _leer(carpeta, ARCHIVO_MUR)

    valles = [(int(r.id), r.lat, r.lon) for r in con.execute(text("SELECT id, lat, lon FROM zona WHERE tipo = 'agricola'")).fetchall()]
    asignacion = asignar_zonas(valles, im["puntos"])
    zona_de: dict[str, int] = {}
    nuevas, siguiente = [], ID_REFERENCIA
    for p in im["puntos"]:
        valle, _ = asignacion[p["id"]]
        if valle is None:
            nuevas.append({"id": siguiente, "nombre": f"{p['nombre']} (punto IMERG)", "region_id": REGION_PIURA, "tipo": "referencia",
                           "lat": p["lat"], "lon": p["lon"], "aproximada": True})  # fmt: skip
            valle, siguiente = siguiente, siguiente + 1
        zona_de[p["id"]] = valle
    if nuevas:
        con.execute(insert(schema.zona), nuevas)

    mensual, diario = _filas_imerg(im, zona_de)
    for lote in (mensual, diario):
        for i in range(0, len(lote), 20000):
            con.execute(insert(schema.observacion), lote[i : i + 20000])
    normales = _normales_imerg(im, mensual, zona_de)
    con.execute(insert(schema.normal_mensual), normales)
    indices = _filas_mur(mur)
    con.execute(insert(schema.indice_climatico), indices)
    cont = contrastes(con)
    if cont:
        con.execute(insert(schema.contraste_fuentes), cont)
    return {
        "carpeta": str(carpeta), "puntos_en_valles": sum(1 for v, _ in asignacion.values() if v), "puntos_de_referencia": len(nuevas),
        "imerg_mensual": len(mensual), "imerg_diario": len(diario), "normales_imerg": len(normales), "mur_nino12_semanal": len(indices),
        "contrastes": len(cont),
    }  # fmt: skip
