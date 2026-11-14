"""Comprueba que cada enlace de los documentos de entrega (References, Uso de IA / datos NASA) abra.

    python -m etl.verificar_enlaces

Los PDF del equipo piden: "Verificar antes de enviar: que cada enlace abra". Escribe data/backup/enlaces_verificados.json.
Un 403/429 de un sitio comercial no siempre es un enlace roto (bloquea robots): se marca "revisar a mano".
"""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import httpx

from .config import BACKUP

ENLACES = {
    "NASA POWER": "https://power.larc.nasa.gov/",
    "NASA POWER · API": "https://power.larc.nasa.gov/docs/services/api/",
    "NASA POWER · visor": "https://power.larc.nasa.gov/data-access-viewer/",
    "SMAP · misión": "https://smap.jpl.nasa.gov/",
    "SMAP · SPL3SMP_E": "https://nsidc.org/data/spl3smp_e",
    "GPM IMERG · misión": "https://gpm.nasa.gov/data/imerg",
    "GPM IMERG · GPM_3IMERGDF": "https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGDF_07/summary",
    "GPM IMERG · GPM_3IMERGDL (dato reciente)": "https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGDL_07/summary",
    "MODIS · misión": "https://modis.gsfc.nasa.gov/",
    "MODIS · MOD13Q1": "https://lpdaac.usgs.gov/products/mod13q1v061/",
    "MUR SST": "https://podaac.jpl.nasa.gov/dataset/MUR-JPL-L4-GLOB-v4.1",
    "Earthdata Login": "https://urs.earthdata.nasa.gov/",
    "AppEEARS": "https://appeears.earthdatacloud.nasa.gov/",
    "CMR (catálogo)": "https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html",
    "Vue.js": "https://vuejs.org/",
    "Leaflet": "https://leafletjs.com/",
    "Chart.js": "https://www.chartjs.org/",
    "Capacitor": "https://capacitorjs.com/",
    "Spring Boot": "https://spring.io/projects/spring-boot",
    "Python": "https://www.python.org/",
    "PostgreSQL": "https://www.postgresql.org/",
    "Microsoft Azure": "https://azure.microsoft.com/",
    "GitHub": "https://github.com/",
    "Canva": "https://www.canva.com/",
    "Groq API": "https://console.groq.com/docs",
    "Llama": "https://www.llama.com/",
    "INDECI · Compendio 2017": "https://cdn.www.gob.pe/uploads/document/file/1048401/20180227171454120200726-15599-1ptpifw.pdf",
    "SENASA · Niño Costero (como sale en el PDF)": "https://www.senasa.gob.pe/senasacontigo/nino-costero-cuantashectareas-se-han-perdido-por-efecto-del-evento-climatico/",
    "SENASA · Niño Costero (con guion)": "https://www.senasa.gob.pe/senasacontigo/nino-costero-cuantas-hectareas-se-han-perdido-por-efecto-del-evento-climatico/",
    "FAO ECOCROP": "https://gaez.fao.org/pages/ecocrop",
    "FAO GAEZ": "https://gaez.fao.org/",
    "NOAA ONI": "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php",
}

CABECERAS = {"User-Agent": "Mozilla/5.0 (compatible; AgroShift link check)", "Accept": "text/html,*/*"}


def revisar(item: tuple[str, str]) -> dict:
    nombre, url = item
    try:
        r = httpx.get(url, headers=CABECERAS, timeout=25, follow_redirects=True)
        codigo, final = r.status_code, str(r.url)
    except httpx.HTTPError as e:
        return {"nombre": nombre, "url": url, "estado": "ERROR", "detalle": type(e).__name__}
    if codigo < 400:
        estado = "OK"
    elif codigo in (401, 403, 429, 999):
        estado = "REVISAR A MANO"
    else:
        estado = "ROTO"
    return {"nombre": nombre, "url": url, "estado": estado, "http": codigo, "urlFinal": final if final != url else None}


def main() -> None:
    with ThreadPoolExecutor(max_workers=8) as pool:
        filas = list(pool.map(revisar, ENLACES.items()))
    BACKUP.mkdir(parents=True, exist_ok=True)
    (BACKUP / "enlaces_verificados.json").write_text(
        json.dumps({"verificado": date.today().isoformat(), "enlaces": filas}, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    for f in filas:
        extra = f" -> {f['urlFinal']}" if f.get("urlFinal") else (f" ({f['detalle']})" if f.get("detalle") else "")
        print(f"{f['estado']:<15} {f.get('http', '---'):<4} {f['nombre']}{extra}")
    malos = [f for f in filas if f["estado"] in ("ROTO", "ERROR")]
    print(f"\n{len(filas) - len(malos)} de {len(filas)} abren. A corregir: {[f['nombre'] for f in malos] or 'ninguno'}")


if __name__ == "__main__":
    main()
