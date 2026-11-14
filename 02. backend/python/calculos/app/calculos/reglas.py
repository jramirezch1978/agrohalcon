"""Reglas puras de nivel (sin red), compartidas por todos los cálculos. Umbrales en config/umbrales.yaml."""
from __future__ import annotations


def anomalia_pct(actual: float, normal: float) -> float:
    if normal == 0:
        return 0.0 if actual == 0 else float("inf")
    return (actual - normal) / normal * 100


def nivel_por_corte(x: float, medio: float, alto: float) -> str:
    """x < medio → bajo; medio ≤ x ≤ alto → medio; x > alto → alto."""
    if x > alto:
        return "alto"
    if x >= medio:
        return "medio"
    return "bajo"


def nivel_lluvia(actual: float, normal: float, u: dict) -> tuple[str, float, str]:
    """Devuelve (nivel, anomalía %, dirección). Riesgo por falta o por exceso."""
    minimo = u["minimo_significativo_mm_dia"]
    anom = anomalia_pct(actual, normal)
    if actual < minimo and normal < minimo:
        return "bajo", anom, "estacion_seca"
    direccion = "deficit" if anom < 0 else "exceso"
    return nivel_por_corte(abs(anom), u["medio"], u["alto"]), anom, direccion


def nivel_humedad(actual: float, normal: float, u: dict) -> tuple[str, float, str]:
    """Solo el déficit es riesgo (sequía). El exceso de agua lo mide el indicador de lluvia."""
    anom = anomalia_pct(actual, normal)
    if anom >= 0:
        return "bajo", anom, "exceso"
    return nivel_por_corte(-anom, u["medio"], u["alto"]), anom, "deficit"


def nivel_calor(diferencia_c: float, u: dict) -> str:
    return nivel_por_corte(diferencia_c, u["medio"], u["alto"])


def nivel_el_nino(anomalia_c: float, u: dict) -> str:
    return nivel_por_corte(anomalia_c, u["medio"], u["alto"])
