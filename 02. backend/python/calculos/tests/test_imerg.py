import json
from datetime import date, timedelta

import pytest

from app.fuentes.imerg import indice_lat, indice_lon, mm_hr_a_mm_dia, mm_hr_a_mm_mes, valido
from app.fuentes.piura import distancia_km, punto_cercano
from app.fuentes.precalculado import ARCHIVO_IMERG
from app.fuentes.selector import lluvia_actual_imerg, lluvia_mensual_imerg, ultimo_dato_imerg

HOY = date(2026, 11, 14)
IDS = ["piura", "bajo_piura", "medio_piura", "alto_piura", "valle_chira", "sechura", "san_lorenzo", "huancabamba", "ayabaca"]


def imerg_json(fin: date = date(2026, 11, 13), dias: int = 45, mm_dia: float | None = 0.6,
               clim_dia: float = 0.2) -> dict:
    fechas = [(fin - timedelta(days=dias - 1 - i)).isoformat() for i in range(dias)]
    meses = ["2016-12", "2017-01", "2017-02", "2017-03"]
    return {
        "metadatos": {"productos": {"mensual": {"short_name": "GPM_3IMERGM"}, "diario": {"short_name": "GPM_3IMERGDL"}}},
        "mensual": {"meses": meses, "mm_mes": {i: [5.0, 57.3, 217.7, 587.0] for i in IDS}},
        "climatologia": {"periodo": "2001-2020", "mm_mes": {i: [19.1] * 12 for i in IDS},
                         "mm_dia": {i: [clim_dia] * 12 for i in IDS}},
        "diario": {"fechas": fechas, "mm_dia": {i: [mm_dia] * dias for i in IDS}},
    }


def escribir(carpeta, datos):
    (carpeta / ARCHIVO_IMERG).write_text(json.dumps(datos), encoding="utf-8")


# ---------- Conversión y rejilla ----------

def test_conversion_mm_hr():
    assert mm_hr_a_mm_mes(1.0, 2017, 3) == pytest.approx(744)    # 24 x 31
    assert mm_hr_a_mm_mes(1.0, 2017, 2) == pytest.approx(672)    # 24 x 28
    assert mm_hr_a_mm_mes(1.0, 2016, 2) == pytest.approx(696)    # bisiesto
    assert mm_hr_a_mm_dia(0.5) == pytest.approx(12)


def test_indices_rejilla_0_1_grados():
    assert indice_lon(-179.95) == 0 and indice_lon(179.95) == 3599
    assert indice_lat(-89.95) == 0 and indice_lat(89.95) == 1799
    assert indice_lon(-80.65) == 993


def test_valores_de_relleno_no_son_dato():
    assert valido(0.0) and valido(3.2)
    assert not valido(-9999.9) and not valido(float("nan")) and not valido(None)


# ---------- Puntos de Piura ----------

def test_punto_cercano_y_distancia():
    p, km = punto_cercano(-5.20, -80.62)
    assert p["id"] == "piura" and km < 2
    assert punto_cercano(-12.05, -77.04) is None                # Lima
    assert distancia_km(0, 0, 0, 1) == pytest.approx(111.2, abs=0.2)


# ---------- Selector ----------

def test_selector_sin_archivo_devuelve_none():
    assert lluvia_actual_imerg(-5.19, -80.63, 30, HOY) is None


def test_selector_usa_imerg_en_piura(precalculado_vacio):
    escribir(precalculado_vacio, imerg_json())
    r = lluvia_actual_imerg(-5.19, -80.63, 30, HOY)
    assert r["fuente"] == "GPM IMERG" and r["valor"] == pytest.approx(0.6) and r["normal"] == pytest.approx(0.2)
    assert r["periodo"]["fin"] == "2026-11-13" and r["punto"]["id"] == "piura"


def test_selector_fuera_de_piura_es_none(precalculado_vacio):
    escribir(precalculado_vacio, imerg_json())
    assert lluvia_actual_imerg(-1.29, 36.82, 30, HOY) is None


def test_selector_dato_atrasado_se_marca(precalculado_vacio):
    escribir(precalculado_vacio, imerg_json(fin=date(2026, 10, 1)))         # 44 días de atraso
    r = lluvia_actual_imerg(-5.19, -80.63, 30, HOY)
    assert r["desactualizado"] is True and r["ultimoDato"] == "2026-10-01"


def test_selector_dato_muy_viejo_es_none(precalculado_vacio):
    escribir(precalculado_vacio, imerg_json(fin=date(2026, 8, 1)))          # > 60 días
    assert lluvia_actual_imerg(-5.19, -80.63, 30, HOY) is None
    assert ultimo_dato_imerg(-5.19, -80.63) == date(2026, 8, 1)




def test_selector_con_nulls_no_rellena(precalculado_vacio):
    escribir(precalculado_vacio, imerg_json(mm_dia=None))
    assert lluvia_actual_imerg(-5.19, -80.63, 30, HOY) is None


def test_serie_mensual_2017_y_null_fuera_de_rango(precalculado_vacio):
    escribir(precalculado_vacio, imerg_json())
    r = lluvia_mensual_imerg(-5.19, -80.63, 2017)
    assert r["valores"][:3] == [57.3, 217.7, 587.0]
    assert r["valores"][3] is None                               # abril no está en el archivo → null
    assert r["fuente"] == "GPM IMERG" and r["unidad"] == "mm/mes"
    assert lluvia_mensual_imerg(-5.19, -80.63, 2030) is None
