"""Rotaciones y 'qué hacer'. Escenario base = el ejemplo del contrato: sequía fuerte, calor y señal de
El Niño. Se verifica el ORDEN y la lógica (no números exactos del ejemplo del PDF, que son ilustrativos)."""

import copy

import pytest

from app import thresholds as T
from app.crops import generar_candidatas
from app.rotations import riesgo_de


def pedir(client, req, catalogo_json, **extra):
    cuerpo = {**req, "cultivos": catalogo_json, "fecha": "2026-11-15", **extra}
    r = client.post("/recomendacion", json=cuerpo)
    assert r.status_code == 200, r.text
    return r.json()


def test_formato_igual_al_contrato(client, req_contrato, catalogo_json):
    d = pedir(client, req_contrato, catalogo_json)
    assert set(d) == {"lat", "lon", "fecha", "indicadores", "rotaciones", "queHacer"}
    assert set(d["queHacer"]) == {"accion", "motivo", "fuente"}
    assert len(d["rotaciones"]) == 3
    for rot in d["rotaciones"]:
        assert set(rot) == {"id", "nombre", "puntaje", "riesgo", "explicacion"}
        assert 0 <= rot["puntaje"] <= 100
        assert rot["riesgo"] in ("bajo", "medio", "alto")


def test_sequia_castiga_al_arroz_y_premia_poca_agua(client, req_contrato, catalogo_json):
    d = pedir(client, req_contrato, catalogo_json, rotacionActualId=1)  # 1 = Arroz - Arroz
    por_nombre = {r["nombre"]: r for r in d["rotaciones"]}
    arroz = por_nombre["Arroz - Arroz"]
    assert arroz["riesgo"] == "alto"
    assert "40 % por debajo de lo normal" in arroz["explicacion"]
    otros = [r for n, r in por_nombre.items() if n != "Arroz - Arroz"]
    assert all(r["puntaje"] > arroz["puntaje"] + 30 for r in otros)
    # ordenadas de mejor a peor
    puntajes = [r["puntaje"] for r in d["rotaciones"]]
    assert puntajes == sorted(puntajes, reverse=True)


def test_que_hacer_como_el_contrato(client, req_contrato, catalogo_json):
    d = pedir(client, req_contrato, catalogo_json, rotacionActualId=1)
    qh = d["queHacer"]
    assert qh["accion"].startswith("No siembres arroz esta quincena; elige la rotación ")
    assert qh["motivo"] == "La humedad del suelo está 40 % por debajo de lo normal"
    assert qh["fuente"] == "SMAP"


def test_la_rotacion_actual_siempre_aparece(client, req_contrato, catalogo_json):
    d = pedir(client, req_contrato, catalogo_json, rotacionActualId=1)
    assert 1 in [r["id"] for r in d["rotaciones"]]


def test_sin_monocultivos_salvo_que_sea_la_actual(client, req_contrato, catalogo_json):
    d = pedir(client, req_contrato, catalogo_json)
    for r in d["rotaciones"]:
        a, b = r["nombre"].split(" - ")
        assert a != b


def test_clima_normal_todo_bajo_y_recomienda_rotar(client, req_contrato, catalogo_json):
    req = copy.deepcopy(req_contrato)
    req["actual"] = {"lluviaMm": 8.4, "humedadSuelo": 0.2, "tempMaxC": 31.0, "sstAnomaliaC": 0.1}
    d = pedir(client, req, catalogo_json, rotacionActualId=1)
    assert {i["nivel"] for i in d["indicadores"].values()} == {"bajo"}
    assert d["queHacer"]["motivo"] == "Los cuatro indicadores están dentro de lo normal"
    mejor = d["rotaciones"][0]
    assert mejor["puntaje"] == 100  # un clima normal no descuenta nada
    arroz_arroz = next(r for r in d["rotaciones"] if r["nombre"] == "Arroz - Arroz")
    assert arroz_arroz["puntaje"] == 100 - T.MONOCULTIVO_PTS
    assert "no corta el ciclo de plagas" in arroz_arroz["explicacion"]


