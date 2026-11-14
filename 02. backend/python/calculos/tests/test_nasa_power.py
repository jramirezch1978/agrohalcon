import asyncio
import json
import time
from datetime import date

import httpx
import pytest

from app.fuentes.cache import CacheDisco
from app.fuentes.nasa_power import (
    ClienteNasaPower, NasaPowerError, parsear_climatologia, parsear_diario, parsear_mensual,
)
from tests.conftest import clima_falso, respuesta_power


def test_parsear_diario_relleno_es_nan():
    df = parsear_diario(respuesta_power({"T2M": {"20261110": 25.0, "20261111": -999.0}}))
    assert df.loc["2026-11-10", "T2M"] == 25.0
    assert df["T2M"].isna().sum() == 1


def test_parsear_mensual_descarta_anual():
    df = parsear_mensual(respuesta_power({"PRECTOTCORR": {"201701": 3.0, "201702": 9.0, "201713": 4.0}}))
    assert len(df) == 2
    assert str(df.index[0]) == "2017-01"


def test_parsear_climatologia_indice_1_a_12():
    df = parsear_climatologia(clima_falso({"T2M": 20.0}))
    assert list(df.index) == list(range(1, 13))


def test_cache_vence(tmp_path):
    c = CacheDisco(tmp_path, ttl_horas=24)
    c.guardar("k", {"a": 1})
    assert c.leer("k") == {"a": 1}
    ruta = next(tmp_path.glob("*.json"))
    contenido = json.loads(ruta.read_text())
    contenido["guardado"] = time.time() - 25 * 3600
    ruta.write_text(json.dumps(contenido))
    assert c.leer("k") is None


def _cliente(tmp_path, handler, reintentos=3):
    return ClienteNasaPower(CacheDisco(tmp_path), reintentos=reintentos, espera_base_s=0,
                            transport=httpx.MockTransport(handler))


def test_reintenta_ante_503_y_luego_usa_cache(tmp_path):
    llamadas = []

    def handler(req: httpx.Request):
        llamadas.append(req.url)
        if len(llamadas) < 3:
            return httpx.Response(503)
        assert req.url.params["community"] == "AG"
        return httpx.Response(200, json=clima_falso({"T2M": 20.0}))

    cli = _cliente(tmp_path, handler)
    asyncio.run(cli.climatologia(-5.19, -80.63))
    asyncio.run(cli.climatologia(-5.19, -80.63))      # segunda vez: caché, sin red
    assert len(llamadas) == 3


def test_422_no_se_reintenta(tmp_path):
    llamadas = []

    def handler(req):
        llamadas.append(1)
        return httpx.Response(422, json={"messages": ["parámetro inválido"]})

    with pytest.raises(NasaPowerError, match="422"):
        asyncio.run(_cliente(tmp_path, handler).diario(0, 0, date(2026, 1, 1), date(2026, 1, 2)))
    assert len(llamadas) == 1


def test_falla_tras_reintentos(tmp_path):
    def handler(req):
        raise httpx.ConnectTimeout("sin red")

    with pytest.raises(NasaPowerError, match="3 intentos"):
        asyncio.run(_cliente(tmp_path, handler, reintentos=2).climatologia(0, 0))
