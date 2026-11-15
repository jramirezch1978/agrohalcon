"""El Niño EXTRAORDINARIO resta puntos a todas las rotaciones (antes la app pedía "preparar drenaje" y a la vez mostraba rotaciones de riesgo bajo)."""
from datetime import date

import pandas as pd
import pytest

from app.calculos.rotaciones import evaluar_rotacion, generar_rotaciones, nino_extremo
from app.catalogo import buscar, cargar_catalogo
from tests.test_fase2 import MEJOR, PIURA, ind, indicadores
from app.calculos.que_hacer import que_hacer

CAT = cargar_catalogo(None)
ARROZ, FRIJOL = buscar(CAT, "arroz"), buscar(CAT, "frijol")
NAIROBI = (-1.29, 36.82)
LIMA = (-12.05, -77.04)  # costa, pero fuera de la costa norte donde El Niño costero trae las lluvias extremas


def nino(valor: float, fuente="MUR SST") -> dict:
    return {"valor": valor, "nivel": "alto" if valor >= 1.5 else "medio", "fuente": fuente, "semana": "2026-11-09"}


def clima_normal() -> pd.DataFrame:
    return pd.DataFrame({"lluvia_mm_dia": 1.0, "lluvia_mm_mes": 30.0, "tmax": 29.0, "tmin": 20.0}, index=range(1, 13))


def evaluar(ii, lat_lon=PIURA, umbrales=None, cultivos=(ARROZ, FRIJOL)):
    return evaluar_rotacion(list(cultivos), "2026-12", clima_normal(), ii, *lat_lon, "es", umbrales)


def test_el_nino_extraordinario_resta_35_a_la_rotacion(umbrales):
    base = evaluar(indicadores(nino=nino(2.9)), umbrales=umbrales)
    r = evaluar(indicadores(nino=nino(6.0)), umbrales=umbrales)
    d = next(x for x in r["descuentos"] if x["regla"] == "el_nino_extremo")
    assert (d["indicador"], d["puntos"], d["fuente"], d["valor"]) == ("elNino", -35, "MUR SST", 6.0)
    assert r["puntaje"] == base["puntaje"] - 35
    assert "El Niño" in r["explicacion"] and "+6.0 °C" in r["explicacion"]


def test_justo_en_el_umbral_cuenta_y_por_debajo_no(umbrales):
    assert any(x["regla"] == "el_nino_extremo" for x in evaluar(indicadores(nino=nino(3.0)), umbrales=umbrales)["descuentos"])
    assert not any(x["regla"] == "el_nino_extremo" for x in evaluar(indicadores(nino=nino(2.99)), umbrales=umbrales)["descuentos"])


@pytest.mark.parametrize("donde", [NAIROBI, LIMA])
def test_fuera_de_la_costa_norte_no_resta(umbrales, donde):
    assert nino_extremo(nino(6.0), *donde, umbrales) is None
    assert not any(x["regla"] == "el_nino_extremo" for x in evaluar(indicadores(nino=nino(6.0)), donde, umbrales)["descuentos"])


def test_sin_dato_real_de_mur_no_inventa_el_descuento(umbrales):
    sin_dato = {"valor": None, "nivel": None, "fuente": "sin dato"}
    assert nino_extremo(sin_dato, *PIURA, umbrales) is None and nino_extremo(None, *PIURA, umbrales) is None


def test_si_el_yaml_no_trae_el_umbral_la_regla_queda_apagada(umbrales):
    u = {**umbrales, "rotaciones": {k: v for k, v in umbrales["rotaciones"].items() if not k.startswith("el_nino_extremo")}}
    assert nino_extremo(nino(6.0), *PIURA, u) is None  # un UMBRALES_PATH viejo sigue funcionando


def test_todas_las_rotaciones_pierden_lo_mismo_y_el_orden_no_cambia(umbrales):
    sin = generar_rotaciones(CAT, "2026-12", clima_normal(), indicadores(), *PIURA, "es", umbrales)
    con = generar_rotaciones(CAT, "2026-12", clima_normal(), indicadores(nino=nino(6.0)), *PIURA, "es", umbrales)
    antes = {r["nombre"]: r["puntaje"] for r in sin}
    assert len(con) == len(sin) and all(r["puntaje"] == max(0, antes[r["nombre"]] - 35) for r in con)  # todas pierden 35 (mínimo 0)
    assert [r["nombre"] for r in con] == [r["nombre"] for r in sorted(con, key=lambda r: -r["puntaje"])]  # y siguen ordenadas


def test_la_app_ya_no_pide_drenar_y_a_la_vez_muestra_riesgo_bajo(umbrales):
    """El caso real de 14-nov-2026 en Piura: El Niño +6,0 °C y rotaciones de 80-90 puntos 'riesgo bajo'."""
    ii = indicadores(nino=nino(6.0))
    ii["elNino"]["nivel"] = "alto"
    q = que_hacer(ii, *PIURA, "es", date(2026, 12, 1), "temporal", MEJOR, ARROZ)
    assert q["tipo"] == "preparar drenaje"
    rotaciones = generar_rotaciones(CAT, "2026-12", clima_normal(), ii, *PIURA, "es", umbrales)
    assert rotaciones and all(r["puntaje"] <= 65 for r in rotaciones), [(r["nombre"], r["puntaje"]) for r in rotaciones]
    assert not any(r["riesgo"] == "bajo" for r in rotaciones)


def test_explicacion_en_ingles(umbrales):
    r = evaluar_rotacion([ARROZ], "2026-12", clima_normal(), indicadores(nino=nino(6.0)), *PIURA, "en", umbrales)
    assert "extraordinary El Niño" in r["explicacion"]