def test_el_nino_2017_exceso_de_lluvia_no_castiga_al_arroz_como_a_la_sequia(
    client, req_contrato, catalogo_json
):
    req = copy.deepcopy(req_contrato)
    req["actual"] = {"lluviaMm": 20.0, "humedadSuelo": 0.35, "tempMaxC": 31.0, "sstAnomaliaC": 2.0}
    d = pedir(client, req, catalogo_json, rotacionActualId=1)
    assert d["indicadores"]["lluvia"]["nivel"] == "alto"
    assert d["indicadores"]["elNino"]["nivel"] == "alto"
    assert d["queHacer"]["motivo"].startswith("La lluvia está")
    assert d["queHacer"]["fuente"] == "GPM IMERG"
    # el cultivo que mejor tolera el encharcamiento (arroz) queda por encima del que peor lo tolera
    por_nombre = {r["nombre"]: r["puntaje"] for r in d["rotaciones"]}
    assert por_nombre["Arroz - Arroz"] > min(por_nombre.values())


def test_inundacion_extrema_nino_costero_2017(client, req_contrato, catalogo_json):
    """Marzo 2017 en Bajo Piura (NASA POWER): ~14,8 mm/día frente a ~1,6 normales (+800 %).
    Nada de recomendar arroz en plena inundación: todas las rotaciones quedan en riesgo alto."""
    req = copy.deepcopy(req_contrato)
    req["actual"] = {"lluviaMm": 14.8, "humedadSuelo": 0.49, "tempMaxC": 30.8, "sstAnomaliaC": 2.0}
    req["historico"] = {"lluviaMm": 1.65, "humedadSuelo": 0.19, "tempMaxC": 37.0}
    d = pedir(client, req, catalogo_json, rotacionActualId=1)
    assert d["indicadores"]["lluvia"]["nivel"] == "alto"
    assert all(r["riesgo"] == "alto" for r in d["rotaciones"])
    assert "inundación" in d["rotaciones"][0]["explicacion"]
    qh = d["queHacer"]
    assert qh["accion"].startswith("Riesgo de inundación: no siembres esta quincena")
    assert "técnico agrario" in qh["accion"]
    assert qh["motivo"].startswith("La lluvia está") and qh["fuente"] == "GPM IMERG"


def test_el_nino_extraordinario_no_deja_al_arroz_con_riesgo_bajo(client, req_contrato, catalogo_json):
    """Niño 1+2 a +5,25 °C (octubre 2026): ni el arroz se salva. Antes salía 'bajo' (86/100) por su tolerancia a la lluvia."""
    req = copy.deepcopy(req_contrato)
    req["actual"] = {"lluviaMm": 2.9, "humedadSuelo": 0.25, "tempMaxC": 33.9, "sstAnomaliaC": 5.25}
    req["historico"] = {"lluviaMm": 0.1, "humedadSuelo": 0.13, "tempMaxC": 33.7}
    d = pedir(client, req, catalogo_json, rotacionActualId=1)
    assert d["indicadores"]["elNino"]["nivel"] == "alto"
    assert all(r["riesgo"] != "bajo" for r in d["rotaciones"]), d["rotaciones"]
    assert any("extraordinaria" in r["explicacion"] for r in d["rotaciones"])
    qh = d["queHacer"]
    assert qh["accion"].startswith("Señal de El Niño extraordinaria") and "ENFEN" in qh["accion"]
    assert qh["fuente"] == "MUR SST"
    assert any(x in qh["motivo"] for x in ("5.2 °C", "5.3 °C"))


def test_lluvia_en_zona_arida_se_describe_con_cifras_reales(client, req_contrato, catalogo_json):
    """2,9 mm/día frente a 0,1 normales NO es '95 % por encima' (el piso de 3 mm achicaba el porcentaje)."""
    req = copy.deepcopy(req_contrato)
    req["actual"] = {"lluviaMm": 2.9, "humedadSuelo": 0.25, "tempMaxC": 33.9, "sstAnomaliaC": 0.0}
    req["historico"] = {"lluviaMm": 0.1, "humedadSuelo": 0.13, "tempMaxC": 33.7}
    ind = client.post("/indicadores", json=req).json()
    from app.indicators import describir
    from app.schemas import Indicador

    assert describir("lluvia", Indicador(**ind["lluvia"])) == "La lluvia está por encima de lo normal: 2.9 mm/día frente a 0.1 mm/día"


