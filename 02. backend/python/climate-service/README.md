# climate-service · AgroShift

Servicio de cálculo en Python (FastAPI, puerto **8000**). Dueño: **David** (rama `feature/datos-python`).

Recibe de la API en Java los datos NASA **ya descargados** y devuelve:
- los **4 indicadores de riesgo** (lluvia, humedad del suelo, calor, señal de El Niño) con nivel bajo/medio/alto,
- el **puntaje de las rotaciones** (0-100) con su explicación,
- **qué hacer esta quincena** (acción, motivo y satélite que respalda el dato).

> Todo con **reglas y fórmulas verificables**. No usa IA para calcular (la IA solo redacta, y es trabajo de Java + Groq).
> Cumple el *Contrato del backend* del equipo: JSON en camelCase, fechas `YYYY-MM-DD`, unidades en el nombre.

## Arranque rápido (Windows)

```powershell
cd "02. backend\python\climate-service"
py -3.11 -m venv .venv                      # Python 3.11 (el 3.14 aún da problemas con librerías científicas)
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy env.example .env                       # y completa EARTHDATA_TOKEN cuando lo tengas
pytest                                      # 65 pruebas sin internet
uvicorn app.main:app --reload --port 8000   # docs interactivas: http://localhost:8000/docs
```

## Endpoints

| Método | Ruta | Estado | Para qué |
|---|---|---|---|
| GET | `/salud` | contrato | Estado del servicio |
| POST | `/indicadores` | contrato | Datos NASA del punto → los 4 indicadores (mismo bloque que `/api/recomendacion`) |
| POST | `/rotaciones` | contrato | Indicadores + catálogo → rotaciones con puntaje, riesgo y explicación |
| POST | `/recomendacion` | **propuesto** | Todo en una llamada: Java solo reenvía la respuesta (`lat, lon, fecha, indicadores, rotaciones, queHacer`) |

Ejemplos listos en [`samples/`](samples). Probar con el servicio encendido:

```powershell
curl.exe -s -X POST http://localhost:8000/indicadores -H "Content-Type: application/json" -d "@samples/indicadores_request.json"
```

**Campos extra (opcionales, no rompen el contrato):** `meta` (declarar la fuente real de un dato), `fecha`, `rotaciones`
(las filas de la tabla `rotaciones`), `rotacionActualId`, `top`. Sin ellos el servicio responde exactamente como el PDF.
Cualquier cambio de campos se avisa al equipo (ver [`docs/DECISIONES_ABIERTAS.md`](docs/DECISIONES_ABIERTAS.md)).

## Cómo se calcula (todo en [`app/thresholds.py`](app/thresholds.py))

| Indicador | Anomalía | Nivel medio desde | Nivel alto desde | Fuente |
|---|---|---|---|---|
| `lluvia` | \|valor − normal\| / max(normal, 3 mm) (déficit **y** exceso) | 25 % | 50 % | GPM IMERG |
| `humedadSuelo` | déficit relativo (normal − valor) / normal | 15 % | 30 % | SMAP |
| `calor` | tempMaxC − tempMaxC normal (solo exceso) | +1,5 °C | +4 °C | NASA POWER |
| `elNino` | anomalía del mar (solo calentamiento) | +0,5 °C | +1,5 °C | MUR SST |

**Puntaje de rotación** = 100 − descuentos. Cada cultivo descuenta por: falta de agua en el suelo (según cuánta agua necesita),
falta o exceso de lluvia, calor sobre su `tempMaxC`, señal de El Niño y siembra fuera de época; el primer cultivo pesa 65 % y
el segundo 35 %. Repetir el mismo cultivo descuenta 5 (no corta plagas). Una lluvia **≥ +200 %** se trata como inundación y
descuenta 60 a cualquier cultivo (Niño costero 2017). Riesgo: ≥ 70 bajo · 45-69 medio · < 45 alto.
Cada explicación sale de los descuentos reales, con el número del dato (p. ej. “40 % por debajo de lo normal”).

## Estructura

```
app/        servicio FastAPI (schemas, indicators, rotations, que_hacer, thresholds)
tests/      65 pruebas sin internet + 3 con internet (pytest -m live)
samples/    JSON de ejemplo del contrato y catálogo de PRUEBA (no validado)
etl/        scripts de datos NASA: se corren en tu PC, no en el servidor
data/backup datos de respaldo y validación 2017 (pequeños, se suben al repo)
docs/       checklist, prompts para Claude Code, enlaces/APIs, base de datos, decisiones abiertas
```

## Scripts de datos NASA (`etl/`)

| Script | Qué hace | Estado |
|---|---|---|
| `nasa_power.py` | Clima diario / mensual / climatología por coordenadas (sin clave) | ✅ probado |
| `inputs.py` | Arma el cuerpo de `POST /indicadores` con datos reales (normal = 1991-2020) | ✅ probado |
| `build_backup.py` | Datos de respaldo + validación de El Niño 2017, por zona | ✅ probado |
| `cmr.py` · `verificar_versiones.py` | Versión exacta y DOI de cada dataset; búsqueda de archivos (sin token) | ✅ probado |
| `oni.py` | Serie ONI de NOAA (años El Niño/La Niña) | ✅ probado |
| `ndvi_modis.py` | NDVI MODIS por punto (ORNL) para validar 2017 | ⚠️ ORNL respondió 502/503 el 14-nov: sin verificar. Alternativa: AppEEARS |
| `verificar_enlaces.py` | Comprueba que cada enlace de References abra | ✅ probado (halló el enlace roto de SENASA) |
| `export_zonas_sql.py` | `zonas_seed.sql` con los 16 valles | ✅ |
| `mur_sst.py` | Temperatura del mar → anomalía de El Niño | ⚠️ ERDDAP de NOAA no respondió desde esta PC (14-nov) |
| `earthdata_download.py` | SMAP / IMERG con token de Earthdata | ❌ falta el token |
| `appeears.py` | Puntos de SMAP / MODIS sin bajar archivos | ❌ falta usuario y clave |

```powershell
python -m etl.verificar_versiones           # versiones exactas para References
python -m etl.build_backup                  # Piura (7 zonas)  ·  --todas = 16 valles  ·  --catalogo <json>  ·  --ndvi
```

## Para empezar a trabajar

1. [`docs/CHECKLIST_DAVID.md`](docs/CHECKLIST_DAVID.md): cuentas, token y flujo de Git.
2. [`docs/PROMPTS_CLAUDE_CODE.md`](docs/PROMPTS_CLAUDE_CODE.md): prompts listos para pegar.
3. [`docs/ENLACES_Y_APIS.md`](docs/ENLACES_Y_APIS.md) y [`docs/BASE_DE_DATOS.md`](docs/BASE_DE_DATOS.md).
