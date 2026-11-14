# Exploración en vivo de las APIs de la NASA (2026-11-14, día 1 del hackathon)

> Completa a [06_apis_nasa](06_apis_nasa.md), que se probó el 18 de octubre, antes de que la NASA publicara los datasets del reto.
> Aquí se prueban los **datasets oficiales de Field Shift** (pestaña Resources del reto, ver [12_field_shift_fuente_completa](12_field_shift_fuente_completa.md) y [15_plan_datos](15_plan_datos.md)) con **valles reales del norte del Perú**.

## 1. Hallazgo clave: NASA POWER es demasiado grueso para los valles

POWER entrega la meteorología en celdas de **0,5° (~55 km)**, así que varios valles de Piura reciben **el mismo dato**:

| Departamento | Valle (coordenada aproximada) | Celda POWER | Lluvia anual (mm) | Mes más lluvioso | T media (°C) | T mín. (°C) | Elevación de la celda (m) |
|---|---|---|---|---|---|---|---|
| Piura | Alto Piura - Chulucanas | (-5.0, -80.0) | 277 | Mar | 22,7 | 11,8 | 1051 ⚠️ |
| Piura | Alto Piura - Morropón | (-5.0, -80.0) | 277 | Mar | 22,7 | 11,8 | 1051 ⚠️ |
| Piura | Medio Piura - Castilla | (-5.0, -80.5) | 139 | Mar | 25,5 | 14,4 | 140 |
| Piura | San Lorenzo - Tambogrande | (-5.0, -80.5) | 139 | Mar | 25,5 | 14,4 | 140 |
| Piura | Valle del Chira - Sullana | (-5.0, -80.5) | 139 | Mar | 25,5 | 14,4 | 140 |
| Piura | Bajo Piura - Catacaos / La Arena | (-5.5, -80.5) | 107 | Mar | 25,0 | 14,3 | 59 |
| Piura | Sechura - Bernal / Vice | (-5.5, -81.0) | 107 | Mar | 25,0 | 14,3 | 59 |
| Piura | Sierra - Huancabamba | (-5.0, -79.5) | 461 | Feb | 17,1 | 7,0 | 2038 |
| Tumbes | Valle de Tumbes | (-3.5, -80.5) | 383 | Mar | 24,8 | 19,1 | 61 |
| Lambayeque | Chancay-Lambayeque | (-6.5, -80.0) | 87 | Mar | 22,8 | 13,9 | 120 |
| Lambayeque | Olmos | (-6.0, -80.0) | 108 | Mar | 24,2 | 13,1 | 355 |
| La Libertad | Chavimochic - Virú | (-8.5, -79.0) | 91 | Mar | 20,2 | 11,8 | 631 |
| La Libertad | Jequetepeque | (-7.0, -79.5) | 204 | Mar | 21,6 | 12,9 | 862 |
| Cajamarca | Jaén | (-5.5, -79.0) | 458 | Feb | 22,1 | 10,5 | 1312 |
| Cajamarca | Valle de Cajamarca | (-7.0, -78.5) | 416 | Mar | 14,4 | 3,0 | 2750 |
| Amazonas | Bagua - Utcubamba | (-5.5, -78.5) | 458 | Feb | 22,1 | 10,5 | 1312 |
| San Martín | Alto Mayo - Moyobamba | (-6.0, -77.0) | 1040 | Mar | 22,2 | 13,7 | 984 |

⚠️ Chulucanas está a ~90 m de altitud, pero su celda promedia la sierra y figura con 1051 m. Lo mismo pasa con Jaén y Bagua, que caen en la misma celda.

**Decisión propuesta:** la app combina dos escalas.

| Escala | Dataset | Resolución | Uso en la app |
|---|---|---|---|
| Región / clima de fondo | **NASA POWER** | 0,5° (~55 km) | Climatología, temperatura, radiación, histórico desde 1981 |
| Valle | **GPM IMERG** (lluvia) | 0,1° (~11 km) | Lluvia por valle, extremos de El Niño |
| Valle | **SMAP L3 Enhanced** (humedad del suelo) | 9 km | Estrés por sequía |
| Parcela | **MODIS MOD13Q1** (NDVI) | 250 m | Vigor del cultivo cada 16 días |
| Parcela | **HLS / Landsat** (NDVI) | 30 m | Detalle de chacra (opcional) |
| Parcela | **ECOSTRESS** (evapotranspiración) | 70 m | Demanda de agua (opcional) |
| Relieve | **SRTM** | 30 m | Pendiente y escorrentía |
| Mar | **MUR SST** | 1 km | Señal de El Niño costero |

