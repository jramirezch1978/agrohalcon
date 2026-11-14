"""MUR SST v4.1 (NASA JPL, 1 km) por OPeNDAP de PO.DAAC: el valor de UN punto en ~2,5 s, sin bajar el
archivo global (~700 MB). Necesita EARTHDATA_TOKEN. Probado el 14-nov-2026 (a diferencia de los ERDDAP de NOAA,
que no respondieron desde esta red). El dataset llega en kelvin.
"""

import io
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from urllib.parse import quote

import httpx

from .config import USER_AGENT, earthdata_token

CONCEPTO = "C1996881146-POCLOUD"  # MUR-JPL-L4-GLOB-v4.1
GRANULO = "{d:%Y%m%d}090000-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v02.0-fv04.1"
BASE = f"https://opendap.earthdata.nasa.gov/collections/{CONCEPTO}/granules/"
# La rejilla: lat[k] = -89.99 + 0.01 k  ·  lon[k] = -179.99 + 0.01 k (comprobado devolviendo lat/lon junto con el valor)
LAT0, LON0, PASO = -89.99, -179.99, 0.01


def _indices(lat: float, lon: float) -> tuple[int, int]:
    return round((lat - LAT0) / PASO), round((lon - LON0) / PASO)


def sst_c(lat: float, lon: float, dia: date, cliente: httpx.Client | None = None) -> float | None:
    """SST (°C) del día en el punto; None si ese día no hay dato (nube/archivo aún no publicado)."""
    import xarray as xr

    i, j = _indices(lat, lon)
    ce = f"/analysed_sst[0][{i}][{j}];/lat[{i}];/lon[{j}]"
    url = BASE + GRANULO.format(d=dia) + ".dap.nc4?dap4.ce=" + quote(ce, safe="/;:")
    cabeceras = {"Authorization": f"Bearer {earthdata_token()}", "User-Agent": USER_AGENT}
    r = (cliente or httpx).get(url, headers=cabeceras, timeout=90, follow_redirects=True)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    ds = xr.open_dataset(io.BytesIO(r.content), engine="h5netcdf")
    try:
        k = float(ds["analysed_sst"].values.squeeze())
    finally:
        ds.close()
    return None if k != k else round(k - 273.15, 3)


def serie(lat: float, lon: float, fechas: list[date], hilos: int = 8) -> dict[str, float]:
    """{'YYYY-MM-DD': °C}. Los días con error o sin dato se omiten."""
    salida: dict[str, float] = {}
    with httpx.Client() as c, ThreadPoolExecutor(max_workers=hilos) as pool:
        def uno(d: date):
            try:
                return d, sst_c(lat, lon, d, c)
            except Exception:
                return d, None

        for d, v in pool.map(uno, fechas):
            if v is not None:
                salida[d.isoformat()] = v
    return salida


def climatologia(lat: float, lon: float, anios: tuple[int, int] = (2003, 2022), dias_mes: tuple[int, ...] = (1, 11, 21)) -> list[dict]:
    """Promedio por día de referencia (3 por mes) sobre los años base: [{'doy', 'media_c', 'n'}]. ~720 consultas."""
    muestras: dict[tuple[int, int], list[float]] = {}
    fechas = [date(a, m, d) for a in range(anios[0], anios[1] + 1) for m in range(1, 13) for d in dias_mes]
    for d_iso, v in serie(lat, lon, fechas).items():
        d = date.fromisoformat(d_iso)
        muestras.setdefault((d.month, d.day), []).append(v)
    return [
        {"mes": m, "dia": d, "doy": date(2001, m, d).timetuple().tm_yday, "media_c": round(sum(v) / len(v), 3), "n": len(v)}
        for (m, d), v in sorted(muestras.items())
    ]


def anomalia(clima: list[dict], dia: date, valor_c: float) -> float | None:
    """valor - climatología interpolada (circular) en el día del año."""
    if not clima:
        return None
    pts = sorted((c["doy"], c["media_c"]) for c in clima)
    doy = dia.timetuple().tm_yday
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    xs_ext = [x - 365 for x in xs] + xs + [x + 365 for x in xs]
    ys_ext = ys + ys + ys
    for k in range(len(xs_ext) - 1):
        if xs_ext[k] <= doy <= xs_ext[k + 1]:
            t = (doy - xs_ext[k]) / (xs_ext[k + 1] - xs_ext[k])
            return round(valor_c - (ys_ext[k] + t * (ys_ext[k + 1] - ys_ext[k])), 3)
    return None


def ultimos_dias(n: int, hasta: date | None = None) -> list[date]:
    hasta = hasta or date.today()
    return [hasta - timedelta(days=k) for k in range(n)][::-1]
