"""NASA POWER (API pública, sin clave): clima diario, mensual y climatología de cualquier punto.

Docs: https://power.larc.nasa.gov/docs/services/api/   ·   Visor: https://power.larc.nasa.gov/data-access-viewer/
Resolución: celdas de 0,5° (~55 km). Latencia del dato diario: ~2-3 días.
"""

from datetime import date

from .config import get_json

BASE = "https://power.larc.nasa.gov/api/temporal"
COMUNIDAD = "AG"  # agroclimatología
FILL = -999.0  # valor que POWER usa para "sin dato"

# T2M_MAX/T2M_MIN °C · PRECTOTCORR mm/día · ALLSKY_SFC_SW_DWN kWh/m²/día · GWETTOP/GWETROOT fracción 0-1
PARAMETROS = ["T2M_MAX", "T2M_MIN", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN", "GWETTOP", "GWETROOT"]
MESES = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def _consultar(tipo: str, lat: float, lon: float, parametros: list[str], extra: dict) -> dict:
    params = {
        "parameters": ",".join(parametros),
        "community": COMUNIDAD,
        "latitude": lat,
        "longitude": lon,
        "format": "JSON",
        **extra,
    }
    datos = get_json(f"{BASE}/{tipo}/point", params, timeout=90)
    serie = datos["properties"]["parameter"]
    # Quitar los -999 (sin dato) para que nunca entren a un promedio
    return {p: {k: v for k, v in s.items() if v != FILL} for p, s in serie.items()}


def diario(lat: float, lon: float, inicio: date, fin: date, parametros: list[str] | None = None) -> dict:
    """{parametro: {'YYYYMMDD': valor}}"""
    return _consultar(
        "daily", lat, lon, parametros or PARAMETROS,
        {"start": inicio.strftime("%Y%m%d"), "end": fin.strftime("%Y%m%d")},
    )  # fmt: skip


def mensual(lat: float, lon: float, anio_ini: int, anio_fin: int, parametros: list[str] | None = None) -> dict:
    """{parametro: {'YYYYMM': valor}}  (la clave 'YYYY13' es el promedio anual; se descarta)"""
    serie = _consultar(
        "monthly", lat, lon, parametros or PARAMETROS, {"start": anio_ini, "end": anio_fin}
    )
    return {p: {k: v for k, v in s.items() if not k.endswith("13")} for p, s in serie.items()}


def climatologia(lat: float, lon: float, parametros: list[str] | None = None) -> dict:
    """{parametro: {'JAN': valor, ..., 'DEC': valor, 'ANN': valor}}: el 'normal histórico' de cada mes."""
    return _consultar("climatology", lat, lon, parametros or PARAMETROS, {})


def promedio_ventana(serie_diaria: dict[str, float], hasta: date, dias: int) -> tuple[float, date] | None:
    """Promedio de los últimos `dias` con dato hasta `hasta`. Devuelve (promedio, último día con dato)."""
    claves = sorted(k for k in serie_diaria if k <= hasta.strftime("%Y%m%d"))[-dias:]
    if not claves:
        return None
    valores = [serie_diaria[k] for k in claves]
    ultimo = date(int(claves[-1][:4]), int(claves[-1][4:6]), int(claves[-1][6:]))
    return sum(valores) / len(valores), ultimo
