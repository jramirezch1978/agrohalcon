"""POST /indicadores-punto: indicadores actuales de UN punto y su nivel (peor indicador).

Lo usa la API Java (agro-service) para el mapa por valle: recorre las zonas de la base de datos (18 valles)
y pide el nivel de cada una. Mismo cálculo que /mapa, pero para cualquier coordenada.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.calculos.indicadores import calcular_indicadores
from app.dependencias import cliente_power
from app.fuentes.nasa_power import ClienteNasaPower, NasaPowerError
from app.routers.mapa import nivel_zona

router = APIRouter()


class PeticionPunto(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    lang: str = "es"


@router.post("/indicadores-punto")
async def indicadores_punto(p: PeticionPunto, cliente: ClienteNasaPower = Depends(cliente_power)) -> dict:
    try:
        r = await calcular_indicadores(p.lat, p.lon, p.lang, cliente)
    except NasaPowerError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    nivel, decisivo = nivel_zona(r["indicadores"])
    return {"lat": p.lat, "lon": p.lon, "nivel": nivel, "indicadorDecisivo": decisivo,
            "indicadores": r["indicadores"], "fecha": r["fecha"]}
