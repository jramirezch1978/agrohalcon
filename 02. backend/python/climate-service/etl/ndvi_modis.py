"""MODIS NDVI (MOD13Q1 v061, 250 m, cada 16 días) por punto, vía el servicio REST de ORNL DAAC (sin clave).

Se usa para VALIDAR: la caída del NDVI en 2017 muestra el daño real en los cultivos de Piura.

⚠️ NO VERIFICADO DE PUNTA A PUNTA: el 14-nov-2026 el servicio de ORNL respondió 502/503 (proxy/servicio no disponible),
   y Jhonny ya había visto que tarda 40-60 s y que MOD16A2 caía con 502. La ruta alternativa es AppEEARS
   (etl/appeears.py, capa MOD13Q1.061 `_250m_16_days_NDVI`). Se corrige aquí un detalle conocido: la API solo acepta fechas
   MODIS válidas del producto (A2017001, A2017017...), por eso se consulta primero /dates.
Docs: https://modis.ornl.gov/data/modis_webservice.html
"""

from datetime import date

from .config import get_json

BASE = "https://modis.ornl.gov/rst/api/v1/MOD13Q1"
BANDA = "250m_16_days_NDVI"
FACTOR = 0.0001  # el NDVI viene como entero escalado
LOTE = 10  # el servicio limita cuántas fechas acepta por consulta


def fechas_disponibles(lat: float, lon: float) -> list[dict]:
    """[{'modis_date': 'A2017001', 'calendar_date': '2017-01-01'}, ...] de ese punto."""
    datos = get_json(f"{BASE}/dates", {"latitude": lat, "longitude": lon}, timeout=90, reintentos=1)
    return datos.get("dates", [])


def serie(lat: float, lon: float, inicio: date, fin: date) -> list[dict]:
    """[{'fecha': 'YYYY-MM-DD', 'ndvi': 0.43, 'producto': 'MOD13Q1.061'}, ...] (celda de 250 m del punto)."""
    fechas = [
        d for d in fechas_disponibles(lat, lon) if inicio.isoformat() <= d["calendar_date"] <= fin.isoformat()
    ]
    salida: list[dict] = []
    for i in range(0, len(fechas), LOTE):
        lote = fechas[i : i + LOTE]
        params = {
            "latitude": lat,
            "longitude": lon,
            "band": BANDA,
            "startDate": lote[0]["modis_date"],
            "endDate": lote[-1]["modis_date"],
            "kmAboveBelow": 0,
            "kmLeftRight": 0,
        }
        datos = get_json(f"{BASE}/subset", params, timeout=120, reintentos=1)
        for s in datos.get("subset", []):
            valores = [v for v in s.get("data", []) if v != -3000]  # -3000 = sin dato
            if valores:
                salida.append(
                    {"fecha": s["calendar_date"], "ndvi": round(valores[0] * FACTOR, 4), "producto": "MOD13Q1.061"}
                )
    return salida


def caida_pct(valores: list[dict], antes: tuple[str, str], durante: tuple[str, str]) -> float | None:
    """Cambio % del NDVI promedio 'durante' frente a 'antes' (negativo = vegetación que cae)."""

    def prom(rango: tuple[str, str]) -> float | None:
        v = [x["ndvi"] for x in valores if rango[0] <= x["fecha"] <= rango[1]]
        return sum(v) / len(v) if v else None

    a, d = prom(antes), prom(durante)
    if a is None or d is None or a == 0:
        return None
    return round((d - a) / a * 100, 1)
