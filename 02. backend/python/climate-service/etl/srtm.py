"""SRTM (NASA/USGS, 30 m): elevación y pendiente de cada valle. Arregla un problema real: la celda de POWER de
Chulucanas dice 1051 m cuando el pueblo está a ~90 m (24_exploracion_apis_nasa.md). Necesita EARTHDATA_TOKEN.
Cada teselas de 1° pesa ~25 MB (SRTMGL1 v003, formato .hgt: enteros de 16 bits big-endian, 3601 x 3601).
"""

import math
import warnings
import zipfile
from pathlib import Path

import numpy as np

from .config import RAW, earthdata_token

SHORT, VERSION = "SRTMGL1", "003"
N = 3601


def nombre_tesela(lat: float, lon: float) -> str:
    return f"{'N' if lat >= 0 else 'S'}{abs(math.floor(lat)):02d}{'E' if lon >= 0 else 'W'}{abs(math.floor(lon)):03d}"


def descargar(lat: float, lon: float) -> Path:
    """Baja (una sola vez) la tesela que cubre el punto y devuelve la ruta del .zip."""
    import earthaccess

    carpeta = RAW / SHORT
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / f"{nombre_tesela(lat, lon)}.SRTMGL1.hgt.zip"
    if destino.exists():
        return destino
    if not earthdata_token():
        raise RuntimeError("Falta EARTHDATA_TOKEN en .env")
    warnings.filterwarnings("ignore")
    earthaccess.login(strategy="environment")
    res = earthaccess.search_data(short_name=SHORT, version=VERSION, point=(lon, lat))
    archivos = earthaccess.download(res[:1], str(carpeta))
    if not archivos:
        raise RuntimeError(f"No se pudo bajar la tesela {nombre_tesela(lat, lon)}")
    return destino


def _leer_hgt(zip_path: Path) -> np.ndarray:
    with zipfile.ZipFile(zip_path) as z:
        nombre = next(n for n in z.namelist() if n.lower().endswith(".hgt"))
        datos = np.frombuffer(z.read(nombre), dtype=">i2")
    return datos.reshape(N, N)


def elevacion_y_pendiente(zip_path: Path, lat: float, lon: float) -> dict:
    """{'elevacion_m', 'pendiente_pct', 'tesela'}: elevación del píxel y pendiente media en ~150 m."""
    mdt = _leer_hgt(zip_path).astype(float)
    mdt[mdt == -32768] = np.nan
    lat0, lon0 = math.floor(lat), math.floor(lon)
    fila = round((lat0 + 1 - lat) * (N - 1))
    col = round((lon - lon0) * (N - 1))
    r = 2  # ventana de 5 x 5 píxeles
    ventana = mdt[max(fila - r, 0) : fila + r + 1, max(col - r, 0) : col + r + 1]
    dy = 30.87  # metros por segundo de arco en latitud
    dx = 30.87 * math.cos(math.radians(lat))
    gy, gx = np.gradient(ventana, dy, dx)
    pendiente = float(np.nanmean(np.hypot(gx, gy)) * 100)
    elev = float(mdt[fila, col])
    return {
        "elevacion_m": None if elev != elev else round(elev, 1),
        "pendiente_pct": None if pendiente != pendiente else round(pendiente, 2),
        "tesela": nombre_tesela(lat, lon),
    }
