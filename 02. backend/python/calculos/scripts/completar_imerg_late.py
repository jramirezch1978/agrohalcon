"""Completa data/precalculado/imerg_piura.json con meses de IMERG Late (GPM_3IMERGDL) sumados por mes,
desde el mes siguiente al último IMERG Final (2025-09) hasta el mes actual.

IMERG Final mensual (GPM_3IMERGM) termina en 2025-09: sin esto, 2025 y 2026 no tienen 12 meses y no aparecen
en "¿Funciona?". Los meses agregados quedan marcados en mensual["fuente_mes"] como "GPM IMERG Late".

Usa el token de NASA Earthdata (EARTHDATA_TOKEN). Recorta en el servidor (OPeNDAP ASCII): pocos KB por día.

    set EARTHDATA_TOKEN=...   (o en el entorno)
    python -m scripts.completar_imerg_late
"""
from __future__ import annotations

import calendar
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import httpx

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO = RAIZ / "data" / "precalculado" / "imerg_piura.json"
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"


def indice_lon(lon: float) -> int:
    return int(round((lon + 179.95) / 0.1))


def indice_lat(lat: float) -> int:
    return int(round((lat + 89.95) / 0.1))


def granulos_late(inicio: date, fin: date) -> dict[str, str]:
    """fecha -> URL OPeNDAP de cada día de GPM_3IMERGDL V07."""
    out: dict[str, str] = {}
    pagina = 1
    while True:
        r = httpx.get(CMR, params={"short_name": "GPM_3IMERGDL", "version": "07", "temporal": f"{inicio}T00:00:00Z,{fin}T23:59:59Z",
                                   "page_size": 200, "page_num": pagina, "sort_key": "start_date"}, timeout=60)
        r.raise_for_status()
        entradas = r.json()["feed"]["entry"]
        if not entradas:
            break
        for e in entradas:
            url = next((l["href"] for l in e.get("links", []) if "opendap" in l["href"].lower()), None)
            if url:
                out[e["time_start"][:10]] = url.rstrip("/").removesuffix(".html")
        pagina += 1
    return out


def main() -> int:
    token = os.environ.get("EARTHDATA_TOKEN", "").strip()
    if not token:
        print("Falta EARTHDATA_TOKEN en el entorno", file=sys.stderr)
        return 1
    datos = json.loads(ARCHIVO.read_text(encoding="utf-8"))
    puntos = datos["puntos"]
    meses = datos["mensual"]["meses"]
    ultimo_final = meses[-1]
    a, m = int(ultimo_final[:4]), int(ultimo_final[5:7])
    inicio = date(a + (m == 12), m % 12 + 1, 1)
    hoy = date.today()
    print(f"Último mes Final: {ultimo_final}. Completo con IMERG Late desde {inicio} hasta {hoy - timedelta(days=1)}")

    urls = granulos_late(inicio, hoy - timedelta(days=1))
    print(f"Gránulos diarios encontrados: {len(urls)}")
    cliente = httpx.Client(timeout=120, follow_redirects=True, headers={"Authorization": f"Bearer {token}"})

    def leer_dia(item: tuple[str, str]) -> tuple[str, dict[str, float | None]]:
        fecha, url = item
        vals: dict[str, float | None] = {}
        for p in puntos:
            i, j = indice_lon(p["lon"]), indice_lat(p["lat"])
            for _ in range(3):
                try:
                    r = cliente.get(f"{url}.ascii?precipitation%5B0%5D%5B{i}%5D%5B{j}%5D")
                    if r.status_code == 200:
                        v = float(r.text.strip().splitlines()[-1].split(",")[-1])
                        vals[p["id"]] = v if v >= 0 else None
                        break
                except (httpx.HTTPError, ValueError, IndexError):
                    pass
            else:
                vals[p["id"]] = None
        return fecha, vals

    with ThreadPoolExecutor(max_workers=6) as ex:
        diarios = dict(ex.map(leer_dia, sorted(urls.items())))

    # Suma por mes (solo meses con todos los días: el mes en curso queda fuera hasta cerrarse)
    nuevos: list[str] = []
    mm_mes = datos["mensual"]["mm_mes"]
    fuente_mes = datos["mensual"].setdefault("fuente_mes", {})
    y, mo = inicio.year, inicio.month
    while (y, mo) < (hoy.year, hoy.month):
        dias = [date(y, mo, d).isoformat() for d in range(1, calendar.monthrange(y, mo)[1] + 1)]
        clave = f"{y}-{mo:02d}"
        if all(d in diarios for d in dias):
            for p in puntos:
                serie = [diarios[d][p["id"]] for d in dias]
                mm_mes[p["id"]].append(round(sum(serie), 2) if all(v is not None for v in serie) else None)
            meses.append(clave)
            fuente_mes[clave] = "GPM IMERG Late"
            nuevos.append(clave)
        else:
            print(f"  {clave}: faltan días en IMERG Late, no se agrega")
        y, mo = (y + 1, 1) if mo == 12 else (y, mo + 1)

    datos["metadatos"].setdefault("notas", []).append(
        f"Meses {nuevos[0] if nuevos else '-'} a {nuevos[-1] if nuevos else '-'}: suma diaria de IMERG Late (GPM_3IMERGDL V07), "
        "porque IMERG Final mensual termina en 2025-09. Late no tiene corrección con pluviómetros.")
    ARCHIVO.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Meses agregados: {nuevos}")
    print("piura:", [mm_mes['piura'][meses.index(k)] for k in nuevos])
    return 0


if __name__ == "__main__":
    sys.exit(main())
