"""Catálogo de cultivos: el que envía Java en 'catalogo' o, si no llega, data/catalogo_ejemplo.json."""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.config import RAIZ

Nivel = Literal["bajo", "medio", "alto"]
Texto = dict[str, str]  # {"es": ..., "en": ...}


def _texto(v: Any) -> Texto:
    """Java puede mandar "Arroz" o {"es": "Arroz", "en": "Rice"}."""
    return {"es": v, "en": v} if isinstance(v, str) else v


class Etapa(BaseModel):
    id: str
    nombre: Texto
    meses: list[int]

    @field_validator("nombre", mode="before")
    @classmethod
    def normalizar_nombre(cls, v: Any) -> Texto:
        return _texto(v)


class AccionCatalogo(BaseModel):
    etapa: str = "*"                                              # "*" = cualquier etapa
    si: Literal["calor", "frio", "lluvia_exceso", "deficit"]       # componente de riesgo que la activa
    nivel: Nivel = "medio"                                         # nivel mínimo que la activa
    accion: Texto

    @field_validator("accion", mode="before")
    @classmethod
    def normalizar_accion(cls, v: Any) -> Texto:
        return _texto(v)


class Cultivo(BaseModel):
    id: str
    nombre: Texto
    tipo: Literal["temporal", "permanente"]
    temp_min: float
    temp_max: float
    agua: Nivel
    usoAgua: Nivel | None = None
    duracion_meses: int | None = Field(default=None, ge=1, le=24)
    meses_siembra: list[int] = Field(default_factory=list)
    tradicional: bool = False
    # Salud del suelo (opcionales: None / False = sin dato, la regla no se aplica)
    familia: str | None = None
    leguminosa: bool = False
    cobertura: bool = False
    profundidad_raiz: Literal["superficial", "media", "profunda"] | None = None
    tolerancia_salinidad: Literal["baja", "media", "alta"] | None = None
    etapas: list[Etapa] = Field(default_factory=list)
    acciones: list[AccionCatalogo] = Field(default_factory=list)

    @field_validator("nombre", mode="before")
    @classmethod
    def normalizar_nombre(cls, v: Any) -> Texto:
        return _texto(v)

    def nombre_en(self, lang: str) -> str:
        return self.nombre.get(lang) or self.nombre.get("es") or self.id

    def etapa_de_mes(self, mes: int) -> Etapa | None:
        return next((e for e in self.etapas if mes in e.meses), None)


@lru_cache
def _ejemplo() -> tuple[Cultivo, ...]:
    datos = json.loads((RAIZ / "data" / "catalogo_ejemplo.json").read_text(encoding="utf-8"))
    return tuple(Cultivo.model_validate(c) for c in datos["cultivos"])


def cargar_catalogo(desde_java: list[dict[str, Any]] | None) -> list[Cultivo]:
    if desde_java:
        return [Cultivo.model_validate(c) for c in desde_java]
    return list(_ejemplo())


def buscar(catalogo: list[Cultivo], id_o_nombre: str) -> Cultivo | None:
    clave = id_o_nombre.strip().lower()
    return next((c for c in catalogo if c.id == clave or clave in {n.lower() for n in c.nombre.values()}), None)
