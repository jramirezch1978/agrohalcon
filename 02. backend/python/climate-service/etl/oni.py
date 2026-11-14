"""Índice ONI (NOAA CPC): marca qué años fueron El Niño / La Niña. Sirve para contrastar la señal de
El Niño del mar con la clasificación oficial y para elegir años de validación (1998, 2017...).

OJO: el ONI mide el Pacífico central; para la costa peruana el ENFEN usa el ICEN (Niño 1+2).
https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php
"""

from .config import get_texto

URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"


def serie() -> list[dict]:
    """[{'trimestre': 'DJF', 'anio': 2017, 'oni': 0.4, 'fase': 'neutral'}, ...]"""
    filas: list[dict] = []
    for linea in get_texto(URL).splitlines()[1:]:  # la primera línea es el encabezado
        partes = linea.split()
        if len(partes) < 4:
            continue
        try:
            oni = float(partes[3])
        except ValueError:
            continue
        filas.append({"trimestre": partes[0], "anio": int(partes[1]), "oni": oni, "fase": fase(oni)})
    return filas


def fase(oni: float) -> str:
    if oni >= 0.5:
        return "el_nino"
    if oni <= -0.5:
        return "la_nina"
    return "neutral"


def anios_el_nino(filas: list[dict] | None = None, minimo_trimestres: int = 3) -> list[int]:
    """Años con al menos `minimo_trimestres` trimestres móviles en fase El Niño (ONI >= +0.5)."""
    filas = filas or serie()
    por_anio: dict[int, int] = {}
    for f in filas:
        if f["fase"] == "el_nino":
            por_anio[f["anio"]] = por_anio.get(f["anio"], 0) + 1
    return sorted(a for a, n in por_anio.items() if n >= minimo_trimestres)
