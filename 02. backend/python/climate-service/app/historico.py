"""Series históricas incluidas en el servicio (app/datos_respaldo/) para la "máquina del tiempo" (/validacion) y el respaldo de El Niño.

No consulta internet ni la base de datos (regla 3 del doc 29): son archivos pequeños, ya descargados de fuentes reales y generados con
`python -m etl.respaldo_validacion`. Si falta un archivo, las funciones devuelven None y el que llama usa NASA POWER: nunca se inventa un dato.

- Alerta de El Niño costero: primera semana (MUR SST, NASA) o primer mes (NOAA CPC, no es NASA) de la temporada de lluvias de la costa
  (diciembre del año anterior a abril) con anomalía del mar en Niño 1+2 en nivel medio (≥ +0,5 °C) o alto (≥ +1,5 °C), los mismos umbrales
  de hoy (`app/thresholds.py`). La fecha es el FIN del periodo (domingo o último día del mes): antes no se conocía ese promedio.
- Lluvia de Piura con GPM IMERG (satélite) si el punto está a menos de 25 km de uno de los 12 puntos de Sheila.
"""

from __future__ import annotations

import calendar
import json
import math
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from . import thresholds as T

CARPETA = Path(__file__).resolve().parent / "datos_respaldo"
DISTANCIA_MAX_KM = 25.0
MEDIO, ALTO = T.EL_NINO_SST_C


@lru_cache
def _leer(nombre: str) -> dict | None:
    try:
        return json.loads((CARPETA / nombre).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def limpiar_cache() -> None:  # para las pruebas
    _leer.cache_clear()


def nino12() -> dict | None:
    return _leer("nino12_historico.json")


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


# ------------------------------------------------------------------ lluvia IMERG de Piura
def lluvia_imerg(lat: float, lon: float, anio: int) -> dict[str, Any] | None:
    """{'valores': 12 mm/mes (None = sin dato), 'normal': 12 mm/mes, 'punto', 'producto', 'normalPeriodo'} o None si el punto no es de Piura."""
    datos = _leer("imerg_piura_mensual.json")
    if not datos:
        return None
    punto = min(datos["puntos"], key=lambda p: _km(lat, lon, p["lat"], p["lon"]))
    km = _km(lat, lon, punto["lat"], punto["lon"])
    if km > DISTANCIA_MAX_KM:
        return None
    a0, m0 = int(datos["desde"][:4]), int(datos["desde"][5:7])
    valores: list[float | None] = []
    for mes in range(1, 13):
        i = (anio - a0) * 12 + (mes - m0)
        valores.append(round(punto["mm_mes"][i], 1) if 0 <= i < len(punto["mm_mes"]) and punto["mm_mes"][i] is not None else None)
    if all(v is None for v in valores):
        return None
    return {
        "valores": valores, "normal": [round(v, 1) for v in punto["normal_mm_mes"]], "producto": datos["producto"], "normalPeriodo": datos["normal_periodo"],
        "punto": {"id": punto["id"], "nombre": punto["nombre"], "distanciaKm": round(km, 1)},
    }  # fmt: skip


# ------------------------------------------------------------------ alerta de El Niño costero
def _nivel(v: float) -> str:
    return "alto" if v >= ALTO else "medio" if v >= MEDIO else "bajo"


def _evento(fecha: date, valor: float, **extra: Any) -> dict[str, Any]:
    return {"fecha": fecha.isoformat(), "valor": round(valor, 2), "nivel": _nivel(valor), **extra}


def alertas_nino(anio: int) -> dict[str, Any] | None:
    """Primera señal media y primera alta de El Niño en la temporada de lluvias que termina en abril de `anio`.

    {'fuente', 'producto', 'medio': {...}|None, 'alto': {...}|None, 'maximo': {...}} o None si no hay serie que cubra esa temporada.
    """
    datos = nino12()
    if not datos:
        return None
    ini, fin = date(anio - 1, 12, 1), date(anio, 4, 30)

    semanas = [(date.fromisoformat(s[0]), s[2]) for s in datos["mur"]["semanas"]]
    if semanas and semanas[0][0] <= ini and semanas[-1][0] >= fin - timedelta(days=6):
        puntos = [(lunes + timedelta(days=6), v, {"semana": lunes.isoformat()}) for lunes, v in semanas if ini <= lunes <= fin]
        fuente, producto = "MUR SST", datos["mur"]["producto"]
    else:
        meses = datos["cpc"]["meses"]
        puntos, y, m = [], ini.year, ini.month
        while (y, m) <= (fin.year, fin.month):
            clave = f"{y}-{m:02d}"
            if clave in meses:
                puntos.append((date(y, m, calendar.monthrange(y, m)[1]), meses[clave], {"mes": clave}))
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        if len(puntos) < 5:  # la serie no cubre la temporada
            return None
        fuente, producto = "NOAA CPC Niño 1+2", datos["cpc"]["producto"]

    primero = lambda umbral: next((_evento(f, v, **e) for f, v, e in puntos if v >= umbral), None)  # noqa: E731
    f, v, e = max(puntos, key=lambda p: p[1])
    return {"fuente": fuente, "producto": producto, "medio": primero(MEDIO), "alto": primero(ALTO), "maximo": _evento(f, v, **e)}
