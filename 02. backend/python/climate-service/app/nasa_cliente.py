"""Descargas de la NASA que hace SOLO climate-service (regla de arquitectura, doc 29).

- NASA POWER: normal climatológica, últimos 30 días y series mensuales (sin login).
- MUR SST (NASA JPL) vía ERDDAP de NOAA: anomalía de la temperatura del mar.
El token de Earthdata (EARTHDATA_TOKEN) vive aquí para los productos que lo piden (IMERG, SMAP).
Las respuestas se guardan en memoria unas horas; la base de datos la maneja Java.
"""

from __future__ import annotations

import time
from datetime import date, timedelta
from typing import Any, Callable

import httpx

POWER = "https://power.larc.nasa.gov/api/temporal"
ERDDAP = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41anom1day.json"
MESES = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
_cache: dict[str, tuple[float, Any]] = {}
_http = httpx.Client(timeout=httpx.Timeout(40, connect=10), headers={"User-Agent": "AllpaShift/1.0 (NASA Space Apps 2026)"})


def _en_cache(clave: str, horas: float, carga: Callable[[], Any]) -> Any:
    ahora = time.time()
    if clave in _cache and _cache[clave][0] > ahora:
        return _cache[clave][1]
    valor = carga()
    if valor is not None:
        _cache[clave] = (ahora + horas * 3600, valor)
    return valor


def _k(lat: float, lon: float) -> str:
    return f"{lat:.2f},{lon:.2f}"


def climatologia(lat: float, lon: float) -> dict[str, list[float]]:
    """Normal de cada mes (12 valores) de PRECTOTCORR (mm/día), GWETTOP, GWETROOT, T2M_MAX, T2M_MIN, T2M."""
    def carga():
        r = _http.get(f"{POWER}/climatology/point", params={
            "parameters": "PRECTOTCORR,GWETTOP,GWETROOT,T2M_MAX,T2M_MIN,T2M", "community": "AG",
            "longitude": lon, "latitude": lat, "format": "JSON"})
        r.raise_for_status()
        p = r.json()["properties"]["parameter"]
        return {nombre: [float(v[m]) for m in MESES] for nombre, v in p.items()}
    return _en_cache("clim:" + _k(lat, lon), 24 * 30, carga)


def reciente(lat: float, lon: float) -> dict[str, Any] | None:
    """Promedio de los últimos 30 días con dato (POWER tiene 2-3 días de atraso)."""
    def carga():
        hoy = date.today()
        r = _http.get(f"{POWER}/daily/point", params={
            "parameters": "PRECTOTCORR,GWETTOP,T2M_MAX,T2M_MIN", "community": "AG", "longitude": lon, "latitude": lat,
            "start": (hoy - timedelta(days=45)).strftime("%Y%m%d"), "end": hoy.strftime("%Y%m%d"), "format": "JSON"})
        r.raise_for_status()
        p = r.json()["properties"]["parameter"]
        dias = sorted(d for d in p["PRECTOTCORR"] if all(p[k][d] != -999 for k in ("PRECTOTCORR", "GWETTOP", "T2M_MAX")))[-30:]
        if len(dias) < 10:
            return None
        prom = lambda k: sum(p[k][d] for d in dias) / len(dias)  # noqa: E731
        return {"lluviaMmDia": prom("PRECTOTCORR"), "humedadSup": prom("GWETTOP"), "tMax": prom("T2M_MAX"),
                "tMin": prom("T2M_MIN"), "ultimoDia": dias[-1], "dias": len(dias)}
    try:
        return _en_cache("rec:" + _k(lat, lon), 3, carga)
    except Exception:  # noqa: BLE001 - sin dato reciente se usa la normal (y se avisa)
        return None


def sst_anomalia(lat: float, lon: float) -> float | None:
    """Anomalía del mar (°C) ~1° mar adentro frente a la costa del Pacífico; None fuera de la costa o si falla."""
    if lon > -78 or lat < -20 or lat > 5:
        return None
    la, lo = max(-18.0, min(2.0, lat)), min(lon - 0.9, -81.2)

    def carga():
        r = _http.get(f"{ERDDAP}?sstAnom%5B(last)%5D%5B({la:.2f})%5D%5B({lo:.2f})%5D")
        r.raise_for_status()
        v = r.json()["table"]["rows"][0][3]
        return float(v) if v is not None else None
    try:
        return _en_cache("sst:" + _k(la, lo), 6, carga)
    except Exception:  # noqa: BLE001
        return None


def mensual(lat: float, lon: float, anio: int) -> dict[str, list[float | None]]:
    """PRECTOTCORR (mm/día) y GWETROOT por mes de un año (None = sin dato)."""
    def carga():
        r = _http.get(f"{POWER}/monthly/point", params={
            "parameters": "PRECTOTCORR,GWETROOT", "community": "AG", "longitude": lon, "latitude": lat,
            "start": anio, "end": anio, "format": "JSON"})
        r.raise_for_status()
        p = r.json()["properties"]["parameter"]
        return {nombre: [None if v.get(f"{anio}{m:02d}", -999) == -999 else float(v[f"{anio}{m:02d}"]) for m in range(1, 13)]
                for nombre, v in p.items()}
    return _en_cache(f"men:{_k(lat, lon)}:{anio}", 24 * 30, carga)
