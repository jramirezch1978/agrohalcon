"""Contraste del dato de El Niño (MUR SST) con el índice SEMANAL Niño 1+2 de NOAA CPC. NO es un dato de la NASA.

https://www.cpc.ncep.noaa.gov/data/indices/wksst9120.for  (OISST v2.1, anomalías frente a 1991-2020)
Formato de cada línea: " 04NOV2026     27.0 5.6     29.5 4.4     30.1 3.3     30.1 1.5"
                         semana (centrada en miércoles)  Niño1+2 (SST, anom)  Niño3  Niño34  Niño4
Solo se usa para decir si el dato de MUR SST concuerda; nunca reemplaza al dato de la NASA.
Se guarda 24 h en disco. Si NOAA no responde, devuelve None y la app sigue igual (sin contraste).
Apagar con NOAA_CONTRASTE=0 (los tests lo apagan).
"""
from __future__ import annotations

import os
from datetime import date, datetime

import httpx

from app.fuentes.cache import CacheDisco

URL = "https://www.cpc.ncep.noaa.gov/data/indices/wksst9120.for"
FUENTE = "NOAA OISST v2.1 (CPC, semanal)"


def parsear(texto: str) -> list[dict]:
    """[{semana: 'YYYY-MM-DD', sst, anomalia}] de las líneas con dato (las de cabecera se saltan)."""
    salida = []
    for linea in texto.splitlines():
        partes = linea.split()
        if len(partes) < 3:
            continue
        try:
            semana = datetime.strptime(partes[0].title(), "%d%b%Y").date()
            salida.append({"semana": semana.isoformat(), "sst": float(partes[1]), "anomalia": float(partes[2])})
        except ValueError:
            continue
    return salida


def mas_cercana(serie: list[dict], dia: date, max_dias: int) -> dict | None:
    if not serie:
        return None
    fila = min(serie, key=lambda f: abs((date.fromisoformat(f["semana"]) - dia).days))
    return fila if abs((date.fromisoformat(fila["semana"]) - dia).days) <= max_dias else None


async def serie_noaa(cache: CacheDisco | None, timeout_s: float = 6) -> list[dict] | None:
    if os.getenv("NOAA_CONTRASTE", "1") == "0":
        return None
    if cache and (guardado := cache.leer("noaa:wksst9120")) is not None:
        return guardado
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as cli:
            r = await cli.get(URL)
            r.raise_for_status()
            serie = parsear(r.text)
    except httpx.HTTPError:
        return None
    if not serie:
        return None
    if cache:
        cache.guardar("noaa:wksst9120", serie)
    return serie


def contraste(anomalia_mur: float, semana_mur: str, serie: list[dict] | None, u: dict) -> dict | None:
    """Compara la semana de MUR (lunes) con la semana de NOAA más cercana (centrada en miércoles)."""
    if not serie:
        return None
    uc = u.get("contraste_nino", {})
    lunes = date.fromisoformat(semana_mur)
    fila = mas_cercana(serie, date.fromordinal(lunes.toordinal() + 2), int(uc.get("max_dias_entre_semanas", 10)))
    if fila is None:
        return None
    dif = round(abs(anomalia_mur - fila["anomalia"]), 2)
    return {"fuente": FUENTE, "url": URL, "semana": fila["semana"], "anomalia": fila["anomalia"], "sst": fila["sst"],
            "diferencia": dif, "concuerda": dif <= float(uc.get("max_diferencia_c", 1.0)),
            "nota": "Base NOAA 1991-2020; base MUR 2003-2014: unas décimas de diferencia son normales."}
