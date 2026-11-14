# APIs y datos de NASA por reto — verificación real

> Probado el 2026-10-18 desde Windows con `Invoke-WebRequest`. "✅ 200" = la API respondió con datos reales.
> Esto es **preparación** (permitida). El proyecto en sí no se puede empezar antes del 14 nov, 9:00 a.m.
> El 28 oct salen los *Challenge Statements* con la lista oficial de datos de cada reto: revisar si piden alguno adicional.

## Resumen

| Reto | ¿Hay datos? | Acceso | Registro necesario |
|---|---|---|---|
| 🌱 Field Shift | ✅ Sí | APIs JSON directas | Ninguno para lo básico; Earthdata (gratis) para SMAP/GPM crudos |
| 🌡️ Trend Detective | ✅ Sí | APIs JSON + CSV | Ninguno para lo básico |
| 🔥 MODIS + VIIRS | ✅ Sí | CSV anuales por país + API | Ninguno para el histórico; MAP_KEY gratis para la API en tiempo real |
| 🧠 Flame in Freefall | ✅ Sí (documentos) | API de NTRS + PDFs | Ninguno para NTRS; PSI pide registro gratis |
| 🎮 Mission Design Game | ✅ Sí | APIs JPL / NASA | Ninguno (DEMO_KEY o clave gratis de api.nasa.gov) |

---

## 🌱 1. Field Shift

| Dato | Fuente / endpoint | Prueba |
|---|---|---|
| Lluvia, temperatura, **humedad del suelo** (superficial y raíz), radiación — diario desde 1981 | **NASA POWER** `https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR,T2M,GWETROOT,GWETTOP&community=AG&longitude=-80.63&latitude=-5.19&start=20240101&end=20240105&format=JSON` | ✅ 200 · 850 ms |
| Climatología mensual (promedios históricos) | **NASA POWER** `/api/temporal/climatology/point` | ✅ 200 · 570 ms (Piura: lluvia máx. en marzo, 1.69 mm/día) |
| Vegetación **NDVI** cada 16 días, 250 m, desde 2000 | **ORNL DAAC MODIS** `https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset?latitude=-5.19&longitude=-80.63&band=250m_16_days_NDVI&...` | ✅ 200 · 3 s |
| Humedad del suelo satelital SMAP | **NASA Earthdata** (colección `SPL3SMP_E`, encontrada vía CMR) | ✅ metadatos 200 · descarga requiere Earthdata Login |
| Lluvia satelital GPM IMERG | **NASA Earthdata** (`GPM_3IMERGDF`) | ✅ metadatos 200 · descarga requiere Earthdata Login |
| Suelo: pH, carbono orgánico (no es NASA, complemento) | **ISRIC SoilGrids** `https://rest.isric.org/soilgrids/v2.0/properties/query?...` | ✅ 200 · ⚠️ lento (37 s) → cachear |

**Ejemplo real:** El Niño 1998 en Piura → enero 16.2 mm/día de lluvia vs ~0 en meses normales (POWER mensual).

## 🌡️ 2. Earth System Trend Detective

| Dato | Fuente / endpoint | Prueba |
|---|---|---|
| Series largas (1981–hoy) de temperatura, lluvia, humedad por coordenada | **NASA POWER** (daily / monthly / climatology) | ✅ 200 |
| Anomalías de temperatura global 1880–hoy | **NASA GISS GISTEMP v4** `https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv` | ✅ 200 · 821 ms |
| Vegetación NDVI 2000–hoy | **ORNL DAAC MODIS** | ✅ 200 |
| Humedad de suelo, lluvia, agua subterránea (GRACE) | **NASA Earthdata** vía CMR | ✅ metadatos · descarga con Earthdata Login |

**Técnica:** prueba de Mann-Kendall + pendiente de Sen para decir si una tendencia es "significativa".

## 🔥 3. Harmonization of MODIS and VIIRS Hot Spots

| Dato | Fuente / endpoint | Prueba |
|---|---|---|
| Focos MODIS por país y año (CSV) | **NASA FIRMS** `https://firms.modaps.eosdis.nasa.gov/data/country/modis/2023/modis_2023_Peru.csv` | ✅ 200 · 1.3 MB |
| Focos VIIRS S-NPP por país y año (CSV) | **NASA FIRMS** `https://firms.modaps.eosdis.nasa.gov/data/country/viirs-snpp/2023/viirs-snpp_2023_Peru.csv` | ✅ 200 · 6.3 MB · 79 577 focos |
| API en tiempo casi real por zona | **NASA FIRMS API** `https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/VIIRS_SNPP_NRT/{bbox}/{días}` | ⚠️ 400 sin clave → pedir **MAP_KEY gratis** en `https://firms.modaps.eosdis.nasa.gov/api/map_key/` |
| Productos crudos MOD14A1 / VNP14IMG | **NASA Earthdata** | ✅ metadatos 200 |

