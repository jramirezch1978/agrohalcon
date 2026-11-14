"""Servicio de cálculo de AgroShift (FastAPI, puerto 8000).

Lo llama SOLO la API en Java. No llama a la NASA ni a la base de datos: recibe los datos ya
descargados y devuelve indicadores y rotaciones. Docs interactivas: http://localhost:8000/docs
"""

from datetime import date

from fastapi import FastAPI, HTTPException

from . import __version__
from .crops import DatosInvalidos
from .indicators import calcular_indicadores
from .que_hacer import construir_que_hacer
from .rotations import rotaciones_para
from .schemas import (
    IndicadoresRequest,
    IndicadoresResponse,
    RecomendacionRequest,
    RecomendacionResponse,
    RotacionesRequest,
    RotacionResultado,
)

app = FastAPI(
    title="AgroShift · climate-service",
    version=__version__,
    description="Indicadores de riesgo (lluvia, humedad del suelo, calor, El Niño) y puntaje de "
    "rotaciones con datos de la NASA. Reglas verificables: no usa IA para calcular.",
)


@app.get("/salud", summary="Estado del servicio")
def salud() -> dict[str, str]:
    return {"estado": "ok", "servicio": "climate-service", "version": __version__}


@app.post("/indicadores", response_model=IndicadoresResponse, summary="Los 4 indicadores")
def indicadores(req: IndicadoresRequest) -> IndicadoresResponse:
    return calcular_indicadores(req)


@app.post("/rotaciones", response_model=list[RotacionResultado], summary="Puntaje de las rotaciones")
def rotaciones(req: RotacionesRequest) -> list[RotacionResultado]:
    try:
        elegidas, _todas = rotaciones_para(
            req.indicadores,
            req.cultivos,
            req.rotaciones,
            req.fecha or date.today(),
            req.top,
            req.rotacionActualId,
        )
    except DatosInvalidos as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return [e.resultado for e in elegidas]


@app.post(
    "/recomendacion",
    response_model=RecomendacionResponse,
    summary="(propuesto) Todo en una llamada: igual que GET /api/recomendacion de Java",
)
def recomendacion(req: RecomendacionRequest) -> RecomendacionResponse:
    ind = calcular_indicadores(req)
    fecha = req.fecha or date.today()
    try:
        elegidas, todas = rotaciones_para(
            ind, req.cultivos, req.rotaciones, fecha, req.top, req.rotacionActualId
        )
    except DatosInvalidos as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return RecomendacionResponse(
        lat=req.lat,
        lon=req.lon,
        fecha=fecha,
        indicadores=ind,
        rotaciones=[e.resultado for e in elegidas],
        queHacer=construir_que_hacer(ind, elegidas, todas),
    )
