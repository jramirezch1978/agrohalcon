"""Descarga GPM IMERG V07 para los puntos de Piura recortando en el servidor (OPeNDAP de GES DISC) y guarda
data/precalculado/imerg_piura.json. Solo se transfieren ~30 KB por archivo (la caja de Piura), no el global.

Requiere cuenta de NASA Earthdata (EARTHDATA_USERNAME / EARTHDATA_PASSWORD o ~/.netrc) con la aplicación
"NASA GESDISC DATA ARCHIVE" autorizada.

    python -m scripts.descargar_imerg                # mensual 2001 → 2025-09 + diario Late 45 días (~5-10 min)
    python -m scripts.descargar_imerg --actualizar   # solo vuelve a pedir el diario reciente (~1 min)

Reanudable: cada archivo procesado queda en data/crudo/imerg/ (unos bytes por archivo).
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import earthaccess
import numpy as np
import xarray as xr

from app.fuentes.imerg import (
    ANIOS_CLIMATOLOGIA, PRODUCTO_DIARIO, PRODUCTO_MENSUAL, indice_lat, indice_lon, mm_hr_a_mm_dia, mm_hr_a_mm_mes, valido,
)
from app.fuentes.piura import CAJA_PIURA, PUNTOS_PIURA

RAIZ = Path(__file__).resolve().parent.parent
CRUDO = RAIZ / "data" / "crudo" / "imerg"
SALIDA = RAIZ / "data" / "precalculado" / "imerg_piura.json"

J0, J1 = indice_lat(CAJA_PIURA["lat"][0]) - 1, indice_lat(CAJA_PIURA["lat"][1]) + 1
I0, I1 = indice_lon(CAJA_PIURA["lon"][0]) - 1, indice_lon(CAJA_PIURA["lon"][1]) + 1


def url_opendap(granulo) -> str:
    for u in granulo["umm"].get("RelatedUrls", []):
        if u.get("Type") == "USE SERVICE API" and "opendap" in u["URL"]:
            return u["URL"]
    raise RuntimeError("Gránulo sin enlace OPeNDAP")


def fecha_granulo(granulo) -> str:
    return granulo["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"][:10]


def valores_puntos(sesion, url: str, variable: str) -> dict[str, float | None]:
    """Pide solo la caja de Piura y devuelve el valor de la celda más cercana a cada punto (unidades de origen)."""
    grupo = variable.rsplit("/", 1)[0]  # "/Grid" o ""
    ce = f"{variable}[0][{I0}:{I1}][{J0}:{J1}];{grupo}/lat[{J0}:{J1}];{grupo}/lon[{I0}:{I1}]"
    r = sesion.get(url + ".dap.nc4?dap4.ce=" + urllib.parse.quote(ce, safe="/[]:"), timeout=180)
    r.raise_for_status()
    with tempfile.NamedTemporaryFile(suffix=".nc4", delete=False) as f:
        f.write(r.content)
    try:
        with xr.open_dataset(f.name, engine="h5netcdf", group=grupo.strip("/") or None) as ds:
            campo = ds[variable.rsplit("/", 1)[1]].isel(time=0).load()
    finally:
        Path(f.name).unlink(missing_ok=True)
    salida = {}
    for p in PUNTOS_PIURA:
        v = float(campo.sel(lon=p["lon"], lat=p["lat"], method="nearest"))
        salida[p["id"]] = v if valido(v) else None
    return salida


def procesar(sesion, granulo, producto: dict, forzar: bool) -> tuple[str, dict]:
    fecha = fecha_granulo(granulo)
    archivo = CRUDO / f"{producto['short_name']}_{fecha}.json"
    if archivo.exists() and not forzar:
        return fecha, json.loads(archivo.read_text())
    for intento in range(4):
        try:
            vals = valores_puntos(sesion, url_opendap(granulo), producto["variable"])
            archivo.parent.mkdir(parents=True, exist_ok=True)
            archivo.write_text(json.dumps(vals))
            return fecha, vals
        except Exception as e:  # noqa: BLE001 — red, OPeNDAP o HDF5: reintentar
            print(f"  ! {producto['short_name']} {fecha}: {type(e).__name__}: {e}", file=sys.stderr)
            time.sleep(3 * 2**intento)
    raise RuntimeError(f"No se pudo procesar {producto['short_name']} {fecha}")


def r2(x: float | None) -> float | None:
    return None if x is None or not np.isfinite(x) else round(float(x), 2)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--desde", default="2001-01")
    ap.add_argument("--dias", type=int, default=45, help="días recientes del diario Late")
    ap.add_argument("--actualizar", action="store_true")
    ap.add_argument("--hilos", type=int, default=4)
    a = ap.parse_args()

    # Busca EARTHDATA_USERNAME/PASSWORD y luego ~/.netrc. Nunca se guardan credenciales en el repositorio.
    if not earthaccess.login().authenticated:
        raise SystemExit("Login de Earthdata falló: revisa EARTHDATA_USERNAME / EARTHDATA_PASSWORD")
    sesion = earthaccess.get_requests_https_session()
    t0 = time.time()

    mensuales = earthaccess.search_data(short_name=PRODUCTO_MENSUAL["short_name"], version="07",
                                        temporal=(f"{a.desde}-01", date.today().isoformat()))
    hoy = date.today()
    diarios = earthaccess.search_data(short_name=PRODUCTO_DIARIO["short_name"], version="07",
                                      temporal=((hoy - timedelta(days=a.dias)).isoformat(), hoy.isoformat()))
    print(f"{len(mensuales)} meses (Final) y {len(diarios)} días (Late) encontrados en CMR")

    with ThreadPoolExecutor(a.hilos) as ex:
        res_m = dict(ex.map(lambda g: procesar(sesion, g, PRODUCTO_MENSUAL, False), mensuales))
        res_d = dict(ex.map(lambda g: procesar(sesion, g, PRODUCTO_DIARIO, a.actualizar), diarios))

    meses = sorted(res_m)
    ids = [p["id"] for p in PUNTOS_PIURA]

    # Mensual: mm/hr → mm/mes
    mm_mes = {i: [r2(mm_hr_a_mm_mes(res_m[m][i], int(m[:4]), int(m[5:7])) if res_m[m][i] is not None else None)
                  for m in meses] for i in ids}

    # Climatología 2001-2020 por mes del año (solo meses con dato; se informa cuántos años entraron)
    a0, a1 = ANIOS_CLIMATOLOGIA
    clim_mes, clim_dia, n_anios = {}, {}, {}
    for i in ids:
        clim_mes[i], clim_dia[i], n_anios[i] = [], [], []
        for mes in range(1, 13):
            vals_hr = [res_m[m][i] for m in meses
                       if a0 <= int(m[:4]) <= a1 and int(m[5:7]) == mes and res_m[m][i] is not None]
            media_hr = float(np.mean(vals_hr)) if vals_hr else None
            clim_dia[i].append(r2(mm_hr_a_mm_dia(media_hr)) if media_hr is not None else None)
            # mm/mes de un mes "típico": media de mm/día x días del mes (año no bisiesto)
            clim_mes[i].append(r2(mm_hr_a_mm_mes(media_hr, 2001, mes)) if media_hr is not None else None)
            n_anios[i].append(len(vals_hr))

    fechas = sorted(res_d)
    diario = {i: [r2(res_d[f][i]) for f in fechas] for i in ids}

    salida = {
        "metadatos": {
            "productos": {
                "mensual": {**PRODUCTO_MENSUAL, "uso": "series mensuales y climatología",
                            "url": "https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGM_07/summary"},
                "diario": {**PRODUCTO_DIARIO, "uso": "últimos días (indicador actual)",
                           "url": "https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGDL_07/summary",
                           "nota": "Late run: casi tiempo real, SIN corrección con pluviómetros. La normal viene "
                                   "del Final mensual (con pluviómetros): puede haber un sesgo entre ambos."},
            },
            "acceso": "OPeNDAP de NASA Earthdata (opendap.earthdata.nasa.gov), recorte en el servidor",
            "proveedor": "NASA GES DISC",
            "zona": {"nombre": "Piura", "lat": list(CAJA_PIURA["lat"]), "lon": list(CAJA_PIURA["lon"])},
            "metodo_puntos": "Celda de 0.1° más cercana a cada punto (sin interpolar)",
            "conversion": "mensual: mm/hr x 24 x días del mes = mm/mes; mm/hr x 24 = mm/día",
            "climatologia": f"Media {a0}-{a1} de IMERG Final mensual",
            "unidades": {"mm_mes": "mm/mes", "mm_dia": "mm/día"},
            "periodo_mensual": {"inicio": meses[0], "fin": meses[-1]},
            "periodo_diario": {"inicio": fechas[0] if fechas else None, "fin": fechas[-1] if fechas else None},
            "descargado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "puntos": PUNTOS_PIURA,
        "mensual": {"meses": [m[:7] for m in meses], "mm_mes": mm_mes},
        "climatologia": {"periodo": f"{a0}-{a1}", "mm_mes": clim_mes, "mm_dia": clim_dia, "anios_con_dato": n_anios},
        "diario": {"fechas": fechas, "mm_dia": diario},
    }
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False), encoding="utf-8")
    print(f"→ {SALIDA} ({SALIDA.stat().st_size / 1024:.0f} KB) en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
