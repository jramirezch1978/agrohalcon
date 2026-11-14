"""GPM IMERG V07: funciones puras (las usa el script de descarga). Verificado en OPeNDAP de GES DISC (nov. 2026):

- GPM_3IMERGM  V07 (Final, mensual, 0.1°): /Grid/precipitation (time, lon, lat) en mm/hr. 1998-01 → 2025-09.
- GPM_3IMERGDL V07 (Late, diario, 0.1°):   /precipitation (time, lon, lat) en mm/day. Casi tiempo real.
  (El diario Final, GPM_3IMERGDF, también termina en 2025-09: no sirve para los últimos 30 días.)
- Rejilla: centros en -179.95 + 0.1·i (lon, 3600) y -89.95 + 0.1·j (lat, 1800).
"""
from __future__ import annotations

import calendar
import math

PRODUCTO_MENSUAL = {"short_name": "GPM_3IMERGM", "version": "07", "variable": "/Grid/precipitation",
                    "unidades_origen": "mm/hr", "doi": "10.5067/GPM/IMERG/3B-MONTH/07",
                    "nombre": "GPM IMERG Final Precipitation L3 1 month 0.1° x 0.1° V07"}
PRODUCTO_DIARIO = {"short_name": "GPM_3IMERGDL", "version": "07", "variable": "/precipitation",
                   "unidades_origen": "mm/day", "doi": "10.5067/GPM/IMERGDL/DAY/07",
                   "nombre": "GPM IMERG Late Precipitation L3 1 day 0.1° x 0.1° V07"}
ANIOS_CLIMATOLOGIA = (2001, 2020)


def indice_lon(lon: float) -> int:
    return int(round((lon + 179.95) / 0.1))


def indice_lat(lat: float) -> int:
    return int(round((lat + 89.95) / 0.1))


def mm_hr_a_mm_mes(mm_hr: float, anio: int, mes: int) -> float:
    return mm_hr * 24 * calendar.monthrange(anio, mes)[1]


def mm_hr_a_mm_dia(mm_hr: float) -> float:
    return mm_hr * 24


def valido(x: float | None) -> bool:
    """IMERG usa NaN o valores negativos (relleno -9999.9) para 'sin dato'."""
    return x is not None and not math.isnan(x) and x >= 0
