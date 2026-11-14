"""Catálogo de cultivos: carga desde JSON y generación de rotaciones candidatas."""

import json
from pathlib import Path

from .schemas import Cultivo, RotacionCandidata


class DatosInvalidos(ValueError):
    """Entrada coherente en formato pero no en contenido (p. ej. un cultivo que no existe)."""


def cargar_catalogo(ruta: str | Path) -> list[Cultivo]:
    """Lee el JSON de Alejandro: una lista de cultivos, o {"cultivos": [...]}."""
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    if isinstance(datos, dict):
        datos = datos.get("cultivos", [])
    return [Cultivo.model_validate(c) for c in datos]


def indexar(cultivos: list[Cultivo]) -> dict[str, Cultivo]:
    return {str(c.id): c for c in cultivos}


def generar_candidatas(cultivos: list[Cultivo]) -> list[RotacionCandidata]:
    """Todas las parejas (cultivo ahora -> cultivo después), incluido el monocultivo (Arroz - Arroz),
    que suele ser la práctica actual. Los ids dependen solo del orden del catálogo."""
    n = len(cultivos)
    return [
        RotacionCandidata(
            id=i * n + j + 1,
            nombre=f"{c1.nombre} - {c2.nombre}",
            cultivo1Id=c1.id,
            cultivo2Id=c2.id,
        )
        for i, c1 in enumerate(cultivos)
        for j, c2 in enumerate(cultivos)
    ]
