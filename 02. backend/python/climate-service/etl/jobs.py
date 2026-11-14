"""Descargas largas hacia la caché (data/raw/cache). Cada trabajo es independiente y se puede repetir.

    python -m etl.jobs power            # NASA POWER: mensual 1981-hoy y diario reciente + 2016/17, 16 valles
    python -m etl.jobs nino             # NOAA Niño 1+2/3/3.4/4 + ONI (sin llave)
    python -m etl.jobs smap             # SMAP: últimos 60 días + ene-may 2017 (token)
    python -m etl.jobs smap-clima       # SMAP: normal 2016-2025 (1 de cada 7 días; ~10 min; token)
    python -m etl.jobs mur              # MUR SST: últimos 60 días en 2 puntos de mar (token)
    python -m etl.jobs mur-clima        # MUR SST: climatología 2003-2022 (~720 consultas, ~5 min; token)
    python -m etl.jobs srtm             # elevación y pendiente por valle (token; ~25 MB por teselas)
    python -m etl.jobs ndvi             # VIIRS NDVI dic-2016..jul-2017 y últimos 9 meses (token)
    python -m etl.jobs suelos           # ISRIC SoilGrids (lento: ~13 s por valle)
    python -m etl.jobs imerg            # GPM IMERG (necesita aceptar el acuerdo GES DISC en Earthdata)
    python -m etl.jobs todo             # todo lo anterior, en orden, sin detenerse por un fallo
"""

import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from . import cache, cpc, mur_opendap, nasa_power, oni, smap, soilgrids, srtm, viirs_ndvi
from .zonas import PUNTOS_MAR, ZONAS

HOY = date.today()
POWER_MENSUAL = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "GWETTOP", "GWETROOT", "ALLSKY_SFC_SW_DWN", "RH2M", "WS2M", "EVPTRNS"]
POWER_DIARIO = ["T2M_MAX", "T2M_MIN", "PRECTOTCORR", "GWETTOP", "GWETROOT", "RH2M", "EVPTRNS"]


def _puntos() -> dict[str, tuple[float, float]]:
    return {z.nombre: (z.lat, z.lon) for z in ZONAS}


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ------------------------------------------------------------------ NASA POWER
def job_power() -> None:
    def uno(z):
        try:
            mensual = nasa_power.mensual(z.lat, z.lon, 1981, HOY.year, POWER_MENSUAL)
        except RuntimeError:  # algún parámetro no disponible en la comunidad AG: se baja el juego base
            mensual = nasa_power.mensual(z.lat, z.lon, 1981, HOY.year)
        diario_2017 = nasa_power.diario(z.lat, z.lon, date(2016, 12, 1), date(2017, 6, 30), POWER_DIARIO)
        reciente = nasa_power.diario(z.lat, z.lon, HOY - timedelta(days=420), HOY, POWER_DIARIO)
        return {"zona": z.nombre, "lat": z.lat, "lon": z.lon, "mensual": mensual, "diario_2017": diario_2017, "diario_reciente": reciente}

    with ThreadPoolExecutor(max_workers=4) as pool:
        resultados = list(pool.map(uno, ZONAS))
    cache.guardar("power", {"descargado": HOY.isoformat(), "zonas": resultados})
    _log(f"power: {len(resultados)} valles, {sum(len(v) for r in resultados for v in r['mensual'].values())} valores mensuales")


# ------------------------------------------------------------------ Índices del Pacífico
def job_nino() -> None:
    filas = cpc.nino_mensual()
    cache.guardar("nino", {"descargado": HOY.isoformat(), "nino": filas, "oni": oni.serie(), "episodios_nino12": cpc.episodios(filas)})
    _log(f"nino: {len(filas)} meses (último {filas[-1]['fecha']}, Niño 1+2 anomalía {filas[-1]['nino12_anom']} °C)")


# ------------------------------------------------------------------ SMAP
def job_smap() -> None:
    pts = _puntos()
    reciente = smap.serie(pts, HOY - timedelta(days=45), HOY)
    _log(f"smap reciente: {len(reciente['datos'])} valores, {reciente['sin_dato']} sin cobertura, {len(reciente['errores'])} errores")
    historico = smap.serie(pts, date(2017, 1, 10), date(2017, 4, 20), cada_dias=2)
    _log(f"smap 2017: {len(historico['datos'])} valores, {historico['sin_dato']} sin cobertura, {len(historico['errores'])} errores")
    cache.guardar("smap", {"descargado": HOY.isoformat(), "reciente": reciente, "ene_may_2017": historico})


def job_smap_clima() -> None:
    """Un día de cada diez de 2016 a 2025: el 'normal' de SMAP por mes (SMAP existe desde 2015)."""
    s = smap.serie(_puntos(), date(2016, 1, 1), date(2025, 12, 31), hilos=4, cada_dias=10)
    _log(f"smap-clima: {len(s['datos'])} valores de {s['granulos']} archivos, {len(s['errores'])} errores")
    cache.guardar("smap_clima", {"descargado": HOY.isoformat(), "muestreo": "1 de cada 10 días, 2016-2025", **s})


