"""Lectura de SMAP con un archivo HDF5 de juguete (misma estructura que SPL3SMP_E): relleno, calidad y píxel correcto."""

import h5py
import numpy as np
import pytest

from etl import smap

PIURA = (-5.19, -80.63)
CHIRA = (-4.90, -80.85)
TUMBES = (-3.57, -80.45)
MAR = (-5.5, -81.5)


@pytest.fixture
def archivo(tmp_path):
    ruta = tmp_path / "SMAP_juguete.h5"
    sm = np.full((smap.FILAS, smap.COLUMNAS), smap.FILL, dtype="float32")
    flag = np.zeros((smap.FILAS, smap.COLUMNAS), dtype="uint16")
    f_piura, c_piura = smap.pixel(*PIURA)
    f_chira, c_chira = smap.pixel(*CHIRA)
    sm[f_piura, c_piura] = 0.21  # buen retrieval
    sm[f_chira, c_chira] = 0.33  # pero con calidad NO recomendada (bit 0)
    flag[f_chira, c_chira] = 1
    # Tumbes se queda en relleno (sin pasada ese día)
    with h5py.File(ruta, "w") as f:
        g = f.create_group("Soil_Moisture_Retrieval_Data_AM")
        g.create_dataset("soil_moisture", data=sm, compression="gzip")
        g.create_dataset("retrieval_qual_flag", data=flag, compression="gzip")
    return ruta


def test_lee_valor_bueno_descarta_calidad_mala_y_marca_sin_cobertura(archivo):
    puntos = {"Piura": PIURA, "Chira": CHIRA, "Tumbes": TUMBES}
    with open(archivo, "rb") as fobj:
        r = smap.leer_puntos(fobj, puntos)
    assert r["Piura"] == {"valor": 0.21, "motivo": None}
    assert r["Chira"]["valor"] is None and r["Chira"]["motivo"] == "calidad no recomendada" and r["Chira"]["bruto"] == 0.33
    assert r["Tumbes"]["valor"] is None and r["Tumbes"]["motivo"] == "sin cobertura ese día"


def test_pixeles_distintos_para_valles_distintos():
    assert len({smap.pixel(*PIURA), smap.pixel(*CHIRA), smap.pixel(*TUMBES)}) == 3
    f, c = smap.pixel(*PIURA)
    assert 0 <= f < smap.FILAS and 0 <= c < smap.COLUMNAS


def test_puntos_en_el_mar_tambien_tienen_pixel_valido_en_la_rejilla():
    f, c = smap.pixel(*MAR)
    assert 0 <= f < smap.FILAS and 0 <= c < smap.COLUMNAS  # la rejilla es global; el dato ahí será relleno
