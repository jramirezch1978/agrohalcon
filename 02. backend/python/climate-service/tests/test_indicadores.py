import pytest

from app import thresholds as T
from app.indicators import anomalia, calcular_indicadores, describir, nivel_de
from app.schemas import IndicadoresRequest


def test_contrato_ejemplo_coincide_exactamente(client, req_contrato, indicadores_contrato):
    """Lo que Java manda a /indicadores debe devolver el bloque `indicadores` del PDF, campo por campo."""
    r = client.post("/indicadores", json=req_contrato)
    assert r.status_code == 200
    assert r.json() == indicadores_contrato


@pytest.mark.parametrize(
    "nombre, valor, normal, esperado",
    [
        # lluvia: |valor-normal| / max(normal, 1)  ->  umbrales 0.25 / 0.50
        ("lluvia", 8.5, 8.5, "bajo"),
        ("lluvia", 6.5, 8.5, "bajo"),  # -23 %
        ("lluvia", 6.0, 8.5, "medio"),  # -29 %
        ("lluvia", 2.1, 8.5, "alto"),  # -75 %
        ("lluvia", 14.0, 8.5, "alto"),  # exceso +65 %: también es riesgo
        # humedad del suelo: solo cuenta el déficit  ->  0.15 / 0.30
        ("humedadSuelo", 0.20, 0.20, "bajo"),
        ("humedadSuelo", 0.30, 0.20, "bajo"),  # más húmedo de lo normal no es sequía
        ("humedadSuelo", 0.16, 0.20, "medio"),  # -20 %
        ("humedadSuelo", 0.12, 0.20, "alto"),  # -40 %
        # calor: solo cuenta el exceso, en °C  ->  1.5 / 4.0
        ("calor", 31.0, 31.0, "bajo"),
        ("calor", 29.0, 31.0, "bajo"),
        ("calor", 33.0, 31.0, "medio"),
        ("calor", 35.0, 31.0, "alto"),
        # El Niño: anomalía del mar en °C  ->  0.5 / 1.5
        ("elNino", 0.3, 0.0, "bajo"),
        ("elNino", -1.0, 0.0, "bajo"),  # mar frío no es señal de El Niño
        ("elNino", 0.5, 0.0, "medio"),
        ("elNino", 1.5, 0.0, "alto"),
    ],
)
def test_niveles_por_umbral(nombre, valor, normal, esperado):
    assert nivel_de(nombre, valor, normal) == esperado


def test_lluvia_en_zona_arida_no_explota():
    """Si casi nunca llueve (normal 0.1 mm/día), 0 mm hoy no es 'alto': se usa un piso de lluvia."""
    assert nivel_de("lluvia", 0.0, 0.1) == "bajo"
    assert anomalia("lluvia", 0.0, 0.1) == pytest.approx(-0.1 / T.LLUVIA_NORMAL_MIN_MM)
    # Bajo Piura, 15-ene-2017 (NASA POWER): 0,28 mm/día frente a 0,80 normales. No es una alerta.
    assert nivel_de("lluvia", 0.276, 0.797) == "bajo"


def test_lluvia_en_zona_arida_si_detecta_el_exceso_de_el_nino():
    """Bajo Piura, 28-feb-2017: 9,96 mm/día frente a 1,46 normales -> alto. 15-feb: 2,6 vs 1,46 -> medio."""
    assert nivel_de("lluvia", 9.959, 1.462) == "alto"
    assert nivel_de("lluvia", 2.601, 1.462) == "medio"


def test_descripciones_con_el_dato_real(req_contrato):
    ind = calcular_indicadores(IndicadoresRequest.model_validate(req_contrato))
    assert describir("humedadSuelo", ind.humedadSuelo) == "La humedad del suelo está 40 % por debajo de lo normal"
    assert describir("lluvia", ind.lluvia) == "La lluvia está 75 % por debajo de lo normal"
    assert describir("calor", ind.calor) == "La temperatura máxima está 3.0 °C por encima de lo normal"
    assert "1.2 °C más caliente" in describir("elNino", ind.elNino)


def test_meta_permite_declarar_la_fuente_real(client, req_contrato):
    """Si la humedad vino de NASA POWER (respaldo), la app no debe decir 'SMAP'."""
    req_contrato["meta"] = {"humedadSuelo": {"fuente": "NASA POWER (GWETTOP)", "unidad": "fracción 0-1"}}
    h = client.post("/indicadores", json=req_contrato).json()["humedadSuelo"]
    assert h["fuente"] == "NASA POWER (GWETTOP)"
    assert h["unidad"] == "fracción 0-1"


def test_entrada_invalida_da_422(client, req_contrato):
    req_contrato["actual"]["humedadSuelo"] = 7  # fuera de 0-1
    assert client.post("/indicadores", json=req_contrato).status_code == 422
    req_contrato["actual"]["humedadSuelo"] = 0.1
    req_contrato["lat"] = -200
    assert client.post("/indicadores", json=req_contrato).status_code == 422


def test_salud(client):
    r = client.get("/salud")
    assert r.status_code == 200
    assert r.json()["estado"] == "ok"
