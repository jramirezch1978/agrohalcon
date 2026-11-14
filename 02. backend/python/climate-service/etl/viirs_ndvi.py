"""NDVI de VIIRS (VNP13A1 v002, 500 m, compuestas de 16 días, desde 2012) leído por píxel desde el HDF-EOS5 remoto.

Es la continuidad de MODIS MOD13Q1 (mismo índice, mismo tipo de compuesta). Se usa porque MOD13Q1 es HDF4 (hay que bajar
el archivo completo) y el servicio de ORNL estuvo caído el 14-nov-2026. DECLARARLO en References si se usa.
Necesita EARTHDATA_TOKEN.

Robustez: el servidor de LP DAAC a veces deja una conexión colgada para siempre (hilos bloqueados, sin error). Por eso cada
archivo se lee en un PROCESO aparte con límite de tiempo duro; si se pasa, se mata y se reintenta.
"""

import math
import multiprocessing as mp
import queue
import re
import time
import warnings
from collections import defaultdict
from datetime import date, timedelta

from .config import earthdata_token

SHORT, VERSION = "VNP13A1", "002"
R = 6371007.181
T = 1111950.5196666666  # lado de una tesela sinusoidal
XMIN, YMAX = -20015109.354, 10007554.677
GRID = "HDFEOS/GRIDS/VIIRS_Grid_16Day_VI_500m/Data Fields/"
NDVI, CONF = GRID + "500 m 16 days NDVI", GRID + "500 m 16 days pixel reliability"
N = 2400
CONFIABLES = (0, 1)  # 0 = buena, 1 = marginal (2 = nieve/hielo, 3 = nube, 255 = sin dato: no son de fiar)
LIMITE_S = 150  # tiempo máximo por archivo
INTENTOS = 3


def tesela_y_pixel(lat: float, lon: float) -> tuple[int, int, int, int]:
    """(h, v, fila, col) en la proyección sinusoidal de MODIS/VIIRS."""
    x = R * math.radians(lon) * math.cos(math.radians(lat))
    y = R * math.radians(lat)
    h, v = int((x - XMIN) // T), int((YMAX - y) // T)
    col = int(((x - XMIN) - h * T) / (T / N))
    fila = int(((YMAX - y) - v * T) / (T / N))
    return h, v, fila, col


def leer_pixeles(f, fecha: str, zonas: dict[str, tuple[float, float]]) -> list[dict]:
    """Lee los píxeles de `zonas` en un archivo HDF5 ya abierto (h5py.File). Sin red: se prueba con archivos de juguete."""
    nd, cf = f[NDVI], f[CONF]
    salida = []
    for zona, (lat, lon) in zonas.items():
        _, _, fila, col = tesela_y_pixel(lat, lon)
        bruto, conf = int(nd[fila, col]), int(cf[fila, col])
        if bruto < -2000 or bruto > 10000 or conf not in CONFIABLES:
            continue
        salida.append({"zona": zona, "fecha": fecha, "ndvi": round(bruto * 0.0001, 4), "confiabilidad": conf})
    return salida


def _trabajo(granulo, fecha: str, zonas: dict, cola) -> None:  # corre en un proceso aparte
    try:
        import earthaccess
        import h5py

        warnings.filterwarnings("ignore")
        earthaccess.login(strategy="environment")
        with h5py.File(earthaccess.open([granulo])[0], "r") as f:
            cola.put(("ok", leer_pixeles(f, fecha, zonas)))
    except Exception as e:  # noqa: BLE001
        cola.put(("error", f"{type(e).__name__}: {str(e)[:100]}"))


def serie(puntos: dict[str, tuple[float, float]], inicio: date, fin: date, paralelo: int = 3) -> dict:
    """{'datos': [{'zona','fecha','ndvi','confiabilidad'}], 'errores': [...]}. `fecha` = inicio de la compuesta."""
    import earthaccess

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

    por_tesela: dict[tuple[int, int], dict[str, tuple[float, float]]] = defaultdict(dict)
    for nombre, (lat, lon) in puntos.items():
        h, v, _, _ = tesela_y_pixel(lat, lon)
        por_tesela[(h, v)][nombre] = (lat, lon)

    pendientes = []  # (ur, granulo, fecha, zonas, intento)
    for g in res:
        ur = g["umm"]["GranuleUR"]
        m = re.search(r"\.A(\d{4})(\d{3})\.h(\d{2})v(\d{2})\.", ur)
        if not m or (int(m.group(3)), int(m.group(4))) not in por_tesela:
            continue
        fecha = (date(int(m.group(1)), 1, 1) + timedelta(days=int(m.group(2)) - 1)).isoformat()
        pendientes.append((ur, g, fecha, por_tesela[(int(m.group(3)), int(m.group(4)))], 1))
    total = len(pendientes)

    ctx = mp.get_context("spawn")
    activos: list[tuple] = []  # (proceso, cola, t0, trabajo)
    datos, errores = [], []
    while pendientes or activos:
        while pendientes and len(activos) < paralelo:
            trabajo = pendientes.pop(0)
            cola = ctx.Queue()
            p = ctx.Process(target=_trabajo, args=(trabajo[1], trabajo[2], trabajo[3], cola), daemon=True)
            p.start()
            activos.append((p, cola, time.time(), trabajo))
        for a in list(activos):
            p, cola, t0, (ur, g, fecha, zonas, intento) = a
            try:
                estado, carga = cola.get(timeout=0.2)
            except queue.Empty:
                if time.time() - t0 > LIMITE_S or not p.is_alive():
                    p.terminate()
                    activos.remove(a)
                    estado, carga = "error", "tiempo agotado o proceso caído"
                else:
                    continue
            else:
                p.join(5)
                activos.remove(a)
            if estado == "ok":
                datos += carga
            elif intento < INTENTOS:
                pendientes.append((ur, g, fecha, zonas, intento + 1))
            else:
                errores.append(f"{ur}: {carga}")
        time.sleep(0.3)
    return {"producto": f"{SHORT}.{VERSION}", "granulos": total, "datos": datos, "errores": errores}
