from tests.test_api_calcular import cliente_api  # noqa: F401  (fixture)


def test_indicadores_punto_da_nivel_e_indicadores(cliente_api):  # noqa: F811
    api, _ = cliente_api
    r = api.post("/indicadores-punto", json={"lat": -1.29, "lon": 36.82}).json()
    assert r["nivel"] == "alto" and r["indicadorDecisivo"] in r["indicadores"]
    assert {"lluvia", "humedadSuelo", "calor", "elNino"} <= set(r["indicadores"])
    assert r["indicadorDecisivo"] != "elNino"          # El Niño no pinta el valle: va aparte
    assert "elNino" in r


def test_indicadores_punto_valida_coordenadas(cliente_api):  # noqa: F811
    api, _ = cliente_api
    assert api.post("/indicadores-punto", json={"lat": 120, "lon": 0}).status_code == 422
