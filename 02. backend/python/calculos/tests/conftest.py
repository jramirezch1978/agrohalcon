"""Respuestas falsas con la MISMA forma que la NASA POWER API real (verificada en nov. 2026)."""
from __future__ import annotations

import os
from datetime import date, timedelta

import pytest

os.environ["NOAA_CONTRASTE"] = "0"   # los tests no salen a internet (contraste con NOAA apagado)

from app.fuentes.nasa_power import MESES_POWER


def respuesta_power(parametros: dict[str, dict[str, float]]) -> dict:
    return {
        "type": "Feature",
        "properties": {"parameter": parametros},
        "header": {"fill_value": -999.0},
    }


def diario_falso(fin: date, dias: int, valores: dict[str, float], relleno_final: int = 3) -> dict:
    """`dias` días con valores constantes y los últimos `relleno_final` en -999 (latencia)."""
    params: dict[str, dict[str, float]] = {p: {} for p in valores}
    for i in range(dias):
        d = fin - timedelta(days=dias - 1 - i)
        k = d.strftime("%Y%m%d")
        for p, v in valores.items():
            params[p][k] = -999.0 if i >= dias - relleno_final else v
    return respuesta_power(params)


def clima_falso(valores: dict[str, float]) -> dict:
    return respuesta_power({p: {**{m: v for m in MESES_POWER}, "ANN": v} for p, v in valores.items()})


@pytest.fixture(autouse=True)
def precalculado_vacio(tmp_path, monkeypatch):
    """Cada test arranca SIN precalculados (carpeta vacía). Devuelve la carpeta para escribir JSON."""
    from app.config import ajustes
    carpeta = tmp_path / "precalculado"
    carpeta.mkdir()
    monkeypatch.setattr(ajustes(), "precalculado_dir", carpeta)
    return carpeta


def mur_json(semanas: list[tuple[str, float | None, float | None]]) -> dict:
    return {
        "metadatos": {"producto": "MUR SST", "version": "v4.1"},
        "semanas": [{"semana": s, "sst": sst, "anomalia": an, "dias": 7} for s, sst, an in semanas],
    }


@pytest.fixture
def umbrales():
    from app.config import umbrales as u
    return u()
