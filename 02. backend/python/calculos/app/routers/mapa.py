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


def nivel_zona(indicadores: dict) -> tuple[str | None, str | None]:
    """(peor nivel, indicador que lo decide) entre los indicadores con dato."""
    con_dato = [(ind["nivel"], clave) for clave, ind in indicadores.items() if ind.get("nivel")]
    if not con_dato:
        return None, None
    return max(con_dato, key=lambda x: NIVELES.index(x[0]))


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
                "fuentes": {k: v["fuente"] for k, v in r["indicadores"].items()}}

    try:
        return {"region": p.region.lower(), "zonas": await asyncio.gather(*(una(z) for z in zonas))}
    except NasaPowerError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
