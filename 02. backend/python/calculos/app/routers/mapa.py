"""POST /mapa: nivel de riesgo de las zonas fijas de una región (config/zonas_piura.yaml).

Nivel de cada zona = el PEOR nivel entre sus indicadores actuales con dato (lluvia, humedad del suelo,
calor, El Niño). Usa la misma caché de 24 h que /calcular, así que después de la primera vez es rápido.
"""
from __future__ import annotations

import asyncio
from datetime import date
from functools import lru_cache

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.calculos.campana import NIVELES
from app.calculos.indicadores import calcular_indicadores
from app.config import RAIZ
from app.dependencias import cliente_power
from app.fuentes.nasa_power import ClienteNasaPower, NasaPowerError

router = APIRouter()
PARALELO = 3  # pocas peticiones simultáneas a NASA POWER


class PeticionMapa(BaseModel):
    region: str = "piura"
    lang: str = "es"


@lru_cache
def zonas_config() -> dict[str, list[dict]]:
    with open(RAIZ / "config" / "zonas_piura.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


# El Niño es el MISMO valor para toda la costa (si entra, pinta todos los valles del mismo color) y la vegetación
# solo informa: el color de cada valle sale de sus indicadores LOCALES. El Niño se informa aparte (senal_el_nino).
NO_CUENTAN_EN_EL_MAPA = ("elNino", "vegetacion")


def nivel_zona(indicadores: dict, excluir: tuple[str, ...] = NO_CUENTAN_EN_EL_MAPA) -> tuple[str | None, str | None]:
    """(peor nivel, indicador que lo decide) entre los indicadores locales con dato."""
    con_dato = [(ind["nivel"], clave) for clave, ind in indicadores.items() if ind.get("nivel") and clave not in excluir]
    if not con_dato:
        return None, None
    return max(con_dato, key=lambda x: NIVELES.index(x[0]))


def senal_el_nino(indicadores: dict) -> dict | None:
    """El Niño para el aviso del mapa (mismo valor en toda la región), o None si no hay dato."""
    n = indicadores.get("elNino") or {}
    if n.get("valor") is None:
        return None
    return {k: n.get(k) for k in ("valor", "nivel", "fuente", "semana", "unidad")}


@router.post("/mapa")
async def mapa(p: PeticionMapa, cliente: ClienteNasaPower = Depends(cliente_power)) -> dict:
    zonas = zonas_config().get(p.region.lower())
    if zonas is None:
        return {"region": p.region, "zonas": []}
    sem = asyncio.Semaphore(PARALELO)
    hoy = date.today()

    async def una(z: dict) -> dict:
        async with sem:
            r = await calcular_indicadores(z["lat"], z["lon"], p.lang, cliente, hoy)
        nivel, decisivo = nivel_zona(r["indicadores"])
        return {"nombre": z["nombre"], "lat": z["lat"], "lon": z["lon"], "nivel": nivel,
                "indicadorDecisivo": decisivo,
                "fuentes": {k: v["fuente"] for k, v in r["indicadores"].items()},
                "elNino": senal_el_nino(r["indicadores"])}

    try:
        resultado = await asyncio.gather(*(una(z) for z in zonas))
        el_nino = next((z.pop("elNino") for z in resultado if z.get("elNino")), None)
        for z in resultado:
            z.pop("elNino", None)
        return {"region": p.region.lower(), "zonas": resultado, "elNino": el_nino}
    except NasaPowerError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
