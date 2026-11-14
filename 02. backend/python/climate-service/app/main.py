"""Servicio de cálculo de AgroShift (FastAPI, puerto 8000).

Lo llama SOLO la API en Java. No llama a la NASA ni a la base de datos: recibe los datos ya
descargados y devuelve indicadores y rotaciones. Docs interactivas: http://localhost:8000/docs
"""

from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__, asistente
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


@app.post(
    "/rotaciones",
    response_model=list[RotacionResultado],
    response_model_exclude_none=True,
    summary="Puntaje de las rotaciones",
)
def rotaciones(req: RotacionesRequest) -> list[RotacionResultado]:
    try:
        elegidas, _todas = rotaciones_para(
            req.indicadores,
            req.cultivos,
            req.rotaciones,
            req.fecha or date.today(),
            req.top,
            req.rotacionActualId,
            req.incertidumbre,
        )
    except DatosInvalidos as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return [e.resultado for e in elegidas]


@app.post(
    "/recomendacion",
    response_model=RecomendacionResponse,
    response_model_exclude_none=True,
    summary="(propuesto) Todo en una llamada: igual que GET /api/recomendacion de Java",
)
def recomendacion(req: RecomendacionRequest) -> RecomendacionResponse:
    ind = calcular_indicadores(req)
    fecha = req.fecha or date.today()
    try:
        elegidas, todas = rotaciones_para(
            ind, req.cultivos, req.rotaciones, fecha, req.top, req.rotacionActualId, req.incertidumbre
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


# ------------------------------------------------------------------ asistente de IA: guardas (propuesto)
class AsistenteContextoRequest(BaseModel):
    pregunta: str = Field(min_length=1, max_length=600)
    idioma: Literal["es", "en"] = "es"
    recomendacion: RecomendacionResponse


class AsistenteValidarRequest(BaseModel):
    respuesta: str | None = Field(default=None, max_length=4000, description="Lo que contestó el modelo (null si falló)")
    idioma: Literal["es", "en"] = "es"
    recomendacion: RecomendacionResponse


@app.post(
    "/asistente/contexto",
    tags=["asistente (propuesto)"],
    summary="Mensajes listos para enviar a Groq: reglas + solo datos ya calculados + la pregunta",
)
def asistente_contexto(req: AsistenteContextoRequest) -> dict:
    return {
        "mensajes": asistente.mensajes(req.pregunta, req.recomendacion, req.idioma),
        "parametrosSugeridos": {"temperature": 0.2, "max_tokens": 350},
        "nota": "Java envía estos mensajes a Groq (GROQ_API_KEY vive en el backend) y luego llama a /asistente/validar.",
    }


@app.post(
    "/asistente/validar",
    tags=["asistente (propuesto)"],
    summary="Revisa la respuesta del modelo y devuelve la que debe mostrar la app (Plan B si falla)",
)
def asistente_validar(req: AsistenteValidarRequest) -> dict:
    return asistente.respuesta_segura(req.respuesta, req.recomendacion, req.idioma)


@app.post(
    "/asistente/plan-b",
    tags=["asistente (propuesto)"],
    summary="Explicación fija con plantillas (cuando Groq no responde)",
)
def asistente_plan_b(req: AsistenteValidarRequest) -> dict:
    return asistente.explicacion_fija(req.recomendacion, req.idioma)


# ------------------------------------------------------------------ panel de desarrollo (solo si existe la carpeta)
_RAIZ = Path(__file__).resolve().parent.parent
if (_RAIZ / "panel").is_dir():  # no existe en la imagen de Docker: solo es una herramienta de David
    if (_RAIZ / "data" / "backup").is_dir():
        app.mount("/panel/datos", StaticFiles(directory=_RAIZ / "data" / "backup"), name="panel-datos")
    app.mount("/panel", StaticFiles(directory=_RAIZ / "panel", html=True), name="panel")
