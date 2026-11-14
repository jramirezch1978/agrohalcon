"""NDVI de VIIRS (VNP13A1 v002, 500 m, compuestas de 16 días, desde 2012) leído por píxel desde el HDF-EOS5 remoto.

Es la continuidad de MODIS MOD13Q1 (mismo índice, mismo tipo de compuesta). Se usa porque MOD13Q1 es HDF4 (hay que bajar
el archivo completo) y el servicio de ORNL estuvo caído el 14-nov-2026. DECLARARLO en References si se usa.
Necesita EARTHDATA_TOKEN. Probado: el archivo se abre en ~7 s y cada píxel es una sola lectura de fila.
"""

import math
import re
import time
import warnings
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from .config import earthdata_token

SHORT, VERSION = "VNP13A1", "002"
R = 6371007.181
T = 1111950.5196666666  # lado de una tesela sinusoidal
XMIN, YMAX = -20015109.354, 10007554.677
GRID = "HDFEOS/GRIDS/VIIRS_Grid_16Day_VI_500m/Data Fields/"
NDVI, CONF = GRID + "500 m 16 days NDVI", GRID + "500 m 16 days pixel reliability"
N = 2400
CONFIABLES = (0, 1)  # 0 = buena, 1 = marginal


def tesela_y_pixel(lat: float, lon: float) -> tuple[int, int, int, int]:
    """(h, v, fila, col) en la proyección sinusoidal de MODIS/VIIRS."""
    x = R * math.radians(lon) * math.cos(math.radians(lat))
    y = R * math.radians(lat)
    h, v = int((x - XMIN) // T), int((YMAX - y) // T)
    col = int(((x - XMIN) - h * T) / (T / N))
    fila = int(((YMAX - y) - v * T) / (T / N))
    return h, v, fila, col


def serie(puntos: dict[str, tuple[float, float]], inicio: date, fin: date, hilos: int = 3) -> dict:
    """{'datos': [{'zona','fecha','ndvi','confiabilidad'}], 'errores': [...]}. `fecha` = inicio de la compuesta.
    Solo se guardan píxeles con confiabilidad 0 (buena) o 1 (marginal)."""
    import earthaccess
    import h5py

    if not earthdata_token():
        raise RuntimeError("Falta EARTHDATA_TOKEN en .env")
    warnings.filterwarnings("ignore")
    earthaccess.login(strategy="environment")
    lats = [p[0] for p in puntos.values()]
    lons = [p[1] for p in puntos.values()]
    res = earthaccess.search_data(
        short_name=SHORT, version=VERSION, temporal=(inicio.isoformat(), fin.isoformat()),
        bounding_box=(min(lons) - 0.2, min(lats) - 0.2, max(lons) + 0.2, max(lats) + 0.2), count=500,
    )  # fmt: skip

    por_tesela: dict[tuple[int, int], list[str]] = defaultdict(list)
    for nombre, (lat, lon) in puntos.items():
        h, v, _, _ = tesela_y_pixel(lat, lon)
        por_tesela[(h, v)].append(nombre)

    def leer(g, h: int, v: int, fecha: str) -> list[dict]:
        """Lee los píxeles de las zonas de esa tesela. Reintenta (502/timeouts del servidor de LP DAAC son comunes)."""
        ultimo: Exception | None = None
        for intento in range(1, 4):
            try:
                salida = []
                with h5py.File(earthaccess.open([g])[0], "r") as f:
                    nd, cf = f[NDVI], f[CONF]
                    for zona in por_tesela[(h, v)]:
                        _, _, fila, col = tesela_y_pixel(*puntos[zona])
                        bruto, conf = int(nd[fila, col]), int(cf[fila, col])
                        if bruto < -2000 or bruto > 10000:  # relleno / fuera de rango
                            continue
                        if conf not in CONFIABLES:  # 2 = nieve/hielo, 3 = nube, 255 = sin dato: el NDVI no es de fiar
                            continue
                        salida.append({"zona": zona, "fecha": fecha, "ndvi": round(bruto * 0.0001, 4), "confiabilidad": conf})
                return salida
            except Exception as e:
                ultimo = e
                time.sleep(5 * intento)
        raise RuntimeError(f"{type(ultimo).__name__}: {str(ultimo)[:100]}")

    trabajos = []
    for g in res:
        ur = g["umm"]["GranuleUR"]
        m = re.search(r"\.A(\d{4})(\d{3})\.h(\d{2})v(\d{2})\.", ur)
        if not m or (int(m.group(3)), int(m.group(4))) not in por_tesela:
            continue
        fecha = (date(int(m.group(1)), 1, 1) + timedelta(days=int(m.group(2)) - 1)).isoformat()
        trabajos.append((ur, g, int(m.group(3)), int(m.group(4)), fecha))

    datos, errores = [], []
    pool = ThreadPoolExecutor(max_workers=hilos)
    futuros = [(ur, pool.submit(leer, g, h, v, fecha)) for ur, g, h, v, fecha in trabajos]
    for ur, fut in futuros:
        try:
            datos += fut.result(timeout=420)  # una conexión colgada no debe tumbar la serie entera
        except Exception as e:
            errores.append(f"{ur}: {type(e).__name__}: {str(e)[:100]}")
    pool.shutdown(wait=False, cancel_futures=True)
    return {"producto": f"{SHORT}.{VERSION}", "granulos": len(trabajos), "datos": datos, "errores": errores}
