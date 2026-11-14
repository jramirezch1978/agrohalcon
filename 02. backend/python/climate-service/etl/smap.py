"""SMAP SPL3SMP_E v006 (humedad del suelo, 9 km) leído SIN bajar el archivo entero (~630 MB por día):
earthaccess abre el HDF5 por HTTP y h5py lee solo el píxel pedido. Necesita EARTHDATA_TOKEN en .env.

Probado el 14-nov-2026: la fórmula EASE-Grid 2.0 (EPSG:6933) coincide exactamente con las coordenadas del archivo
(8 de 8 píxeles al azar). SMAP cubre cada punto cada 2-3 días: habrá días sin dato (-9999), es normal.
"""

import re
import warnings
from concurrent.futures import ThreadPoolExecutor
from datetime import date

from .config import earthdata_token

SHORT, VERSION = "SPL3SMP_E", "006"
X0, Y0, RES = -17367530.445, 7314540.8307, 9008.055  # origen y tamaño de celda de EASE2 global 9 km
FILAS, COLUMNAS = 1624, 3856
FILL = -9999.0
_transformador = None


def pixel(lat: float, lon: float) -> tuple[int, int]:
    """(fila, columna) de la rejilla EASE-Grid 2.0 global de 9 km."""
    global _transformador
    if _transformador is None:
        from pyproj import Transformer

        _transformador = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
    x, y = _transformador.transform(lon, lat)
    return int((Y0 - y) // RES), int((x - X0) // RES)


def _login():
    import earthaccess

    if not earthdata_token():
        raise RuntimeError("Falta EARTHDATA_TOKEN en .env")
    warnings.filterwarnings("ignore")
    earthaccess.login(strategy="environment")
    return earthaccess


def leer_puntos(fobj, puntos: dict[str, tuple[float, float]]) -> dict[str, dict]:
    """Valor de soil_moisture (m3/m3, pasada de la mañana) de cada punto en un archivo abierto."""
    import h5py

    salida: dict[str, dict] = {}
    with h5py.File(fobj, "r") as f:
        g = f["Soil_Moisture_Retrieval_Data_AM"]
        # Se lee el arreglo completo UNA vez (~6 s, comprimido) en vez de 2 lecturas remotas por punto: ~5x más rápido
        sm, flag = g["soil_moisture"][:], g["retrieval_qual_flag"][:]
        for nombre, (lat, lon) in puntos.items():
            fila, col = pixel(lat, lon)
            v = float(sm[fila, col])
            q = int(flag[fila, col])
            if v == FILL or v < 0:
                salida[nombre] = {"valor": None, "motivo": "sin cobertura ese día"}
            elif q & 1:  # bit 0 = calidad NO recomendada
                salida[nombre] = {"valor": None, "motivo": "calidad no recomendada", "bruto": round(v, 4)}
            else:
                salida[nombre] = {"valor": round(v, 4), "motivo": None}
    return salida


def serie(puntos: dict[str, tuple[float, float]], inicio: date, fin: date, hilos: int = 4, cada_dias: int = 1) -> dict:
    """{'datos': [{'zona','fecha','valor'}], 'sin_dato': n, 'errores': [...]}.
    `cada_dias`=7 toma un día de cada siete (para climatologías de muchos años sin leer miles de archivos)."""
    ea = _login()
    res = ea.search_data(short_name=SHORT, version=VERSION, temporal=(inicio.isoformat(), fin.isoformat()))
    por_dia: dict[str, object] = {}
    for g in res:
        m = re.search(r"_(\d{8})_", g["umm"]["GranuleUR"])
        if m:
            por_dia[m.group(1)] = g
    if cada_dias > 1:
        por_dia = dict(list(sorted(por_dia.items()))[::cada_dias])
    datos, errores, sin_dato = [], [], 0

    def procesar(item):
        d8, gr = item
        fobj = ea.open([gr])[0]
        return d8, leer_puntos(fobj, puntos)

    with ThreadPoolExecutor(max_workers=hilos) as pool:
        futuros = {d8: pool.submit(procesar, (d8, g)) for d8, g in sorted(por_dia.items())}
        for d8, fut in futuros.items():
            try:
                _, valores = fut.result()
            except Exception as e:  # un día roto no tumba la serie
                errores.append(f"{d8}: {type(e).__name__}: {str(e)[:120]}")
                continue
            fecha = f"{d8[:4]}-{d8[4:6]}-{d8[6:]}"
            for zona, r in valores.items():
                if r["valor"] is None:
                    sin_dato += 1
                else:
                    datos.append({"zona": zona, "fecha": fecha, "valor": r["valor"]})
    return {"producto": f"{SHORT}.{VERSION}", "granulos": len(por_dia), "datos": datos, "sin_dato": sin_dato, "errores": errores}
