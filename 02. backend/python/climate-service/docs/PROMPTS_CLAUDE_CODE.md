# Prompts para Claude Code (David · Python + datos NASA)

**Cómo usarlos:** abre VS Code en `D:\NASA SPACE APPS\AgroShift`, abre una terminal en
`02. backend\python\climate-service`, activa el entorno (`.venv\Scripts\Activate.ps1`) y escribe `claude`.
Claude Code lee solo el archivo `CLAUDE.md` de esta carpeta (reglas del contrato, comandos y estado). Pega **un prompt a la vez**,
espera el resultado, **lee lo que cambió** (`git diff`) y corre `pytest` antes de seguir.

> Todo lo que genere una IA debe ser **revisado y validado por ti** (lo declaramos en *Use of AI*). Si no entiendes un cambio, pídele que lo explique.
> Pídele siempre: *“no cambies campos del contrato”*, *“agrega pruebas”* y *“no imprimas ni guardes tokens”*.

---

## 0 · Arranque de sesión
```text
Lee CLAUDE.md y docs/DECISIONES_ABIERTAS.md. Corre pytest y dime en 5 líneas el estado del servicio, qué está probado,
qué no, y cuál es el siguiente paso de mayor valor para la demo. No cambies código todavía.
```

## 1 · Integrar el catálogo real de Alejandro (cuando lo entregue)
```text
Alejandro entregó el catálogo de cultivos en data/crops/ (JSON). Valida que cargar_catalogo() lo lee sin errores y que
cumple los campos de la tabla `cultivos` del contrato (id, nombre, tempMinC, tempMaxC, aguaNecesaria baja|media|alta,
mesesSiembra, mesesCosecha, accionesPorEtapa). Lista cualquier cultivo con datos raros (temperaturas invertidas, meses
fuera de 1-12, agua mal escrita). Luego corre `python -m etl.build_backup --catalogo <ruta>` y muéstrame, para Bajo Piura,
las 3 rotaciones de hoy y de marzo 2017. No cambies el contrato.
```

## 2 · Calibrar el modelo con datos (umbrales, tendencias, incertidumbre)
```text
Con NASA POWER (etl/nasa_power.py, serie mensual 1981-hoy) para las 7 zonas de Piura:
1) Calcula la distribución de anomalías mensuales de lluvia y temperatura y compárala con los umbrales de app/thresholds.py
   (medio/alto). Propón ajustes basados en percentiles (p. ej. medio ≈ p75, alto ≈ p90) y muéstrame la tabla antes de tocar nada.
2) Añade tendencia con Mann-Kendall + pendiente de Sen (pymannkendall) para lluvia y temperatura, por zona.
3) Añade una medida de INCERTIDUMBRE por indicador: variabilidad entre años (desviación estándar) y, cuando haya,
   diferencia entre fuentes (POWER vs IMERG).
Cada cambio con su prueba en tests/. Sin cambiar los campos del contrato: lo extra va como campos opcionales y lo anotas en docs/DECISIONES_ABIERTAS.md.
```

## 3 · Descargar SMAP e IMERG con el token de Earthdata (necesita `.env` con `EARTHDATA_TOKEN`)
```text
Ya tengo EARTHDATA_TOKEN en .env. Revisa etl/earthdata_download.py (marcado NO PROBADO) y haz que funcione de verdad:
- GPM_3IMERGDL v07 (dato reciente, ~25 MB/día) y GPM_3IMERGDF v07 (2017, para la validación) en el punto de Bajo Piura.
- Extraer el valor del píxel más cercano con xarray; abre un archivo real para confirmar nombres de variables/grupos.
- NO bajar SMAP día completo (~630 MB): para SMAP usa el prompt 4 (AppEEARS).
Guarda las descargas en data/raw/ (ignorado por git) y los valores en data/backup/. Compara IMERG contra POWER (PRECTOTCORR)
del mismo día y dime la diferencia. Nunca imprimas el token.
```

## 4 · SMAP y NDVI por zona con AppEEARS
```text
Usa etl/appeears.py (NO PROBADO; necesita EARTHDATA_USERNAME/PASSWORD en .env) para pedir, para las 7 zonas de Piura
(etl/zonas.py), SMAP SPL3SMP_E.006 (humedad del suelo, AM) de 2016-11-01 a hoy y MOD13Q1.061 NDVI de 2016-11-01 a 2017-07-31.
Verifica primero los nombres de capa con GET /product/<id>. Espera la tarea, baja el CSV, y guarda en data/backup/ un
JSON pequeño por zona. Después calcula la anomalía de SMAP contra su propia climatología (2015-2025) y conéctala a
etl/inputs.py para que `humedadSuelo` use SMAP real (fuente "SMAP") en vez de GWETTOP de POWER.
```

## 5 · Señal de El Niño (temperatura del mar)
```text
etl/mur_sst.py no pudo conectar a los ERDDAP de NOAA desde mi PC. Haz funcionar la señal de El Niño de una de estas formas
(en este orden): (1) reintentar los ERDDAP; (2) MUR SST v4.1 desde PO.DAAC usando mi token (earthaccess), extrayendo solo
el punto (-5.5, -81.5) y un punto costero cercano a Paita; (3) una serie manual en CSV (fecha,anomaliaC) que build_backup.py
ya acepta con --sst-csv. Calcula la anomalía contra 2003-2022 del mismo día del año, y compárala con el ONI y con el ICEN de ENFEN
(busca los valores oficiales; no los inventes). Explica por qué dio +9 °C en el dataset anom1day. Agrega pruebas.
```

