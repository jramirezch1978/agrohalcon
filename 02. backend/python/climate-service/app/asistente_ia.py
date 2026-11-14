"""POST /asistente/preguntar: el asistente de IA completo, en el servicio Python (decisión del equipo, 14-nov-2026).

Antes Java armaba el prompt, llamaba a Groq y luego llamaba a /asistente/validar. Ahora todo ocurre aquí, en un solo paso,
para que la clave de Groq no salga de este servicio (el repositorio es público):

    pregunta + recomendación calculada → prompt cerrado (asistente.mensajes) → Groq gpt-oss-20b (groq_cliente)
    → validación sin IA (asistente.validar_respuesta: ni números, ni cultivos, ni satélites que no estén en los datos)
    → respuesta del modelo si pasa; si no, el Plan B con plantillas (asistente.explicacion_fija).

La IA solo REDACTA lo que ya calcularon las reglas. No cambia el puntaje ni la recomendación.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from . import asistente, groq_cliente
from .schemas import RecomendacionResponse

router = APIRouter(prefix="/asistente", tags=["asistente (Groq)"])


class PreguntaRequest(BaseModel):
    pregunta: str = Field(min_length=1, max_length=400)
    idioma: Literal["es", "en"] = "es"
    recomendacion: RecomendacionResponse = Field(description="La recomendación ya calculada (forma del contrato): lo único que el modelo puede usar")


def _cliente(request: Request) -> str:
    """Quién pregunta: la primera IP de X-Forwarded-For (el api-gateway la pone) o la del socket. Solo para el límite."""
    adelante = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    return (adelante or (request.client.host if request.client else "desconocido"))[:64]


@router.get("/estado", summary="¿Está Groq configurado? (nunca devuelve la clave)")
def estado() -> dict:
    return {
        "groq": groq_cliente.disponible(), "modelo": groq_cliente.modelo(), "licenciaModelo": groq_cliente.LICENCIA,
        "limites": {"porMinutoPorCliente": groq_cliente.limitador.por_cliente, "porMinuto": groq_cliente.limitador.global_min, "porDia": groq_cliente.limitador.diario},
        "sinClave": "Sin GROQ_API_KEY responde el Plan B con plantillas (sin IA).",
    }  # fmt: skip


@router.post("/preguntar", summary="Responde con Groq (gpt-oss-20b) y valida la respuesta; si algo falla, Plan B con plantillas")
def preguntar(req: PreguntaRequest, request: Request) -> dict:
    motivo = None if groq_cliente.disponible() else "sin clave de Groq (GROQ_API_KEY)"
    if motivo is None:
        motivo = groq_cliente.limitador.permitir(_cliente(request))
    if motivo is None:
        r = groq_cliente.completar(asistente.mensajes(req.pregunta, req.recomendacion, req.idioma))
        if r.texto:
            salida = asistente.respuesta_segura(r.texto, req.recomendacion, req.idioma)
            if salida["origen"] == "modelo":
                return {**salida, "origen": f"groq:{r.modelo}", "ms": r.ms}
            return {**salida, "modelo": r.modelo, "ms": r.ms}  # el modelo contestó pero la validación lo rechazó: ya viene el Plan B
        motivo = r.error
    return {**asistente.explicacion_fija(req.recomendacion, req.idioma), "origen": f"plantilla ({motivo})", "validacion": None}
