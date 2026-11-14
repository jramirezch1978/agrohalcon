# Enlaces, APIs y llaves (David)

✅ = probado desde esta PC el 14-nov-2026 · ⚠️ = según el doc de Jhonny, no reproducido aquí · ❌ = no probado (falta cuenta/token).
Verificador automático de los enlaces de la entrega: `python -m etl.verificar_enlaces` → `data/backup/enlaces_verificados.json`.

## 1. Reto y documentos del evento
| Qué | Enlace |
|---|---|
| Reto *Field Shift: Adapting Farms with NASA Data* | https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/ (carga con JavaScript: en el repo está copiado en `01. documentacion/11_reto_field_shift.md` y `12_...`) |
| Enviar el proyecto | https://www.spaceappschallenge.org → página del equipo → pestaña **Project** → completar y **Submit** |
| Guía de participantes, cronograma y mentoría | `01. documentacion/oficial/*.pdf` (en el repo) |
| Repo del equipo | https://github.com/jramirezch1978/agrohalcon |

## 2. APIs de NASA (con ejemplos)
| Dato | API / enlace | Llave | Estado |
|---|---|---|---|
| **NASA POWER** (clima) | Docs: https://power.larc.nasa.gov/docs/services/api/ · Visor: https://power.larc.nasa.gov/data-access-viewer/ | no | ✅ |
| **CMR** (catálogo: versiones, archivos) | https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html | no | ✅ |
| **SMAP** SPL3SMP_E v006 (9 km) | https://nsidc.org/data/spl3smp_e · vía AppEEARS o Earthdata (≈ 630 MB por día global) | Earthdata | ❌ |
| **GPM IMERG** diario | `GPM_3IMERGDL` v07 (reciente, 25 MB/día): https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGDL_07/summary · `GPM_3IMERGDF` v07 (final; en CMR termina 2025-09-30): https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGDF_07/summary | Earthdata + app *GESDISC* | ❌ |
| **MODIS NDVI** MOD13Q1 v061 (250 m) | https://lpdaac.usgs.gov/products/mod13q1v061/ · servicio ORNL: `https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset?...` | no (ORNL) | ⚠️ lento (40-60 s) |
| **MUR SST** v4.1 (1 km) | https://podaac.jpl.nasa.gov/dataset/MUR-JPL-L4-GLOB-v4.1 · ERDDAP: `https://upwell.pfeg.noaa.gov/erddap/griddap/jplMURSST41` | no (ERDDAP) / Earthdata (PO.DAAC) | ⚠️ ERDDAP sin respuesta desde esta PC |
| **AppEEARS** (puntos sin descargar archivos) | https://appeears.earthdatacloud.nasa.gov/ · API: https://appeears.earthdatacloud.nasa.gov/api/ | Earthdata (usuario y clave) | ❌ |
| **Earthdata Login** (cuenta y token) | https://urs.earthdata.nasa.gov/ | — | ❌ falta la de David |
| **ONI** (El Niño/La Niña, NOAA) | https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt | no | ✅ |
| FAO ECOCROP (catálogo de cultivos) · GAEZ | https://gaez.fao.org/pages/ecocrop · https://gaez.fao.org/ | no | ✅ abre |
| ECOSTRESS / SRTM / HLS (opcionales) | `ECO_L3T_JET` v003 · `SRTMGL1` v003 · `HLSL30` v2.0 (LP DAAC) | Earthdata | ❌ |
| FIRMS (focos de calor, opcional) | https://firms.modaps.eosdis.nasa.gov/api/map_key | solo correo | ❌ |

### Ejemplos que funcionan (PowerShell, `curl.exe`)
```powershell
# Lluvia y humedad MENSUAL 2016-2017 en un punto (marzo 2017 = El Niño costero)
curl.exe -s "https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=PRECTOTCORR,GWETTOP&community=AG&longitude=-80.63&latitude=-5.19&start=2016&end=2017&format=JSON"

# Diario, últimos días (POWER tiene ~2-3 días de rezago)
curl.exe -s "https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M_MAX,T2M_MIN,PRECTOTCORR&community=AG&longitude=-80.63&latitude=-5.19&start=20261101&end=20261111&format=JSON"

# ¿Qué versión y DOI tiene SMAP? (para References)
curl.exe -s "https://cmr.earthdata.nasa.gov/search/collections.umm_json?short_name=SPL3SMP_E&version=006"

# ¿Qué archivos de IMERG cubren Piura?
curl.exe -s "https://cmr.earthdata.nasa.gov/search/granules.json?short_name=GPM_3IMERGDL&version=07&point=-80.63,-5.19&temporal=2026-11-08T00:00:00Z,2026-11-12T23:59:59Z&page_size=3"
```
Con token de Earthdata, para descargar un archivo: `curl.exe -L -H "Authorization: Bearer %EARTHDATA_TOKEN%" -O <url-del-archivo>` (nunca pegues el token en un chat o archivo del repo).

## 3. Llaves y cuentas: qué necesitas tú y qué no
| Llave | ¿Para qué? | ¿De quién? | ¿Dónde va? |
|---|---|---|---|
| `EARTHDATA_TOKEN` | Descargar SMAP, IMERG, MODIS, ECOSTRESS | **David** (cuenta propia) | `climate-service/.env` |
| `EARTHDATA_USERNAME` / `PASSWORD` | Solo AppEEARS por API | David | `climate-service/.env` |
| `GROQ_API_KEY` | Asistente de IA (Llama) | **Jhonny** (backend Java) | `deploy/vps/.env` del servidor; **nunca** en la app ni en el repo |
| NASA POWER, CMR, ONI, MUR (ERDDAP) | — | no necesitan llave | — |
| Azure / Hetzner | Despliegue | Jhonny | — |

## 4. Herramientas de desarrollo (todas ya instaladas o en el entorno)
| Herramienta | Enlace | Nota |
|---|---|---|
| FastAPI | https://fastapi.tiangolo.com/ | docs en vivo en `http://localhost:8000/docs` |
| Pydantic v2 | https://docs.pydantic.dev/ | valida el contrato |
| earthaccess | https://earthaccess.readthedocs.io/ | descargas con token |
| pandas · scipy · xarray · h5py | https://pandas.pydata.org/ · https://scipy.org/ · https://docs.xarray.dev/ · https://www.h5py.org/ | datos y archivos HDF5/NetCDF |
| pymannkendall | https://pypi.org/project/pymannkendall/ | tendencias (Mann-Kendall y Sen) |
| Groq API (Jhonny) | https://console.groq.com/docs | modelos Llama: elegir uno vigente en `/docs/models` |
| Leaflet · Chart.js · Vue · Capacitor (Sheila) | https://leafletjs.com/ · https://www.chartjs.org/ · https://vuejs.org/ · https://capacitorjs.com/ | — |

## 5. Fuentes locales (Alejandro y la validación 2017)
| Fuente | Enlace |
|---|---|
| INDECI, Compendio Estadístico 2017 (daños por El Niño costero) | https://cdn.www.gob.pe/uploads/document/file/1048401/20180227171454120200726-15599-1ptpifw.pdf |
| SENASA, hectáreas perdidas por el Niño costero ⚠️ **el enlace del PDF *References* da 404: lleva guion en `cuantas-hectareas`** | https://www.senasa.gob.pe/senasacontigo/nino-costero-cuantas-hectareas-se-han-perdido-por-efecto-del-evento-climatico/ |
| MIDAGRI: calendarios de siembra (por completar por Alejandro) · SENAMHI: estaciones · ENFEN: comunicados e ICEN | buscar en gob.pe (Midagri, Senamhi, ENFEN) |
