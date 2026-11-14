"""MUR SST v4.1 en la caja Niño 1+2: funciones puras de procesamiento (las usa el script de descarga).

Verificado en el ERDDAP de NOAA CoastWatch (nov. 2026):
- jplMURSST41          "Multi-scale Ultra-high Resolution (MUR) SST Analysis fv04.1, Global, 0.01°, Daily"
                       variable analysed_sst (degree_C), desde 2002-06-01.
- jplMURSST41anom1day  "MUR SST Analysis Anomaly fv04.1, Global, 0.01°, Daily", variable sstAnom (degree_C).
                       Anomalía creada por NOAA ERD frente a la climatología de JPL MUR 2003-2014.
- Tierra = NaN (la caja toca la costa de Perú y Ecuador): solo se promedia océano.

Verificación de la anomalía de ~+6 °C de oct.-nov. 2026 (no es un error de unidades):
- sstAnom viene en °C (no K); sst - anomalía da ~20-21 °C, la climatología típica de Niño 1+2 en octubre.
- Fuente oficial independiente: índice semanal Niño 1+2 de NOAA CPC (OISST v2.1, base 1991-2020),
  https://www.cpc.ncep.noaa.gov/data/indices/wksst9120.for → semana del 04-nov-2026: SST 27.0 °C, SSTA +5.6 °C.
  MUR da 27.15 °C y +6.05 °C esa semana. La diferencia (~0.4 °C) se explica por la climatología base
  (MUR 2003-2014 vs. CPC 1991-2020) y por el producto (MUR 0.01° vs. OISST 0.25°).
- Control 2017: CPC 25-ene-2017 +1.6 °C; MUR semana del 23-ene-2017 +2.38 °C (misma diferencia de base).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

ERDDAP = "https://coastwatch.pfeg.noaa.gov/erddap/griddap"
DATASET_SST = "jplMURSST41"
DATASET_ANOM = "jplMURSST41anom1day"
VAR_SST = "analysed_sst"
VAR_ANOM = "sstAnom"

# Niño 1+2: 0° a 10° S, 90° a 80° O
CAJA_NINO12 = {"lat": (-10.0, 0.0), "lon": (-90.0, -80.0)}
# 0.01° x 25 = 0.25°: ~1 600 celdas por día. Suficiente para un promedio de una caja de 10° x 10°.
STRIDE = 25
MIN_DIAS_SEMANA = 4  # una semana con menos días válidos no se publica (supuesto)


def media_caja(df: pd.DataFrame, variable: str) -> pd.Series:
    """Promedio diario de la caja ponderado por cos(lat) (área de cada celda), ignorando tierra (NaN).

    df: columnas time, latitude, longitude, <variable> (formato CSV de ERDDAP).
    Devuelve una serie indexada por fecha (día).
    """
    d = df.dropna(subset=[variable]).copy()
    d["peso"] = np.cos(np.deg2rad(d["latitude"].astype(float)))
    d["fecha"] = pd.to_datetime(d["time"]).dt.tz_localize(None).dt.normalize()
    d["vp"] = d[variable].astype(float) * d["peso"]
    g = d.groupby("fecha")
    return (g["vp"].sum() / g["peso"].sum()).rename(variable)


def a_semanas(diaria: pd.DataFrame, min_dias: int = MIN_DIAS_SEMANA) -> pd.DataFrame:
    """Promedio por semana ISO (lunes a domingo). 'semana' = fecha del lunes.

    diaria: índice de fechas, columnas sst y anomalia (pueden tener NaN).
    """
    lunes = diaria.index - pd.to_timedelta(diaria.index.weekday, unit="D")
    g = diaria.groupby(lunes)
    sem = g.mean()
    sem["dias"] = g["anomalia"].count()
    sem = sem[sem["dias"] >= min_dias]
    sem.index.name = "semana"
    return sem
