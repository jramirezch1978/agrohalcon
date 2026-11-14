# Decisiones abiertas y hallazgos (para la reunión de la primera hora)

Reglas del equipo: *“Después de aprobar el contrato nadie cambia un campo sin avisar.”* Todo lo de esta lista son
**propuestas o hallazgos de David / Claude Code**, no decisiones tomadas. Cada una dice quién debe decidir.

## A. Contrato: lo que el PDF no define (decidir antes de integrar)

| # | Duda | Qué hizo `climate-service` mientras tanto | Decide |
|---|---|---|---|
| A1 | `/rotaciones` ¿devuelve un **arreglo** o `{ "rotaciones": [...] }`? | Arreglo, igual que el bloque `rotaciones` de `/api/recomendacion` (Java reenvía) | Jhonny + David |
| A2 | ¿Quién arma **`queHacer`** (acción, motivo, fuente)? No está asignado | Python lo calcula en `POST /recomendacion` (endpoint **propuesto**, extra). Si no se aprueba, se borra sin afectar nada más | Jhonny |
| A3 | `/rotaciones`: ¿las candidatas vienen de la tabla `rotaciones` o las genera Python? | Acepta ambas: si Java manda `rotaciones` las puntúa; si no, genera parejas con el catálogo (sin monocultivos) | Jhonny + Alejandro |
| A4 | ¿Cómo se marca la **rotación actual** del agricultor? (el reto exige comparar 3, **incluida la actual**) | Campo opcional `rotacionActualId`: siempre aparece en el resultado | Sheila + Jhonny |
| A5 | **`fuente` real**: el contrato fija `humedadSuelo = SMAP` y `lluvia = GPM IMERG`, pero mientras no estén descargados salen de POWER | Campo opcional `meta` por indicador (`fuente`, `unidad`). Sin él, usa los nombres del contrato | David |
| A6 | `/salud` del servicio: el PDF no dice qué devuelve | `{"estado":"ok","servicio":"climate-service","version":"0.1.0"}` | Jhonny |
| A7 | **Nombre**: el equipo eligió **AgroShift**, pero el repo (`agrohalcon`), carpetas y docs dicen AgroHalcón | No se renombró nada. El código nuevo dice AgroShift | Jhonny (renombrar repo en GitHub: Settings → Rename) |

## B. Modelo: supuestos que Alejandro debe validar

| # | Supuesto actual (en `app/thresholds.py`) | Qué falta |
|---|---|---|
| B1 | El catálogo **de prueba** (`samples/catalogo_cultivos_ejemplo.json`) usa valores ilustrativos de arroz, maíz, algodón y frijol | Catálogo real de Alejandro (FAO ECOCROP + calendarios MIDAGRI), mismos campos que la tabla `cultivos` |
| B2 | El arroz tolera encharcamiento y la poca agua no (`EXCESO_FACTOR`) | Campo opcional por cultivo (`toleraInundacion`) |
| B3 | Los cultivos **permanentes** (mango, limón, banano, cacao, café) **no** rotan: reciben acciones (propuesta del equipo, doc 23) | Definir campo `tipo: anual|permanente`; yo calculo acciones por indicador |
| B4 | El puntaje solo mide **riesgo climático**. El reto pide también beneficios y sacrificios (fijación de nitrógeno, raíz profunda, cobertura, erosión, mercado) | Campos opcionales del catálogo; yo sumo bonificaciones y muestro **incertidumbre** |
| B5 | “Esta quincena” usa solo el clima de hoy. Doc 23 propone evaluar **el ciclo completo** (siembra→cosecha, barra de meses verde/ámbar/rojo) | Aprobar un endpoint nuevo (p. ej. `POST /campana`) y el formato para Sheila |
| B6 | Pesos 65 % / 35 % entre primer y segundo cultivo; −5 por monocultivo; ≥ +200 % de lluvia = inundación | Calibrar con la validación 2017 y con el técnico (Claudia Grados, mentoría sábado 14:00) |

## C. Hallazgos con datos reales (14-nov-2026)

1. **El ONI no vio el Niño costero de 2017** (trimestres ene-may 2017: −0,08 a +0,35 = “neutral”), aunque fue un evento muy fuerte en Piura.
   Es la mejor justificación para usar la **temperatura del mar local (MUR SST)** en vez de un índice del Pacífico central. (Prueba automática: `pytest -m live`.)
