"""AppEEARS (NASA): valores de un PUNTO sin bajar archivos enteros. Es la vía recomendada para SMAP y MODIS.

⚠️ NO PROBADO TODAVÍA: necesita usuario y clave de Earthdata en .env (EARTHDATA_USERNAME/PASSWORD).
   Ajusta los nombres de producto/capa con el catálogo oficial: GET {BASE}/product y GET {BASE}/product/<id>.
Docs de la API: https://appeears.earthdatacloud.nasa.gov/api/
Flujo: login -> enviar tarea de punto -> esperar -> bajar el CSV de resultados.
"""

import base64
import os
import time

import httpx

from .config import RAW, USER_AGENT

BASE = "https://appeears.earthdatacloud.nasa.gov/api"

# Capas candidatas (verificar con GET /product/<id>):
CAPAS = {
    "smap_am": {"product": "SPL3SMP_E.006", "layer": "Soil_Moisture_Retrieval_Data_AM_soil_moisture"},
    "modis_ndvi": {"product": "MOD13Q1.061", "layer": "_250m_16_days_NDVI"},
}


def _token() -> str:
    usuario, clave = os.getenv("EARTHDATA_USERNAME"), os.getenv("EARTHDATA_PASSWORD")
    if not usuario or not clave:
        raise RuntimeError("Faltan EARTHDATA_USERNAME / EARTHDATA_PASSWORD en .env")
    basic = base64.b64encode(f"{usuario}:{clave}".encode()).decode()
    r = httpx.post(f"{BASE}/login", headers={"Authorization": f"Basic {basic}", "User-Agent": USER_AGENT}, timeout=60)
    r.raise_for_status()
    return r.json()["token"]


def enviar_tarea_punto(nombre: str, puntos: list[dict], inicio: str, fin: str, capas: list[str]) -> str:
    """puntos: [{'id': 'bajo_piura', 'latitude': -5.35, 'longitude': -80.7, 'category': 'zona'}]
    inicio/fin: 'MM-DD-YYYY'. Devuelve el task_id."""
    cuerpo = {
        "task_type": "point",
        "task_name": nombre,
        "params": {
            "dates": [{"startDate": inicio, "endDate": fin}],
            "layers": [CAPAS[c] for c in capas],
            "coordinates": puntos,
        },
    }
    r = httpx.post(f"{BASE}/task", json=cuerpo, headers={"Authorization": f"Bearer {_token()}"}, timeout=60)
    r.raise_for_status()
    return r.json()["task_id"]


def esperar_y_descargar(task_id: str, cada_s: int = 20, max_min: int = 30):
    """Espera a que termine la tarea y baja el CSV de resultados a data/raw/appeears/."""
    h = {"Authorization": f"Bearer {_token()}"}
    limite = time.time() + max_min * 60
    while time.time() < limite:
        estado = httpx.get(f"{BASE}/task/{task_id}", headers=h, timeout=60).json().get("status")
        if estado == "done":
            break
        if estado == "error":
            raise RuntimeError(f"AppEEARS marcó error en la tarea {task_id}")
        time.sleep(cada_s)
    archivos = httpx.get(f"{BASE}/bundle/{task_id}", headers=h, timeout=60).json()["files"]
    carpeta = RAW / "appeears"
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas = []
    for a in archivos:
        if a["file_name"].endswith(".csv"):
            destino = carpeta / a["file_name"].split("/")[-1]
            destino.write_bytes(httpx.get(f"{BASE}/bundle/{task_id}/{a['file_id']}", headers=h, timeout=300, follow_redirects=True).content)
            rutas.append(destino)
    return rutas
