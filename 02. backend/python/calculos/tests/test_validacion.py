"""/validacion: lluvia de IMERG en Piura (POWER fuera), humedad y NDVI null, alerta con la fuente correcta."""
import json

import pytest

from app.calculos.validacion import alerta_lluvia, semanas_anticipacion
from app.fuentes.precalculado import ARCHIVO_IMERG, ARCHIVO_MUR
from tests.conftest import mur_json
from tests.test_api_calcular import cliente_api  # noqa: F401  (fixture)
from tests.test_imerg import IDS

# Lluvia 2017 en Piura (IMERG Final real, mm/mes) y normal 2001-2020
LLUVIA_2017 = [57.3, 217.7, 587.0, 38.2, 21.6, 1.4, 7.4, 2.2, 0.7, 1.5, 0.7, 5.2]
NORMAL = [19.1, 55.5, 112.6, 27.2, 6.8, 2.7, 2.6, 1.2, 0.8, 2.3, 3.2, 5.1]


def imerg_validacion() -> dict:
    meses = [f"2016-{m:02d}" for m in range(1, 13)] + [f"2017-{m:02d}" for m in range(1, 13)]
    serie_2016 = [10.0] * 11 + [6.0]
    return {
        "metadatos": {"productos": {"mensual": {"short_name": "GPM_3IMERGM"}, "diario": {"short_name": "GPM_3IMERGDL"}}},
        "mensual": {"meses": meses, "mm_mes": {i: serie_2016 + LLUVIA_2017 for i in IDS}},
        "climatologia": {"periodo": "2001-2020", "mm_mes": {i: NORMAL for i in IDS}, "mm_dia": {i: [0.5] * 12 for i in IDS}},
        "diario": {"fechas": [], "mm_dia": {i: [] for i in IDS}},
    }


@pytest.fixture
def con_imerg(precalculado_vacio):
    (precalculado_vacio / ARCHIVO_IMERG).write_text(json.dumps(imerg_validacion()), encoding="utf-8")
    return precalculado_vacio


def test_2017_sin_mur_lluvia_imerg_y_alerta_solo_lluvia(cliente_api, con_imerg):  # noqa: F811
    api, _ = cliente_api
    r = api.get("/validacion", params={"anio": 2017, "lat": -5.19, "lon": -80.63, "lang": "es"}).json()
    ll = r["series"]["lluvia"]
    assert ll["fuente"] == "GPM IMERG" and ll["valores"] == LLUVIA_2017 and ll["normal"] == NORMAL
    for k in ("humedadSuelo", "ndvi"):
        assert r["series"][k]["fuente"] == "sin dato" and r["series"][k]["valores"] == [None] * 12
    # Enero: 57.3 vs 19.1 → +200 % (alto) → alerta al cierre de enero, solo con lluvia
    assert r["alerta"]["fecha"] == "2017-01-31" and r["alerta"]["fuente"] == "GPM IMERG"
    assert r["alerta"]["nota"] == "Alerta calculada solo con la lluvia; con la temperatura del mar llegaría antes"
    assert r["mesLluviaMaxima"] == "2017-03" and r["semanasAnticipacion"] == 4
    assert r["evento"]["nombre"] == "El Niño costero 2017" and r["realidad"]["fuente"] == "INDECI"
    # Compatibilidad con el frontend actual
    assert len(r["serie"]) == 12 and r["serie"][2] == {"mes": 3, "lluvia": 587.0, "lluviaNormal": 112.6, "lluviaParcial": False,
                                                        "ndvi": None, "ndviNormal": None}
    assert r["recomendacionPrevia"]["fuente"] == "GPM IMERG" and r["resumen"]


def test_2017_con_mur_alerta_desde_el_mar(cliente_api, con_imerg):  # noqa: F811
    semanas = [(f"2016-{m:02d}-{d:02d}", 22.0, 0.2) for m, d in ((11, 28), (12, 5))] + [
        ("2016-12-12", 23.0, 0.62), ("2017-01-16", 26.4, 1.85), ("2017-05-01", 26.0, 1.0)]
    (con_imerg / ARCHIVO_MUR).write_text(json.dumps(mur_json(semanas)), encoding="utf-8")
    api, _ = cliente_api
    r = api.get("/validacion", params={"anio": 2017}).json()
    a = r["alerta"]
    assert a["fuente"] == "MUR SST" and a["fecha"] == "2016-12-12" and a["nivel"] == "medio" and "nota" not in a
    assert a["alertaDrenaje"]["fecha"] == "2017-01-16"
    assert r["semanasAnticipacion"] == 11                         # 12-dic-2016 → 1-mar-2017
    assert r["series"]["lluvia"]["fuente"] == "GPM IMERG"


def test_fuera_de_piura_usa_power_y_lo_dice(cliente_api, con_imerg):  # noqa: F811
    api, _ = cliente_api
    r = api.get("/validacion", params={"anio": 2017, "lat": -1.29, "lon": 36.82}).json()
    assert r["series"]["lluvia"]["fuente"] == "NASA POWER"
    assert "punto" not in r["series"]["lluvia"]


def test_otro_anio_sin_evento_ni_realidad(cliente_api, con_imerg):  # noqa: F811
    api, _ = cliente_api
    r = api.get("/validacion", params={"anio": 2016}).json()
    assert r["evento"] is None and r["realidad"] is None


def fuentes(obj) -> set[str]:
    """Todos los valores de campos 'fuente' de una respuesta (recursivo)."""
    if isinstance(obj, dict):
        return {v for k, v in obj.items() if k == "fuente" and isinstance(v, str)} | set().union(
            *(fuentes(v) for v in obj.values()))
    if isinstance(obj, list):
        return set().union(*(fuentes(v) for v in obj)) if obj else set()
    return set()


def test_ninguna_fuente_dice_smap_modis_ni_mur_sin_archivo(cliente_api, con_imerg):  # noqa: F811
    api, _ = cliente_api
    f = fuentes(api.get("/validacion", params={"anio": 2017}).json())
    assert f <= {"GPM IMERG", "sin dato", "INDECI"}               # sin archivo de MUR en este test
    assert not any(p in x for x in f for p in ("SMAP", "MODIS", "MUR SST"))


def test_anios_solo_con_datos_reales(cliente_api, con_imerg):  # noqa: F811
    api, _ = cliente_api
    r = api.get("/validacion/anios", params={"lat": -5.19, "lon": -80.63}).json()
    assert r == {"anios": [2016, 2017], "fuente": "GPM IMERG", "conMurSst": []}   # el fixture tiene 2016-2017
    lejos = api.get("/validacion/anios", params={"lat": -1.29, "lon": 36.82}).json()
    assert lejos["fuente"] == "NASA POWER" and lejos["anios"][0] == 2001


def test_semanas_anticipacion_nunca_negativas():
    assert semanas_anticipacion("2017-01-16", 2017, 3) == 6
    assert semanas_anticipacion("2017-04-10", 2017, 3) == 0
    assert semanas_anticipacion(None, 2017, 3) is None


def test_alerta_lluvia_respeta_estacion_seca(umbrales):
    lluvia = {"valores": [0.6] * 12, "normal": [0.1] * 12, "fuente": "GPM IMERG"}  # +500 % pero ~0 mm
    assert alerta_lluvia(2017, lluvia, 0.6, "es", umbrales) is None
