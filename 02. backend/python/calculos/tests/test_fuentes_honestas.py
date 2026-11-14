"""Ninguna respuesta etiqueta como SMAP, GPM IMERG, MODIS o MUR SST un dato que no viene de ese producto."""
import json
from datetime import timedelta

import pytest

from app.fuentes.precalculado import ARCHIVO_IMERG, ARCHIVO_MUR
from tests.conftest import mur_json
from tests.test_api_calcular import cliente_api  # noqa: F401  (fixture)

PRODUCTOS_SATELITALES = {"SMAP", "GPM IMERG", "MODIS NDVI", "MUR SST"}
# Archivo precalculado del que DEBE salir cada producto
ARCHIVO_DE = {"MUR SST": ARCHIVO_MUR, "GPM IMERG": ARCHIVO_IMERG}


def _fuentes(resp: dict) -> dict[str, str]:
    return {k: v["fuente"] for k, v in resp["indicadores"].items()}


@pytest.mark.parametrize("lat,lon", [(-5.19, -80.63), (-1.29, 36.82), (42.0, -93.6)])
def test_sin_precalculados_nada_dice_satelite(cliente_api, lat, lon):  # noqa: F811
    api, _ = cliente_api
    r = api.post("/calcular", json={"lat": lat, "lon": lon}).json()
    for clave, ind in r["indicadores"].items():
        assert ind["fuente"] not in PRODUCTOS_SATELITALES, f"{clave} dice {ind['fuente']} sin tener el archivo"
        if ind["fuente"] == "sin dato":
            assert ind["valor"] is None


def test_mur_solo_cuando_el_valor_sale_del_archivo(cliente_api, precalculado_vacio):  # noqa: F811
    (precalculado_vacio / ARCHIVO_MUR).write_text(json.dumps(mur_json([("2026-11-02", 27.15, 6.05)])), encoding="utf-8")
    api, _ = cliente_api
    r = api.post("/calcular", json={"lat": -5.19, "lon": -80.63}).json()
    nino = r["indicadores"]["elNino"]
    assert nino["fuente"] == "MUR SST" and nino["valor"] == 6.05 and nino["nivel"] == "alto"
    # Los demás siguen siendo NASA POWER (aún no hay IMERG ni SMAP)
    assert {r["indicadores"][k]["fuente"] for k in ("lluvia", "humedadSuelo", "calor")} == {"NASA POWER"}
    for clave, fuente in _fuentes(r).items():
        if fuente in PRODUCTOS_SATELITALES:
            assert (precalculado_vacio / ARCHIVO_DE[fuente]).exists(), f"{clave}: {fuente} sin archivo"


@pytest.mark.parametrize("lat,lon,esperada", [(-5.19, -80.63, "GPM IMERG"), (-1.29, 36.82, "NASA POWER")])
def test_imerg_solo_en_piura(cliente_api, precalculado_vacio, lat, lon, esperada):  # noqa: F811
    from datetime import date

    from tests.test_imerg import escribir, imerg_json
    escribir(precalculado_vacio, imerg_json(fin=date.today() - timedelta(days=1)))
    api, _ = cliente_api
    ll = api.post("/calcular", json={"lat": lat, "lon": lon}).json()["indicadores"]["lluvia"]
    assert ll["fuente"] == esperada
    if esperada == "GPM IMERG":
        assert ll["valor"] == 0.6 and ll["punto"]["id"] == "piura"
    else:
        assert "punto" not in ll
    # humedad y calor siguen siendo NASA POWER (SMAP no se integra)


def test_piura_sin_imerg_reciente_avisa(cliente_api, precalculado_vacio):  # noqa: F811
    from datetime import date

    from tests.test_imerg import escribir, imerg_json
    viejo = date.today() - timedelta(days=90)
    escribir(precalculado_vacio, imerg_json(fin=viejo))
    api, _ = cliente_api
    ll = api.post("/calcular", json={"lat": -5.19, "lon": -80.63}).json()["indicadores"]["lluvia"]
    assert ll["fuente"] == "NASA POWER" and viejo.isoformat() in ll["aviso"]
