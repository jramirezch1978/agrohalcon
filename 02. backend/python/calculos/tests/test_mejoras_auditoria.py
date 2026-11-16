"""Mejoras de la auditoría: escenarios con efecto, simulador de El Niño, contraste con NOAA y resumen de validación."""
from datetime import date

from app.calculos.recomendacion import con_nino_hipotetico
from app.calculos.rotaciones import agua_con_escenario, generar_rotaciones
from app.calculos.validacion import clasificar
from app.catalogo import cargar_catalogo
from app.fuentes.noaa_nino12 import contraste, parsear
from tests.test_api_calcular import cliente_api  # noqa: F401  (fixture)
from tests.test_fase2 import NAIROBI, clima, indicadores

CAT = cargar_catalogo(None)
PIURA = (-5.19, -80.63)


def test_escenario_mueve_el_agua_de_riego(umbrales):
    assert agua_con_escenario(None, "seco", umbrales) == "poca"
    assert agua_con_escenario("poca", "seco", umbrales) == "poca"          # no baja de "poca"
    assert agua_con_escenario("normal", "lluvioso", umbrales) == "suficiente"
    assert agua_con_escenario("poca", "normal", umbrales) == "poca"
    assert agua_con_escenario(None, None, umbrales) is None


def test_seco_y_lluvioso_dan_puntajes_distintos(umbrales):
    def mejor(esc, factor):
        c = clima(lluvia_mm_mes=40 * factor)
        return generar_rotaciones(CAT, "2027-01", c, indicadores(), *NAIROBI, "es", umbrales,
                                  agua_disponible=agua_con_escenario(None, esc, umbrales))
    seco, lluvioso = mejor("seco", 0.6), mejor("lluvioso", 1.6)
    assert [r["puntaje"] for r in seco] != [r["puntaje"] for r in lluvioso]


def test_meses_medio_restan(umbrales):
    rots = generar_rotaciones(CAT, "2027-01", clima(tmin=5), indicadores(), *NAIROBI, "es", umbrales)
    assert any(d["regla"] == "riesgo_medio" for r in rots for d in r["descuentos"]) or \
        any(d["regla"] == "riesgo_alto" for r in rots for d in r["descuentos"])


def test_nino_hipotetico_reemplaza_solo_lo_que_decide(umbrales):
    base = indicadores(nino={"valor": 0.2, "nivel": "bajo", "fuente": "MUR SST", "semana": "2026-11-09"})
    sim = con_nino_hipotetico(base, 3.5, "es", umbrales)
    assert sim["elNino"]["nivel"] == "alto" and sim["elNino"]["fuente"] == "hipotético" and sim["elNino"]["hipotetico"]
    assert base["elNino"]["valor"] == 0.2                      # el dato real no se toca
    assert con_nino_hipotetico(base, None, "es", umbrales) is base


def test_api_nino_hipotetico_dispara_drenaje_en_la_costa(cliente_api):  # noqa: F811
    api, _ = cliente_api
    base = {"lat": PIURA[0], "lon": PIURA[1], "lang": "es", "tipoCultivo": "temporal", "mesSiembra": "2027-01"}
    r = api.post("/calcular", json={**base, "ninoHipotetico": 4.0}).json()
    assert r["queHacer"]["tipo"] == "preparar drenaje" and r["perfil"]["ninoHipotetico"] == 4.0
    assert r["indicadores"]["elNino"].get("fuente") != "hipotético"   # lo mostrado sigue siendo real
    assert any(d["regla"] == "el_nino_extremo" for d in r["rotaciones"][0]["descuentos"])
    assert api.post("/calcular", json={**base, "ninoHipotetico": 9}).status_code == 422


def test_api_avisa_cuando_el_escenario_no_cambia_nada(cliente_api):  # noqa: F811
    api, _ = cliente_api
    base = {"lat": -1.29, "lon": 36.82, "lang": "es", "tipoCultivo": "temporal", "mesSiembra": "2027-01"}
    r = api.post("/calcular", json={**base, "escenario": "seco"}).json()
    p = r["perfil"]
    assert p["aguaConEscenario"] == "poca"
    assert isinstance(p["escenarioSinEfecto"], bool)
    assert (p["notaEscenario"] is not None) == p["escenarioSinEfecto"]


NOAA = """ Weekly SST data starts week centered on 3Jan1990
                Nino1+2      Nino3        Nino34        Nino4
 Week          SST SSTA     SST SSTA     SST SSTA     SST SSTA
 28OCT2026     26.7 5.4     29.5 4.4     30.2 3.4     30.1 1.4
 04NOV2026     27.0 5.6     29.5 4.4     30.1 3.3     30.1 1.5
"""


def test_contraste_noaa(umbrales):
    serie = parsear(NOAA)
    assert serie[-1] == {"semana": "2026-11-04", "sst": 27.0, "anomalia": 5.6}
    c = contraste(6.05, "2026-11-02", serie, umbrales)       # lunes 2/11 → miércoles 4/11
    assert c["semana"] == "2026-11-04" and c["concuerda"] and c["diferencia"] == 0.45
    assert not contraste(3.0, "2026-11-02", serie, umbrales)["concuerda"]
    assert contraste(1.0, "2020-01-06", serie, umbrales) is None   # sin semana cercana
    assert contraste(1.0, "2026-11-02", None, umbrales) is None


def test_clasificar():
    assert clasificar(True, True) == "acierto"
    assert clasificar(True, False) == "falsa_alarma"
    assert clasificar(False, True) == "no_avisado"
    assert clasificar(False, False) == "correcto"
    assert clasificar(True, None) == "pendiente"


def test_fecha_en_palabras_y_calificacion(umbrales):
    from app.calculos.rotaciones import calificacion
    from app.textos.plantillas import fecha_larga, texto
    assert fecha_larga("es", f"{date.today().year}-11-09") == "9 de noviembre"
    assert fecha_larga("en", "2017-01-16") == "January 16, 2017"
    assert "2026-11-09" not in texto("es", "q_drenaje_m", anom=6.0, semana="2026-11-09")
    assert [calificacion(p, umbrales) for p in (79, 54, 7)] == ["buena", "regular", "riesgosa"]


def test_tradicional_explica_en_una_frase(umbrales):
    rots = generar_rotaciones(CAT, "2027-01", clima(), indicadores(), *PIURA, "es", umbrales)
    trad = next(r for r in rots if r["tradicional"])
    assert trad["calificacion"] in ("buena", "regular", "riesgosa")
    assert "Es lo que se siembra siempre en tu zona" in trad["explicacion"]
    assert "MUR SST" not in trad["explicacion"] and "Niño 1+2" not in trad["explicacion"]
