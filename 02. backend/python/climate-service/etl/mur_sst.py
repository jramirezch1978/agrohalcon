"""Temperatura del mar MUR SST (NASA JPL, 1 km) -> seÃ±al de El NiÃ±o costero.

Se lee por ERDDAP de NOAA (sin clave): https://upwell.pfeg.noaa.gov/erddap/griddap/jplMURSST41
(coastwatch.pfeg.noaa.gov estuvo caÃ­do el 14-11-2026; el respaldo oficial es PO.DAAC con token Earthdata).
Producto: https://podaac.jpl.nasa.gov/dataset/MUR-JPL-L4-GLOB-v4.1  Â·  desde 2002-06-01.

La anomalÃ­a NO se toma del dataset 'anom1day' (dio +9 Â°C en un punto costero: por validar). Se calcula
aquÃ­: valor de hoy menos el promedio de la misma Ã©poca (Â±15 dÃ­as) en los aÃ±os base 2003-2022.
"""

import csv
import io
from datetime import date, timedelta

from .config import get_texto
from .zonas import PUNTO_MAR_PIURA

# Se prueban en orden. El 14-11-2026 'upwell' respondiÃ³ a Jhonny, pero desde otra red ninguno de los
# dos respondiÃ³ (timeout). Si fallan ambos, el mÃ³dulo devuelve None y el flujo sigue (ver inputs.py).
# Plan B oficial: PO.DAAC con el token de Earthdata (earthdata_download.py).
SERVIDORES = [
    "https://upwell.pfeg.noaa.gov/erddap/griddap/jplMURSST41.csv",
    "https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41.csv",
]
HORA = "T09:00:00Z"  # MUR publica un campo diario a las 09:00 UTC


class SSTNoDisponible(RuntimeError):
    """NingÃºn servidor ERDDAP respondiÃ³."""


def _leer_csv(texto: str) -> list[tuple[date, float]]:
    filas = list(csv.reader(io.StringIO(texto)))
    salida: list[tuple[date, float]] = []
    for fila in filas[2:]:  # fila 0 = nombres, fila 1 = unidades
        try:
            dia = date.fromisoformat(fila[0][:10])
            valor = float(fila[3])
        except (ValueError, IndexError):
            continue  # vacÃ­o / NaN (nube, tierra)
        if valor == valor:  # descarta NaN
            salida.append((dia, valor))
    return salida


def serie_punto(
    lat: float, lon: float, inicio: date, fin: date, paso_dias: int = 1
) -> list[tuple[date, float]]:
    """SST (Â°C) en un punto. paso_dias=7 baja el volumen para climatologÃ­as de muchos aÃ±os."""
    consulta = (
        f"analysed_sst[({inicio.isoformat()}{HORA}):{paso_dias}:({fin.isoformat()}{HORA})]"
        f"[({lat}):1:({lat})][({lon}):1:({lon})]"
    )
    # La consulta de ERDDAP va tal cual en la URL (los corchetes y parÃ©ntesis no se codifican)
    errores = []
    for servidor in SERVIDORES:
        try:
            return _leer_csv(get_texto(f"{servidor}?{consulta}", timeout=25, reintentos=1))
        except RuntimeError as e:
            errores.append(str(e)[:120])
    raise SSTNoDisponible("NingÃºn servidor ERDDAP respondiÃ³: " + " | ".join(errores))


def sst_dia(lat: float, lon: float, dia: date) -> float | None:
    """SST del dÃ­a pedido, o del mÃ¡s reciente disponible en los 5 dÃ­as previos (hay rezago de ~1-2 dÃ­as)."""
    for atras in range(0, 6):
        d = dia - timedelta(days=atras)
        datos = serie_punto(lat, lon, d, d)
        if datos:
            return datos[0][1]
    return None


def climatologia_dia(
    lat: float, lon: float, dia: date, anios_base: tuple[int, int] = (2003, 2022), ventana_dias: int = 15
) -> float | None:
    """Promedio de la SST en la misma Ã©poca del aÃ±o (Â±ventana) sobre los aÃ±os base."""
    valores: list[float] = []
    serie = serie_punto(lat, lon, date(anios_base[0], 1, 1), date(anios_base[1], 12, 31), paso_dias=3)
    for d, v in serie:
        try:
            mismo_dia = d.replace(year=dia.year)
        except ValueError:  # 29 de febrero
            continue
        # distancia circular en el aÃ±o
        delta = abs((mismo_dia - dia).days)
        delta = min(delta, 365 - delta)
        if delta <= ventana_dias:
            valores.append(v)
    return sum(valores) / len(valores) if valores else None


def anomalia_sst(
    dia: date, punto: tuple[float, float] = PUNTO_MAR_PIURA, anios_base: tuple[int, int] = (2003, 2022)
) -> dict | None:
    """{'sstC', 'normalC', 'anomaliaC', 'punto', 'aniosBase'} o None si el servicio no responde."""
    lat, lon = punto
    try:
        valor = sst_dia(lat, lon, dia)
        normal = climatologia_dia(lat, lon, dia, anios_base)
    except SSTNoDisponible:
        return None
    if valor is None or normal is None:
        return None
    return {
        "sstC": round(valor, 2),
        "normalC": round(normal, 2),
        "anomaliaC": round(valor - normal, 2),
        "punto": {"lat": lat, "lon": lon},
        "aniosBase": list(anios_base),
        "fecha": dia.isoformat(),
        "fuente": "MUR SST v4.1 (NASA JPL) vÃ­a ERDDAP",
    }

