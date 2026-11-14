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

## B+. Cambios nuevos en el servicio (todos opcionales o internos; el contrato por defecto no cambia)

| # | Cambio | Decide |
|---|---|---|
| B7 | **Incertidumbre** (`"incertidumbre": true` en `/rotaciones` y `/recomendacion`): añade `puntajeMin`, `puntajeMax` y `confianza` (alta/media/baja) a cada rotación. Se mueve cada indicador 1 σ por separado (lluvia ±25 %, humedad ±0,04 m3/m3, calor ±1,5 °C, mar ±0,3 °C) y los cambios se suman en cuadratura. Sin pedirla, la respuesta es idéntica al PDF | Jhonny + Sheila |
| B8 | **Señal de El Niño extraordinaria** (anomalía ≥ +3 °C en Niño 1+2): descuenta 35 puntos a **todos** los cultivos y `queHacer` pide seguir a ENFEN y consultar a un técnico. Supuesto basado en 1983, 1998 y 2023-26. Antes, con +5,25 °C, el arroz salía con riesgo "bajo" (86/100) | Alejandro + mentoría agro-clima |
| B9 | **Texto de la lluvia en zonas áridas**: si lo normal es < 3 mm/día se dicen las cifras reales ("2,9 mm/día frente a 0,1") y no un porcentaje engañoso | David |
| A8 | **Asistente de IA con guardas** (propuesto): `POST /asistente/contexto` arma el prompt para Groq (reglas + solo datos calculados + la pregunta, que no puede cerrar las etiquetas); `POST /asistente/validar` rechaza respuestas con números, cultivos o satélites que no están en los datos y devuelve el **Plan B** (explicación con plantillas); `POST /asistente/plan-b`. Java sigue llamando a Groq con `GROQ_API_KEY` | Jhonny |
| A9 | **Base de datos con esquema único** (`db/`): SQLite para trabajar y SQL de PostgreSQL generado (`db/postgres/`) con la vista `v_datos_nasa` = tabla `datosNasa` del contrato | Jhonny |

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
9. **La anomalía de +9 °C de MUR SST que vio Jhonny NO era un error del dataset.** Con el token de Earthdata se leyó MUR v4.1 por OPeNDAP de PO.DAAC (`etl/mur_opendap.py`) y se calculó la anomalía
   contra una climatología propia 2003-2022 (36 fechas de referencia al año): mar adentro frente a Piura (-5,5; -81,5) dio **27,5 °C el 11-nov-2026, +9,1 °C** sobre lo normal de ese día.
   El índice mensual de NOAA para toda la región Niño 1+2 es **+5,25 °C** (octubre): la región promedia mar adentro y costa, y octubre es anterior. Las dos cifras son coherentes con un evento extraordinario.
10. **Los ERDDAP de NOAA (`upwell` / `coastwatch.pfeg.noaa.gov`) no respondieron desde la PC de David** (timeout). **Resuelto:** MUR SST se lee por OPeNDAP de PO.DAAC con el token (valor de un punto en ~2,5 s), y la
    señal de El Niño del servicio usa el **índice Niño 1+2 mensual de NOAA CPC** (público, 1982-hoy). Es de NOAA, no de la NASA: declararlo en *References* y en *Use of AI / NASA Data*. MUR SST queda como dato NASA complementario (valor y anomalía propia).
11. **El Niño 2026 es el mayor de todo el registro 1982-2026:** pico de **+5,25 °C** en Niño 1+2 (octubre 2026, y subiendo), frente a +4,03 (1983), +3,73 (1998), +3,30 (2023), +2,48 (2016) y +1,83 (2017).
    Los episodios (≥ +1,0 °C durante ≥ 3 meses) se **calculan** de los datos; no están escritos a mano. Niño 3.4: +3,25 °C; ONI (ASO 2026): +2,46. **Confirmar con ENFEN/IGP antes de presentarlo.**