## 2. Resultados de las pruebas (Piura, -5.19, -80.63)

| API | Resultado | Dato real |
|---|---|---|
| **POWER climatología** (comunidad AG) | ✅ 200 · 0,8 s | Lluvia máxima en marzo (1,69 mm/día). Temperatura de 23,4 °C (agosto) a 28 °C (marzo) |
| **POWER mensual 2016-2017** ("máquina del tiempo") | ✅ 200 · 0,6 s | **Marzo 2017: 12,88 mm/día** contra 1,4 en marzo de 2016. Humedad de raíz de 0,42 a **0,61** |
| **POWER diario** | ✅ 200 · 0,3 s | Latencia de **~2-3 días** (último dato: 11 nov) |
| **ORNL MODIS NDVI** (MOD13Q1) | ✅ 200, pero **lento (40-60 s)** | Última compuesta 2026-10-16: NDVI 0,064 (suelo casi desnudo en el punto). ➜ **Cachear** |
| **ORNL MODIS MOD16A2** (ET) | ❌ 502 (servidor caído en ese momento) | Reintentar o usar AppEEARS |
| **MUR SST** (`upwell.pfeg.noaa.gov` ERDDAP) | ✅ 200 · 1-2 s, sin login | Frente a Paita (-5.1, -81.3): **27,2 °C** el 13 nov 2026 |
| **MUR SST anomalía** (`jplMURSST41anom1day`) | ✅ 200 | **+9,0 °C** el 12 nov 2026 ⚠️ (por validar: es un punto costero). En el Niño Costero de marzo 2017: +6,5 °C |
| **CMR** (catálogo Earthdata) | ✅ 200 | Ver la tabla de colecciones de abajo |
| **AppEEARS** (catálogo) | ✅ 200 | 193 productos, entre ellos SMAP (`SPL3SMP_E.006`, `SPL4SMGP.008`) y ECOSTRESS |
| **FIRMS VIIRS Perú 2025** (CSV anual) | ✅ 200 | 53 579 focos de calor en el Perú en 2025 |
| **GES DISC** (IMERG / GLDAS por OPeNDAP o Data Rods) | ⏳ No probado | **Falta el token de Earthdata** en `deploy/vps/.env` |

⚠️ La anomalía de +9 °C es muy alta: hay que contrastarla con el índice **Niño 1+2 / ICEN del ENFEN** antes de mostrarla en la demo.

### Colecciones oficiales del reto en CMR

| Colección | Versión | Desde | Hasta | Centro |
|---|---|---|---|---|
| SPL3SMP_E (SMAP 9 km) | 006 | 2015-03-31 | vigente | NSIDC |
| SPL4SMGP (SMAP L4 humedad de raíz) | 008 | 2015-03-31 | vigente | NSIDC |
| GPM_3IMERGDL (IMERG diario, rápido) | 07 | 1998-01-01 | vigente | GES DISC |
| GPM_3IMERGM (IMERG mensual) | 07 | 1998-01-01 | 2025-09-30 | GES DISC |
| GLDAS_NOAH025_M | 2.1 | 2000-01-01 | vigente | GES DISC |
| SRTMGL1 | 003 | 2000 (misión única) | — | LP DAAC |
| ECO_L3T_JET (ECOSTRESS ET) | 003 | 2018-07-09 | vigente | LP DAAC |
| HLSL30 (Landsat armonizado) | 2.0 | 2013-04-11 | vigente | LP DAAC |
| VNP13A1 (VIIRS NDVI) | 002 | 2012-01-17 | vigente | LP DAAC |

## 2b. Pruebas con el token de Earthdata (2026-11-14, tarde)

