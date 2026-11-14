# climate-service · AgroShift

Servicio de cálculo en Python (FastAPI, puerto **8000**) + capa de datos NASA y bases de datos. Dueño: **David** (rama `feature/datos-python`).

Recibe de la API en Java los datos NASA **ya descargados** y devuelve:
- los **4 indicadores de riesgo** (lluvia, humedad del suelo, calor, señal de El Niño) con nivel bajo/medio/alto,
- el **puntaje de las rotaciones** (0-100) con su explicación y, si se pide, su **incertidumbre**,
- **qué hacer esta quincena** (acción, motivo y satélite que respalda el dato),
- las **guardas del asistente de IA**: la IA explica, no inventa.

> Todo con **reglas y fórmulas verificables**. No usa IA para calcular. Cumple el *Contrato del backend*: JSON en camelCase, fechas `YYYY-MM-DD`, unidades en el nombre.

## Arranque rápido (Windows)

```powershell
cd "02. backend\python\climate-service"
py -3.11 -m venv .venv                      # Python 3.11 (el 3.14 aún da problemas con librerías científicas)
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy env.example .env                       # y pon tu EARTHDATA_TOKEN (solo en .env)
pytest                                      # ~120 pruebas sin internet
uvicorn app.main:app --reload --port 8000   # docs: http://localhost:8000/docs · panel: http://localhost:8000/panel/
```

## Endpoints

| Método | Ruta | Estado | Para qué |
|---|---|---|---|
| GET | `/salud` | contrato | Estado del servicio |
| POST | `/indicadores` | contrato | Datos NASA del punto → los 4 indicadores |
| POST | `/rotaciones` | contrato | Indicadores + catálogo → rotaciones con puntaje, riesgo y explicación |
| POST | `/recomendacion` | **propuesto** | Todo en una llamada (`lat, lon, fecha, indicadores, rotaciones, queHacer`) |
| POST | `/asistente/contexto` | **propuesto** | Mensajes listos para Groq: reglas + solo datos calculados + la pregunta |
| POST | `/asistente/validar` | **propuesto** | Revisa la respuesta del modelo; si inventa algo, devuelve el Plan B |
| POST | `/asistente/preguntar` | **propuesto** | El asistente completo: llama a Groq (`openai/gpt-oss-20b`) desde aquí, valida la respuesta y, si algo falla o falta la clave, responde con plantillas |
| GET | `/asistente/estado` | **propuesto** | ¿Hay clave de Groq? modelo y límites (nunca devuelve la clave) |
| POST | `/asistente/plan-b` | **propuesto** | Explicación con plantillas (sin IA) cuando Groq no responde |

**Campos extra (opcionales):** `meta` (fuente real de un dato), `fecha`, `rotaciones`, `rotacionActualId`, `top`, `incertidumbre`.
Sin ellos la respuesta es exactamente la del PDF. Ver [`docs/DECISIONES_ABIERTAS.md`](docs/DECISIONES_ABIERTAS.md).

## Cómo se calcula (todo en [`app/thresholds.py`](app/thresholds.py))

| Indicador | Anomalía | Medio desde | Alto desde | Fuente |
|---|---|---|---|---|
| `lluvia` | \|valor − normal\| / max(normal, 3 mm) (déficit **y** exceso) | 25 % | 50 % | GPM IMERG / POWER |
| `humedadSuelo` | déficit relativo | 15 % | 30 % | SMAP / POWER |
| `calor` | tempMaxC − normal (solo exceso) | +1,5 °C | +4 °C | NASA POWER |
| `elNino` | anomalía del mar (solo calentamiento) | +0,5 °C | +1,5 °C | NOAA Niño 1+2 / MUR SST |

**Puntaje** = 100 − descuentos: agua del suelo según lo que necesita el cultivo, lluvia (falta o exceso), calor sobre su límite, El Niño y época de siembra (65 % primer cultivo, 35 % segundo; monocultivo −5).
**Casos extremos:** lluvia ≥ +200 % = inundación (−60 a todo cultivo); **El Niño ≥ +3 °C = señal extraordinaria** (−35 a todo cultivo, pide seguir a ENFEN y consultar a un técnico).
**Incertidumbre** (opcional): cada indicador se mueve 1 σ por separado y los cambios se suman en cuadratura → `puntajeMin`, `puntajeMax`, `confianza`.

## Estructura

