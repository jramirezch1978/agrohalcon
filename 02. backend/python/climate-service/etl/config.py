"""Rutas, variables de entorno y cliente HTTP con reintentos (las APIs de la NASA a veces dan 502/503)."""

import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
BACKUP = DATA / "backup"  # JSON/CSV pequeños: SÍ se suben al repo (Plan B de la demo)
RAW = DATA / "raw"  # descargas pesadas: NO se suben (.gitignore)

load_dotenv(RAIZ / ".env")

USER_AGENT = "AgroShift-NASA-SpaceApps/0.1 (hackathon; contacto: ver repositorio)"


def earthdata_token() -> str | None:
    """Token de Earthdata (Perfil -> Generate Token). Vive en .env, nunca en el código."""
    return os.getenv("EARTHDATA_TOKEN") or None


def get_json(
    url: str,
    params: dict | None = None,
    *,
    timeout: float = 60.0,
    reintentos: int = 3,
    headers: dict | None = None,
):
    """GET con reintentos para errores temporales (5xx, timeouts). Devuelve el JSON."""
    ultimo: Exception | None = None
    for intento in range(1, reintentos + 1):
        try:
            r = httpx.get(
                url,
                params=params,
                timeout=timeout,
                headers={"User-Agent": USER_AGENT, **(headers or {})},
                follow_redirects=True,
            )
            if r.status_code >= 500:
                raise httpx.HTTPStatusError(f"{r.status_code} en {url}", request=r.request, response=r)
            r.raise_for_status()
            return r.json()
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as e:
            ultimo = e
            time.sleep(2 * intento)
    raise RuntimeError(f"Falló {url} tras {reintentos} intentos: {ultimo}")


def get_texto(url: str, params: dict | None = None, *, timeout: float = 60.0, reintentos: int = 3) -> str:
    ultimo: Exception | None = None
    for intento in range(1, reintentos + 1):
        try:
            r = httpx.get(
                url,
                params=params,
                timeout=timeout,
                headers={"User-Agent": USER_AGENT},
                follow_redirects=True,
            )
            if r.status_code >= 500:
                raise httpx.HTTPStatusError(f"{r.status_code} en {url}", request=r.request, response=r)
            r.raise_for_status()
            return r.text
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as e:
            ultimo = e
            time.sleep(2 * intento)
    raise RuntimeError(f"Falló {url} tras {reintentos} intentos: {ultimo}")
