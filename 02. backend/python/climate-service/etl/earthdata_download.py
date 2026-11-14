"""Descarga de SMAP, GPM IMERG y MUR SST (con token de Earthdata) y extracción del valor en un punto.

⚠️ NO PROBADO TODAVÍA: falta el token de Earthdata de David (Perfil -> Generate Token -> .env).
   Lo que SÍ está probado: la búsqueda de archivos con etl/cmr.py (sin token).
   Cuando tengas el token, usa el prompt "3. Descargar SMAP/IMERG" de docs/PROMPTS_CLAUDE_CODE.md y ajusta
   los nombres de variables mirando el archivo con `xarray` / `h5py` (cambian entre versiones).

Tamaños (CMR, nov 2026): SMAP SPL3SMP_E ≈ 630 MB POR DÍA (global) · IMERG diario ≈ 25 MB · por eso,
para SMAP conviene AppEEARS (etl/appeears.py: valor del punto sin bajar el archivo entero).
Requiere:  pip install -r requirements-etl.txt   (earthaccess, xarray, h5py)
"""

from datetime import date
from pathlib import Path

import numpy as np

from .config import RAW, earthdata_token


def login():
    """earthaccess toma EARTHDATA_TOKEN del entorno (lo carga config.py desde .env)."""
    import earthaccess

    if not earthdata_token():
        raise RuntimeError("Falta EARTHDATA_TOKEN en .env (ver env.example y docs/CHECKLIST_DAVID.md)")
    earthaccess.login(strategy="environment")
    return earthaccess


def descargar(short_name: str, version: str, lat: float, lon: float, inicio: date, fin: date, carpeta: Path | None = None):
    """Descarga los archivos que cubren el punto en el rango. Devuelve las rutas locales."""
    ea = login()
    destino = (carpeta or RAW / short_name)
    destino.mkdir(parents=True, exist_ok=True)
    resultados = ea.search_data(
        short_name=short_name,
        version=version,
        temporal=(inicio.isoformat(), fin.isoformat()),
        point=(lon, lat),
    )
    print(f"{short_name} v{version}: {len(resultados)} archivos")
    return ea.download(resultados, str(destino))


def valor_smap(ruta_h5: str, lat: float, lon: float) -> float | None:
    """Humedad del suelo (m3/m3) del píxel más cercano en un archivo SPL3SMP_E (HDF5, rejilla EASE 9 km).
    Grupo 'Soil_Moisture_Retrieval_Data_AM': variables soil_moisture, latitude, longitude (2D)."""
    import h5py

    with h5py.File(ruta_h5, "r") as f:
        g = f["Soil_Moisture_Retrieval_Data_AM"]
        lats, lons, sm = g["latitude"][:], g["longitude"][:], g["soil_moisture"][:]
    # distancia al cuadrado en grados: basta para elegir el píxel más cercano en un valle
    d2 = (lats - lat) ** 2 + (lons - lon) ** 2
    d2 = np.where(np.isfinite(lats) & np.isfinite(lons) & (lats > -90), d2, np.inf)
    i = np.unravel_index(np.argmin(d2), d2.shape)
    v = float(sm[i])
    return None if v < 0 or not np.isfinite(v) else v  # -9999 = sin dato


def valor_imerg(ruta_nc: str, lat: float, lon: float) -> float | None:
    """Lluvia diaria (mm/día) del píxel más cercano en un archivo GPM_3IMERGDF/DL (netCDF4, 0,1°).
    La variable se llama 'precipitation'. Si el archivo trae un grupo 'Grid', abre con group='Grid'."""
    import xarray as xr

    try:
        ds = xr.open_dataset(ruta_nc)
        if "precipitation" not in ds:
            ds = xr.open_dataset(ruta_nc, group="Grid")
        v = float(ds["precipitation"].sel(lat=lat, lon=lon, method="nearest").squeeze())
    finally:
        ds.close()
    return None if not np.isfinite(v) else v
