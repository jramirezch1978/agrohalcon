"""CMR: el catálogo público de la NASA (sin clave). Sirve para:
  1) anotar la VERSIÓN EXACTA de cada dato (campo References: "que las versiones coincidan con las que descargamos")
  2) buscar qué archivos (gránulos) existen para un punto y fechas, antes de descargar nada.
Docs: https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html
"""

from .config import get_json

CMR = "https://cmr.earthdata.nasa.gov/search"

# Productos que usa AgroShift. (short_name, versión preferida)
PRODUCTOS = {
    "SMAP humedad del suelo 9 km": ("SPL3SMP_E", "006"),
    "SMAP L4 humedad de raíz": ("SPL4SMGP", "008"),
    "GPM IMERG diario (final)": ("GPM_3IMERGDF", "07"),
    "GPM IMERG diario (rápido, para el dato actual)": ("GPM_3IMERGDL", "07"),
    "MODIS NDVI 250 m": ("MOD13Q1", "061"),
    "MUR SST": ("MUR-JPL-L4-GLOB-v4.1", None),
    "SRTM elevación 30 m": ("SRTMGL1", "003"),
    "ECOSTRESS evapotranspiración": ("ECO_L3T_JET", "003"),
}


def coleccion(short_name: str, version: str | None = None) -> dict | None:
    """Metadatos de la colección: versión, rango de fechas, centro de datos, DOI."""
    params = {"short_name": short_name, "page_size": 20}
    if version:
        params["version"] = version
    datos = get_json(f"{CMR}/collections.umm_json", params)
    items = datos.get("items", [])
    if not items:
        return None
    umm = items[0]["umm"]
    rango = (umm.get("TemporalExtents") or [{}])[0].get("RangeDateTimes") or [{}]
    doi = (umm.get("DOI") or {}).get("DOI")
    return {
        "shortName": umm.get("ShortName"),
        "version": umm.get("Version"),
        "titulo": umm.get("EntryTitle"),
        "desde": rango[0].get("BeginningDateTime", "")[:10],
        "hasta": (rango[0].get("EndingDateTime") or "vigente")[:10],
        "doi": doi,
        "doiUrl": f"https://doi.org/{doi}" if doi else None,
        "idCmr": items[0]["meta"].get("concept-id"),
    }


def granulos(
    short_name: str,
    version: str,
    lat: float,
    lon: float,
    inicio: str,
    fin: str,
    maximo: int = 10,
) -> list[dict]:
    """Archivos que cubren el punto en el rango (fechas 'YYYY-MM-DD'). No descarga nada."""
    params = {
        "short_name": short_name,
        "version": version,
        "point": f"{lon},{lat}",
        "temporal": f"{inicio}T00:00:00Z,{fin}T23:59:59Z",
        "page_size": maximo,
        "sort_key": "start_date",
    }
    datos = get_json(f"{CMR}/granules.json", params)
    return [
        {
            "titulo": e.get("title"),
            "inicio": e.get("time_start"),
            "tamanoMb": e.get("granule_size"),
            "descarga": next(
                (
                    link["href"]
                    for link in e.get("links", [])
                    if link.get("rel", "").endswith("/data#") and link["href"].startswith("http")
                ),
                None,
            ),
        }
        for e in datos.get("feed", {}).get("entry", [])
    ]


def versiones_usadas() -> list[dict]:
    """Tabla de versiones exactas de todos los productos (para References y 'Uso de IA / Datos NASA')."""
    filas = []
    for etiqueta, (short, version) in PRODUCTOS.items():
        try:
            info = coleccion(short, version)
        except RuntimeError as e:  # el catálogo puede dar 5xx un rato: se anota y se sigue
            info = {"error": str(e)}
        buscado = f"{short} v{version}" if version else short
        filas.append({"uso": etiqueta, "buscado": buscado, **(info or {"error": "no encontrado"})})
    return filas
