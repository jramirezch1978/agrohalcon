"""Catálogos fijos: regiones, fuentes de datos (con versión y DOI verificados en CMR el 14-nov-2026) y variables.

`estado` de cada fuente: en_uso (el código la usa hoy) · probado (se pudo leer, aún no se usa) ·
bloqueado (falta una acción del usuario) · planeado. build.py lo ajusta según lo que realmente haya en caché.
"""

REGIONES = [
    (1, "piura", "Piura"), (2, "tumbes", "Tumbes"), (3, "lambayeque", "Lambayeque"), (4, "la_libertad", "La Libertad"),
    (5, "cajamarca", "Cajamarca"), (6, "amazonas", "Amazonas"), (7, "san_martin", "San Martín"), (8, "mar_piura", "Mar frente a Piura"),
]  # fmt: skip

# (id, codigo, nombre, institucion, producto, version, doi, resolucion, cobertura, url, acceso, estado, nota)
FUENTES = [
    (1, "POWER", "NASA POWER (AG)", "NASA LaRC", "POWER monthly/daily", "v2.10", None, "0,5° (~55 km)", "1981-hoy (rezago 2-3 días)",
     "https://power.larc.nasa.gov/docs/services/api/", "API pública, sin llave", "en_uso",
     "Normal histórico 1991-2020 calculado aquí. T2M_MAX parece sesgado al calor en Piura: comparar anomalías."),
    (2, "SMAP", "SMAP L3 humedad del suelo (mejorada)", "NASA / NSIDC DAAC", "SPL3SMP_E", "006", "10.5067/M20OXIZHY3RJ", "9 km", "2015-hoy, cada 2-3 días",
     "https://nsidc.org/data/spl3smp_e", "Earthdata (token)", "probado", "Lectura parcial del HDF5 por HTTP (~630 MB/día si se bajara entero)."),
    (3, "IMERG_DL", "GPM IMERG diario, corrida rápida", "NASA GES DISC", "GPM_3IMERGDL", "07", "10.5067/GPM/IMERGDL/DAY/07", "0,1° (~11 km)", "1998-hoy",
     "https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGDL_07/summary", "Earthdata (token) + aceptar acuerdo de GES DISC", "bloqueado",
     "403 'EULA Acceptance Failure' hasta que el usuario acepte el acuerdo de la app NASA GESDISC DATA ARCHIVE."),
    (4, "IMERG_DF", "GPM IMERG diario, corrida final", "NASA GES DISC", "GPM_3IMERGDF", "07", "10.5067/GPM/IMERGDF/DAY/07", "0,1° (~11 km)", "1998-2025-09-30 en CMR",
     "https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGDF_07/summary", "Earthdata (token) + aceptar acuerdo de GES DISC", "bloqueado",
     "Termina 2025-09-30 en el catálogo: para dato reciente usar IMERG_DL."),
    (5, "MOD13Q1", "MODIS NDVI 250 m (16 días)", "NASA LP DAAC", "MOD13Q1", "061", "10.5067/MODIS/MOD13Q1.061", "250 m", "2000-hoy",
     "https://lpdaac.usgs.gov/products/mod13q1v061/", "Earthdata (token)", "probado", "Autorizado, pero es HDF4 (hay que bajar el archivo) y el servicio ORNL estuvo caído. Se usa VIIRS."),
    (6, "VNP13A1", "VIIRS NDVI 500 m (16 días)", "NASA LP DAAC", "VNP13A1", "002", None, "500 m", "2012-hoy",
     "https://lpdaac.usgs.gov/products/vnp13a1v002/", "Earthdata (token)", "probado", "Continuidad de MODIS; HDF5 legible por píxel. DECLARAR en References si se usa."),
    (7, "MUR_SST", "MUR SST v4.1", "NASA JPL / PO.DAAC", "MUR-JPL-L4-GLOB-v4.1", "4.1", "10.5067/GHGMR-4FJ04", "0,01° (~1 km)", "2002-hoy",
     "https://podaac.jpl.nasa.gov/dataset/MUR-JPL-L4-GLOB-v4.1", "Earthdata (token) · OPeNDAP", "probado", "Valor por punto en ~2,5 s. Anomalía propia vs 2003-2022."),
    (8, "SRTM", "SRTM 1 arcsec", "NASA / USGS LP DAAC", "SRTMGL1", "003", "10.5067/MEASURES/SRTM/SRTMGL1.003", "30 m", "2000 (misión única)",
     "https://lpdaac.usgs.gov/products/srtmgl1v003/", "Earthdata (token)", "probado", "Elevación y pendiente por valle."),
    (9, "CPC_NINO", "Índices Niño (OISST) mensuales", "NOAA CPC", "sstoi.indices", None, None, "regiones Niño", "1982-hoy",
     "https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices", "pública, sin llave", "en_uso", "Niño 1+2 = costa de Perú. NO es NASA: declarar."),
    (10, "ONI", "Oceanic Niño Index", "NOAA CPC", "oni.ascii.txt", None, None, "Pacífico central", "1950-hoy",
     "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt", "pública, sin llave", "en_uso", "No detectó el Niño costero de 2017 (marcó neutral)."),
    (11, "SOILGRIDS", "ISRIC SoilGrids v2", "ISRIC", "soilgrids 2.0", "2.0", None, "250 m", "mapa global",
     "https://rest.isric.org/soilgrids/v2.0/docs", "pública, sin llave", "en_uso", "No es NASA. Vacío en puntos urbanos o sin suelo mapeado."),
    (12, "ECOSTRESS", "ECOSTRESS evapotranspiración", "NASA LP DAAC", "ECO_L3T_JET", "003", "10.5067/ECOSTRESS/ECO_L3T_JET.003", "70 m", "2018-hoy",
     "https://lpdaac.usgs.gov/products/eco_l3t_jetv003/", "Earthdata (token)", "planeado", "Demanda de agua por parcela (opcional del reto)."),
    (13, "GLDAS", "GLDAS Noah 0,25° mensual", "NASA GES DISC", "GLDAS_NOAH025_M", "2.1", None, "0,25°", "2000-hoy",
     "https://disc.gsfc.nasa.gov/datasets/GLDAS_NOAH025_M_2.1/summary", "Earthdata + acuerdo GES DISC", "bloqueado", "Respaldo de humedad del suelo."),
    (14, "SMAP_L4", "SMAP L4 humedad de raíz", "NASA / NSIDC DAAC", "SPL4SMGP", "008", "10.5067/T5RUATAQREF8", "9 km", "2015-hoy",
     "https://nsidc.org/data/spl4smgp", "Earthdata (token)", "planeado", "Humedad de la zona de raíz (modelada con SMAP)."),
    (15, "FAO_ECOCROP", "FAO ECOCROP", "FAO", "EcoCrop", None, None, "por cultivo", "n/a",
     "https://gaez.fao.org/pages/ecocrop", "pública", "planeado", "Fuente del catálogo de cultivos (Alejandro)."),
    (16, "MIDAGRI", "Calendarios de siembra MIDAGRI", "MIDAGRI Perú", "calendarios agrícolas", None, None, "por región", "n/a",
     "https://www.gob.pe/midagri", "pública", "planeado", "Meses de siembra y cosecha (Alejandro)."),
]  # fmt: skip