Aplicaciones autorizadas: NASA GESDISC DATA ARCHIVE, LP DAAC Data Pool, NSIDC_DATAPOOL_OPS. **Falta LP DAAC Cumulus PROD.**

| Dataset | Resultado | Dato real |
|---|---|---|
| **GPM IMERG mensual** (OPeNDAP GES DISC, 0,1°) | ✅ 200 · ~20 s para 16 consultas | **Sí distingue valles** (tabla de abajo) |
| **SMAP SPL3SMP_E** (NSIDC) | ✅ descarga autorizada | Archivo global de ~660 MB por día ➜ no se descarga entero: recortar con AppEEARS u OPeNDAP |
| **HLS Landsat 30 m** (LP DAAC) | ✅ 200 | Tesela `T17MNQ` del 22 oct 2026 sobre Piura |
| **SRTM 30 m** (LP DAAC) | ✅ 200 | Tesela `S06W081` (8,2 MB): relieve y pendiente de los valles |
| **ECOSTRESS ET** (`ECO_L3T_JET`) | 🟡 sin pasadas sobre Piura en oct-nov 2026 | Su órbita es irregular: ampliar el periodo o dejarlo opcional |
| **GLDAS** (Data Rods) | ❌ devuelve una página HTML, no datos | Usar GLDAS por OPeNDAP |

**Lluvia de marzo por valle con IMERG (mm/mes), año normal frente a Niño Costero:**

| Valle | Marzo 2016 | Marzo 2017 | Veces más |
|---|---|---|---|
| Chulucanas | 152 | 577 | ×3,8 |
| Morropón | 132 | 506 | ×3,8 |
| Castilla (Medio Piura) | 77 | 580 | ×7,5 |
| Catacaos (Bajo Piura) | 68 | 540 | ×7,9 |
| Sechura | 61 | 552 | ×9,0 |
| Tambogrande (San Lorenzo) | 138 | 590 | ×4,3 |
| Sullana (Chira) | 99 | 542 | ×5,5 |
| Huancabamba (sierra) | 160 | 320 | ×2,0 |

➜ IMERG separa valles que en POWER salían idénticos, y muestra que el Niño Costero golpeó más al **Bajo Piura y Sechura** (hasta 9 veces la lluvia normal). Es el dato estrella para la "máquina del tiempo".

## 3. Accesos que faltan (los hace Jhonny)

| Acceso | Para qué | Cómo |
|---|---|---|
| **Token de Earthdata** | IMERG, GLDAS, SMAP, ECOSTRESS, HLS | urs.earthdata.nasa.gov → *Generate Token*. Pegarlo en `deploy/vps/.env` (`EARTHDATA_TOKEN=`). **No compartirlo ni subirlo** |
| **Autorizar aplicaciones** en Earthdata | Descargas de cada centro | *Applications → Authorized Apps*: **NASA GESDISC DATA ARCHIVE**, **LP DAAC**, **NSIDC** |
| **AppEEARS** | SMAP, ECOSTRESS y HLS por punto o polígono, sin descargar archivos enormes | appeears.earthdatacloud.nasa.gov, entrar con la misma cuenta de Earthdata |
| FIRMS MAP_KEY (opcional) | Focos de calor en tiempo casi real | firms.modaps.eosdis.nasa.gov/api/map_key (solo correo) |

## 4. Mapa con valles y zonas agrícolas

- Pasar de "7 regiones" a **valles**: Alto, Medio y Bajo Piura, San Lorenzo, Chira, Sechura (sí existe agricultura en Bernal, Vice y Cristo Nos Valga), Huancabamba, Tumbes, Chancay-Lambayeque, Olmos, Jequetepeque, Chavimochic, Jaén, Cajamarca, Bagua-Utcubamba y Alto Mayo.
- Capas: imagen satelital de fondo, más **polígonos de superficie agrícola** del MIDAGRI (GeoMIDAGRI) o **ESA WorldCover 10 m** (clase *cropland*), más el NDVI de MODIS por encima.
- Las coordenadas de la tabla son **aproximadas** (centro del valle). Alejandro debe validarlas en el catálogo (`feature/catalogo-cultivos`).
