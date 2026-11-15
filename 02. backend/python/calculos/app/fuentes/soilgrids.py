"""Textura del suelo de un punto desde SoilGrids 2.0 (ISRIC, licencia CC-BY 4.0). NO es un dato de la NASA.

Se usa solo para PROPONER el tipo de suelo de la parcela; el agricultor lo puede cambiar. Promedio 0-30 cm de arena,
limo y arcilla (g/kg → %), clasificado en arenoso / franco / arcilloso con los cortes de config/umbrales.yaml.
Si SoilGrids falla o no tiene dato (zonas urbanas, agua), devuelve tipoSuelo = None y la app pide el dato a mano.
"""
from __future__ import annotations

import httpx

from app.fuentes.cache import CacheDisco

URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
FUENTE = "SoilGrids (ISRIC)"
LICENCIA = "CC-BY 4.0"
PROFUNDIDADES = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15}   # espesor de cada capa (cm) para el promedio 0-30 cm


def sin_dato(motivo: str) -> dict:
    return {"tipoSuelo": None, "arena": None, "limo": None, "arcilla": None, "fuente": "sin dato", "motivo": motivo}


def textura_de_respuesta(datos: dict) -> dict[str, float] | None:
    """{'arena': %, 'limo': %, 'arcilla': %} promedio 0-30 cm, o None si alguna capa viene vacía."""
    salida = {}
    nombres = {"sand": "arena", "silt": "limo", "clay": "arcilla"}
    for capa in datos.get("properties", {}).get("layers", []):
        if capa.get("name") not in nombres:
            continue
        factor = capa.get("unit_measure", {}).get("d_factor") or 10
        suma = peso = 0.0
        for d in capa.get("depths", []):
            v, w = d.get("values", {}).get("mean"), PROFUNDIDADES.get(d.get("label"))
            if v is None or w is None:
                return None
            suma += v / factor * w
            peso += w
        if not peso:
            return None
        salida[nombres[capa["name"]]] = round(suma / peso, 1)
    return salida if len(salida) == 3 else None


def clasificar(textura: dict[str, float], u: dict) -> str:
    c = u["suelo_textura"]
    if textura["arena"] >= c["arenoso_arena_desde"]:
        return "arenoso"
    if textura["arcilla"] >= c["arcilloso_arcilla_desde"]:
        return "arcilloso"
    return "franco"


class ClienteSoilGrids:
    def __init__(self, cache: CacheDisco | None = None, timeout_s: float = 55,   # SoilGrids tarda 20-60 s (nov-2026)
                 transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.cache, self.timeout_s, self.transport = cache, timeout_s, transport

    async def suelo(self, lat: float, lon: float, u: dict) -> dict:
        clave = f"soilgrids:{lat:.3f},{lon:.3f}"
        if self.cache and (guardado := self.cache.leer(clave)) is not None:
            return guardado
        params = [("lat", lat), ("lon", lon), ("value", "mean")]
        params += [("property", p) for p in ("sand", "silt", "clay")] + [("depth", d) for d in PROFUNDIDADES]
        try:
            async with httpx.AsyncClient(timeout=self.timeout_s, transport=self.transport) as cli:
                r = await cli.get(URL, params=params)
                r.raise_for_status()
                textura = textura_de_respuesta(r.json())
        except (httpx.HTTPError, ValueError) as e:
            return sin_dato(f"SoilGrids no respondió ({type(e).__name__})")   # no se guarda: se reintenta luego
        if textura is None:
            out = sin_dato("SoilGrids no tiene dato en este punto (zona urbana o agua)")
        else:
            out = {"tipoSuelo": clasificar(textura, u), **textura, "profundidad": "0-30 cm",
                   "fuente": FUENTE, "licencia": LICENCIA}
        if self.cache:
            self.cache.guardar(clave, out)
        return out