# (id, codigo, nombre, unidad, fuente_id, descripcion)
VARIABLES = [
    (1, "T2M", "Temperatura media a 2 m", "°C", 1, "Promedio diario de la temperatura del aire a 2 metros"),
    (2, "T2M_MAX", "Temperatura máxima a 2 m", "°C", 1, "Máxima diaria; en la celda de Piura da 37-39 °C en marzo (sesgo cálido probable)"),
    (3, "T2M_MIN", "Temperatura mínima a 2 m", "°C", 1, "Mínima diaria"),
    (4, "PRECTOTCORR", "Precipitación corregida", "mm/día", 1, "Lluvia diaria promedio (reanálisis corregido, no es IMERG)"),
    (5, "GWETTOP", "Humedad superficial del suelo", "fracción 0-1", 1, "Humedad relativa de la capa superior; no equivale a m3/m3 de SMAP"),
    (6, "GWETROOT", "Humedad de la zona de raíz", "fracción 0-1", 1, "Humedad relativa de la zona de raíz"),
    (7, "ALLSKY_SFC_SW_DWN", "Radiación solar", "MJ/m²/día", 1, "Irradiancia de onda corta, cielo real"),
    (8, "RH2M", "Humedad relativa a 2 m", "%", 1, "Humedad relativa del aire"),
    (9, "WS2M", "Viento a 2 m", "m/s", 1, "Velocidad del viento a 2 metros"),
    (10, "EVPTRNS", "Evapotranspiración (flujo de energía)", "MJ/m²/día", 1, "Demanda de agua del cultivo (aprox.)"),
    (11, "SMAP_SM", "Humedad del suelo SMAP (mañana)", "m3/m3", 2, "soil_moisture AM, calidad recomendada"),
    (12, "IMERG_PRECIP", "Precipitación IMERG", "mm/día", 3, "Lluvia diaria de satélite"),
    (13, "VNP13A1_NDVI", "NDVI VIIRS (16 días)", "índice", 6, "NDVI de la compuesta de 16 días, píxel de 500 m"),
    (14, "MUR_SST", "Temperatura del mar MUR", "°C", 7, "analysed_sst convertida de kelvin"),
]  # fmt: skip

CODIGO_VARIABLE = {v[1]: v[0] for v in VARIABLES}
CODIGO_FUENTE = {f[1]: f[0] for f in FUENTES}
