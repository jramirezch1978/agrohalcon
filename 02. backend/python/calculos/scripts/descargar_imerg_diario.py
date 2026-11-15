"""Descarga la lluvia DIARIA de GPM IMERG V07 para los puntos de Piura (2001 → ayer) y guarda
data/precalculado/imerg_diario_piura.json. Sirve para el detalle por días y semanas de "¿Funciona?".

- Hasta 2025-09-30: IMERG Final diario (GPM_3IMERGDF, corregido con pluviómetros).
- Desde 2025-10-01: IMERG Late diario (GPM_3IMERGDL, casi tiempo real).
- Una sola petición por día: OPeNDAP recorta en el servidor la caja de Piura (~6 KB), nunca el archivo global.
- Incremental: si el archivo ya existe, solo baja los días que faltan.

    set EARTHDATA_TOKEN=...
    python -m scripts.descargar_imerg_diario
"""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import httpx

from app.fuentes.imerg import indice_lat, indice_lon
from app.fuentes.piura import PUNTOS_PIURA

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "precalculado" / "imerg_diario_piura.json"
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
INICIO = date(2001, 1, 1)
FIN_FINAL = date(2025, 9, 30)   # último día de IMERG Final diario
PRODUCTOS = {
    "GPM_3IMERGDF": {"nombre": "GPM IMERG Final Precipitation L3 1 day 0.1° x 0.1° V07", "doi": "10.5067/GPM/IMERGDF/DAY/07"},
    "GPM_3IMERGDL": {"nombre": "GPM IMERG Late Precipitation L3 1 day 0.1° x 0.1° V07", "doi": "10.5067/GPM/IMERGDL/DAY/07"},
}

I = {p["id"]: indice_lon(p["lon"]) for p in PUNTOS_PIURA}
J = {p["id"]: indice_lat(p["lat"]) for p in PUNTOS_PIURA}
I0, I1, J0, J1 = min(I.values()), max(I.values()), min(J.values()), max(J.values())


def granulos(short: str, inicio: date, fin: date) -> dict[str, str]:
    out: dict[str, str] = {}
    pagina = 1
    while True:
        r = httpx.get(CMR, params={"short_name": short, "version": "07", "temporal": f"{inicio}T00:00:00Z,{fin}T23:59:59Z",
                                   "page_size": 2000, "page_num": pagina}, timeout=120)
        r.raise_for_status()
        ent = r.json()["feed"]["entry"]
        if not ent:
            return out
        for e in ent:
            u = next((l["href"] for l in e.get("links", []) if "opendap" in l["href"].lower()), None)
            if u:
                out[e["time_start"][:10]] = u.rstrip("/").removesuffix(".html")
        pagina += 1


def leer_dia(cliente: httpx.Client, url: str) -> dict[str, float | None] | None:
    """mm/día de cada punto ese día (None = sin dato). Devuelve None si la descarga falló."""
    for _ in range(4):
        try:
            r = cliente.get(f"{url}.ascii?precipitation%5B0%5D%5B{I0}:{I1}%5D%5B{J0}:{J1}%5D")
            if r.status_code != 200:
                continue
            filas = [l.split(",")[1:] for l in r.text.splitlines() if l.startswith("precipitation.precipitation[")]
            out: dict[str, float | None] = {}
            for pid in I:
                v = float(filas[I[pid] - I0][J[pid] - J0])
                out[pid] = round(v, 2) if v >= 0 else None
            return out
        except (httpx.HTTPError, ValueError, IndexError):
            pass
    return None


def main() -> int:
    token = os.environ.get("EARTHDATA_TOKEN", "").strip()
    if not token:
        print("Falta EARTHDATA_TOKEN", file=sys.stderr)
        return 1
    ayer = date.today() - timedelta(days=1)
    previo = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else None
    datos: dict[str, dict[str, float | None]] = {}   # fecha -> {punto: mm}
    if previo:
        f0 = date.fromisoformat(previo["inicio"])
        for k, pid in enumerate(previo["puntos_id"]):
            for n, v in enumerate(previo["mm_dia"][pid]):
                datos.setdefault((f0 + timedelta(days=n)).isoformat(), {})[pid] = v
        datos = {f: v for f, v in datos.items() if f not in previo.get("faltan", [])}

    urls: dict[str, str] = {}
    for anio in range(INICIO.year, ayer.year + 1):
        a, b = max(INICIO, date(anio, 1, 1)), min(ayer, date(anio, 12, 31))
        if all((a + timedelta(days=n)).isoformat() in datos for n in range((b - a).days + 1)):
            continue
        if a <= FIN_FINAL:
            urls.update(granulos("GPM_3IMERGDF", a, min(b, FIN_FINAL)))
        if b > FIN_FINAL:
            urls.update(granulos("GPM_3IMERGDL", max(a, FIN_FINAL + timedelta(days=1)), b))
    pendientes = sorted(f for f in urls if f not in datos)
    print(f"Días por descargar: {len(pendientes)}", flush=True)

    cliente = httpx.Client(timeout=120, follow_redirects=True, headers={"Authorization": f"Bearer {token}"})
    hechos = 0

    def tarea(f: str) -> tuple[str, dict | None]:
        return f, leer_dia(cliente, urls[f])

    with ThreadPoolExecutor(max_workers=12) as ex:
        for f, v in ex.map(tarea, pendientes):
            if v is not None:
                datos[f] = v
            hechos += 1
            if hechos % 250 == 0:
                print(f"  {hechos}/{len(pendientes)} ({f})", flush=True)

    fechas = [(INICIO + timedelta(days=n)).isoformat() for n in range((ayer - INICIO).days + 1)]
    faltan = [f for f in fechas if f not in datos]
    SALIDA.write_text(json.dumps({
        "metadatos": {
            "productos": PRODUCTOS,
            "fuente_por_fecha": f"GPM_3IMERGDF hasta {FIN_FINAL}; GPM_3IMERGDL desde {FIN_FINAL + timedelta(days=1)}",
            "unidades": "mm/día", "rejilla": "0.1°; valor de la celda que contiene cada punto",
            "generado": date.today().isoformat(),
        },
        "inicio": INICIO.isoformat(), "fin": ayer.isoformat(), "fin_final": FIN_FINAL.isoformat(),
        "puntos_id": list(I), "faltan": faltan,
        "mm_dia": {pid: [datos.get(f, {}).get(pid) for f in fechas] for pid in I},
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Guardado {SALIDA} · {len(fechas)} días · faltan {len(faltan)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
