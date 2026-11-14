"""Lectura tolerante de meses: el catálogo puede traer 9, "9", "sep", "Septiembre" o "setiembre"."""

from typing import Any

_PREFIJOS = {
    "ene": 1, "jan": 1, "feb": 2, "mar": 3, "abr": 4, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "aug": 8, "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12, "dec": 12,
}  # fmt: skip

NOMBRES_MES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]  # fmt: skip


def parse_mes(valor: Any) -> int:
    """Devuelve el mes como entero 1-12 o lanza ValueError con un mensaje claro."""
    if isinstance(valor, bool):
        raise ValueError(f"Mes no válido: {valor!r}")
    if isinstance(valor, int | float):
        mes = int(valor)
    else:
        texto = str(valor).strip().lower()
        if texto.isdigit():
            mes = int(texto)
        else:
            mes = _PREFIJOS.get(texto[:3], 0)
    if not 1 <= mes <= 12:
        raise ValueError(f"Mes no válido: {valor!r} (usa 1-12 o el nombre del mes)")
    return mes


def parse_meses(valores: Any) -> list[int]:
    if valores is None:
        return []
    if isinstance(valores, str | int):
        valores = [valores]
    return sorted({parse_mes(v) for v in valores})