## 6 · Validación del Niño costero 2017 (diapositiva de Impacto)
```text
Con data/backup/validacion_2017.json y el NDVI de MODIS de 2017, prepara la evidencia para la diapositiva de Impacto:
1) Una figura (matplotlib, PNG 1600x900, fondo oscuro verde #0E1E14, textos en inglés y colores verde #78CD6E / oro #E8B740) con
   la línea de tiempo ene-jun 2017 de Bajo Piura: lluvia vs normal, nivel del indicador (verde/ámbar/rojo) y NDVI.
2) Una tabla: fecha en que AgroShift habría dado la primera alerta ALTA vs fecha en que cae el NDVI (caída %).
3) Un párrafo en español y otro en inglés (máx. 60 palabras) con el resultado. Solo con datos reales; si algo no está disponible, dilo.
Guarda en docs/img/validacion_2017.png (si no existe, créalo) y el texto en docs/validacion_2017.md.
```

## 7 · Perspectiva de la campaña (ciclo completo) y cultivos permanentes — *primero acordar con Jhonny y Sheila*
```text
Lee la propuesta del doc "01. documentacion/23_propuestas_equipo_y_ramas.md". Diseña (sin implementar aún) un endpoint opcional
POST /campana que, dado el catálogo y la fecha de siembra, devuelva para cada mes del ciclo (siembra→cosecha) el nivel de
riesgo (bajo/medio/alto) y el indicador que lo causa; y para los cultivos permanentes (tipo = permanente) una lista de ACCIONES
en lugar de una rotación. Entrégame el JSON de ejemplo y las preguntas abiertas para Sheila y Jhonny. Cuando lo aprueben,
impleméntalo con pruebas, sin modificar los endpoints del contrato.
```

## 8 · Beneficios de la rotación (lo que pide el reto)
```text
El reto pide mostrar beneficios y sacrificios de cada rotación (fijación de nitrógeno, raíz profunda, cobertura, erosión,
demanda de agua, mercado) y dónde faltan datos. Propón campos opcionales para el catálogo (para Alejandro), súmalos al
puntaje como BONIFICACIONES verificables en app/thresholds.py (con tope) y añade a cada rotación una lista "beneficios",
"sacrificios" y "vaciosDeInformacion" como campos opcionales de la respuesta. Que la explicación diga de dónde sale cada punto.
Con pruebas y sin romper el contrato.
```

## 9 · Datos de respaldo en PostgreSQL (con Jhonny)
```text
Lee docs/BASE_DE_DATOS.md y data/backup/datos_nasa_respaldo.csv. Escribe un script SQL (DDL + COPY) que cargue ese CSV en la
tabla `datosNasa` del contrato (id, lat, lon, fecha, fuente, variable, valor), con índices por (lat, lon, fecha). Pruébalo contra
un PostgreSQL local temporal si hay Docker o psql; si no, solo valida la sintaxis y dime qué falta. Déjalo en
"04. base de datos/ddl/seed/" solo si Jhonny está de acuerdo; si no, déjalo en docs/.
```

## 10 · Tabla de datasets NASA (campo *Use of AI / NASA Data*) y References
```text
Con data/backup/versiones_datasets.json y data/backup/enlaces_verificados.json genera docs/tabla_datasets_nasa_en.md EN INGLÉS para
Edwin: una tabla (dataset, versión exacta, variables usadas, cómo contribuye a la solución, cómo lo obtuvimos, enlace) para
POWER, SMAP, GPM IMERG (DL y DF), MODIS MOD13Q1, MUR SST. Marca cuáles ya usa el código hoy y cuáles son "planned" (no mentir).
Añade al final los enlaces rotos o a revisar. No inventes datos.
```

## 11 · Contrato con Java (probar de punta a punta)
```text
Levanta el servicio (uvicorn, puerto 8000) y prueba con curl.exe los 4 endpoints usando samples/. Genera docs/openapi.json
(el de FastAPI) y un ejemplo de cuerpo para POST /recomendacion que Jhonny pueda copiar a su cliente Java (RestClient/WebClient).
Comprueba los casos de error: JSON inválido (422), cultivo inexistente (422), servicio apagado. Dime qué debe hacer Java ante cada uno
(Plan B del contrato: usar los cálculos guardados en la base de datos).
```

## 12 · Despliegue (Dockerfile del servicio)
```text
Revisa el Dockerfile de esta carpeta (NO PROBADO: no hay Docker en mi PC). Asegura imagen mínima con solo requirements.txt,
usuario no root, HEALTHCHECK a /salud, y puerto 8000. Escribe el bloque de docker-compose para deploy/vps/ (servicio `climate-service`)
y pásamelo como texto para Jhonny, sin tocar deploy/vps/ ni .env.
```

## 13 · Revisión final antes del Submit (domingo 15:00)
```text
Haz una revisión final de mi rama: (1) busca secretos (tokens, claves, .env) en todo el historial de git con `git log -p`;
(2) corre pytest, pytest -m live y ruff; (3) confirma que data/raw/ no está en git y que el repo es público sin datos pesados;
(4) verifica que README, docs y comentarios no afirmen nada que el código no haga (SMAP, IMERG, SST: ¿están realmente conectados?);
(5) lista lo que quedó "NO PROBADO". Dame un informe corto con severidades.
```

## 14 · Git y Pull Request
```text
Muestra git status y git diff --stat. Agrupa los cambios en commits pequeños con mensajes en español
(feat/fix/data/docs(alcance): ...). No hagas push ni PR todavía: espera mi confirmación.
```
