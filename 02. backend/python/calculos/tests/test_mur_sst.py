import json
from datetime import date

import numpy as np
import pandas as pd
import pytest

from app.calculos.el_nino import en_zona_costera, indicador_el_nino, primera_alerta
from app.fuentes.mur_sst import a_semanas, media_caja
from app.fuentes.precalculado import ARCHIVO_MUR, serie_mur
from tests.conftest import mur_json

HOY = date(2026, 11, 14)


def escribir(carpeta, semanas):
    (carpeta / ARCHIVO_MUR).write_text(json.dumps(mur_json(semanas)), encoding="utf-8")


# ---------- Procesamiento (lo usa el script) ----------

def test_media_caja_pondera_por_latitud_e_ignora_tierra():
    df = pd.DataFrame({
        "time": ["2017-01-01T09:00:00Z"] * 3,
        "latitude": [0.0, -60.0, -5.0],
        "longitude": [-85.0, -85.0, -80.0],
        "sstAnom": [1.0, 4.0, np.nan],  # la celda en NaN es tierra
    })
    s = media_caja(df, "sstAnom")
    # pesos cos(0)=1 y cos(60°)=0.5 → (1*1 + 4*0.5) / 1.5 = 2
    assert s.iloc[0] == pytest.approx(2.0)
    assert s.index[0] == pd.Timestamp("2017-01-01")


def test_a_semanas_lunes_y_minimo_de_dias():
    idx = pd.date_range("2017-01-02", "2017-01-12")  # lunes 2 → jueves 12
    diaria = pd.DataFrame({"sst": 25.0, "anomalia": np.arange(len(idx), dtype=float)}, index=idx)
    sem = a_semanas(diaria, min_dias=4)
    assert list(sem.index) == [pd.Timestamp("2017-01-02"), pd.Timestamp("2017-01-09")]
    assert sem.loc["2017-01-02", "anomalia"] == pytest.approx(3.0)   # media de 0..6
    assert sem.loc["2017-01-09", "dias"] == 4
    assert len(a_semanas(diaria, min_dias=5)) == 1                     # la semana de 4 días se omite


# ---------- Lectura del JSON ----------

def test_sin_archivo_devuelve_none():
    assert serie_mur() is None


def test_lectura_json_null_es_nan(precalculado_vacio):
    escribir(precalculado_vacio, [("2017-01-02", 25.1, 0.8), ("2017-01-09", None, None)])
    s = serie_mur()
    assert s.semanas.loc["2017-01-02", "anomalia"] == 0.8
    assert np.isnan(s.semanas.loc["2017-01-09", "anomalia"])
    assert s.metadatos["version"] == "v4.1"


# ---------- Indicador ----------

def test_indicador_sin_dato_no_inventa(umbrales):
    ind = indicador_el_nino(-5.19, -80.63, "es", umbrales, HOY)
    assert ind["valor"] is None and ind["nivel"] is None
    assert ind["fuente"] == "sin dato" and ind["disponible"] is False


def test_indicador_usa_ultima_semana_valida(precalculado_vacio, umbrales):
    escribir(precalculado_vacio, [("2026-10-26", 26.8, 0.9), ("2026-11-02", 27.2, 2.4), ("2026-11-09", None, None)])
    ind = indicador_el_nino(-5.19, -80.63, "es", umbrales, HOY)
    assert ind["valor"] == 2.4 and ind["nivel"] == "alto" and ind["fuente"] == "MUR SST"
    assert ind["semana"] == "2026-11-02" and ind["sst"] == 27.2
    assert ind["aplicaAjusteCosta"] is True and ind["desactualizado"] is False


def test_indicador_fuera_de_la_costa_solo_informa(precalculado_vacio, umbrales):
    escribir(precalculado_vacio, [("2026-11-02", 27.2, 2.4)])
    ind = indicador_el_nino(-1.29, 36.82, "en", umbrales, HOY)  # Nairobi
    assert ind["valor"] == 2.4 and ind["aplicaAjusteCosta"] is False


def test_indicador_avisa_si_esta_desactualizado(precalculado_vacio, umbrales):
    escribir(precalculado_vacio, [("2026-09-01", 25.0, 1.0)])
    assert indicador_el_nino(-5.19, -80.63, "es", umbrales, HOY)["desactualizado"] is True


def test_zona_costera():
    assert en_zona_costera(-5.19, -80.63)      # Piura
    assert en_zona_costera(-2.2, -79.9)        # Guayaquil
    assert not en_zona_costera(-12.05, -77.04)  # Lima
    assert not en_zona_costera(-1.29, 36.82)    # Nairobi


# ---------- Alerta ----------

def test_primera_alerta_es_la_primera_semana_alta(precalculado_vacio, umbrales):
    escribir(precalculado_vacio, [
        ("2016-12-26", 23.0, 0.3), ("2017-01-02", 24.0, 0.9), ("2017-01-09", 25.0, 1.7),
        ("2017-01-16", 26.0, 2.5), ("2017-04-03", 27.0, 3.0),
    ])
    s = serie_mur()
    assert primera_alerta(s, "2016-12-01", "2017-03-31", umbrales)["semana"] == "2017-01-09"
    assert primera_alerta(s, "2016-12-01", "2017-03-31", umbrales, nivel="medio")["semana"] == "2017-01-02"
    assert primera_alerta(s, "2016-12-01", "2016-12-31", umbrales) is None
