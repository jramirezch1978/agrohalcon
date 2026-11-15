"""Descarga SMAP L3 Enhanced (SPL3SMP_E V006, 9 km) para los puntos de Piura y guarda
data/precalculado/smap_piura.json. Recorta en el servidor (OPeNDAP en la nube de Earthdata): solo
pide la caja de Piura de cada día (~2 KB), nunca el archivo global (~630 MB).

- Actual: promedio de los últimos 30 días con dato (SMAP pasa cada 2-3 días; pasadas AM y PM).
- Normal: misma ventana de días del año, 2016-2025 (un día de cada dos, para ir rápido).

    set EARTHDATA_TOKEN=...
    python -m scripts.descargar_smap
"""
from __future__ import annotations

import json
import math
import os
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import httpx

from app.fuentes.piura import CAJA_PIURA, PUNTOS_PIURA

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "precalculado" / "smap_piura.json"
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
SHORT, VERSION = "SPL3SMP_E", "006"

# EASE-Grid 2.0 global 9 km (EPSG:6933), fórmula exacta (elipsoide WGS84, paralelo estándar 30°)
A, E = 6378137.0, 0.0818191908426
K0 = math.cos(math.radians(30)) / math.sqrt(1 - E * E * math.sin(math.radians(30)) ** 2)
X0, Y0, RES = -17367530.445, 7314540.8307, 9008.055


def pixel(lat: float, lon: float) -> tuple[int, int]:
    s = math.sin(math.radians(lat))
    q = (1 - E * E) * (s / (1 - E * E * s * s) - (1 / (2 * E)) * math.log((1 - E * s) / (1 + E * s)))
    x, y = A * K0 * math.radians(lon), A * q / (2 * K0)
    return int((Y0 - y) // RES), int((x - X0) // RES)


F0, C0 = pixel(CAJA_PIURA["lat"][1], CAJA_PIURA["lon"][0])   # esquina norte-oeste
F1, C1 = pixel(CAJA_PIURA["lat"][0], CAJA_PIURA["lon"][1])   # esquina sur-este


def granulos(inicio: date, fin: date) -> dict[str, str]:
    out: dict[str, str] = {}
    pagina = 1
    while True:
        r = httpx.get(CMR, params={"short_name": SHORT, "version": VERSION, "temporal": f"{inicio}T00:00:00Z,{fin}T23:59:59Z",
                                   "page_size": 500, "page_num": pagina}, timeout=60)
        r.raise_for_status()
        ent = r.json()["feed"]["entry"]
        if not ent:
            return out
        for e in ent:
            u = next((l["href"] for l in e.get("links", []) if "opendap.earthdata.nasa.gov" in l["href"]), None)
            if u:
                out[e["time_start"][:10]] = u
        pagina += 1


def leer_dia(cliente: httpx.Client, url: str) -> dict[str, float | None]:
    """Humedad (m3/m3) de cada punto ese día: promedio de las pasadas AM y PM válidas."""
    valores: dict[str, list[float]] = {p["id"]: [] for p in PUNTOS_PIURA}
    for var in ("/Soil_Moisture_Retrieval_Data_AM/soil_moisture", "/Soil_Moisture_Retrieval_Data_PM/soil_moisture_pm"):
        ce = urllib.parse.quote(f"{var}[{F0}:{F1}][{C0}:{C1}]", safe="")
        try:
            r = cliente.get(f"{url}.dap.csv?dap4.ce={ce}")
            if r.status_code != 200:
                continue
        except httpx.HTTPError:
            continue
        filas = [l.split(",")[1:] for l in r.text.splitlines() if l.startswith(var)]
        for p in PUNTOS_PIURA:
            f, c = pixel(p["lat"], p["lon"])
            try:
                v = float(filas[f - F0][c - C0])
            except (IndexError, ValueError):
                continue
            if 0 <= v <= 1:
                valores[p["id"]].append(v)
    return {k: (sum(v) / len(v) if v else None) for k, v in valores.items()}


def promedio(dias: list[dict[str, float | None]]) -> tuple[dict, dict]:
    prom, n = {}, {}
    for p in PUNTOS_PIURA:
        vals = [d[p["id"]] for d in dias if d.get(p["id"]) is not None]
        prom[p["id"]] = round(sum(vals) / len(vals), 4) if vals else None
        n[p["id"]] = len(vals)
    return prom, n


def main() -> int:
    token = os.environ.get("EARTHDATA_TOKEN", "").strip()
    if not token:
        print("Falta EARTHDATA_TOKEN", file=sys.stderr)
        return 1
    cliente = httpx.Client(timeout=120, follow_redirects=True, headers={"Authorization": f"Bearer {token}"})
    hoy = date.today()
    fin, ini = hoy - timedelta(days=1), hoy - timedelta(days=30)

    rec = granulos(ini, fin)
    with ThreadPoolExecutor(max_workers=8) as ex:
        dias_rec = list(ex.map(lambda u: leer_dia(cliente, u), rec.values()))
    actual, n_act = promedio(dias_rec)
    print(f"Actual {ini}→{fin}: {len(rec)} días SMAP; piura={actual['piura']} ({n_act['piura']} días con dato)")

    trabajos = []
    for anio in range(2016, hoy.year):
        g = granulos(ini.replace(year=anio), fin.replace(year=anio))
        trabajos += [u for i, (_, u) in enumerate(sorted(g.items())) if i % 2 == 0]
    with ThreadPoolExecutor(max_workers=8) as ex:
        dias_hist = list(ex.map(lambda u: leer_dia(cliente, u), trabajos))
    normal, n_nor = promedio(dias_hist)
    print(f"Normal 2016-{hoy.year - 1} (misma ventana): {len(trabajos)} días; piura={normal['piura']}")

    SALIDA.write_text(json.dumps({
        "metadatos": {
            "producto": {"short_name": SHORT, "version": VERSION, "nombre": "SMAP Enhanced L3 Radiometer Global Daily 9 km EASE-Grid Soil Moisture V006",
                         "variable": "soil_moisture (AM) y soil_moisture_pm (PM)", "unidades": "m3/m3", "doi": "10.5067/M20OXIZHY3RJ",
                         "url": "https://nsidc.org/data/spl3smp_e/versions/6"},
            "generado": hoy.isoformat(),
            "metodo": "Promedio de pasadas AM/PM válidas en el píxel de 9 km de cada punto. Normal = misma ventana de días, 2016 al año pasado.",
        },
        "puntos": PUNTOS_PIURA,
        "actual": {"inicio": ini.isoformat(), "fin": fin.isoformat(), "m3m3": actual, "diasConDato": n_act},
        "normal": {"periodo": f"2016-{hoy.year - 1}", "m3m3": normal, "diasConDato": n_nor},
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Guardado {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
