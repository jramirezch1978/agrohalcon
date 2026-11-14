"""Incertidumbre opcional del puntaje. Sin pedirla, la respuesta es EXACTAMENTE la del contrato."""

import copy

import pytest

from app.indicators import calcular_indicadores
from app.rotations import perturbar
from app.schemas import IndicadoresRequest

CONTRATO = {"id", "nombre", "puntaje", "riesgo", "explicacion"}


def reco(client, req, cat, **extra):
    r = client.post("/recomendacion", json={**req, "cultivos": cat, "fecha": "2026-11-15", **extra})
    assert r.status_code == 200, r.text
    return r.json()


def test_por_defecto_no_aparecen_campos_nuevos(client, req_contrato, catalogo_json):
    d = reco(client, req_contrato, catalogo_json)
    assert all(set(r) == CONTRATO for r in d["rotaciones"])


def test_con_incertidumbre_agrega_rango_y_confianza(client, req_contrato, catalogo_json):
    d = reco(client, req_contrato, catalogo_json, incertidumbre=True, rotacionActualId=1)
    for r in d["rotaciones"]:
        assert set(r) == CONTRATO | {"puntajeMin", "puntajeMax", "confianza"}
        assert r["puntajeMin"] <= r["puntaje"] <= r["puntajeMax"]
        assert r["confianza"] in ("alta", "media", "baja")
    # el puntaje base y el resto de la respuesta no cambian por pedir incertidumbre
    base = reco(client, req_contrato, catalogo_json, rotacionActualId=1)
    assert [r["puntaje"] for r in base["rotaciones"]] == [r["puntaje"] for r in d["rotaciones"]]
    assert base["queHacer"] == d["queHacer"]


def test_rotaciones_endpoint_tambien_lo_soporta(client, req_contrato, catalogo_json):
    ind = client.post("/indicadores", json=req_contrato).json()
    r = client.post("/rotaciones", json={"indicadores": ind, "cultivos": catalogo_json, "incertidumbre": True})
    assert r.status_code == 200
    assert all("puntajeMin" in x for x in r.json())


def test_perturbar_empuja_hacia_el_lado_malo_y_el_bueno(req_contrato):
    ind = calcular_indicadores(IndicadoresRequest.model_validate(req_contrato))
    malo, bueno = perturbar(ind, +1), perturbar(ind, -1)
    assert malo.humedadSuelo.valor < ind.humedadSuelo.valor < bueno.humedadSuelo.valor  # menos humedad = peor
    assert malo.calor.valor > ind.calor.valor > bueno.calor.valor  # más calor = peor
    assert malo.elNino.valor > ind.elNino.valor > bueno.elNino.valor
    # lluvia por DEBAJO de lo normal: peor = aún menos lluvia
    assert malo.lluvia.valor < ind.lluvia.valor < bueno.lluvia.valor


def test_perturbar_lluvia_en_exceso_se_aleja_de_lo_normal(req_contrato):
    req = copy.deepcopy(req_contrato)
    req["actual"]["lluviaMm"] = 20.0  # exceso frente a 8.5 normales
    ind = calcular_indicadores(IndicadoresRequest.model_validate(req))
    assert perturbar(ind, +1).lluvia.valor > 20.0 > perturbar(ind, -1).lluvia.valor


def test_perturbar_respeta_limites_fisicos(req_contrato):
    req = copy.deepcopy(req_contrato)
    req["actual"]["humedadSuelo"] = 0.01
    req["actual"]["lluviaMm"] = 0.0
    ind = calcular_indicadores(IndicadoresRequest.model_validate(req))
    malo = perturbar(ind, +1)
    assert malo.humedadSuelo.valor >= 0.0 and malo.lluvia.valor >= 0.0
    req["actual"]["humedadSuelo"] = 0.99
    assert perturbar(calcular_indicadores(IndicadoresRequest.model_validate(req)), -1).humedadSuelo.valor <= 1.0


def test_perturbar_solo_mueve_el_indicador_pedido(req_contrato):
    ind = calcular_indicadores(IndicadoresRequest.model_validate(req_contrato))
    p = perturbar(ind, +1, "calor")
    assert p.calor.valor > ind.calor.valor
    assert (p.lluvia, p.humedadSuelo, p.elNino) == (ind.lluvia, ind.humedadSuelo, ind.elNino)


def test_clima_normal_el_mejor_puntaje_ya_es_el_techo(client, req_contrato, catalogo_json):
    req = copy.deepcopy(req_contrato)
    req["actual"] = {"lluviaMm": 8.4, "humedadSuelo": 0.2, "tempMaxC": 29.0, "sstAnomaliaC": 0.0}
    d = reco(client, req, catalogo_json, incertidumbre=True)
    mejor = d["rotaciones"][0]
    assert mejor["puntaje"] == mejor["puntajeMax"] == 100  # no se puede estar mejor que "todo normal"
    assert mejor["puntajeMin"] < 100  # pero los datos podrían estar equivocados hacia el lado malo


def test_en_sequia_lo_que_necesita_mucha_agua_es_lo_mas_incierto(client, req_contrato, catalogo_json):
    d = reco(client, req_contrato, catalogo_json, incertidumbre=True, rotacionActualId=1)  # 1 = Arroz - Arroz
    ancho = {r["nombre"]: r["puntajeMax"] - r["puntajeMin"] for r in d["rotaciones"]}
    arroz = ancho.pop("Arroz - Arroz")
    assert arroz >= max(ancho.values())


@pytest.mark.parametrize("ancho, esperado", [(0, "alta"), (10, "alta"), (11, "media"), (25, "media"), (26, "baja")])
def test_umbrales_de_confianza(ancho, esperado):
    from app.rotations import _confianza

    assert _confianza(ancho) == esperado