def test_fuera_de_temporada_descuenta(client, req_contrato, catalogo_json):
    en_epoca = pedir(client, req_contrato, catalogo_json, fecha="2026-12-01")
    fuera = pedir(client, req_contrato, catalogo_json, fecha="2026-07-01")  # julio: nadie siembra
    mejor_en_epoca = max(r["puntaje"] for r in en_epoca["rotaciones"])
    mejor_fuera = max(r["puntaje"] for r in fuera["rotaciones"])
    assert mejor_fuera < mejor_en_epoca
    assert "fuera de su época de siembra" in fuera["rotaciones"][0]["explicacion"]


def test_rotaciones_candidatas_de_la_tabla(client, req_contrato, catalogo_json):
    """Java puede mandar las filas de la tabla `rotaciones`: se puntúan tal cual, con sus ids."""
    indicadores = client.post("/indicadores", json=req_contrato).json()
    cuerpo = {
        "indicadores": indicadores,
        "cultivos": catalogo_json,
        "fecha": "2026-11-15",
        "rotaciones": [
            {"id": 1, "nombre": "Frijol - Maíz", "cultivo1Id": 4, "cultivo2Id": 2},
            {"id": 2, "nombre": "Arroz - Arroz", "cultivo1Id": 1, "cultivo2Id": 1},
            {"id": 3, "nombre": "Maíz - Algodón", "cultivo1Id": 2, "cultivo2Id": 3},
        ],
    }
    r = client.post("/rotaciones", json=cuerpo)
    assert r.status_code == 200, r.text
    rots = r.json()
    assert [x["id"] for x in rots][-1] == 2  # arroz-arroz queda último
    assert {x["nombre"] for x in rots} == {"Frijol - Maíz", "Arroz - Arroz", "Maíz - Algodón"}
    assert next(x for x in rots if x["id"] == 2)["riesgo"] == "alto"


def test_cultivo_inexistente_da_422_claro(client, req_contrato, catalogo_json):
    indicadores = client.post("/indicadores", json=req_contrato).json()
    cuerpo = {
        "indicadores": indicadores,
        "cultivos": catalogo_json,
        "rotaciones": [{"id": 9, "cultivo1Id": 99, "cultivo2Id": 1}],
    }
    r = client.post("/rotaciones", json=cuerpo)
    assert r.status_code == 422
    assert "99" in r.json()["detail"]


def test_catalogo_con_meses_en_texto(client, req_contrato, catalogo_json):
    """Alejandro puede escribir 'sep' o 'Septiembre' en vez de 9."""
    cat = copy.deepcopy(catalogo_json)
    cat[0]["mesesSiembra"] = ["nov", "Diciembre", "ene", "Febrero"]
    d = pedir(client, req_contrato, cat)
    assert len(d["rotaciones"]) == 3


def test_generar_candidatas_ids_estables(catalogo):
    cands = generar_candidatas(catalogo)
    assert len(cands) == len(catalogo) ** 2
    assert [c.id for c in cands] == list(range(1, len(cands) + 1))
    assert cands[0].nombre == "Arroz - Arroz"


@pytest.mark.parametrize("p, riesgo", [(100, "bajo"), (70, "bajo"), (69, "medio"), (45, "medio"), (44, "alto"), (0, "alto")])
def test_riesgo_segun_puntaje(p, riesgo):
    assert riesgo_de(p) == riesgo


def test_todas_en_alto_pide_consultar_a_un_tecnico(client, req_contrato, catalogo_json):
    req = copy.deepcopy(req_contrato)
    req["actual"].update({"lluviaMm": 0.0, "humedadSuelo": 0.02, "tempMaxC": 42.0, "sstAnomaliaC": 2.5})
    solo_arroz = [c for c in catalogo_json if c["id"] == 1] + [
        {**catalogo_json[0], "id": 9, "nombre": "Arroz B"}
    ]
    d = pedir(client, req, solo_arroz)
    assert d["rotaciones"][0]["riesgo"] == "alto"
    assert "técnico agrario" in d["queHacer"]["accion"]
