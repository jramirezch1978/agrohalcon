"""Lectura de VIIRS NDVI con un HDF5 de juguete (misma estructura que VNP13A1): relleno, nubes y escala."""

import h5py
import numpy as np
import pytest

from etl import viirs_ndvi as v

PIURA = (-5.19, -80.63)
CHIRA = (-4.90, -80.85)
TUMBES = (-3.57, -80.45)


@pytest.fixture
def archivo(tmp_path):
    ruta = tmp_path / "VNP13A1_juguete.h5"
    nd = np.full((v.N, v.N), -15000, dtype="int16")
    cf = np.full((v.N, v.N), 255, dtype="uint8")
    for (lat, lon), valor, conf in ((PIURA, 3200, 0), (CHIRA, 6500, 3), (TUMBES, 5100, 1)):
        _, _, fila, col = v.tesela_y_pixel(lat, lon)
        nd[fila, col], cf[fila, col] = valor, conf
    with h5py.File(ruta, "w") as f:
        g = f.create_group("HDFEOS/GRIDS/VIIRS_Grid_16Day_VI_500m/Data Fields")
        g.create_dataset("500 m 16 days NDVI", data=nd)
        g.create_dataset("500 m 16 days pixel reliability", data=cf)
    return ruta


def test_escala_y_filtro_de_nubes(archivo):
    zonas = {"Piura": PIURA, "Chira": CHIRA, "Tumbes": TUMBES}
    with h5py.File(archivo, "r") as f:
        r = {x["zona"]: x for x in v.leer_pixeles(f, "2017-03-06", zonas)}
    assert r["Piura"]["ndvi"] == 0.32 and r["Piura"]["confiabilidad"] == 0
    assert r["Tumbes"]["ndvi"] == 0.51 and r["Tumbes"]["confiabilidad"] == 1  # marginal: se acepta
    assert "Chira" not in r  # confiabilidad 3 = nube: el NDVI no es de fiar


def test_valores_de_relleno_se_descartan(tmp_path):
    ruta = tmp_path / "vacio.h5"
    with h5py.File(ruta, "w") as f:
        g = f.create_group("HDFEOS/GRIDS/VIIRS_Grid_16Day_VI_500m/Data Fields")
        g.create_dataset("500 m 16 days NDVI", data=np.full((v.N, v.N), -15000, dtype="int16"))
        g.create_dataset("500 m 16 days pixel reliability", data=np.zeros((v.N, v.N), dtype="uint8"))
    with h5py.File(ruta, "r") as f:
        assert v.leer_pixeles(f, "2017-03-06", {"Piura": PIURA}) == []
