"""Modelos Pydantic de entrada (la salida es un dict documentado en cada cálculo)."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PeticionCalculo(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    lang: Literal["es", "en"] = "es"
    tipoCultivo: Literal["temporal", "permanente"] = "temporal"
    mesSiembra: str | None = Field(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    cultivo: str | None = None
    # Catálogo que envía Java. Se tipa en la fase 2 (rotaciones y campaña).
    catalogo: list[dict[str, Any]] = Field(default_factory=list)