2. **NASA POWER sí muestra 2017**: en Bajo Piura la lluvia pasa de 0,8 mm/día normales a 2,3 (31-ene), 10,0 (28-feb) y 14,8 (15-mar). El indicador de lluvia sube a
   **alto desde el 31 de enero**, ~6 semanas antes del pico de marzo. Detalle por zona en `data/backup/validacion_2017.json`.
3. **El ONI de hoy es +2,46 (ASO 2026)** y POWER marca lluvia muy por encima de lo normal en Piura estos días (ver `data/backup/actual.json`).
   La demo “en vivo” va a mostrar **alerta alta**. Conviene contrastarla con SENAMHI / ENFEN antes de presentarla. POWER es un reanálisis, no una estación.
4. **`T2M_MAX` de POWER en la celda de Piura es muy alto en marzo (~37-39 °C)** y baja a ~34 °C en 2017 (nubosidad). Parece sesgado al calor frente a lo observado.
   Efecto: comparar el `calor` absoluto con el `tempMaxC` del cultivo puede castigar siempre. Opciones: (a) comparar solo **anomalías**; (b) usar `T2M` (media) si el catálogo
   viene de ECOCROP (rangos en temperatura media); (c) calibrar con SENAMHI. **Decide:** David + Alejandro.
5. **POWER es grueso (0,5° ≈ 55 km):** varios valles reciben el mismo dato (ya lo documentó Jhonny en el doc 24). Por eso IMERG (0,1°) y SMAP (9 km) importan para la demo por valle.
6. **El “normal” de la climatología de POWER no declara su periodo** y difiere de promediar 1991-2020 (marzo, lluvia: 1,69 vs 1,97 mm/día; `T2M_MAX`: 39,1 vs 37,5 °C).
   El servicio usa **promedio 1991-2020 del mismo mes**, calculado a partir de la serie mensual.
7. **`GPM_3IMERGDF` termina el 2025-09-30 en el catálogo CMR.** Para datos recientes hay que usar **`GPM_3IMERGDL`** (V07C, diario rápido, 25 MB/día).
   El PDF *Uso de IA y datos NASA* solo cita `GPM_3IMERGDF`: agregar el `DL` en *References*.
8. **SMAP pesa ~630 MB por día** (global). No descargar días enteros: usar **AppEEARS** (valor del punto) o subconjuntos OPeNDAP/Harmony.
9. **La anomalía de +9 °C de MUR SST** que vio Jhonny (dataset `anom1day`, punto costero) es sospechosa. `etl/mur_sst.py` calcula la anomalía contra su propia
   climatología 2003-2022 en un punto **mar adentro** (-5,5; -81,5). Pendiente de comprobar y de contrastar con el ICEN de ENFEN.
10. **Los ERDDAP de NOAA (`upwell` / `coastwatch.pfeg.noaa.gov`) no respondieron desde la PC de David** (timeout) el 14-nov. Sin ese dato, `sstAnomaliaC` queda en 0 y se avisa en el JSON.
    Plan: PO.DAAC con el token de Earthdata, o pedirle a Jhonny que ejecute `python -m etl.build_backup` desde su red (a él sí le respondió).

## D. References / documentos de entrega (de `python -m etl.verificar_enlaces`)

- ❌ El enlace de **SENASA** del PDF *References* da **404**. La versión correcta lleva guion: `.../nino-costero-cuantas-hectareas-se-han-perdido-por-efecto-del-evento-climatico/`
  (al copiar desde un PDF se pierde el guion de fin de línea). Corregir en el formulario.
- ⚠️ `https://modis.gsfc.nasa.gov/` no respondió desde esta PC. Alternativa que sí abre: `https://www.earthdata.nasa.gov/data/catalog/lpcloud-mod13q1-061`.
- ⚠️ Canva devuelve 403 a los robots: revisar a mano.
- ➕ Agregar a *References*: `GPM_3IMERGDL`, el CMR (para las versiones) y, si se usa, el ONI de NOAA.
- 📌 Versiones exactas de cada dataset (SMAP SPL3SMP_E **v006**, MOD13Q1 **v061**, MUR **v4.1**, IMERG **V07**) en `data/backup/versiones_datasets.json`.
