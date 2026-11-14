"""Selección de fuente según la coordenada.

Si la coordenada está a menos de 25 km de un punto del piloto de Piura y existe el precalculado del
producto satelital, se usa ese producto (y "fuente" lo dice). Si no, el que llama usa NASA POWER.
Nunca se rellena: si el satelital no tiene datos suficientes, devuelve None y se usa NASA POWER.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from app.fuentes.piura import punto_cercano
from app.fuentes.precalculado import imerg_piura

FUENTE_IMERG = "GPM IMERG"
MAX_DIAS_ATRASO = 10        # más viejo que esto: se usa igual, pero marcado "desactualizado" y con aviso (supuesto)
MAX_DIAS_USO = 60           # más viejo que esto: ya no es "estado actual"; se usa NASA POWER CON aviso (supuesto)
MIN_FRACCION_DIAS = 0.8     # mínimo de días con dato dentro de la ventana (supuesto)


def _ref_punto(p: dict, km: float) -> dict:
    return {"id": p["id"], "nombre": p["nombre"], "distanciaKm": round(km, 1)}


def _serie_diaria(datos: dict, punto_id: str) -> pd.Series:
    return pd.Series(datos["diario"]["mm_dia"][punto_id], index=pd.to_datetime(datos["diario"]["fechas"]),
                     dtype="float64")


def ultimo_dato_imerg(lat: float, lon: float) -> date | None:
    """Fecha del último día con lluvia IMERG para el punto de Piura más cercano (None si no aplica)."""
    cercano = punto_cercano(lat, lon)
    datos = imerg_piura()
    if cercano is None or datos is None or not datos.get("diario", {}).get("fechas"):
        return None
    validos = _serie_diaria(datos, cercano[0]["id"]).dropna()
    return None if validos.empty else validos.index.max().date()


def lluvia_actual_imerg(lat: float, lon: float, dias: int, hoy: date) -> dict[str, Any] | None:
    """Lluvia media de los últimos `dias` días (IMERG Late) y su normal (IMERG Final 2001-2020), en mm/día."""
    cercano = punto_cercano(lat, lon)
    datos = imerg_piura()
    if cercano is None or datos is None or not datos.get("diario", {}).get("fechas"):
        return None
    punto, km = cercano
    serie = _serie_diaria(datos, punto["id"])
    validos = serie.dropna()
    if validos.empty:
        return None
    atraso = (pd.Timestamp(hoy) - validos.index.max()).days
    if atraso > MAX_DIAS_USO:
        return None
    fin = validos.index.max()
    ventana = serie.loc[fin - pd.Timedelta(days=dias - 1):fin]
    if ventana.count() < MIN_FRACCION_DIAS * dias:
        return None

    clim = datos["climatologia"]["mm_dia"][punto["id"]]
    normales = [clim[m - 1] for m in ventana.index.month]
    if any(n is None for n in normales):
        return None
    meta = datos["metadatos"]["productos"]
    return {
        "valor": float(ventana.mean()),
        "normal": float(sum(normales) / len(normales)),
        "fuente": FUENTE_IMERG,
        "parametro": f"precipitation ({meta['diario']['short_name']} V07 Late; normal {meta['mensual']['short_name']} "
                     f"V07 Final {datos['climatologia']['periodo']})",
        "periodo": {"inicio": ventana.index.min().date().isoformat(), "fin": fin.date().isoformat(), "dias": dias},
        "punto": _ref_punto(punto, km),
        "ultimoDato": fin.date().isoformat(),
        "desactualizado": atraso > MAX_DIAS_ATRASO,
    }


def lluvia_mensual_imerg(lat: float, lon: float, anio: int) -> dict[str, Any] | None:
    """Serie mensual de un año (mm/mes) y su normal 2001-2020, desde IMERG Final. None si no aplica."""
    cercano = punto_cercano(lat, lon)
    datos = imerg_piura()
    if cercano is None or datos is None:
        return None
    punto, km = cercano
    meses = datos["mensual"]["meses"]
    valores = []
    for m in range(1, 13):
        clave = f"{anio}-{m:02d}"
        valores.append(datos["mensual"]["mm_mes"][punto["id"]][meses.index(clave)] if clave in meses else None)
    if all(v is None for v in valores):
        return None
    return {
        "unidad": "mm/mes", "fuente": FUENTE_IMERG, "valores": valores,
        "normal": datos["climatologia"]["mm_mes"][punto["id"]],
        "producto": "GPM_3IMERGM V07 (Final)", "punto": _ref_punto(punto, km),
    }