# ------------------------------------------------------------------ MUR SST
def job_mur() -> None:
    salida = {}
    for z in PUNTOS_MAR:
        s = mur_opendap.serie(z.lat, z.lon, mur_opendap.ultimos_dias(60, HOY - timedelta(days=3)))
        salida[z.nombre] = {"lat": z.lat, "lon": z.lon, "sst_c": s}
        _log(f"mur {z.nombre}: {len(s)} días")
    cache.guardar("mur", {"descargado": HOY.isoformat(), "puntos": salida})


def job_mur_clima() -> None:
    salida = {}
    for z in PUNTOS_MAR:
        salida[z.nombre] = mur_opendap.climatologia(z.lat, z.lon)
        _log(f"mur-clima {z.nombre}: {len(salida[z.nombre])} fechas de referencia")
    cache.guardar("mur_clima", {"descargado": HOY.isoformat(), "anios_base": [2003, 2022], "puntos": salida})


# ------------------------------------------------------------------ SRTM
def job_srtm() -> None:
    filas = []
    for z in ZONAS:
        try:
            ruta = srtm.descargar(z.lat, z.lon)
            filas.append({"zona": z.nombre, **srtm.elevacion_y_pendiente(ruta, z.lat, z.lon)})
            _log(f"srtm {z.nombre}: {filas[-1]['elevacion_m']} m, pendiente {filas[-1]['pendiente_pct']} %")
        except Exception as e:
            filas.append({"zona": z.nombre, "error": f"{type(e).__name__}: {str(e)[:120]}"})
            _log(f"srtm {z.nombre}: ERROR {e}")
    cache.guardar("srtm", {"descargado": HOY.isoformat(), "zonas": filas})


# ------------------------------------------------------------------ NDVI
def job_ndvi() -> None:
    pts = _puntos()
    a = viirs_ndvi.serie(pts, date(2016, 12, 1), date(2017, 7, 31))
    _log(f"ndvi 2017: {len(a['datos'])} valores, {len(a['errores'])} errores")
    b = viirs_ndvi.serie(pts, HOY - timedelta(days=270), HOY)
    _log(f"ndvi reciente: {len(b['datos'])} valores, {len(b['errores'])} errores")
    cache.guardar("ndvi", {"descargado": HOY.isoformat(), "dic2016_jul2017": a, "reciente": b})


# ------------------------------------------------------------------ Suelos
def job_suelos() -> None:
    filas = []
    for z in ZONAS:
        try:
            filas.append({"zona": z.nombre, **soilgrids.suelo_punto(z.lat, z.lon)})
        except Exception as e:
            filas.append({"zona": z.nombre, "error": str(e)[:120]})
        _log(f"suelos {z.nombre}: {filas[-1]}")
        time.sleep(4)
    cache.guardar("suelos", {"descargado": HOY.isoformat(), "fuente": "ISRIC SoilGrids v2.0 (0-30 cm, promedio ponderado)", "zonas": filas})


# ------------------------------------------------------------------ IMERG (requiere aceptar el acuerdo GES DISC)
def job_imerg() -> None:
    import warnings

    import earthaccess
    import xarray as xr

    from .config import RAW

    warnings.filterwarnings("ignore")
    earthaccess.login(strategy="environment")
    carpeta = RAW / "GPM_3IMERGDL"
    carpeta.mkdir(parents=True, exist_ok=True)
    res = earthaccess.search_data(short_name="GPM_3IMERGDL", version="07", temporal=((HOY - timedelta(days=30)).isoformat(), HOY.isoformat()))
    archivos = earthaccess.download(res, str(carpeta))
    datos = []
    for ruta in archivos:
        ds = xr.open_dataset(ruta)
        d8 = str(ruta).split("IMERG.")[1][:8]
        for z in ZONAS:
            v = float(ds["precipitation"].sel(lat=z.lat, lon=z.lon, method="nearest").squeeze())
            if v == v:
                datos.append({"zona": z.nombre, "fecha": f"{d8[:4]}-{d8[4:6]}-{d8[6:]}", "valor": round(v, 3)})
        ds.close()
    cache.guardar("imerg", {"descargado": HOY.isoformat(), "producto": "GPM_3IMERGDL.07", "datos": datos})
    _log(f"imerg: {len(datos)} valores")


JOBS = {
    "power": job_power, "nino": job_nino, "smap": job_smap, "smap-clima": job_smap_clima, "mur": job_mur, "mur-clima": job_mur_clima,
    "srtm": job_srtm, "ndvi": job_ndvi, "suelos": job_suelos, "imerg": job_imerg,
}  # fmt: skip


def main(argv: list[str]) -> None:
    pedidos = list(JOBS) if argv == ["todo"] else argv
    if not pedidos or any(p not in JOBS for p in pedidos):
        print(__doc__)
        sys.exit(1)
    for p in pedidos:
        _log(f"=== {p} ===")
        t0 = time.time()
        try:
            JOBS[p]()
            _log(f"{p}: OK en {time.time() - t0:.0f} s")
        except Exception as e:
            _log(f"{p}: FALLÓ ({type(e).__name__}: {str(e)[:200]})")
            traceback.print_exc(limit=2)
    sys.stdout.flush()
    os._exit(0)  # hilos de red colgados no deben impedir que el proceso termine (la caché ya se guardó)


if __name__ == "__main__":
    main(sys.argv[1:])
