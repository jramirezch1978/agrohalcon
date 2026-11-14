"""Descarga NDVI de MODIS Terra (MOD13Q1 V061, 250 m, compuesto de 16 días) para los puntos de Piura y
guarda data/precalculado/ndvi_piura.json. Usa el servicio REST del ORNL DAAC (NASA), sin login.

- Actual: el último compuesto disponible (píxel del punto).
- Normal: el mismo compuesto (mismo día del año) en 2016-2025.

    python -m scripts.descargar_ndvi
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import httpx

from app.fuentes.piura import PUNTOS_PIURA

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "precalculado" / "ndvi_piura.json"
ORNL = "https://modis.ornl.gov/rst/api/v1/MOD13Q1"
BANDA = "250m_16_days_NDVI"
cliente = httpx.Client(timeout=180, headers={"Accept": "application/json"})


def ndvi(lat: float, lon: float, fecha_modis: str) -> float | None:
    for _ in range(3):
        try:
            r = cliente.get(f"{ORNL}/subset", params={"latitude": lat, "longitude": lon, "band": BANDA,
                                                      "startDate": fecha_modis, "endDate": fecha_modis,
                                                      "kmAboveBelow": 0, "kmLeftRight": 0})
            if r.status_code == 200:
                sub = r.json().get("subset", [])
                if sub:
                    v = sub[0]["data"][0]
                    return round(v * 0.0001, 4) if v > -3000 else None
                return None
        except (httpx.HTTPError, ValueError, KeyError, IndexError):
            pass
    return None


def main() -> int:
    p0 = PUNTOS_PIURA[0]
    fechas = cliente.get(f"{ORNL}/dates", params={"latitude": p0["lat"], "longitude": p0["lon"]}).json()["dates"]
    ultima = fechas[-1]
    doy = ultima["modis_date"][5:]                      # "AYYYYDDD" → "DDD"
    anio_ult = int(ultima["modis_date"][1:5])
    print(f"Último compuesto MOD13Q1: {ultima['calendar_date']} ({ultima['modis_date']})")
    trabajos = [(p, ultima["modis_date"], "actual") for p in PUNTOS_PIURA]
    trabajos += [(p, f"A{a}{doy}", a) for p in PUNTOS_PIURA for a in range(2016, anio_ult)]
    with ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(lambda t: (t[0]["id"], t[2], ndvi(t[0]["lat"], t[0]["lon"], t[1])), trabajos))
    actual = {pid: v for pid, k, v in res if k == "actual"}
    normal = {}
    for p in PUNTOS_PIURA:
        vals = [v for pid, k, v in res if pid == p["id"] and k != "actual" and v is not None]
        normal[p["id"]] = round(sum(vals) / len(vals), 4) if vals else None
    print("piura actual", actual["piura"], "normal", normal["piura"])
    SALIDA.write_text(json.dumps({
        "metadatos": {
            "producto": {"short_name": "MOD13Q1", "version": "061", "nombre": "MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061",
                         "variable": BANDA, "escala": 0.0001, "doi": "10.5067/MODIS/MOD13Q1.061",
                         "url": "https://lpdaac.usgs.gov/products/mod13q1v061/", "servicio": "ORNL DAAC MODIS Web Service"},
            "generado": date.today().isoformat(),
            "metodo": f"NDVI del píxel de 250 m de cada punto; normal = mismo compuesto (día {doy}) en 2016-{anio_ult - 1}.",
        },
        "puntos": PUNTOS_PIURA,
        "actual": {"fecha": ultima["calendar_date"], "ndvi": actual},
        "normal": {"periodo": f"2016-{anio_ult - 1}", "ndvi": normal},
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Guardado {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