12. **El Niño costero en años:** Dic-Abr con Niño 1+2 ≥ +1,0 °C → **1983, 1998, 2016 y 2017**. En Bajo Piura la lluvia de marzo en esos años fue **~5,5 veces** la de años normales (6,6 vs 1,2 mm/día; `composite_nino`).
13. **Tendencias (Mann-Kendall + pendiente de Sen, 1981-2025, POWER):** la temperatura sube de forma significativa (p < 0,05) en 9 de 16 valles, entre +0,15 y +0,33 °C por década. La lluvia anual no muestra tendencia
    significativa en 10 de 16 valles: lo que cambia es la **variabilidad entre años**, no el promedio.
14. **SRTM arregla la elevación de POWER:** Chulucanas está a **95 m** (la celda de POWER decía 1051 m). Elevación y pendiente de los 16 valles están en la tabla `zona`.
15. **SMAP cubre cada punto cada 2-3 días y a veces no hay retrieval:** en los últimos 45 días solo ~17 % de las combinaciones valle-día tuvieron valor válido (el resto, sin pasada o calidad no recomendada). Por eso el indicador usa
    una ventana de 14 días (≥ 2 valores) y un normal propio de SMAP 2016-2025; si falta, cae a `GWETTOP` de POWER y lo declara en `meta`.
16. **VIIRS en lugar de MODIS:** `MOD13Q1` es HDF4 (hay que bajar el archivo completo) y el servicio de ORNL estuvo caído. Se usa **VIIRS `VNP13A1` v002** (500 m, 16 días, mismo tipo de compuesta, HDF5 legible por píxel). **Declararlo en References** (el PDF dice MODIS).
17. **AppEEARS no acepta el token de Earthdata como Bearer** (403): pide su propio login con usuario y clave. No hizo falta: SMAP, SRTM, VIIRS y MUR se leen directo con el token.
18. **GES DISC (IMERG y GLDAS) está BLOQUEADO hasta que el usuario acepte el acuerdo:** responde `403 EULA Acceptance Failure`. Acción de David (1 clic, con la sesión de Earthdata iniciada):
    https://urs.earthdata.nasa.gov/approve_app?client_id=e2WVk8Pw6weeLUKZYOxvTQ → después `python -m etl.jobs imerg` y `python -m db.build`. SMAP (NSIDC), LP DAAC (SRTM, MOD13Q1, VNP13A1, ECOSTRESS) y PO.DAAC (MUR) **ya están autorizados**.
19. **SoilGrids (ISRIC, no NASA)** devuelve suelo solo donde está mapeado: 5 de 16 valles tienen pH, carbono, arcilla y arena; el resto queda `NULL` (urbano o sin dato). No se inventa.
20. **La web en línea del equipo (http://2.29.101.199) se llama "AllpaShift"**; el repo dice "agrohalcon" y el equipo eligió "AgroShift". Hay **tres nombres**: decidir uno antes del Submit (portada, README, logo, APK, textos en inglés).
    Además su sección "Datos de la NASA que usamos" lista SMAP, GPM/IMERG, ECOSTRESS, MODIS/VIIRS y SRTM: hoy el código solo usa POWER, SMAP, MUR, VIIRS y SRTM; **IMERG** está bloqueado y **ECOSTRESS** no está integrado. Lo no usado debe decir *planned*.

## D. References / documentos de entrega (de `python -m etl.verificar_enlaces`)

- ❌ El enlace de **SENASA** del PDF *References* da **404**. La versión correcta lleva guion: `.../nino-costero-cuantas-hectareas-se-han-perdido-por-efecto-del-evento-climatico/`
  (al copiar desde un PDF se pierde el guion de fin de línea). Corregir en el formulario.
- ⚠️ `https://modis.gsfc.nasa.gov/` no respondió desde esta PC. Alternativa que sí abre: `https://www.earthdata.nasa.gov/data/catalog/lpcloud-mod13q1-061`.
- ⚠️ Canva devuelve 403 a los robots: revisar a mano.
- ➕ Agregar a *References*: `GPM_3IMERGDL`, el CMR (para las versiones) y, si se usa, el ONI de NOAA.
- 📌 Versiones exactas de cada dataset (SMAP SPL3SMP_E **v006**, MOD13Q1 **v061**, MUR **v4.1**, IMERG **V07**) en `data/backup/versiones_datasets.json`.
