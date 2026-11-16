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
15. **SMAP cubre cada punto cada 2-3 días y a veces no hay retrieval:** en los últimos 45 días solo **121 de 688 combinaciones valle-día (17,6 %)** tuvieron valor válido (el resto, sin pasada o calidad no recomendada). Por eso el indicador usa
    una ventana de 14 días (≥ 2 valores) y un normal propio de SMAP 2016-2025; si falta, cae a `GWETTOP` de POWER y lo declara en `meta`.
16. **VIIRS en lugar de MODIS:** `MOD13Q1` es HDF4 (hay que bajar el archivo completo) y el servicio de ORNL estuvo caído. Se usa **VIIRS `VNP13A1` v002** (500 m, 16 días, mismo tipo de compuesta, HDF5 legible por píxel). **Declararlo en References** (el PDF dice MODIS).
17. **AppEEARS no acepta el token de Earthdata como Bearer** (403): pide su propio login con usuario y clave. No hizo falta: SMAP, SRTM, VIIRS y MUR se leen directo con el token.
18. **GES DISC (IMERG y GLDAS) está BLOQUEADO hasta que el usuario acepte el acuerdo:** responde `403 EULA Acceptance Failure`. Acción de David (1 clic, con la sesión de Earthdata iniciada):
    https://urs.earthdata.nasa.gov/approve_app?client_id=e2WVk8Pw6weeLUKZYOxvTQ → después `python -m etl.jobs imerg` y `python -m db.build`. SMAP (NSIDC), LP DAAC (SRTM, MOD13Q1, VNP13A1, ECOSTRESS) y PO.DAAC (MUR) **ya están autorizados**.
