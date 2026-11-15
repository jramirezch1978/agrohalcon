"""Escenario hipotético ("¿y si el año viene seco o lluvioso?") y rotaciones sin repetir los mismos cultivos."""
from app.calculos.campana import escenario_lluvia
from app.calculos.rotaciones import generar_rotaciones
from app.catalogo import cargar_catalogo
from tests.test_api_calcular import cliente_api  # noqa: F401  (fixture)
from tests.test_fase2 import NAIROBI, clima, indicadores

CAT = cargar_catalogo(None)


def test_escenario_cambia_solo_la_lluvia():
    c = clima(lluvia_mm_mes=100)
    s = escenario_lluvia(c, 0.6)
    assert s["lluvia_mm_mes"].iloc[0] == 60 and s["tmax"].iloc[0] == c["tmax"].iloc[0]
    assert escenario_lluvia(c, 1.0) is c


def test_no_repite_los_mismos_cultivos_en_otro_orden(umbrales):
    for esc in (clima(), clima(lluvia_mm_mes=400)):
        rots = generar_rotaciones(CAT, "2027-01", esc, indicadores(), *NAIROBI, "es", umbrales)
        conjuntos = [frozenset(r["cultivos"]) for r in rots if not r["tradicional"]]
        assert len(conjuntos) == len(set(conjuntos))


def test_api_escenario(cliente_api):  # noqa: F811
    api, _ = cliente_api
    base = {"lat": -1.29, "lon": 36.82, "lang": "es", "tipoCultivo": "temporal", "mesSiembra": "2027-01"}
    r = api.post("/calcular", json={**base, "escenario": "seco"}).json()
    assert r["perfil"]["escenario"] == "seco" and r["perfil"]["factorLluvia"] == 0.6
    assert api.post("/calcular", json=base).json()["perfil"]["escenario"] == "normal"
    assert api.post("/calcular", json={**base, "escenario": "catastrofe"}).status_code == 422
