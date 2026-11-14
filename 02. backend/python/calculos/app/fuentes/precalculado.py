"""Lectura de los JSON precalculados por los scripts de scripts/ (el servicio nunca descarga datos pesados).

Si un archivo no existe, las funciones devuelven None y el cálculo dice "sin dato". Nunca se rellena.
Los archivos se releen solos si cambian (p. ej. tras correr el script de actualización).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import ajustes

ARCHIVO_MUR = "mur_sst_nino12.json"
ARCHIVO_IMERG = "imerg_piura.json"

_cache: dict[Path, tuple[float, Any]] = {}


def leer_json(nombre: str) -> dict | None:
    ruta = ajustes().precalculado_dir / nombre
    if not ruta.exists():
        return None
    mtime = ruta.stat().st_mtime
    if ruta not in _cache or _cache[ruta][0] != mtime:
        _cache[ruta] = (mtime, json.loads(ruta.read_text(encoding="utf-8")))
    return _cache[ruta][1]


@dataclass
class SerieMur:
    semanas: pd.DataFrame  # índice = lunes de la semana; columnas sst, anomalia (°C, NaN = sin dato), dias
    metadatos: dict


def imerg_piura() -> dict | None:
    """JSON de GPM IMERG para los puntos de Piura (ver scripts/descargar_imerg.py), o None."""
    return leer_json(ARCHIVO_IMERG)


def serie_mur() -> SerieMur | None:
    datos = leer_json(ARCHIVO_MUR)
    if not datos or not datos.get("semanas"):
        return None
    df = pd.DataFrame(datos["semanas"])
    df["semana"] = pd.to_datetime(df["semana"])
    df = df.set_index("semana").sort_index()
    df[["sst", "anomalia"]] = df[["sst", "anomalia"]].astype("float64")  # None → NaN
    return SerieMur(df, datos.get("metadatos", {}))
