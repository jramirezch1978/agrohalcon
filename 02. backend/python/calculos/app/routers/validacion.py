from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.calculos.validacion import anios_disponibles, calcular_validacion
from app.dependencias import cliente_power
from app.fuentes.nasa_power import ClienteNasaPower, NasaPowerError

router = APIRouter()


@router.get("/validacion/anios")
async def validacion_anios(
    lat: float = Query(-5.19, ge=-90, le=90),
    lon: float = Query(-80.63, ge=-180, le=180),
) -> dict:
    """Años con datos reales para la máquina del tiempo (el frontend solo ofrece estos)."""
    return anios_disponibles(lat, lon)


@router.get("/validacion")
async def validacion(
    anio: int = Query(2017, ge=2001, le=2100),
    lat: float = Query(-5.19, ge=-90, le=90),
    lon: float = Query(-80.63, ge=-180, le=180),
    lang: Literal["es", "en"] = "es",
    cliente: ClienteNasaPower = Depends(cliente_power),
) -> dict:
    try:
        return await calcular_validacion(anio, lat, lon, lang, cliente)
    except NasaPowerError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
