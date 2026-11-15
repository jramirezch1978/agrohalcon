from fastapi import APIRouter, Depends, Query

from app.config import umbrales
from app.dependencias import cliente_soilgrids
from app.fuentes.soilgrids import ClienteSoilGrids

router = APIRouter()


@router.get("/suelo")
async def suelo(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180),
                cliente: ClienteSoilGrids = Depends(cliente_soilgrids)) -> dict:
    """Tipo de suelo PROPUESTO para la parcela (SoilGrids, ISRIC). Si no hay dato, tipoSuelo = null."""
    return await cliente.suelo(lat, lon, umbrales())