**Ejemplo real — focos VIIRS 2023 en la zona aproximada de Piura (2 633 en total):**

| Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Dic |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 274 | 51 | 25 | 3 | 9 | 138 | 233 | 202 | **584** | 233 | 488 | 393 |

→ Ya se ve un "calendario de quemas": pico en septiembre y noviembre (temporada seca), casi nada en marzo-mayo (lluvias). Caja usada: lat −6.4 a −4.0, lon −81.4 a −79.2 (incluye bordes de regiones vecinas).

## 🧠 4. Flame in Freefall

| Dato | Fuente / endpoint | Prueba |
|---|---|---|
| Papers y reportes de NASA sobre combustión en microgravedad | **NASA Technical Reports Server (NTRS) API** `https://ntrs.nasa.gov/api/citations/search?q=microgravity%20combustion%20flame` | ✅ 200 · 550 resultados (1 076 con "microgravity combustion"), la mayoría con PDF descargable |
| Datos experimentales de la ISS (FLEX, ACME, BASS…) | **NASA Physical Sciences Informatics (PSI)** `https://psi.nasa.gov/` | ✅ sitio 200 · descarga de datos requiere registro gratis |

Ejemplos reales devueltos por NTRS: *Advanced Combustion via Microgravity Experiments (ACME) on the ISS*, *Cool-Flame Combustion of Normal-Alkane Droplets in Microgravity*, *Fourth International Microgravity Combustion Workshop*.
**Técnica:** descargar PDFs → indexar (RAG) → LLM que resume, rankea e interpreta. El reto pide declarar el uso de IA.

## 🎮 5. Space Mission Design Game

| Dato | Fuente / endpoint | Prueba |
|---|---|---|
| Datos físicos y efemérides de planetas (masa, radio, gravedad, órbitas) | **JPL Horizons API** `https://ssd.jpl.nasa.gov/api/horizons.api?format=json&COMMAND='499'&OBJ_DATA='YES'&MAKE_EPHEM='NO'` | ✅ 200 · Marte: radio 3389.92 km |
| Asteroides y cometas (órbitas, tamaños) | **JPL Small-Body Database API** `https://ssd-api.jpl.nasa.gov/sbdb.api?sstr=Bennu` | ✅ 200 |
| Exoplanetas (para misiones "más allá") | **NASA Exoplanet Archive TAP** | ✅ 200 |
| Imágenes / contenido NASA (APOD, etc.) | **api.nasa.gov** con `DEMO_KEY` (o clave gratis) | ✅ 200 |

Datos como masa/costo de cohetes y presupuestos de misiones no salen de una API: se toman de fichas públicas de NASA y se cargan como tabla en el juego. El Challenge Statement (28 oct) probablemente sugerirá fuentes concretas.

## 🌑 10. Earth Analogs for Moon/Mars (propuesto por Edwin)

| Dato | Fuente / endpoint | Prueba |
|---|---|---|
| Relieve / imágenes de Marte | **NASA Mars Trek WMTS** `https://trek.nasa.gov/tiles/Mars/EQ/Mars_MGS_MOLA_ClrShade_merge_global_463m/1.0.0/WMTSCapabilities.xml` | ✅ 200 (la capa `..._MOLA_DEM_mosaic...` da 404) |
| Imágenes de la Luna | **NASA Moon Trek WMTS** `.../Moon/EQ/LRO_WAC_Mosaic_Global_303ppd_v02/...` | ✅ 200 |
| Productos de misiones a Marte (mineralogía, térmicos…) | **PDS Geosciences ODE REST** `https://oderest.rsl.wustl.edu/live2/?query=iipy&target=mars&output=JSON` | ✅ 200 |
| Relieve de la Tierra | **ASTER GDEM / SRTM** (Earthdata, colecciones `ASTGTM`, `SRTMGL1`) | ✅ metadatos 200 · descarga con Earthdata Login |
| Clima del sitio terrestre | **NASA POWER** climatología | ✅ 200 |

**Dato real — Desierto de Sechura (−5.8, −80.7):** lluvia 0.21 mm/día (muy árido ✅), pero **humedad relativa 70.8%** (neblina costera ❌, Marte es extremadamente seco). Es un argumento a favor de comparar varios sitios y no asumir que Sechura es el mejor análogo.

---

## Cuentas gratuitas a crear antes del evento (permitido)

| Cuenta | Para qué | Enlace |
|---|---|---|
| **Earthdata Login** | SMAP, GPM, GRACE, productos MODIS/VIIRS crudos | https://urs.earthdata.nasa.gov |
| **FIRMS MAP_KEY** | API de focos de calor en tiempo casi real | https://firms.modaps.eosdis.nasa.gov/api/map_key/ |
| **api.nasa.gov key** | Más cuota que DEMO_KEY | https://api.nasa.gov |
| **PSI** | Datos de experimentos de combustión en la ISS | https://psi.nasa.gov |