19. **SoilGrids (ISRIC, no NASA)** devuelve suelo solo donde está mapeado: 5 de 16 valles tienen pH, carbono, arcilla y arena; el resto queda `NULL` (urbano o sin dato). No se inventa.
20. **La web en línea del equipo (https://allpashift.crisaor.org) se llama "AllpaShift"**; el repo dice "agrohalcon" y el equipo eligió "AgroShift". Hay **tres nombres**: decidir uno antes del Submit (portada, README, logo, APK, textos en inglés). **David confirmó el 14-nov: AllpaShift** (falta renombrar los textos de `climate-service/`).
    Además su sección "Datos de la NASA que usamos" lista SMAP, GPM/IMERG, ECOSTRESS, MODIS/VIIRS y SRTM: hoy el código solo usa POWER, SMAP, MUR, VIIRS y SRTM; **IMERG** está bloqueado y **ECOSTRESS** no está integrado. Lo no usado debe decir *planned*.

21. ⚠️ **La "caída del NDVI" de 2017 NO aparece con este método; el NDVI SUBIÓ.** VIIRS VNP13A1 (566 valores válidos, solo píxeles con confiabilidad buena o marginal) en el punto central de cada valle: de dic-2016/ene-2017 a mar-may-2017
    el NDVI **sube en los 10 valles** que tienen datos en ambos periodos (Bajo Piura 0,43 → 0,52 · Chira 0,61 → 0,71 · Sechura 0,37 → 0,70 · Jequetepeque 0,20 → 0,44; en Medio Piura casi no cambia: +3 %). Es el conocido "reverdecimiento" del desierto de Piura por la lluvia de El Niño.
    El PDF *Project Details* afirma que se valida "con la caída de la vegetación medida por MODIS NDVI" y la diapositiva de Impacto lo repite: **hay que corregir el texto o el método** antes del Submit. Opciones (decide David + Alejandro):
    (a) comparar el NDVI con el **mismo periodo de años normales** (anomalía de NDVI, no antes/después), (b) medir solo **píxeles de cultivo** (máscara de ESA WorldCover o MIDAGRI) y no el punto central del valle, (c) mirar **abril-junio** (después de las inundaciones), cuando se pierden cultivos,
    (d) usar como verdad de campo las **hectáreas perdidas de INDECI/SENASA** (ya están en *References*) en vez de NDVI. Lo que sí está respaldado por datos: la lluvia y la señal del mar anticiparon el evento semanas antes (alerta MEDIA el 15-ene-2017 y ALTA el 31-ene en Bajo Piura).
    Nubes: el filtro de confiabilidad deja pocos píxeles en la temporada de lluvias (solo 12 de 16 valles tienen ≥ 3 valores en mar-may; Alto Piura, Olmos, Huancabamba y Cajamarca quedan sin dato en ese periodo).

22. **Los umbrales de `calculos/` (Sheila) y de `climate-service` (David) no coinciden: decidir una sola regla** (`REVISION_CALCULOS_SHEILA.md`, sección 3). No se cambió ninguno: afecta lo que ve el agricultor.

    | | Sheila (`umbrales.yaml`) | David (`app/thresholds.py`, en producción) |
    |---|---|---|
    | Lluvia medio / alto (anomalía) | 20 % / 40 % | 25 % / 50 % |
    | Lluvia sin señal si valor y normal están bajo | 1 mm/día | 3 mm/día |
    | Humedad del suelo (déficit) | 20 % / 40 % | 15 % / 30 % |
    | Calor (°C sobre lo normal) | +1,5 / +3,0 | +1,5 / +4,0 |
    | Normal climática | 2001-2025 | 1991-2020 |

    Propuesta: quedarse con los de David (normal de 30 años estándar, probados con 2017 y con los 16 valles) y documentar los de Sheila como alternativa en la entrega.
23. **IMERG y MUR Niño 1+2 los bajó Sheila (con su cuenta de Earthdata), no David.** Están en la base (`en_uso`) y en *References* hay que decirlo así: el token de David sigue sin poder leer IMERG (punto 18).
    Contraste real: MUR vs NOAA CPC en Niño 1+2 **r = 0,987** (126 meses); IMERG vs POWER en lluvia mensual **r = 0,69-0,91** (297 meses). IMERG llueve más que POWER (+0,2 a +1,0 mm/día): en marzo de 2017 (Bajo Piura)
    IMERG dio 6,1 veces su normal y POWER 8,6 veces la suya. **Nunca mezclar valores de las dos fuentes; comparar anomalías de la misma fuente.**
24. **Respaldo de El Niño dentro del servicio** (`app/datos_respaldo/nino12_historico.json`): si el ERDDAP de NOAA no responde, se usa la última semana de MUR SST (caja Niño 1+2) siempre que tenga ≤ 21 días; el indicador lo avisa en `aviso`
    y conserva `fuente = "MUR SST"`. La serie de Sheila llega hasta la semana del **2026-11-09**: vence alrededor del 30-nov-2026. Para renovarlo: que Sheila corra `scripts.descargar_mur_sst --actualizar` y luego `python -m etl.respaldo_validacion`.
25. **Hay dos esquemas de PostgreSQL**: el de David (`db/postgres/01_schema.sql`, modelo en estrella, para pruebas locales y el panel) y el de Jhonny (`04. base de datos/ddl/00-schema.sql`, el que lee y graba Java). **El oficial es el de Jhonny.**
    `db/export_allpashift.py` lleva los datos reales a sus tablas (`seed/02-datos-nasa.sql`); verificado en PostgreSQL 16.2 real. `database-deploy.bat` aún no ejecuta ese archivo (línea para agregar en `REVISION_CALCULOS_SHEILA.md`, sección 6).
26. **`feature/frontend-sheila` duplica `03. frontend/`** (solo cambian el renombre AgroShift → AllpaShift y un `||` por `??`): no abrir ese Pull Request. `calculos/` queda en la raíz del repositorio; se sugiere moverla a `02. backend/python/calculos-sheila/`.

27. **Asistente de IA: Groq con `openai/gpt-oss-20b`, llamado desde Python (decisión del equipo, 14-nov).** Licencia Apache 2.0; la clave `GROQ_API_KEY` solo en el servidor porque el repositorio es público.
    Implementado en `climate-service`: `POST /asistente/preguntar` (Groq → validación sin IA → Plan B), `GET /asistente/estado`, límites de preguntas y 18 pruebas con un transporte simulado. **No se probó contra Groq real: no hay clave.**
    ⚠ La rama `feature/integracion-sheila` pone el asistente con Groq **en Java** (`GroqClient.java`, `GROQ_API_KEY` en `agro-service`): hay que elegir un solo lugar. Si queda en Python, Java solo llama a `/asistente/preguntar` y no necesita la clave.
28. **Máquina del tiempo con la señal del mar (`/validacion`).** Antes el aviso de 2017 salía el 15-mar con **0 semanas** de anticipación (solo miraba la lluvia mensual de POWER). Ahora usa el primer aviso entre el mar y la lluvia:
    en Piura 2017, **MUR SST (NASA) pasó a nivel medio el 11-dic-2016 (11 semanas antes del mes más lluvioso) y a nivel alto el 22-ene-2017 (5 semanas antes)**; la lluvia de IMERG llegó a 3 veces lo normal recién al terminar febrero.
    Solo cuenta como anticipación si la lluvia extrema realmente ocurrió. ⚠ **El nivel medio de MUR se activa también en años sin inundación** (2018, 2019, 2020, 2021, 2022: falsas alarmas; la base climática de MUR 2003-2014 da +0,4 °C más que la de NOAA 1991-2020),
    por eso solo el nivel **alto** pide drenar (en 2018-2022 nunca llegó a alto). Antes de 2016 se usa el índice mensual de NOAA CPC (no es NASA) y llega con 0-1 semanas (1998). Datos dentro de `app/datos_respaldo/` (MUR, CPC, IMERG de Piura).

29. **Estado real tras las integraciones del 14-nov (ya en `develop`):** Java llama **solo a `calculos`** (Sheila, :8001) para calcular; `climate-service` sigue desplegado pero **ya no está en el flujo de la app**. El asistente con Groq
    (`openai/gpt-oss-20b`) quedó **en Java** (`AsistenteService`, `GroqClient`; la clave en el contenedor `agro-service`): el punto 27 y `POST /asistente/preguntar` de este servicio quedan como alternativa no usada. `climate-service` hoy aporta el panel técnico,
    la base de datos de análisis y la referencia de las guardas. Decidir con Jhonny si se retira del `docker-compose.app.yml` o se le da un uso.
30. **Plan gratuito de Groq (docs de Groq, 14-nov): para `openai/gpt-oss-20b` son 30 solicitudes/min, 1 000/día, 8 000 tokens/min y 200 000 tokens/día, POR CLAVE (no por IP).** Cada pregunta gasta unos 2 600 tokens (estimado sobre la recomendación real de Piura: ~6 700 caracteres de JSON ≈ 2 100 tokens de entrada + ~400 de salida; confirmarlo con `usage.total_tokens` en el primer día): caben ~3 preguntas por minuto y ~70 al día
    para todos los usuarios juntos; el límite de 10 preguntas por minuto por IP no protege eso. Con el cupo agotado el asistente cae a "respaldo" (sigue funcionando, sin IA). Propuesto en un PR (`feature/groq-cupo-gratuito`): llevar la cuenta del cupo y no llamar a Groq cuando se acabó,
    respetar `Retry-After` de un 429, guardar 30 min las respuestas repetidas (las preguntas sugeridas se repiten) y rechazar respuestas con números que no están en la recomendación. **Para la demo: probar el asistente antes y no depender de él más de ~3 veces por minuto.**
31. **Con El Niño en +6,0 °C la app pedía "preparar drenaje" y a la vez mostraba rotaciones de riesgo bajo (80-90 puntos).** `calculos` solo subía un nivel la lluvia de enero-abril. Propuesto en un PR (`feature/rotaciones-el-nino-extremo`): con dato real de MUR SST ≥ +3,0 °C en la costa norte se resta 35 puntos a TODAS las rotaciones
    (en Piura: 90 → 55, 80 → 45, 70 → 35). Valores en `config/umbrales.yaml` (`el_nino_extremo_c`, `el_nino_extremo_puntos`): supuesto del equipo, los mismos que usa `climate-service`.
32. **La plataforma completa corre en una PC sin Docker** (`deploy/local/`, propuesto en `feature/levantar-local`): PostgreSQL embebido con el esquema y los seeds del equipo + calculos + agro-service + api-gateway + frontend. Verificado el 14-nov con Java 17 (Temurin portable), 32 pruebas de Java, 105 de `calculos` y `npm run build`.
    Se encontró que el PostgreSQL de `pgserver` para Windows no trae zonas horarias (la API Java fallaba con `invalid value for parameter "TimeZone"`); el script lo arregla.

## D. References / documentos de entrega (de `python -m etl.verificar_enlaces`)

- ❌ El enlace de **SENASA** del PDF *References* da **404**. La versión correcta lleva guion: `.../nino-costero-cuantas-hectareas-se-han-perdido-por-efecto-del-evento-climatico/`
  (al copiar desde un PDF se pierde el guion de fin de línea). Corregir en el formulario.
- ⚠️ `https://modis.gsfc.nasa.gov/` no respondió desde esta PC. Alternativa que sí abre: `https://www.earthdata.nasa.gov/data/catalog/lpcloud-mod13q1-061`.
- ⚠️ Canva devuelve 403 a los robots: revisar a mano.
- ➕ Agregar a *References*: `GPM_3IMERGDL`, el CMR (para las versiones) y, si se usa, el ONI de NOAA.
- 📌 Versiones exactas de cada dataset (SMAP SPL3SMP_E **v006**, MOD13Q1 **v061**, MUR **v4.1**, IMERG **V07**) en `data/backup/versiones_datasets.json`.
