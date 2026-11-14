"""NOAA CPC: temperatura del mar y anomalías mensuales de las regiones Niño (OISST), desde 1982.

Niño 1+2 (0°-10°S, 90°W-80°W) es la región de la COSTA DE PERÚ: la señal de El Niño costero.
Es de NOAA (no de NASA); se usa como señal oficial mientras MUR SST se valida. Sin llave.
https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices
"""

from .config import get_texto

URL = "https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices"
COLUMNAS = ["nino12", "nino12_anom", "nino3", "nino3_anom", "nino4", "nino4_anom", "nino34", "nino34_anom"]


def nino_mensual() -> list[dict]:
    """[{'fecha': '2017-03-01', 'nino12': 27.9, 'nino12_anom': 3.0, ...}, ...] (°C)"""
    filas = []
    for linea in get_texto(URL).splitlines()[1:]:
        p = linea.split()
        if len(p) < 10:
            continue
        try:
            valores = [float(x) for x in p[2:10]]
            anio, mes = int(p[0]), int(p[1])
        except ValueError:
            continue
        filas.append({"fecha": f"{anio}-{mes:02d}-01", **dict(zip(COLUMNAS, valores, strict=True))})
    return filas


def episodios(filas: list[dict], clave: str = "nino12_anom", umbral: float = 1.0, minimo_meses: int = 3) -> list[dict]:
    """Episodios calientes: meses seguidos con anomalía >= umbral. Se calculan, no se escriben a mano.
    Devuelve [{'inicio','fin','meses','pico_anom','pico_fecha','media_anom'}]."""
    salida, actual = [], []
    for f in filas + [{"fecha": "9999-12-01", clave: -99.0}]:  # centinela para cerrar el último episodio
        if f[clave] >= umbral:
            actual.append(f)
            continue
        if len(actual) >= minimo_meses:
            pico = max(actual, key=lambda x: x[clave])
            salida.append(
                {
                    "inicio": actual[0]["fecha"], "fin": actual[-1]["fecha"], "meses": len(actual),
                    "pico_anom": pico[clave], "pico_fecha": pico["fecha"],
                    "media_anom": round(sum(x[clave] for x in actual) / len(actual), 2),
                }
            )  # fmt: skip
        actual = []
    return salida
