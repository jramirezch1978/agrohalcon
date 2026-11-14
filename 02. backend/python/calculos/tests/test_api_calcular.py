import time
from datetime import date

import httpx
import pytest
from fastapi.testclient import TestClient

from app.dependencias import cliente_power
from app.fuentes.cache import CacheDisco
from app.fuentes.nasa_power import ClienteNasaPower
from app.main import app
from tests.conftest import clima_falso, diario_falso, respuesta_power

HOY = date.today()


@pytest.fixture
def cliente_api(tmp_path):
    """Sequía de libro: lluvia -70 %, humedad -45 %, máxima +3.5 °C."""
    llamadas = []

    def handler(req: httpx.Request):
        llamadas.append(req.url.path)
        if req.url.path.endswith("/daily/point") and req.url.params["start"] == "20010101":
            # Serie histórica de máximas y mínimas diarias: 32 °C y 21 °C todos los días
            return httpx.Response(200, json=diario_falso(date(2025, 12, 31), 9131, {"T2M_MAX": 32.0, "T2M_MIN": 21.0},
                                                         relleno_final=0))
        if req.url.path.endswith("/monthly/point"):
            a0, a1 = int(req.url.params["start"]), int(req.url.params["end"])
            meses = {f"{a}{m:02d}": 1.0 for a in range(a0, a1 + 1) for m in range(1, 13)}
            return httpx.Response(200, json=respuesta_power({"PRECTOTCORR": meses}))
        if req.url.path.endswith("/daily/point"):
            return httpx.Response(200, json=diario_falso(HOY, 50, {
                "PRECTOTCORR": 3.0, "GWETTOP": 0.11, "T2M_MAX": 35.5, "T2M": 28.0,
                "T2M_MIN": 20.0, "GWETROOT": 0.3, "ALLSKY_SFC_SW_DWN": 20.0}))
        return httpx.Response(200, json=clima_falso({
            "PRECTOTCORR": 10.0, "GWETTOP": 0.20, "T2M_MAX": 38.0,
            "T2M": 26.0, "T2M_MIN": 15.0, "GWETROOT": 0.3, "ALLSKY_SFC_SW_DWN": 20.0}))

    falso = ClienteNasaPower(CacheDisco(tmp_path), espera_base_s=0, transport=httpx.MockTransport(handler))
    app.dependency_overrides[cliente_power] = lambda: falso
    yield TestClient(app), llamadas
    app.dependency_overrides.clear()


def test_calcular_indicadores(cliente_api):
    api, _ = cliente_api
    r = api.post("/calcular", json={"lat": -5.19, "lon": -80.63, "lang": "es", "mesSiembra": "2026-12"})
    assert r.status_code == 200, r.text
    ind = r.json()["indicadores"]
    assert ind["lluvia"]["nivel"] == "alto" and ind["lluvia"]["anomalia"] == -70.0
    assert ind["humedadSuelo"]["nivel"] == "alto" and ind["humedadSuelo"]["anomalia"] == -45.0
    assert ind["calor"]["nivel"] == "alto" and ind["calor"]["anomalia"] == 3.5
    # Normal de calor = media de máximas diarias 2001-2025 (32), nunca el extremo climatológico (38)
    assert ind["calor"]["normal"] == 32.0
    # Fuera de Piura (y sin precalculado) todo sale de NASA POWER; El Niño no se inventa
    assert {ind[k]["fuente"] for k in ("lluvia", "humedadSuelo", "calor")} == {"NASA POWER"}
    assert ind["elNino"]["valor"] is None and ind["elNino"]["disponible"] is False
    assert ind["elNino"]["fuente"] == "sin dato"
    assert r.json()["periodo"]["dias"] == 30


def test_calcular_con_cache_menos_de_5s(cliente_api):
    api, llamadas = cliente_api
    cuerpo = {"lat": -5.19, "lon": -80.63, "lang": "en"}
    api.post("/calcular", json=cuerpo)
    n = len(llamadas)
    t0 = time.perf_counter()
    r = api.post("/calcular", json=cuerpo)
    assert r.status_code == 200
    assert time.perf_counter() - t0 < 5
    assert len(llamadas) == n          # la segunda vez no tocó la red
    assert "mm/day" == r.json()["indicadores"]["lluvia"]["unidad"]


def test_validacion_de_entrada(cliente_api):
    api, _ = cliente_api
    assert api.post("/calcular", json={"lat": 200, "lon": 0}).status_code == 422
    assert api.post("/calcular", json={"lat": 0, "lon": 0, "mesSiembra": "2026-13"}).status_code == 422
