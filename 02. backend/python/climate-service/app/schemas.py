"""Contrato del backend (PDF "AgroShift: Contrato del backend"): JSON en camelCase.

Regla del equipo: nadie cambia un campo sin avisar. Los campos marcados "(extra)" son OPCIONALES y
se agregaron sin romper el contrato; si no se envían, el servicio se comporta exactamente como el PDF.
"""

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .meses import parse_meses

Nivel = Literal["bajo", "medio", "alto"]
Agua = Literal["baja", "media", "alta"]
IdCultivo = int | str


class _Base(BaseModel):
    # Se ignoran campos desconocidos para que Java pueda agregar datos sin romper este servicio.
    model_config = ConfigDict(extra="ignore")


# ------------------------------------------------------------------ POST /indicadores
class ClimaActual(_Base):
    lluviaMm: float = Field(ge=0, description="Lluvia diaria promedio reciente (mm/día)")
    humedadSuelo: float = Field(ge=0, le=1, description="Humedad del suelo (m3/m3 en SMAP)")
    tempMaxC: float
    tempMinC: float | None = None  # reservado para heladas
    sstAnomaliaC: float = Field(description="Anomalía de la temperatura del mar (MUR SST), °C")


class ClimaHistorico(_Base):
    lluviaMm: float = Field(ge=0)
    humedadSuelo: float = Field(ge=0, le=1)
    tempMaxC: float
    tempMinC: float | None = None


class MetaIndicador(_Base):
    """(extra) Permite declarar la fuente real cuando un dato viene de respaldo, p. ej.
    humedadSuelo = {"fuente": "NASA POWER (GWETTOP)", "unidad": "fracción 0-1"}.
    Así la app nunca dice 'SMAP' si el dato salió de otro lado."""

    fuente: str | None = None
    unidad: str | None = None


class IndicadoresRequest(_Base):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    actual: ClimaActual
    historico: ClimaHistorico
    meta: dict[str, MetaIndicador] = Field(default_factory=dict, description="(extra)")


class Indicador(_Base):
    valor: float
    normal: float
    unidad: str
    nivel: Nivel
    fuente: str


class IndicadoresResponse(_Base):
    """Mismo formato que el bloque `indicadores` de /api/recomendacion."""

    lluvia: Indicador
    humedadSuelo: Indicador
    calor: Indicador
    elNino: Indicador


# ------------------------------------------------------------------ catálogo y rotaciones
class Cultivo(_Base):
    """Fila de la tabla `cultivos` (la entrega Alejandro en JSON)."""

    id: IdCultivo
    nombre: str
    tempMinC: float
    tempMaxC: float
    aguaNecesaria: Agua
    mesesSiembra: list[int] = Field(default_factory=list)
    mesesCosecha: list[int] = Field(default_factory=list)
    accionesPorEtapa: Any = None

    @field_validator("mesesSiembra", "mesesCosecha", mode="before")
    @classmethod
    def _meses(cls, v: Any) -> list[int]:
        return parse_meses(v)

    @field_validator("aguaNecesaria", mode="before")
    @classmethod
    def _agua(cls, v: Any) -> Any:
        return v.strip().lower() if isinstance(v, str) else v


class RotacionCandidata(_Base):
    """Fila de la tabla `rotaciones`."""

    id: int
    nombre: str | None = None
    cultivo1Id: IdCultivo
    cultivo2Id: IdCultivo


class RotacionesOpciones(_Base):
    fecha: date | None = Field(default=None, description="(extra) Por defecto, hoy")
    cultivos: list[Cultivo] = Field(min_length=1)
    rotaciones: list[RotacionCandidata] | None = Field(
        default=None,
        description="(extra) Candidatas de la tabla `rotaciones`. Si falta, se generan con el catálogo.",
    )
    rotacionActualId: int | None = Field(
        default=None, description="(extra) Rotación que hoy usa el agricultor: siempre se incluye."
    )
    top: int = Field(default=3, ge=1, le=10, description="(extra) Cuántas rotaciones devolver")


class RotacionesRequest(RotacionesOpciones):
    indicadores: IndicadoresResponse


class RotacionResultado(_Base):
    id: int
    nombre: str
    puntaje: int = Field(ge=0, le=100)
    riesgo: Nivel
    explicacion: str


# ------------------------------------------------------------------ POST /recomendacion (propuesto)
class QueHacer(_Base):
    accion: str
    motivo: str
    fuente: str


class RecomendacionRequest(IndicadoresRequest, RotacionesOpciones):
    """(propuesto) Todo en una llamada: Java manda los datos NASA + el catálogo y reenvía la respuesta."""


class RecomendacionResponse(_Base):
    lat: float
    lon: float
    fecha: date
    indicadores: IndicadoresResponse
    rotaciones: list[RotacionResultado]
    queHacer: QueHacer
