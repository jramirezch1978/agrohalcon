"""SoilGrids (ISRIC): textura → tipo de suelo, sin dato y fallas de red sin romper nada (respuestas falsas)."""
import asyncio

import httpx

from app.fuentes.cache import CacheDisco
from app.fuentes.soilgrids import ClienteSoilGrids, clasificar


def respuesta(arena, limo, arcilla, soc=None):
    capa = lambda n, v: {"name": n, "unit_measure": {"d_factor": 10}, "depths": [  # noqa: E731
        {"label": d, "values": {"mean": v}} for d in ("0-5cm", "5-15cm", "15-30cm")]}
    capas = [capa("sand", arena), capa("silt", limo), capa("clay", arcilla)]
    if soc is not None:
        capas.append(capa("soc", soc))
    return {"properties": {"layers": capas}}


def cliente(handler, tmp_path=None):
    cache = CacheDisco(tmp_path) if tmp_path else None
    return ClienteSoilGrids(cache, transport=httpx.MockTransport(handler))


def test_clasifica_los_tres_tipos(umbrales):
    assert clasificar({"arena": 80, "limo": 10, "arcilla": 10}, umbrales) == "arenoso"
    assert clasificar({"arena": 20, "limo": 35, "arcilla": 45}, umbrales) == "arcilloso"
    assert clasificar({"arena": 66, "limo": 22, "arcilla": 12}, umbrales) == "franco"   # Bajo Piura (dato real, nov-2026)


def test_respuesta_valida_cita_soilgrids_y_guarda_en_cache(umbrales, tmp_path):
    llamadas = []

    def h(req):
        llamadas.append(req)
        return httpx.Response(200, json=respuesta(800, 100, 100, soc=85))
    c = cliente(h, tmp_path)
    r = asyncio.run(c.suelo(-5.4, -80.6, umbrales))
    assert r["tipoSuelo"] == "arenoso" and r["arena"] == 80.0 and r["fuente"] == "SoilGrids (ISRIC)"
    assert r["licencia"] == "CC-BY 4.0" and "NASA" not in r["fuente"]
    assert r["carbonoOrganico"] == 8.5 and r["infiltracion"] == "alta"
    asyncio.run(c.suelo(-5.4, -80.6, umbrales))
    assert len(llamadas) == 1                                        # la segunda vez sale de la caché


def test_sin_dato_en_zona_urbana(umbrales):
    r = asyncio.run(cliente(lambda req: httpx.Response(200, json=respuesta(None, None, None))).suelo(-5.19, -80.63, umbrales))
    assert r["tipoSuelo"] is None and r["fuente"] == "sin dato"


def test_si_soilgrids_falla_no_rompe(umbrales):
    def caido(req):
        raise httpx.ConnectError("sin red")
    r = asyncio.run(cliente(caido).suelo(-5.4, -80.6, umbrales))
    assert r["tipoSuelo"] is None and "no respondió" in r["motivo"]
    r = asyncio.run(cliente(lambda req: httpx.Response(503)).suelo(-5.4, -80.6, umbrales))
    assert r["tipoSuelo"] is None
