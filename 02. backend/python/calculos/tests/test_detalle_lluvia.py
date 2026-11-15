"""/validacion/detalle: lluvia de un mes día por día y por semana, sin rellenar huecos."""
import asyncio
import json
from datetime import date, timedelta

import pytest

from app.calculos.detalle_lluvia import calcular_detalle, dias_imerg
from app.fuentes.precalculado import ARCHIVO_IMERG, ARCHIVO_IMERG_DIARIO
from tests.test_imerg import IDS
from tests.test_validacion import imerg_validacion

INICIO = date(2017, 2, 1)


def diario(mm: list[float | None]) -> dict:
    return {"inicio": INICIO.isoformat(), "fin": (INICIO + timedelta(days=len(mm) - 1)).isoformat(),
            "fin_final": "2025-09-30", "puntos_id": IDS, "faltan": [], "mm_dia": {i: mm for i in IDS}}


@pytest.fixture
def con_datos(precalculado_vacio):
    # Febrero 2017: 28 días; el 14 llueve 40 mm, la semana 2 es la más lluviosa; marzo solo tiene 2 días
    mm = [1.0] * 28 + [5.0, None]
    mm[13] = 40.0
    (precalculado_vacio / ARCHIVO_IMERG_DIARIO).write_text(json.dumps(diario(mm)), encoding="utf-8")
    (precalculado_vacio / ARCHIVO_IMERG).write_text(json.dumps(imerg_validacion()), encoding="utf-8")


def test_detalle_por_dia_y_semana(con_datos):
    d = asyncio.run(calcular_detalle(2017, 2, -5.19, -80.63, cliente=None))
    assert d["fuente"] == "GPM IMERG" and "Final" in d["producto"]
    assert len(d["dias"]) == 28 and d["total"] == 67.0
    assert d["diaMaximo"] == {"fecha": "2017-02-14", "mm": 40.0}
    assert [s["mm"] for s in d["semanas"]] == [7.0, 46.0, 7.0, 7.0]
    assert d["semanaMaxima"] == 2 and d["diasConLluvia"] == 28
    assert d["normalMes"] == 55.5 and d["veces"] == pytest.approx(67.0 / 55.5, abs=0.01)
    assert d["parcial"] is False


def test_mes_incompleto_no_se_rellena(con_datos):
    d = asyncio.run(calcular_detalle(2017, 3, -5.19, -80.63, cliente=None))
    assert d["dias"][0]["mm"] == 5.0 and all(x["mm"] is None for x in d["dias"][1:])
    assert d["parcial"] is True and d["hasta"] == "2017-03-01" and d["total"] == 5.0
    assert len(d["semanas"]) == 5 and d["semanas"][4]["mm"] is None


def test_fuera_de_piura_no_usa_imerg(con_datos):
    assert dias_imerg(-12.0, -77.0, 2017, 2) is None
