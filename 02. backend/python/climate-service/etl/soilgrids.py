"""ISRIC SoilGrids v2 (no es NASA): pH, carbono orgánico, arcilla y arena a 0-30 cm. Sin llave, pero es LENTO
(~13 s por punto) y limita llamadas: se espacian. Si el punto es urbano o desierto sin suelo mapeado, devuelve vacío
y se guarda como "sin dato" (no se inventa). https://rest.isric.org/soilgrids/v2.0/docs
"""

import time

import httpx

from .config import USER_AGENT

URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
PROPIEDADES = {"phh2o": ("ph", 10.0), "soc": ("carbono_organico_g_kg", 10.0), "clay": ("arcilla_pct", 10.0), "sand": ("arena_pct", 10.0)}
PROFUNDIDADES = ("0-5cm", "5-15cm", "15-30cm")
PESOS = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15}  # promedio ponderado por espesor de capa


def suelo_punto(lat: float, lon: float, reintentos: int = 3) -> dict:
    """{'ph','carbono_organico_g_kg','arcilla_pct','arena_pct'} (None si no hay dato). Convierte las unidades de SoilGrids."""
    params = [("lon", lon), ("lat", lat), ("value", "mean")]
    params += [("property", p) for p in PROPIEDADES] + [("depth", d) for d in PROFUNDIDADES]
    ultimo = None
    for intento in range(1, reintentos + 1):
        try:
            r = httpx.get(URL, params=params, timeout=90, headers={"User-Agent": USER_AGENT})
            if r.status_code == 429:
                time.sleep(20 * intento)
                continue
            r.raise_for_status()
            capas = r.json()["properties"]["layers"]
            break
        except (httpx.HTTPError, KeyError) as e:
            ultimo = e
            time.sleep(5 * intento)
    else:
        raise RuntimeError(f"SoilGrids falló: {ultimo}")

    salida: dict = dict.fromkeys(v[0] for v in PROPIEDADES.values())
    for capa in capas:
        nombre, divisor = PROPIEDADES.get(capa["name"], (None, 1.0))
        pares = [(PESOS[d["label"]], d["values"]["mean"]) for d in capa["depths"] if d["values"].get("mean") is not None]
        if nombre and pares:
            peso = sum(p for p, _ in pares)
            salida[nombre] = round(sum(p * v for p, v in pares) / peso / divisor, 2)
    return salida
