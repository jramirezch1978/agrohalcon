from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError

from app.calculos.recomendacion import calcular_recomendacion
from app.dependencias import cliente_power
from app.fuentes.nasa_power import ClienteNasaPower, NasaPowerError
from app.modelos import PeticionCalculo

router = APIRouter()


@router.post("/calcular")
async def calcular(p: PeticionCalculo, cliente: ClienteNasaPower = Depends(cliente_power)) -> dict:
    """Indicadores + rotaciones (temporal) o plan (permanente) + qué hacer esta quincena."""
    try:
        return await calcular_recomendacion(p, cliente)
    except NasaPowerError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