```
app/        servicio FastAPI: contrato (schemas), indicadores, rotaciones, qué hacer, asistente, thresholds
etl/        descargas NASA y NOAA (se corren en tu PC): POWER, SMAP, MUR SST, VIIRS NDVI, SRTM, Niño/ONI, SoilGrids, CMR
db/         bases de datos: esquema único (SQLAlchemy) → SQLite + SQL de PostgreSQL, ingesta, análisis, exportadores
panel/      panel técnico (Leaflet + Chart.js) servido en /panel/: mapa de riesgo, Niño 1982-2026, validación 2017, comparador en vivo
tests/      ~120 pruebas sin internet + 3 con internet (pytest -m live)
data/       backup/ (se sube al repo) · raw/ (descargas, ignorado) · agroshift.sqlite (generada, ignorada)
docs/       checklist, prompts, enlaces/APIs, base de datos, decisiones abiertas, uso de IA
.claude/    agentes y comandos de Claude Code para este proyecto (ver abajo)
```

## Bases de datos

Un solo esquema ([`db/schema.py`](db/schema.py)) genera **SQLite** (para trabajar aquí) y **PostgreSQL** (`db/postgres/`, para el VPS). Modelo en estrella:
`region · zona · fuente_dato · variable · cultivo · rotacion` (dimensiones) y `observacion · normal_mensual · indice_climatico · episodio_calido · sst_clima · tendencia · composite_nino · validacion_quincena · recomendacion_cache · consulta` (hechos).
Cada dato guarda su **fuente y versión** (`fuente_dato`: DOI y estado `en_uso / probado / bloqueado / planeado`). La tabla `datosNasa` del contrato es la vista `v_datos_nasa`.

```powershell
python -m etl.jobs power nino mur mur-clima srtm suelos ndvi smap smap-clima   # descargas a data/raw/cache (con token)
python -m db.build                  # base SQLite desde la caché (comprueba claves foráneas)
python -m db.export_postgres        # 01_schema.sql (validado con sqlglot) + semillas CSV para \copy
python -m db.export_panel           # data/backup/panel.json para el panel
```

| Fuente | Qué aporta | Estado (14-nov) |
|---|---|---|
| NASA POWER | clima 1981-hoy, 16 valles, 10 variables; normal 1991-2020 | ✅ en uso |
| NOAA CPC Niño 1+2 · ONI | señal de El Niño costero; episodios calculados | ✅ en uso (no es NASA) |
| MUR SST v4.1 (PO.DAAC) | temperatura del mar y anomalía propia vs 2003-2022 | ✅ en uso |
| SRTM 30 m | elevación y pendiente por valle | ✅ en uso |
| ISRIC SoilGrids | pH, carbono, arcilla y arena (donde está mapeado) | ✅ parcial (no es NASA) |
| SMAP SPL3SMP_E v006 | humedad del suelo (lectura parcial del HDF5) | ⏳ descarga en curso: ver `fuente_dato.estado` |
| VIIRS NDVI VNP13A1 v002 | vegetación 500 m, 16 días (en lugar de MODIS) | ⏳ descarga en curso |
| GPM IMERG · GLDAS | lluvia por valle · humedad de respaldo | ⛔ **bloqueado**: falta aceptar el acuerdo de GES DISC (ver checklist) |
| ECOSTRESS · SMAP L4 | evapotranspiración · humedad de raíz | 📝 planeado |

## Panel técnico

`uvicorn app.main:app` y abrir **http://localhost:8000/panel/**: KPI de El Niño, 16 valles coloreados por nivel, serie Niño 1982-2026 con episodios, "máquina del tiempo" 2017, comparador de rotaciones **en vivo** contra `POST /recomendacion`,
explicación del asistente (Plan B) y la tabla de bases de datos. Es una herramienta de desarrollo (no existe en la imagen de Docker); el catálogo de cultivos del comparador es de **PRUEBA**.

## Agentes y comandos de Claude Code (`.claude/`)

Lanza `claude` desde esta carpeta. Agentes: `ingeniero-datos-nasa` (ingestas y base), `guardian-del-contrato` (solo lectura: que nada rompa el PDF), `revisor-agronomico` (umbrales y catálogo),
`auditor-de-entrega` (secretos, enlaces, versiones, uso de IA). Comandos: `/probar`, `/base-de-datos`, `/estado-nino`, `/revisar-contrato`.

## Para empezar a trabajar
1. [`docs/CHECKLIST_DAVID.md`](docs/CHECKLIST_DAVID.md) · 2. [`docs/PROMPTS_CLAUDE_CODE.md`](docs/PROMPTS_CLAUDE_CODE.md) · 3. [`docs/ENLACES_Y_APIS.md`](docs/ENLACES_Y_APIS.md) · 4. [`docs/BASE_DE_DATOS.md`](docs/BASE_DE_DATOS.md) · 5. [`docs/DECISIONES_ABIERTAS.md`](docs/DECISIONES_ABIERTAS.md)
