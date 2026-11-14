"""Cliente de la NASA POWER API (comunidad AG), con caché en disco y reintentos.

Verificado contra la API real (v2.10, nov. 2026):
- Diaria:       /api/temporal/daily/point        start/end = AAAAMMDD, claves "AAAAMMDD"
- Mensual:      /api/temporal/monthly/point      start/end = AAAA,     claves "AAAAMM" (+ "AAAA13" = anual)
- Climatología: /api/temporal/climatology/point  claves "JAN".."DEC" (+ "ANN"); periodo 2001-2025
- Valor de relleno: -999.0. La serie diaria va ~3 días detrás de hoy (los últimos días vienen en -999).
- Unidades: PRECTOTCORR mm/día (también en mensual y climatología), T2M* °C,
  GWETTOP/GWETROOT fracción 0-1 (humedad relativa del suelo, NO m³/m³), ALLSKY_SFC_SW_DWN MJ/m²/día.
- OJO: en mensual y climatología, T2M_MAX / T2M_MIN son el EXTREMO del mes, y T2M_MAX_AVG es el
  PROMEDIO DE ESOS EXTREMOS (verificado: Iowa, octubre → T2M_MAX_AVG 27.1 °C vs media de máximas
  diarias 17.2 °C). Ninguno sirve como "normal" de la máxima diaria: esa normal se calcula con la
  serie diaria 2001-2025 (ver calculos/indicadores.py).
"""
from __future__ import annotations

import asyncio
from datetime import date

import httpx
import numpy as np
import pandas as pd

from app.fuentes.cache import CacheDisco

BASE_URL = "https://power.larc.nasa.gov/api/temporal"
FILL_VALUE = -999.0
MESES_POWER = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
REINTENTAR_HTTP = {429, 500, 502, 503, 504}

# Solo lo que usan los cálculos (lluvia, humedad del suelo superficial y temperatura máxima)
PARAMS_DIARIOS = ["PRECTOTCORR", "GWETTOP", "T2M_MAX"]
PARAMS_CLIMATOLOGIA = ["PRECTOTCORR", "GWETTOP"]
# Mismo periodo que la climatología de NASA POWER, para que todas las "normales" sean comparables
ANIOS_NORMAL = (2001, 2025)


class NasaPowerError(RuntimeError):
    pass


def _coord(x: float) -> float:
    # 2 decimales (~1 km) basta: la rejilla de POWER es de 0.5° x 0.625°. Así la caché se reutiliza.
    return round(float(x), 2)


def _serie(valores: dict[str, float]) -> pd.Series:
    s = pd.Series(valores, dtype="float64")
    return s.where(s != FILL_VALUE, np.nan)


def parsear_diario(datos: dict) -> pd.DataFrame:
    """JSON diario → DataFrame con índice de fechas y una columna por parámetro (NaN = sin dato)."""
    cols = {p: _serie(v) for p, v in datos["properties"]["parameter"].items()}
    df = pd.DataFrame(cols)
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    return df.sort_index()


def parsear_mensual(datos: dict) -> pd.DataFrame:
    """JSON mensual → DataFrame con índice de periodos mensuales. Se descarta la clave anual AAAA13."""
    cols = {p: _serie(v) for p, v in datos["properties"]["parameter"].items()}
    df = pd.DataFrame(cols)
    df = df[~df.index.str.endswith("13")]
    df.index = pd.PeriodIndex(pd.to_datetime(df.index, format="%Y%m"), freq="M")
    return df.sort_index()


def parsear_climatologia(datos: dict) -> pd.DataFrame:
    """JSON de climatología → DataFrame con índice 1..12 (mes). Se descarta ANN."""
    cols = {p: _serie(v) for p, v in datos["properties"]["parameter"].items()}
    df = pd.DataFrame(cols).reindex(MESES_POWER)
    df.index = range(1, 13)
    return df


class ClienteNasaPower:
    def __init__(
        self,
        cache: CacheDisco,
        timeout_s: float = 30,
        reintentos: int = 3,
        espera_base_s: float = 1.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.cache = cache
        self.timeout_s = timeout_s
        self.reintentos = reintentos
        self.espera_base_s = espera_base_s
        self.transport = transport  # para pruebas (httpx.MockTransport)

    async def _get(self, ruta: str, params: dict[str, str | float]) -> dict:
        params = {**params, "community": "AG", "format": "JSON"}
        clave = ruta + "?" + "&".join(f"{k}={params[k]}" for k in sorted(params))
        if (en_cache := self.cache.leer(clave)) is not None:
            return en_cache

        ultimo_error = ""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=self.timeout_s, transport=self.transport) as cli:
            for intento in range(self.reintentos + 1):
                try:
                    r = await cli.get(ruta, params=params)
                    if r.status_code in REINTENTAR_HTTP:
                        ultimo_error = f"HTTP {r.status_code}"
                    elif r.status_code != 200:
                        # 422 = parámetros inválidos: no tiene sentido reintentar
                        raise NasaPowerError(f"NASA POWER respondió HTTP {r.status_code}: {r.text[:300]}")
                    else:
                        datos = r.json()
                        if "properties" not in datos:
                            raise NasaPowerError(f"Respuesta inesperada de NASA POWER: {str(datos)[:300]}")
                        self.cache.guardar(clave, datos)
                        return datos
                except httpx.TransportError as e:  # timeout, conexión caída…
                    ultimo_error = f"{type(e).__name__}: {e}"
                if intento < self.reintentos:
                    await asyncio.sleep(self.espera_base_s * 2**intento)
        raise NasaPowerError(f"NASA POWER no respondió tras {self.reintentos + 1} intentos ({ultimo_error})")

    async def diario(self, lat: float, lon: float, inicio: date, fin: date,
                     parametros: list[str] = PARAMS_DIARIOS) -> pd.DataFrame:
        datos = await self._get("/daily/point", {
            "parameters": ",".join(parametros), "latitude": _coord(lat), "longitude": _coord(lon),
            "start": inicio.strftime("%Y%m%d"), "end": fin.strftime("%Y%m%d"),
        })
        return parsear_diario(datos)

    async def mensual(self, lat: float, lon: float, anio_inicio: int, anio_fin: int,
                      parametros: list[str] = PARAMS_DIARIOS) -> pd.DataFrame:
        datos = await self._get("/monthly/point", {
            "parameters": ",".join(parametros), "latitude": _coord(lat), "longitude": _coord(lon),
            "start": anio_inicio, "end": anio_fin,
        })
        return parsear_mensual(datos)

    async def climatologia(self, lat: float, lon: float,
                           parametros: list[str] = PARAMS_CLIMATOLOGIA) -> pd.DataFrame:
        datos = await self._get("/climatology/point", {
            "parameters": ",".join(parametros), "latitude": _coord(lat), "longitude": _coord(lon),
        })
        return parsear_climatologia(datos)
